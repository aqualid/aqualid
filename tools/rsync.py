import sys
import os.path
import itertools

import aql

# ==============================================================================


class ErrorNoCommonSourcesDir(Exception):

    def __init__(self, sources):
        msg = "Can't rsync disjoined files: %s" % (sources,)
        super(ErrorNoCommonSourcesDir, self).__init__(msg)

# ==============================================================================


def _to_cygwin_path(path):

    if not path:
        return '.'

    path_sep = '/'
    drive, path = aql.split_drive(path)
    if drive.find(':') == 1:
        drive = "/cygdrive/" + drive[0]
    path = drive + path

    if path[-1] in ('\\', '/'):
        last_sep = path_sep
    else:
        last_sep = ''

    path = path.replace('\\', '/')

    return path + last_sep


# ==============================================================================

def _norm_local_path(path):

    if not path:
        return '.'

    path_sep = os.path.sep

    path = str(path)

    if path[-1] in (path_sep, os.path.altsep):
        last_sep = path_sep
    else:
        last_sep = ''

    path = os.path.normcase(os.path.normpath(path))

    return path + last_sep

# ==============================================================================


def _norm_remote_path(path):

    if not path:
        return '.'

    path_sep = '/'

    if path[-1] in (path_sep, os.path.altsep):
        last_sep = path_sep
    else:
        last_sep = ''

    path = os.path.normpath(path).replace('\\', path_sep)

    return path + last_sep

# ==============================================================================


def _split_remote_path(remote_path):
    if os.path.isabs(remote_path):
        host = ''
        user = ''
    else:
        # [USER@]HOST:DEST
        remote_path = remote_path.strip()
        user_pos = remote_path.find('@')
        if user_pos == -1:
            user = ''
        else:
            user = remote_path[:user_pos]
            remote_path = remote_path[user_pos + 1:]

        host_pos = remote_path.find(':')
        if host_pos == -1:
            host = ''
        else:
            host = remote_path[:host_pos]
            remote_path = remote_path[host_pos + 1:]

    remote_path = _norm_remote_path(remote_path)

    return user, host, remote_path

# ==============================================================================


class RemotePath(object):

    __slots__ = ('path', 'host', 'user')

    def __init__(self, remote_path, user=None, host=None):

        u, h, remote_path = _split_remote_path(remote_path)
        if not user:
            user = u

        if not host:
            host = h

        self.path = remote_path
        self.host = host
        self.user = user

    # -----------------------------------------------------------

    def is_remote(self):
        return bool(self.host)

    # -----------------------------------------------------------

    def __str__(self):
        return self.get()

    # -----------------------------------------------------------

    def join(self, other):
        if self.host:
            path = self.path + '/' + _norm_remote_path(other)
        else:
            path = os.path.join(self.path, _norm_local_path(other))

        return RemotePath(path, self.user, self.host)

    # -----------------------------------------------------------

    def basename(self):
        if self.host:
            last_slash_pos = self.path.rfind('/')
            return self.path[last_slash_pos + 1:]
        else:
            return os.path.basename(self.path)

    # -----------------------------------------------------------

    def get(self, cygwin_path=False):
        if self.host:
            if self.user:
                return "%s@%s:%s" % (self.user, self.host, self.path)

            return "%s:%s" % (self.host, self.path)
        else:
            if cygwin_path:
                return _to_cygwin_path(self.path)

            return self.path

# ==============================================================================


class RSyncPushBuilder(aql.FileBuilder):

    NAME_ATTRS = ('remote_path', 'source_base')
    SIGNATURE_ATTRS = ('cmd', )

    def __init__(self, options, remote_path, source_base=None,
                 host=None, login=None, key_file=None, exclude=None):

        self.rsync_cygwin = (
            sys.platform != 'cygwin') and options.rsync_cygwin.get()

        if source_base:
            self.source_base = _norm_local_path(source_base)
        else:
            self.source_base = None

        self.remote_path = RemotePath(remote_path, login, host)

        self.cmd = self.__get_cmd(options, key_file, exclude)
        self.rsync = options.rsync.get()

        self.file_value_type = aql.FileTimestampEntity

    # -----------------------------------------------------------

    def __get_cmd(self, options, key_file, excludes):
        cmd = [options.rsync.get()]

        cmd += options.rsync_flags.get()

        if excludes:
            excludes = aql.to_sequence(excludes)
            cmd += itertools.chain(*itertools.product(['--exclude'], excludes))

        if self.remote_path.is_remote():
            ssh_flags = options.rsync_ssh_flags.get()
            if key_file:
                if self.rsync_cygwin:
                    key_file = _to_cygwin_path(key_file)
                ssh_flags += ['-i', key_file]

            cmd += ['-e', 'ssh %s' % ' '.join(ssh_flags)]

        return cmd

    # -----------------------------------------------------------

    def _get_sources(self, source_entities):

        sources = [_norm_local_path(src.get()) for src in source_entities]

        source_base = self.source_base
        if source_base:
            sources_base_len = len(source_base)
            for i, src in enumerate(sources):
                if src.startswith(source_base):
                    src = src[sources_base_len:]
                    if not src:
                        src = '.'

                    sources[i] = src

        return sources

    # -----------------------------------------------------------

    def _set_targets(self, source_entities, sources, targets):

        remote_path = self.remote_path
        source_base = self.source_base

        value_type = aql.SimpleEntity if remote_path.is_remote(
        ) else self.get_file_entity_type()

        for src_value, src in zip(source_entities, sources):

            if not source_base:
                src = os.path.basename(src)

            target_path = remote_path.join(src)

            target_value = value_type(target_path.get())
            targets[src_value].add(target_value)

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):
        sources = self._get_sources(source_entities)

        cmd = list(self.cmd)

        tmp_r, tmp_w = None, None
        try:
            if self.rsync_cygwin:
                sources = map(_to_cygwin_path, sources)

            sorted_sources = sorted(sources)

            source_base = self.source_base

            if source_base:
                if self.rsync_cygwin:
                    source_base = _to_cygwin_path(source_base)

                tmp_r, tmp_w = os.pipe()
                os.write(tmp_w, '\n'.join(sorted_sources).encode('utf-8'))
                os.close(tmp_w)
                tmp_w = None
                cmd += ["--files-from=-", source_base]
            else:
                cmd += sorted_sources

            remote_path = self.remote_path.get(self.rsync_cygwin)

            cmd.append(remote_path)

            out = self.exec_cmd(cmd, stdin=tmp_r)

        finally:
            if tmp_r:
                os.close(tmp_r)
            if tmp_w:
                os.close(tmp_w)

        self._set_targets(source_entities, sources, targets)

        return out

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        if brief:
            name = self.cmd[0]
            name = os.path.splitext(os.path.basename(name))[0]
        else:
            name = ' '.join(self.cmd)

        return name

