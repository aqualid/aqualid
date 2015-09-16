#
# Copyright (c) 2012-2015 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
#  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import io
import os
import re
import imp
import sys
import time
import types
import errno
import marshal
import hashlib
import inspect
import tempfile
import traceback
import threading
import subprocess
import multiprocessing


from aql.util_types import u_str, is_string, cast_str, is_unicode, to_unicode,\
    decode_bytes, encode_str, UniqueList, to_sequence, is_sequence, \
    SIMPLE_TYPES_SET

__all__ = (
    'open_file', 'read_bin_file', 'read_text_file', 'write_bin_file',
    'write_text_file',
    'exec_file', 'remove_files', 'new_hash', 'dump_simple_object',
    'simple_object_signature', 'data_signature',
    'file_signature', 'file_time_signature', 'file_checksum',
    'load_module', 'load_package',
    'get_function_name', 'print_stacks',
    'equal_function_args', 'check_function_args', 'get_function_args',
    'execute_command', 'ExecCommandResult', 'get_shell_script_env',
    'cpu_count', 'memory_usage',
    'flatten_list', 'simplify_value',
    'Chrono', 'ItemsGroups', 'group_items'
)

# ==============================================================================

# noinspection PyUnusedLocal


class ErrorInvalidExecCommand(Exception):

    def __init__(self, arg):
        msg = "Invalid type of command argument: %s(%s)" % (arg, type(arg))
        super(ErrorInvalidExecCommand, self).__init__(msg)

# ==============================================================================


class ErrorFileName(Exception):

    def __init__(self, filename):
        msg = "Invalid file name: %s(%s)" % (filename, type(filename))
        super(ErrorFileName, self).__init__(msg)

# ==============================================================================


class ErrorUnmarshallableObject(Exception):

    def __init__(self, obj):
        msg = "Unmarshallable object: '%s'" % (obj, )
        super(ErrorUnmarshallableObject, self).__init__(msg)

# ==============================================================================

if hasattr(os, 'O_NOINHERIT'):
    _O_NOINHERIT = os.O_NOINHERIT
else:
    _O_NOINHERIT = 0

if hasattr(os, 'O_SYNC'):
    _O_SYNC = os.O_SYNC
else:
    _O_SYNC = 0

if hasattr(os, 'O_BINARY'):
    _O_BINARY = os.O_BINARY
else:
    _O_BINARY = 0

# -------------------------------------------------------------------------------


def open_file(filename,
              read=True,
              write=False,
              binary=False,
              sync=False,
              encoding=None):

    if not is_string(filename):
        raise ErrorFileName(filename)

    flags = _O_NOINHERIT | _O_BINARY
    mode = 'r'

    if not write:
        flags |= os.O_RDONLY
        sync = False
    else:
        flags |= os.O_CREAT
        mode += '+'

        if read:
            flags |= os.O_RDWR
        else:
            flags |= os.O_WRONLY

        if sync:
            flags |= _O_SYNC

    if binary:
        mode += 'b'

    fd = os.open(filename, flags)
    try:
        if sync:
            # noinspection PyTypeChecker
            return io.open(fd, mode, 0, encoding=encoding)
        else:
            # noinspection PyTypeChecker
            return io.open(fd, mode, encoding=encoding)
    except:
        os.close(fd)
        raise

# ==============================================================================


def read_text_file(filename, encoding='utf-8'):
    with open_file(filename, encoding=encoding) as f:
        return f.read()


def read_bin_file(filename):
    with open_file(filename, binary=True) as f:
        return f.read()


def write_text_file(filename, data, encoding='utf-8'):
    with open_file(filename, write=True, encoding=encoding) as f:
        f.truncate()
        if isinstance(data, (bytearray, bytes)):
            data = decode_bytes(data, encoding)
        f.write(data)


def write_bin_file(filename, data, encoding=None):
    with open_file(filename, write=True, binary=True, encoding=encoding) as f:
        f.truncate()
        if is_unicode(data):
            data = encode_str(data, encoding)

        f.write(data)

# ==============================================================================


