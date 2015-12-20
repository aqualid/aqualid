#
# Copyright (c) 2014-2015 The developers of Aqualid project
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


import os
import errno
import operator

from aql.util_types import FilePath, to_sequence, to_string
from aql.utils import simple_object_signature, simplify_value, execute_command,\
    event_debug, log_debug, group_paths_by_dir, group_items, relative_join,\
    relative_join_list

from aql.entity import EntityBase, FileChecksumEntity, FileTimestampEntity,\
    FileEntityBase, SimpleEntity

__all__ = (
    'Builder', 'FileBuilder',
)


# ==============================================================================
@event_debug
def event_exec_cmd(settings, cmd, cwd, env):
    if settings.trace_exec:
        cmd = ' '.join(cmd)
        log_debug("CWD: '%s', CMD: '%s'", cwd, cmd)


# ==============================================================================
def _get_trace_arg(entity, brief):
    if isinstance(entity, FileEntityBase):
        value = entity.get()
        if brief:
            value = os.path.basename(value)
    else:
        if isinstance(entity, FilePath):
            value = entity

            if brief:
                value = os.path.basename(value)

        else:
            if isinstance(entity, EntityBase):
                value = to_string(entity.get())
            else:
                value = to_string(entity)

            value = value.strip()

            max_len = 64 if brief else 256
            src_len = len(value)

            if src_len > max_len:
                value = "%s...%s" % (value[:max_len // 2],
                                     value[src_len - (max_len // 2):])

            value = value.replace('\r', '')
            value = value.replace('\n', ' ')

    return value


# ==============================================================================
def _join_args(entities, brief):

    args = [_get_trace_arg(arg, brief) for arg in to_sequence(entities)]

    if not brief or (len(args) < 3):
        return ' '.join(args)

    wish_size = 128

    args_str = [args.pop(0)]
    last = args.pop()

    size = len(args_str[0]) + len(last)

    for arg in args:
        size += len(arg)

        if size > wish_size:
            args_str.append('...')
            break

        args_str.append(arg)

    args_str.append(last)

    return ' '.join(args_str)


# ==============================================================================
def _get_trace_str(name, sources, targets, brief):

    name = _join_args(name, brief)
    sources = _join_args(sources, brief)

    targets = _join_args(targets, brief)

    build_str = name
    if sources:
        build_str += " << " + sources
    if targets:
        build_str += " >> " + targets

    return build_str


# ==============================================================================
def _make_build_path(path_dir, _path_cache=set()):
    if path_dir not in _path_cache:
        if not os.path.isdir(path_dir):
            try:
                os.makedirs(path_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        _path_cache.add(path_dir)


# ==============================================================================
def _make_build_paths(dirnames):
    for dirname in dirnames:
        _make_build_path(dirname)


# ==============================================================================
def _split_filename_ext(filename, ext, replace_ext):
    if ext:
        if filename.endswith(ext):
            return filename[:-len(ext)], ext

        if not replace_ext:
            return filename, ext

    ext_pos = filename.rfind(os.path.extsep)
    if ext_pos > 0:
        if not ext:
            ext = filename[ext_pos:]
        filename = filename[:ext_pos]

    return filename, ext


# ==============================================================================
def _split_file_name(file_path,
                     ext=None,
                     prefix=None,
                     suffix=None,
                     replace_ext=False
                     ):

    if isinstance(file_path, EntityBase):
        file_path = file_path.get()

    dirname, filename = os.path.split(file_path)
    filename, ext = _split_filename_ext(filename, ext, replace_ext)

    if prefix:
        filename = prefix + filename

    if suffix:
        filename += suffix

    if ext:
        filename += ext

    return dirname, filename


# ==============================================================================
def _split_file_names(file_paths,
                      ext=None,
                      prefix=None,
                      suffix=None,
                      replace_ext=False):

    dirnames = []
    filenames = []
    for file_path in file_paths:
        dirname, filename = _split_file_name(file_path, ext, prefix, suffix,
                                             replace_ext)
        dirnames.append(dirname)
        filenames.append(filename)

    return dirnames, filenames


# ==============================================================================
def _get_file_signature_type(file_signature_type):
    if file_signature_type == 'timestamp':
        return FileTimestampEntity

    return FileChecksumEntity


# ==============================================================================
class BuilderInitiator(object):

    __slots__ = ('is_initiated', 'builder', 'options', 'args', 'kw')

    def __init__(self, builder, options, args, kw):

        self.is_initiated = False
        self.builder = builder
        self.options = options
        self.args = self.__store_args(args)
        self.kw = self.__store_kw(kw)

    # ==========================================================

    def __store_args(self, args):
        return tuple(map(self.options._store_value, args))

    # ==========================================================

    def __load_args(self):
        return tuple(map(self.options._load_value, self.args))

    # ==========================================================

    def __store_kw(self, kw):
        store_value = self.options._store_value
        return dict((name, store_value(value)) for name, value in kw.items())

    # ==========================================================

    def __load_kw(self):
        load_value = self.options._load_value
        return dict((name, load_value(value))
                    for name, value in self.kw.items())

    # ==========================================================

    def initiate(self):

        if self.is_initiated:
            return self.builder

        builder = self.builder

        kw = self.__load_kw()
        args = self.__load_args()

        options = self.options

        builder._init_attrs(options)

        builder.__init__(options, *args, **kw)

        if not hasattr(builder, 'name'):
            builder.set_name()

        if not hasattr(builder, 'signature'):
            builder.set_signature()

        self.is_initiated = True

        return builder

    # ==========================================================

    def can_build_batch(self):
        return self.builder.can_build_batch()

    def can_build(self):
        return self.builder.can_build()

    def is_batch(self):
        return self.builder.is_batch()


# ==============================================================================
class Builder (object):

    """
    Base class for all builders

    'name' - uniquely identifies builder
    'signature' - uniquely identifies builder's parameters

    """

    NAME_ATTRS = None
    SIGNATURE_ATTRS = None

    # -----------------------------------------------------------

    def __new__(cls, options, *args, **kw):

        self = super(Builder, cls).__new__(cls)
        return BuilderInitiator(self, options, args, kw)

    # -----------------------------------------------------------

    def _init_attrs(self, options):
        self.build_dir = options.build_dir.get()
        self.build_path = options.build_path.get()
        self.relative_build_paths = options.relative_build_paths.get()
        if options.file_signature == 'timestamp':
            self.use_timestamp = True
            self.file_entity_type = FileTimestampEntity
        else:
            self.use_timestamp = False
            self.file_entity_type = FileChecksumEntity

        self.env = options.env.get()

        is_batch = (options.batch_build.get() or not self.can_build()) and \
            self.can_build_batch()

        self.__is_batch = is_batch
        if is_batch:
            self.batch_groups = options.batch_groups.get()
            self.batch_size = options.batch_size.get()

    # -----------------------------------------------------------

    def can_build_batch(self):
        return self.__class__.build_batch != Builder.build_batch

    # -----------------------------------------------------------

    def can_build(self):
        return self.__class__.build != Builder.build

    # -----------------------------------------------------------

    def is_batch(self):
        return self.__is_batch

    # -----------------------------------------------------------

    def initiate(self):
        return self

    # -----------------------------------------------------------

    def set_name(self):

        cls = self.__class__
        name = [cls.__module__,
                cls.__name__,
                simplify_value(self.build_path),
                bool(self.relative_build_paths)]

        if self.NAME_ATTRS:
            name.extend(simplify_value(getattr(self, attr_name))
                        for attr_name in self.NAME_ATTRS)

        self.name = simple_object_signature(name)

    # -----------------------------------------------------------

    def set_signature(self):
        sign = []

        if self.SIGNATURE_ATTRS:
            sign.extend(simplify_value(getattr(self, attr_name))
                        for attr_name in self.SIGNATURE_ATTRS)

        self.signature = simple_object_signature(sign)

    # -----------------------------------------------------------

    def check_actual(self, target_entities):
        """
        Checks that previous target entities are still up to date.
        It called only if all other checks were successful.
        Returns None if all targets are actual.
        Otherwise first not actual target.
        :param target_entities: Previous target entities
        """
        for entity in target_entities:
            if not entity.is_actual():
                return target_entities

        return None

    # -----------------------------------------------------------

    def get_actual(self, target_entities):
        """
        Returns a list of actual target entities.
        :param target_entities: Previous target entities
        """

        # By default we return the same list as it has been just checked
        return target_entities

    # -----------------------------------------------------------

    def clear(self, target_entities, side_effect_entities):
        for entity in target_entities:
            entity.remove()

        for entity in side_effect_entities:
            entity.remove()

    # -----------------------------------------------------------

    def depends(self, options, source_entities):
        """
        Could be used to dynamically generate dependency nodes
        Returns list of dependency nodes or None
        """
        return None

    # -----------------------------------------------------------

    def replace(self, options, source_entities):
        """
        Could be used to dynamically replace sources
        Returns list of nodes/entities or None (if sources are not changed)
        """
        return None

    # -----------------------------------------------------------

    def split(self, source_entities):
        """
        Could be used to dynamically split building sources to several nodes
        Returns list of groups of source entities or None
        """
        return None

    # -----------------------------------------------------------

    def split_single(self, source_entities):
        """
        Implementation of split for splitting one-by-one
        """
        return source_entities

    # -----------------------------------------------------------

    def split_batch(self, source_entities):
        """
        Implementation of split for splitting to batch groups of batch size
        """
        return group_items(source_entities, self.batch_groups, self.batch_size)

    # -----------------------------------------------------------

    def split_batch_by_build_dir(self, source_entities):
        """
        Implementation of split for grouping sources by output
        """
        num_groups = self.batch_groups
        group_size = self.batch_size

        if self.relative_build_paths:
            path_getter = operator.methodcaller('get')

            groups = group_paths_by_dir(source_entities,
                                        num_groups,
                                        group_size,
                                        path_getter=path_getter)
        else:
            groups = group_items(source_entities, num_groups, group_size)

        return groups

    # -----------------------------------------------------------

    def get_weight(self, source_entities):
        return len(source_entities)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        """
        Builds a node
        Returns a build output string or None
        """
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):
        """
        Builds a node
        Returns a build output string or None
        """
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        """
        If it's possible returns target entities of the node, otherwise None
        """
        return None

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return self.__class__.__name__

    # -----------------------------------------------------------

    def get_trace_sources(self, source_entities, brief):
        return source_entities

    # -----------------------------------------------------------

    def get_trace_targets(self, target_entities, brief):
        return target_entities

    # -----------------------------------------------------------

    def get_trace(self,
                  source_entities=None,
                  target_entities=None,
                  brief=False):
        try:
            name = self.get_trace_name(source_entities, brief)
        except Exception:
            name = ''

        try:
            sources = self.get_trace_sources(source_entities, brief)
        except Exception:
            sources = None

        try:
            if (target_entities is None) and source_entities:
                target_entities = self.get_target_entities(source_entities)

            targets = self.get_trace_targets(target_entities, brief)
        except Exception:
            targets = None

        return _get_trace_str(name, sources, targets, brief)

    # -----------------------------------------------------------

    def get_build_dir(self):
        _make_build_path(self.build_dir)

        return self.build_dir

    # -----------------------------------------------------------

    def get_build_path(self):
        _make_build_path(self.build_path)
        return self.build_path

    # -----------------------------------------------------------

    def get_target_path(self, target, ext=None, prefix=None):
        target_dir, name = _split_file_name(target,
                                            prefix=prefix,
                                            ext=ext,
                                            replace_ext=False)

        if target_dir.startswith((os.path.curdir, os.path.pardir)):
            target_dir = os.path.abspath(target_dir)
        elif not os.path.isabs(target_dir):
            target_dir = os.path.abspath(os.path.join(self.build_path,
                                                      target_dir))

        _make_build_path(target_dir)

        target = os.path.join(target_dir, name)
        return target

    # -----------------------------------------------------------

    @staticmethod
    def makedirs(path):
        _make_build_path(path)

    # -----------------------------------------------------------

    def get_target_dir(self, target_dir):
        target_dir, name = os.path.split(target_dir)
        if not name:
            target_dir, name = os.path.split(target_dir)

        elif not target_dir and name in (os.path.curdir, os.path.pardir):
            target_dir = name
            name = ''

        if target_dir.startswith((os.path.curdir, os.path.pardir)):
            target_dir = os.path.abspath(target_dir)

        elif not os.path.isabs(target_dir):
            target_dir = os.path.abspath(os.path.join(self.build_path,
                                                      target_dir))

        target_dir = os.path.join(target_dir, name)

        _make_build_path(target_dir)

        return target_dir

    # -----------------------------------------------------------

    def get_source_target_path(self,
                               file_path,
                               ext=None,
                               prefix=None,
                               suffix=None,
                               replace_ext=True):

        build_path = self.build_path

        dirname, filename = _split_file_name(file_path,
                                             ext=ext,
                                             prefix=prefix,
                                             suffix=suffix,
                                             replace_ext=replace_ext)

        if self.relative_build_paths:
            build_path = relative_join(build_path, dirname)

        _make_build_path(build_path)

        build_path = os.path.join(build_path, filename)

        return build_path

    # -----------------------------------------------------------

    def get_source_target_paths(self,
                                file_paths,
                                ext=None,
                                prefix=None,
                                suffix=None,
                                replace_ext=True):

        build_path = self.build_path

        dirnames, filenames = _split_file_names(file_paths,
                                                ext=ext,
                                                prefix=prefix,
                                                suffix=suffix,
                                                replace_ext=replace_ext)

        if self.relative_build_paths:
            dirnames = relative_join_list(build_path, dirnames)
            _make_build_paths(dirnames)

            build_paths = [os.path.join(dirname, filename)
                           for dirname, filename in zip(dirnames, filenames)]

        else:
            _make_build_path(build_path)

            build_paths = [
                os.path.join(build_path, filename) for filename in filenames]

        return build_paths

    # -----------------------------------------------------------

    def make_entity(self, value, tags=None):
        if isinstance(value, FilePath):
            return self.make_file_entity(name=value, tags=tags)

        return SimpleEntity(value, tags=tags)

    # -----------------------------------------------------------

    def make_simple_entity(self, value, tags=None):
        return SimpleEntity(value, tags=tags)

    # -----------------------------------------------------------

    def make_file_entity(self, value, tags=None):
        return self.file_entity_type(name=value, tags=tags)

    # -----------------------------------------------------------

    def make_file_entities(self, entities, tags=None):
        make_file_entity = self.make_file_entity
        for entity in to_sequence(entities):
            if isinstance(entity, EntityBase):
                yield entity
            else:
                yield make_file_entity(entity, tags)

    # ----------------------------------------------------------

    def make_entities(self, entities, tags=None):
        make_entity = self.make_entity
        for entity in to_sequence(entities):
            if isinstance(entity, EntityBase):
                yield entity
            else:
                yield make_entity(entity, tags)

    # -----------------------------------------------------------

    def exec_cmd(self, cmd, cwd=None, env=None, file_flag=None, stdin=None):

        result = self.exec_cmd_result(
            cmd, cwd=cwd, env=env, file_flag=file_flag, stdin=stdin)
        if result.failed():
            raise result

        return result.output()

    # -----------------------------------------------------------

    def exec_cmd_result(self,
                        cmd,
                        cwd=None,
                        env=None,
                        file_flag=None,
                        stdin=None):

        if env is None:
            env = self.env

        if cwd is None:
            cwd = self.get_build_path()

        result = execute_command(
            cmd, cwd=cwd, env=env, file_flag=file_flag, stdin=stdin)

        event_exec_cmd(cmd, cwd, env)

        return result


# ==============================================================================
class FileBuilder (Builder):
    make_entity = Builder.make_file_entity
