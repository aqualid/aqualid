
import sys
import io
import os
import os.path
import shutil
import zipfile
import tarfile
import itertools

from aql.util_types import is_unicode, encode_str, decode_bytes,\
    is_string, to_sequence
from aql.utils import open_file
from aql.entity import FileEntityBase
from aql.nodes import Builder, FileBuilder
from .aql_tools import Tool

__all__ = (
    "BuiltinTool",
)


class ErrorDistCommandInvalid(Exception):

    def __init__(self, command):
        msg = "distutils command '%s' is not supported" % (command,)
        super(ErrorDistCommandInvalid, self).__init__(msg)

# ==============================================================================


def _get_method_full_name(m):
    full_name = []
    mod = getattr(m, '__module__', None)
    if mod:
        full_name.append(mod)

    name = getattr(m, '__qualname__', None)
    if name:
        full_name.append(name)
    else:
        cls = getattr(m, 'im_class', None)
        if cls is not None:
            cls_name = getattr(cls, '__name__', None)
            if cls_name:
                full_name.append(cls_name)

        name = getattr(m, '__name__', None)
        if name:
            full_name.append(name)

    return '.'.join(full_name)

# ==============================================================================


class ExecuteCommandBuilder (Builder):

    NAME_ATTRS = ('targets', 'cwd')

    def __init__(self, options, target=None, target_flag=None, cwd=None):

        self.targets = [
            self.get_target_file_path(target) for target in to_sequence(target)]
        self.target_flag = target_flag

        if cwd:
            cwd = self.get_target_dir_path(cwd)

        self.cwd = cwd

    # -----------------------------------------------------------

    def _get_cmd_targets(self):

        targets = self.targets

        prefix = self.target_flag
        if not prefix:
            return tuple(targets)

        prefix = prefix.lstrip()

        if not prefix:
            return tuple(targets)

        rprefix = prefix.rstrip()

        if prefix != rprefix:
            return tuple(itertools.chain(*((rprefix, target)
                                           for target in targets)))

        return tuple("%s%s" % (prefix, target) for target in targets)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        cmd = tuple(src.get() for src in source_entities)

        cmd_targets = self._get_cmd_targets()
        if cmd_targets:
            cmd += cmd_targets

        out = self.exec_cmd(cmd, cwd=self.cwd)

        targets.add_files(self.targets)

        return out

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.targets

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        try:
            return source_entities[0]
        except Exception:
            return self.__class__.__name__

    # -----------------------------------------------------------

    def get_trace_sources(self, source_entities, brief):
        return source_entities[1:]

# ==============================================================================


class ExecuteMethodBuilder (Builder):

    NAME_ATTRS = ('method_name',)
    SIGNATURE_ATTRS = ('args', 'kw')

    def __init__(self,
                 options,
                 method,
                 args,
                 kw,
                 single,
                 make_files,
                 clear_targets):

        self.method_name = _get_method_full_name(method)
        self.method = method
        self.args = args if args else []
        self.kw = kw if kw else {}

        if not clear_targets:
            self.clear = lambda target_entities, side_effect_entities: None

        if single:
            self.split = self.split_single

        if make_files:
            self.make_entity = self.make_file_entity

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        return self.method(self, source_entities, targets,
                           *self.args, **self.kw)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        name = self.method_name

        if not brief:
            args = ''
            if self.args:
                args = ','.join(self.args)

            if self.kw:
                if args:
                    args += ','
                args += ','.join("%s=%s" % (k, v) for k, v in self.kw.items())

            if args:
                return "%s(%s)" % (name, args)

        return name

# ==============================================================================


class CopyFilesBuilder (FileBuilder):

    NAME_ATTRS = ['target']

    def __init__(self, options, target):
        self.target = self.get_target_dir_path(target)
        self.split = self.split_batch

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):
        target = self.target

        for src_entity in source_entities:
            src = src_entity.get()

            dst = os.path.join(target, os.path.basename(src))
            shutil.copyfile(src, dst)
            shutil.copymode(src, dst)

            targets[src_entity].add(dst)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Copy files"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        src = source_entities[0].get()
        return os.path.join(self.target, os.path.basename(src)),

# ==============================================================================