def exec_file(filename, file_locals):

    if not file_locals:
        file_locals = {}

    source = read_text_file(filename)
    code = compile(source, filename, 'exec')
    file_locals_orig = file_locals.copy()

    exec(code, file_locals)

    result = {}
    for key, value in file_locals.items():
        if key.startswith('_') or isinstance(value, types.ModuleType):
            continue

        if key not in file_locals_orig:
            result[key] = value

    return result

# ==============================================================================


def dump_simple_object(obj):

    if isinstance(obj, (bytes, bytearray)):
        data = obj

    elif isinstance(obj, u_str):
        data = obj.encode('utf-8')

    else:
        try:
            data = marshal.dumps(obj, 0)  # use version 0, for a raw dump
        except ValueError:
            raise ErrorUnmarshallableObject(obj)

    return data

# ==============================================================================


def simple_object_signature(obj, common_hash=None):
    data = dump_simple_object(obj)
    return data_signature(data, common_hash)

# ==============================================================================


def new_hash(data=b''):
    return hashlib.md5(data)

# ==============================================================================


def data_signature(data, common_hash=None):
    if common_hash is None:
        obj_hash = hashlib.md5(data)
    else:
        obj_hash = common_hash.copy()
        obj_hash.update(data)

    return obj_hash.digest()

# ==============================================================================


def file_signature(filename, offset=0):

    checksum = hashlib.md5()
    chunk_size = checksum.block_size * 4096

    with open_file(filename, binary=True) as f:
        f.seek(offset)

        read = f.read
        checksum_update = checksum.update

        chunk = True

        while chunk:
            chunk = read(chunk_size)
            checksum_update(chunk)

    # print("file_signature: %s: %s" % (filename, checksum.hexdigest()) )
    return checksum.digest()

# ==============================================================================


def file_time_signature(filename):
    stat = os.stat(filename)
    # print("file_time_signature: %s: %s" %
    #                           (filename, (stat.st_size, stat.st_mtime)) )
    return simple_object_signature((stat.st_size, stat.st_mtime))

# ==============================================================================


def file_checksum(filename, offset=0, size=-1, alg='md5', chunk_size=262144):

    checksum = hashlib.__dict__[alg]()

    with open_file(filename, binary=True) as f:
        read = f.read
        f.seek(offset)
        checksum_update = checksum.update

        chunk = True

        while chunk:
            chunk = read(chunk_size)
            checksum_update(chunk)

            if size > 0:
                size -= len(chunk)
                if size <= 0:
                    break

            checksum_update(chunk)

    return checksum

# ==============================================================================


def get_function_name(currentframe=inspect.currentframe):

    frame = currentframe()
    if frame:
        return frame.f_back.f_code.co_name

    return "__not_available__"

# ==============================================================================


def print_stacks():
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])

    # noinspection PyProtectedMember
    for thread_id, stack in sys._current_frames().items():
        print("\n" + ("=" * 64))
        print("Thread: %s (%s)" % (id2name.get(thread_id, ""), thread_id))
        traceback.print_stack(stack)


# ==============================================================================

try:
    # noinspection PyUnresolvedReferences
    _getargspec = inspect.getfullargspec
except AttributeError:
    _getargspec = inspect.getargspec

# ==============================================================================


def get_function_args(function, getargspec=_getargspec):

    args = getargspec(function)[:4]

    if isinstance(function, types.MethodType):
        if function.__self__:
            args = tuple([args[0][1:]] + list(args[1:]))

    return args

# ==============================================================================


def equal_function_args(function1, function2):
    if function1 is function2:
        return True

    args1 = get_function_args(function1)
    args2 = get_function_args(function2)

    return args1[0:3] == args2[0:3]

# ==============================================================================