# ==============================================================================


class RSyncPullBuilder(aql.Builder):
    # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i
    # dev.key" c4dev@dev:/work/cp/bp2_int/components .

    NAME_ATTRS = ('target_path', )
    SIGNATURE_ATTRS = ('cmd', )

    def __init__(self, options, target, host=None,
                 login=None, key_file=None, exclude=None):

        self.rsync_cygwin = (
            sys.platform != 'cygwin') and options.rsync_cygwin.get()

        self.target_path = _norm_local_path(target)
        self.host = host
        self.login = login

        self.cmd = self.__get_cmd(options, key_file, exclude)
        self.rsync = options.rsync.get()

        self.file_value_type = aql.FileTimestampEntity

    # -----------------------------------------------------------

    def make_entity(self, value):
        if aql.is_string(value):
            remote_path = RemotePath(value, self.login, self.host)
            if not remote_path.is_remote():
                return self.make_file_entity(value)

        return self.make_simple_entity(value)

    # -----------------------------------------------------------

    def __get_cmd(self, options, key_file, excludes):
        cmd = [options.rsync.get()]

        cmd += options.rsync_flags.get()

        if excludes:
            excludes = aql.to_sequence(excludes)
            cmd += itertools.chain(*itertools.product(['--exclude'], excludes))

        if self.host:
            ssh_flags = options.rsync_ssh_flags.get()
            if key_file:
                if self.rsync_cygwin:
                    key_file = _to_cygwin_path(key_file)
                ssh_flags += ['-i', key_file]

            cmd += ['-e', 'ssh %s' % ' '.join(ssh_flags)]

        return cmd

    # -----------------------------------------------------------

    def _get_sources_and_targets(self, source_entities):

        sources = []
        targets = []
        target_path = self.target_path

        host = self.host
        login = self.login

        cygwin_path = self.rsync_cygwin

        for src in source_entities:
            src = src.get()
            remote_path = RemotePath(src, login, host)

            path = os.path.join(target_path, remote_path.basename())
            targets.append(path)
            sources.append(remote_path.get(cygwin_path))

        sources.sort()

        return sources, targets

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        sources, target_files = self._get_sources_and_targets(source_entities)

        cmd = list(self.cmd)

        target_path = self.target_path

        if self.rsync_cygwin:
            target_path = _to_cygwin_path(target_path)

        cmd += sources

        cmd.append(target_path)

        out = self.exec_cmd(cmd)

        targets.add_files(target_files)

        return out

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        if brief:
            name = self.cmd[0]
            name = os.path.splitext(os.path.basename(name))[0]
        else:
            name = ' '.join(self.cmd)

        return name

# ==============================================================================


@aql.tool('rsync')
class ToolRsync(aql.Tool):

    @classmethod
    def setup(cls, options):

        rsync = cls.find_program(options, 'rsync')

        options.rsync = rsync
        if not options.rsync_cygwin.is_set():
            options.rsync_cygwin = rsync.find('cygwin') != -1

    # -----------------------------------------------------------

    @classmethod
    def options(cls):
        options = aql.Options()

        options.rsync = aql.PathOptionType(
            description="File path to rsync program.")
        options.rsync_cygwin = aql.BoolOptionType(
            description="Is rsync uses cygwin paths.")

        options.rsync_flags = aql.ListOptionType(
            description="rsync tool flags", separators=None)
        options.rsync_ssh_flags = aql.ListOptionType(
            description="rsync tool SSH flags", separators=None)

        return options

    # -----------------------------------------------------------

    def __init__(self, options):
        super(ToolRsync, self).__init__(options)

        options.rsync_flags = ['-a', '-v', '-z']
        options.rsync_ssh_flags = [
            '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes']

        options.set_group("rsync")

    # -----------------------------------------------------------

    def pull(self, options, target, host=None,
             login=None, key_file=None, exclude=None):

        return RSyncPullBuilder(options, target,
                                host=host, login=login,
                                key_file=key_file, exclude=exclude)

    Pull = pull

    # ----------------------------------------------------------

    def push(self, options, target, source_base=None,
             host=None, login=None, key_file=None, exclude=None):

        builder = RSyncPushBuilder(options, target,
                                   source_base=source_base,
                                   host=host, login=login,
                                   key_file=key_file, exclude=exclude)

        return builder

    Push = push

    # ----------------------------------------------------------