class CopyFileAsBuilder (FileBuilder):

    NAME_ATTRS = ['target']

    def __init__(self, options, target):
        self.target = self.get_target_file_path(target)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        source = source_entities[0].get()
        target = self.target

        shutil.copyfile(source, target)
        shutil.copymode(source, target)

        targets.add(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Copy file"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target

# ==============================================================================


class TarFilesBuilder (FileBuilder):

    NAME_ATTRS = ['target']
    SIGNATURE_ATTRS = ['rename', 'basedir']

    def __init__(self, options, target, mode, rename, basedir, ext):

        if not mode:
            mode = "w:bz2"

        if not ext:
            if mode == "w:bz2":
                ext = ".tar.bz2"
            elif mode == "w:gz":
                ext = ".tar.gz"
            elif mode == "w":
                ext = ".tar"

        self.target = self.get_target_file_path(target, ext)
        self.mode = mode
        self.rename = rename if rename else tuple()
        self.basedir = os.path.normcase(
            os.path.normpath(basedir)) if basedir else None

    # -----------------------------------------------------------

    def __get_arcname(self, file_path):
        for arc_name, path in self.rename:
            if file_path == path:
                return arc_name

        basedir = self.basedir
        if basedir:
            if file_path.startswith(basedir):
                return file_path[len(basedir):]

        return os.path.basename(file_path)

    # -----------------------------------------------------------

    def __add_file(self, arch, filepath):
        arcname = self.__get_arcname(filepath)
        arch.add(filepath, arcname)

    # -----------------------------------------------------------

    @staticmethod
    def __add_entity(arch, entity):
        arcname = entity.name
        data = entity.get()
        if is_unicode(data):
            data = encode_str(data)

        tinfo = tarfile.TarInfo(arcname)
        tinfo.size = len(data)
        arch.addfile(tinfo, io.BytesIO(data))

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target = self.target

        arch = tarfile.open(name=self.target, mode=self.mode)
        try:
            for entity in source_entities:
                if isinstance(entity, FileEntityBase):
                    self.__add_file(arch, entity.get())
                else:
                    self.__add_entity(arch, entity)

        finally:
            arch.close()

        targets.add(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Create Tar"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target

# ==============================================================================


class ZipFilesBuilder (FileBuilder):

    NAME_ATTRS = ['target']
    SIGNATURE_ATTRS = ['rename', 'basedir']

    def __init__(self, options, target, rename, basedir, ext):

        if ext is None:
            ext = ".zip"

        self.target = self.get_target_file_path(target, ext=ext)
        self.rename = rename if rename else tuple()
        self.basedir = os.path.normcase(
            os.path.normpath(basedir)) if basedir else None

    # -----------------------------------------------------------

    def __open_arch(self, large=False):
        try:
            return zipfile.ZipFile(self.target,
                                   "w",
                                   zipfile.ZIP_DEFLATED,
                                   large)
        except RuntimeError:
            pass

        return zipfile.ZipFile(self.target, "w", zipfile.ZIP_STORED, large)

    # -----------------------------------------------------------

    def __get_arcname(self, file_path):
        for arc_name, path in self.rename:
            if file_path == path:
                return arc_name

        basedir = self.basedir
        if basedir:
            if file_path.startswith(basedir):
                return file_path[len(basedir):]

        return os.path.basename(file_path)

    # -----------------------------------------------------------

    def __add_files(self, arch, source_entities):
        for entity in source_entities:
            if isinstance(entity, FileEntityBase):
                filepath = entity.get()
                arcname = self.__get_arcname(filepath)
                arch.write(filepath, arcname)
            else:
                arcname = entity.name
                data = entity.get()
                if is_unicode(data):
                    data = encode_str(data)

                arch.writestr(arcname, data)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target = self.target

        arch = self.__open_arch()

        try:
            self.__add_files(arch, source_entities)
        except zipfile.LargeZipFile:
            arch.close()
            arch = None
            arch = self.__open_arch(large=True)

            self.__add_files(arch, source_entities)
        finally:
            if arch is not None:
                arch.close()

        targets.add(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Create Zip"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target

# ==============================================================================


class WriteFileBuilder (Builder):

    NAME_ATTRS = ['target']

    def __init__(self, options, target, binary=False, encoding=None):
        self.binary = binary
        self.encoding = encoding
        self.target = self.get_target_file_path(target)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target = self.target

        with open_file(target,
                      write=True,
                      binary=self.binary,
                      encoding=self.encoding) as f:
            f.truncate()
            for src in source_entities:
                src = src.get()
                if self.binary:
                    if is_unicode(src):
                        src = encode_str(src, self.encoding)
                else:
                    if isinstance(src, (bytearray, bytes)):
                        src = decode_bytes(src, self.encoding)

                f.write(src)

        targets.add_files(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Writing content"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target

# ==============================================================================


class DistBuilder (FileBuilder):

    NAME_ATTRS = ('target', 'command', 'formats')
    SIGNATURE_ATTRS = ('script_args', )

    def __init__(self, options, command, args, target):

        target = self.get_target_dir_path(target)

        script_args = [command]

        if command.startswith('bdist'):
            temp_dir = self.get_build_path()
            script_args += ['--bdist-base', temp_dir]

        elif command != 'sdist':
            raise ErrorDistCommandInvalid(command)

        args = self._get_args(args)
        script_args += args

        formats = self._get_formats(args, command)

        script_args += ['--dist-dir', target]

        self.command = command
        self.target = target
        self.script_args = script_args
        self.formats = formats

    # -----------------------------------------------------------

    @staticmethod
    def _get_args(args):
        if args:
            return args.split() if is_string(args) else to_sequence(args)

        return tuple()

    # -----------------------------------------------------------

    @staticmethod
    def _get_formats(args, command):

        if not command.startswith('bdist'):
            return None

        formats = set()
        for arg in args:
            if arg.startswith('--formats='):
                v = arg[len('--formats='):].split(',')
                formats.update(v)

            elif arg.startswith('--plat-name='):
                v = arg[len('--plat-name='):]
                formats.add(v)

        return formats

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "distutils %s" % ' '.join(self.script_args)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        script = source_entities[0].get()

        cmd = [sys.executable, script]
        cmd += self.script_args

        script_dir = os.path.dirname(script)
        out = self.exec_cmd(cmd, script_dir)

        # TODO: Add parsing of setup.py output
        # "copying <filepath> -> <detination dir>"

        return out

# ==============================================================================


class InstallDistBuilder (FileBuilder):

    NAME_ATTRS = ('user',)

    def __init__(self, options, user):

        self.user = user

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "distutils install"

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        script = source_entities[0].get()

        cmd = [sys.executable, script, "install"]
        if self.user:
            cmd.append("--user")

        script_dir = os.path.dirname(script)
        out = self.exec_cmd(cmd, script_dir)

        # TODO: Add parsing of setup.py output
        # "copying <filepath> -> <detination dir>"

        return out

# ==============================================================================


class BuiltinTool(Tool):

    def ExecuteCommand(self, options, target=None, target_flag=None, cwd=None):
        return ExecuteCommandBuilder(options, target=target,
                                     target_flag=target_flag, cwd=cwd)

    Command = ExecuteCommand

    def ExecuteMethod(self, options, method, args=None, kw=None, single=True,
                      make_files=True, clear_targets=True):
        return ExecuteMethodBuilder(options, method=method, args=args, kw=kw,
                                    single=single, make_files=make_files,
                                    clear_targets=clear_targets)

    Method = ExecuteMethod

    def CopyFiles(self, options, target):
        return CopyFilesBuilder(options, target)

    def CopyFileAs(self, options, target):
        return CopyFileAsBuilder(options, target)

    def WriteFile(self, options, target, binary=False, encoding=None):
        return WriteFileBuilder(options, target,
                                binary=binary, encoding=encoding)

    def CreateDist(self, options, target, command, args=None):
        return DistBuilder(options, target=target, command=command, args=args)

    def InstallDist(self, options, user=True):
        return InstallDistBuilder(options, user=user)

    def CreateZip(self, options, target, rename=None, basedir=None, ext=None):
        return ZipFilesBuilder(options, target=target, rename=rename,
                               basedir=basedir, ext=ext)

    def CreateTar(self, options, target, mode=None, rename=None,
                  basedir=None, ext=None):

        return TarFilesBuilder(options, target=target, mode=mode,
                               rename=rename, basedir=basedir, ext=ext)