def check_function_args(function, args, kw, getargspec=_getargspec):

    f_args, f_varargs, f_varkw, f_defaults = getargspec(function)[:4]

    current_args_num = len(args) + len(kw)

    args_num = len(f_args)

    if not f_varargs and not f_varkw:
        if current_args_num > args_num:
            return False

    if f_defaults:
        def_args_num = len(f_defaults)
    else:
        def_args_num = 0

    min_args_num = args_num - def_args_num
    if current_args_num < min_args_num:
        return False

    kw = set(kw)
    unknown_args = kw - set(f_args)

    if unknown_args and not f_varkw:
        return False

    def_args = f_args[args_num - def_args_num:]
    non_def_kw = kw - set(def_args)

    non_def_args_num = len(args) + len(non_def_kw)
    if non_def_args_num < min_args_num:
        return False

    twice_args = set(f_args[:len(args)]) & kw
    if twice_args:
        return False

    return True

# ==============================================================================


def remove_files(files):

    for f in to_sequence(files):
        try:
            os.remove(f)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise

# ==============================================================================


def _decode_data(data):
    if not data:
        return str()

    data = to_unicode(data)

    data = data.replace('\r\n', '\n')
    data = data.replace('\r', '\n')

    return data

# ==============================================================================


class ExecCommandException(Exception):
    __slots__ = ('exception',)

    def __init__(self, cmd, exception):

        msg = ' '.join(to_sequence(cmd))
        msg += '\n%s' % (exception,)

        self.exception = exception

        super(ExecCommandException, self).__init__(msg)

    @staticmethod
    def failed():
        return True

    def __bool__(self):
        return self.failed()

    def __nonzero__(self):
        return self.failed()


class ExecCommandResult(Exception):
    __slots__ = ('cmd', 'status', 'stdout', 'stderr')

    def __init__(self, cmd, status=None, stdout=None, stderr=None):

        self.cmd = tuple(to_sequence(cmd))
        self.status = status

        self.stdout = stdout if stdout else ''
        self.stderr = stderr if stderr else ''

        super(ExecCommandResult, self).__init__()

    # -----------------------------------------------------------

    def __str__(self):
        msg = ' '.join(self.cmd)

        out = self.output()
        if out:
            msg += '\n' + out

        if self.status:
            msg += "\nExit status: %s" % (self.status,)

        return msg

    # -----------------------------------------------------------

    def failed(self):
        return self.status != 0

    # -----------------------------------------------------------

    def output(self):
        out = self.stdout
        if self.stderr:
            if out:
                out += '\n'
                out += self.stderr
            else:
                out = self.stderr

        return out

    def __bool__(self):
        return self.failed()

    def __nonzero__(self):
        return self.failed()


# ==============================================================================

try:
    _MAX_CMD_LENGTH = os.sysconf('SC_ARG_MAX')
except AttributeError:
    _MAX_CMD_LENGTH = 32000  # 32768 default for Windows


def _gen_exec_cmd_file(cmd, file_flag, max_cmd_length=_MAX_CMD_LENGTH):
    if not file_flag:
        return cmd, None

    cmd_length = sum(map(len, cmd)) + len(cmd) - 1
    if cmd_length <= max_cmd_length:
        return cmd, None

    cmd_str = subprocess.list2cmdline(cmd[1:]).replace('\\', '\\\\')

    cmd_file = tempfile.NamedTemporaryFile(mode='w+',
                                           suffix='.args',
                                           delete=False)

    with cmd_file:
        cmd_file.write(cmd_str)

    cmd_file = cmd_file.name

    cmd = [cmd[0], file_flag + cmd_file]
    return cmd, cmd_file

# ==============================================================================


def _exec_command_result(cmd, cwd, env, shell, stdin):
    try:
        if env:
            env = dict((cast_str(key), cast_str(value))
                       for key, value in env.items())

        p = subprocess.Popen(cmd, cwd=cwd, env=env,
                             shell=shell,
                             stdin=stdin, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=False)

        stdout, stderr = p.communicate()
        returncode = p.poll()

    except Exception as ex:
        raise ExecCommandException(cmd, exception=ex)

    stdout = _decode_data(stdout)
    stderr = _decode_data(stderr)

    return ExecCommandResult(cmd, status=returncode,
                             stdout=stdout, stderr=stderr)

# ==============================================================================


def execute_command(cmd, cwd=None, env=None, stdin=None, file_flag=None):

    if is_string(cmd):
        shell = True
        cmd_file = None
    else:
        shell = False
        cmd, cmd_file = _gen_exec_cmd_file(cmd, file_flag)

    try:
        return _exec_command_result(cmd, cwd, env, shell, stdin)
    finally:
        if cmd_file:
            remove_files(cmd_file)

# ==============================================================================


def get_shell_script_env(script, args=None, _var_re=re.compile(r'^\w+=')):

    args = to_sequence(args)

    script_path = os.path.abspath(
        os.path.expanduser(os.path.expandvars(script)))

    os_env = os.environ

    cwd, script = os.path.split(script_path)

    if os.name == "nt":
        cmd = ['call', script]
        cmd += args
        cmd += ['&&', 'set']

    else:
        cmd = ['.', './' + script]
        cmd += args
        cmd += ['&&', 'printenv']
        cmd = ' '.join(cmd)

    try:
        p = subprocess.Popen(cmd, cwd=cwd, shell=True, env=os_env,
                             stdin=None, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, universal_newlines=False)

        stdout, stderr = p.communicate()
        status = p.poll()

    except Exception as ex:
        raise ExecCommandException(cmd, exception=ex)

    stdout = _decode_data(stdout)
    stderr = _decode_data(stderr)

    if status != 0:
        raise ExecCommandResult(cmd, status, stdout, stderr)

    script_env = {}

    for line in stdout.split('\n'):
        match = _var_re.match(line)

        if match:
            name, sep, value = line.partition('=')
            value = value.strip()

            current = os_env.get(name, None)
            if (current is None) or (value != current.strip()):
                script_env[name] = value

    return script_env

# ==============================================================================


def cpu_count():

    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        pass

    count = int(os.environ.get('NUMBER_OF_PROCESSORS', 0))
    if count > 0:
        return count

    try:
        if 'SC_NPROCESSORS_ONLN' in os.sysconf_names:
            count = os.sysconf('SC_NPROCESSORS_ONLN')
        elif 'SC_NPROCESSORS_CONF' in os.sysconf_names:
            count = os.sysconf('SC_NPROCESSORS_CONF')
        if count > 0:
            return cpu_count

    except AttributeError:
        pass

    count = 1  # unable to detect number of CPUs

    return count

# ==============================================================================


def _memory_usage_smaps():
    private = 0

    with open("/proc/self/smaps") as smaps:
        for line in smaps:
            if line.startswith("Private"):
                private += int(line.split()[1])

    return private

# ==============================================================================


def _memory_usage_statm():
    page_size = os.sysconf("SC_PAGE_SIZE")

    with open('/proc/self/statm') as f:
        mem_stat = f.readline().split()
        rss = int(mem_stat[1]) * page_size
        shared = int(mem_stat[2]) * page_size

        private = rss - shared

    return private // 1024

# ==============================================================================


def memory_usage_linux():
    try:
        return _memory_usage_smaps()
    except IOError:
        try:
            return _memory_usage_statm()
        except IOError:
            return memory_usage_unix()

# ==============================================================================


def memory_usage_unix():
    res = resource.getrusage(resource.RUSAGE_SELF)
    return res.ru_maxrss

# ==============================================================================


def memory_usage_windows():
    process_handle = win32api.GetCurrentProcess()
    memory_info = win32process.GetProcessMemoryInfo(process_handle)
    return memory_info['PeakWorkingSetSize']

try:
    import resource

    if sys.platform[:5] == "linux":
        memory_usage = memory_usage_linux
    else:
        memory_usage = memory_usage_unix

except ImportError:
    try:
        import win32process
        import win32api

        memory_usage = memory_usage_windows

    except ImportError:
        def memory_usage():
            return 0

# ==============================================================================


def load_module(module_file, package_name=None):

    module_dir, module_file = os.path.split(module_file)

    module_name = os.path.splitext(module_file)[0]

    if package_name:
        full_module_name = package_name + '.' + module_name
    else:
        full_module_name = module_name

    module = sys.modules.get(full_module_name)
    if module is not None:
        return module

    fp, pathname, description = imp.find_module(module_name, [module_dir])

    module = imp.load_module(full_module_name, fp, pathname, description)
    return module

# ==============================================================================


def load_package(path, name=None, generate_name=False):
    find_path, find_name = os.path.split(path)

    if not name:
        if generate_name:
            name = new_hash(dump_simple_object(path)).hexdigest()
        else:
            name = find_name

    package = sys.modules.get(name)
    if package is not None:
        return package

    fp, pathname, description = imp.find_module(find_name, [find_path])

    package = imp.load_module(name, fp, pathname, description)
    return package

# ==============================================================================


def flatten_list(seq):

    out_list = list(to_sequence(seq))

    i = 0

    while i < len(out_list):

        value = out_list[i]

        if is_sequence(value):
            if value:
                out_list[i: i + 1] = value
            else:
                del out_list[i]

            continue

        i += 1

    return out_list

# ==============================================================================

_SIMPLE_SEQUENCES = (list, tuple, UniqueList, set, frozenset)


def simplify_value(value,
                   simple_types=SIMPLE_TYPES_SET,
                   simple_lists=_SIMPLE_SEQUENCES):

    if value is None:
        return None

    value_type = type(value)

    if value_type in simple_types:
        return value

    for simple_type in simple_types:
        if isinstance(value, simple_type):
            return simple_type(value)

    if isinstance(value, simple_lists):
        return [simplify_value(v) for v in value]

    if isinstance(value, dict):
        return dict((key, simplify_value(v)) for key, v in value.items())

    try:
        return simplify_value(value.get())
    except Exception:
        pass

    return value

# ==============================================================================


class Chrono (object):
    __slots__ = ('elapsed', )

    def __init__(self):
        self.elapsed = 0

    def __enter__(self):
        self.elapsed = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.elapsed

        return False

    def get(self):
        return self.elapsed

    def __str__(self):
        elapsed = self.elapsed

        minutes = int(elapsed / 60)
        seconds = int(elapsed - minutes * 60)
        milisecs = int((elapsed - int(elapsed)) * 1000)

        result = []
        if minutes:
            result.append("%s min" % minutes)
            milisecs = 0

        if seconds:
            result.append("%s sec" % seconds)
        if milisecs:
            result.append("%s ms" % milisecs)

        if not minutes and not seconds and not milisecs:
            result.append("0 ms")

        return ' '.join(result)

# ==============================================================================


class ItemsGroups(object):
    __slots__ = (
        'wish_groups',
        'max_group_size',
        'group_size',
        'tail_size',
        'groups',
    )

    def __init__(self, size, wish_groups, max_group_size):
        wish_groups = max(1, wish_groups)

        group_size = size // wish_groups

        if max_group_size < 0:
            max_group_size = size
        elif max_group_size == 0:
            max_group_size = group_size + 1

        group_size = max(1, group_size)

        self.wish_groups = wish_groups
        self.group_size = min(max_group_size, group_size)
        self.max_group_size = max_group_size
        self.tail_size = size
        self.groups = [[]]

    # -----------------------------------------------------------

    def add_group(self):

        groups = self.groups
        if not groups[0]:
            return

        group_size = max(
            1, self.tail_size // max(1, self.wish_groups - len(self.groups)))
        self.group_size = min(self.max_group_size, group_size)

        group_files = []
        self.groups.append(group_files)
        return group_files

    # -----------------------------------------------------------

    def add(self, item):
        group_files = self.groups[-1]
        if len(group_files) >= self.group_size:
            group_files = self.add_group()

        group_files.append(item)
        self.tail_size -= 1

    # -----------------------------------------------------------

    def get(self):
        groups = self.groups
        if not groups[-1]:
            del groups[-1]

        return groups

# ==============================================================================


def group_items(items, wish_groups=1, max_group_size=-1):

    groups = ItemsGroups(len(items), wish_groups, max_group_size)
    for item in items:
        groups.add(item)

    return groups.get()
