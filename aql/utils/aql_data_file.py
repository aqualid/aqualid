#
# Copyright (c) 2011-2015 The developers of Aqualid project
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
import operator
import struct
import mmap

from .aql_utils import openFile
from .aql_logging import logInfo

__all__ = ('DataFile', )

# ==============================================================================


class ErrorDataFileFormatInvalid(Exception):

    def __init__(self):
        msg = "Data file format is not valid."
        super(ErrorDataFileFormatInvalid, self).__init__(msg)

# ==============================================================================


class ErrorDataFileChunkInvalid(Exception):

    def __init__(self):
        msg = "Data file chunk format is not valid."
        super(ErrorDataFileChunkInvalid, self).__init__(msg)

# ==============================================================================


class ErrorDataFileVersionInvalid(Exception):

    def __init__(self):
        msg = "Data file version is changed."
        super(ErrorDataFileVersionInvalid, self).__init__(msg)

# ==============================================================================


class ErrorDataFileCorrupted(Exception):

    def __init__(self):
        msg = "Data file is corrupted"
        super(ErrorDataFileCorrupted, self).__init__(msg)

# ==============================================================================


class _MmapFile(object):

    def __init__(self, filename):
        self.check_resize_available()

        stream = openFile(filename, write=True, binary=True, sync=False)

        try:
            memmap = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_WRITE)
        except ValueError:
            stream.seek(0)
            stream.write(b'\0')
            stream.flush()

            memmap = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_WRITE)

        self.stream = stream
        self.memmap = memmap
        self.size = memmap.size
        self.resize = memmap.resize
        self.flush = memmap.flush

    # -----------------------------------------------------------

    def check_resize_available(self):
        mm = mmap.mmap(-1, 1)
        try:
            mm.resize(1)
        finally:
            mm.close()

    # -----------------------------------------------------------

    def close(self):
        self.memmap.flush()
        self.memmap.close()
        self.stream.close()

    # -----------------------------------------------------------

    def read(self, offset, size):
        return self.memmap[offset: offset + size]

    # -----------------------------------------------------------

    def write(self, offset, data):
        memmap = self.memmap

        end_offset = offset + len(data)
        if end_offset > memmap.size():
            page_size = mmap.ALLOCATIONGRANULARITY
            size = ((end_offset + (page_size - 1)) // page_size) * page_size
            if size == 0:
                size = page_size

            self.resize(size)

        memmap[offset: end_offset] = data

    # -----------------------------------------------------------

    def move(self, dest, src, size):
        memmap = self.memmap

        end_offset = dest + size
        if end_offset > memmap.size():
            self.resize(end_offset)

        memmap.move(dest, src, size)

# ==============================================================================


class _IOFile(object):

    def __init__(self, filename):
        stream = openFile(filename, write=True, binary=True, sync=False)

        self.stream = stream
        self.resize = stream.truncate
        self.flush = stream.flush

    # -----------------------------------------------------------

    def close(self):
        self.stream.close()

    # -----------------------------------------------------------

    def read(self, offset, size):
        stream = self.stream
        stream.seek(offset)
        return stream.read(size)

    # -----------------------------------------------------------

    def write(self, offset, data):
        stream = self.stream
        stream.seek(offset)
        stream.write(data)

    # -----------------------------------------------------------

    def move(self, dest, src, size):
        stream = self.stream
        stream.seek(src)
        data = stream.read(size)
        stream.seek(dest)
        stream.write(data)

    # -----------------------------------------------------------

    def size(self, io_SEEK_END=io.SEEK_END):
        return self.stream.seek(0, io_SEEK_END)

# ==============================================================================


class MetaData (object):
    __slots__ = (

        'offset',
        'key',
        'id',
        'data_offset',
        'data_size',
        'data_capacity',
    )

    # big-endian, 8 bytes (key), 16 bytes (id), 4 bytes (size), 4 bytes
    # (capacity)
    _META_STRUCT = struct.Struct(">Q16sLL")
    size = _META_STRUCT.size

    # -----------------------------------------------------------

    def __init__(self, meta_offset, key, data_id, data_offset, data_size):

        self.offset = meta_offset
        self.key = key
        self.id = data_id
        self.data_offset = data_offset
        self.data_size = data_size
        self.data_capacity = data_size + 4

    # -----------------------------------------------------------

    def dump(self, meta_struct=_META_STRUCT):
        return meta_struct.pack(self.key, self.id,
                                self.data_size, self.data_capacity)

    # -----------------------------------------------------------

    @classmethod
    def load(cls, dump, meta_struct=_META_STRUCT):

        self = cls.__new__(cls)

        try:
            self.key, self.id, data_size, data_capacity = meta_struct.unpack(
                dump)
        except struct.error:
            raise ErrorDataFileChunkInvalid()

        if data_capacity < data_size:
            raise ErrorDataFileChunkInvalid()

        self.data_size = data_size
        self.data_capacity = data_capacity

        return self

    # -----------------------------------------------------------

    def resize(self, data_size):

        self.data_size = data_size

        capacity = self.data_capacity
        if capacity >= data_size:
            return 0

        self.data_capacity = data_size + min(data_size // 4, 128)

        return self.data_capacity - capacity

    # -----------------------------------------------------------

    def __repr__(self):
        return self.__str__()

    # -----------------------------------------------------------

    def __str__(self):
        s = []
        for v in self.__slots__:
            s.append("%s: %s" % (v, getattr(self, v)))

        return ", ".join(s)

# ==============================================================================


class DataFile (object):

    __slots__ = (
        'next_key',
        'id2data',
        'key2id',
        'meta_end',
        'data_begin',
        'data_end',
        'handle',
    )

    # +-----------------------------------+
    # |8 bytes (MAGIC TAG)                |
    # +-----------------------------------+
    # |4 bytes (file version)             |
    # +-----------------------------------+
    # |8 bytes (next unique key)          |
    # +-----------------------------------+
    # |4 bytes (data begin)               |
    # +-----------------------------------+
    # | meta1 (40 bytes)                  |
    # +-----------------------------------+
    # | meta2 (40 bytes)                  |
    # +-----------------------------------+
    #           .......
    # +-----------------------------------+
    # | metaN (40 bytes)                  |
    # +-----------------------------------+
    # |  data1 (x bytes)                  |
    # +-----------------------------------+
    # |  data2 (y bytes)                  |
    # +-----------------------------------+
    #           .......
    # +-----------------------------------+
    # |  dataN (z bytes)                  |
    # +-----------------------------------+

    MAGIC_TAG = b".AQL.DB."
    VERSION = 1

    # big-endian, 8 bytes(MAGIC TAG), 4 bytes (file version)
    _HEADER_STRUCT = struct.Struct(">8sL")
    _HEADER_SIZE = _HEADER_STRUCT.size

    _KEY_STRUCT = struct.Struct(">Q")  # 8 bytes (next unique key)
    _KEY_OFFSET = _HEADER_SIZE
    _KEY_SIZE = _KEY_STRUCT.size

    # 4 bytes (offset of data area)
    _META_TABLE_HEADER_STRUCT = struct.Struct(">L")
    _META_TABLE_HEADER_SIZE = _META_TABLE_HEADER_STRUCT.size
    _META_TABLE_HEADER_OFFSET = _KEY_OFFSET + _KEY_SIZE

    _META_TABLE_OFFSET = _META_TABLE_HEADER_OFFSET + _META_TABLE_HEADER_SIZE

    # -----------------------------------------------------------

    def __init__(self, filename, force=False):

        self.id2data = {}
        self.key2id = {}
        self.meta_end = 0
        self.data_begin = 0
        self.data_end = 0
        self.handle = None
        self.next_key = None

        self.open(filename, force=force)

    # -----------------------------------------------------------

    def open(self, filename, force=False):
        self.close()

        try:
            self.handle = _MmapFile(filename)
        except Exception as e:
            logInfo("Default handler _IOFile, mmap not supported: {}".format(e))
            self.handle = _IOFile(filename)

        self._init_header(force)

        self.next_key = self._key_generator()

        self._init_meta_table()

    # -----------------------------------------------------------

    def close(self):

        if self.handle is not None:
            self.handle.close()
            self.handle = None

            self.id2data.clear()
            self.key2id.clear()
            self.meta_end = 0
            self.data_begin = 0
            self.data_end = 0
            self.next_key = None

    # -----------------------------------------------------------

    def clear(self):

        self._reset_meta_table()

        self.next_key = self._key_generator()

        self.id2data.clear()
        self.key2id.clear()

    # -----------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # -----------------------------------------------------------

    def _init_header(self, force, header_struct=_HEADER_STRUCT):

        header = self.handle.read(0, header_struct.size)

        try:
            tag, version = header_struct.unpack(header)

            if tag != self.MAGIC_TAG:
                if not force:
                    raise ErrorDataFileFormatInvalid()

            elif version == self.VERSION:
                return

        except struct.error:
            if (header and header != b'\0') and not force:
                raise ErrorDataFileFormatInvalid()

        # -----------------------------------------------------------
        # init the file
        header = header_struct.pack(self.MAGIC_TAG, self.VERSION)
        self.handle.resize(len(header))
        self.handle.write(0, header)

    # -----------------------------------------------------------

    def _key_generator(self,
                       key_offset=_KEY_OFFSET,
                       key_struct=_KEY_STRUCT,
                       MAX_KEY=(2 ** 64) - 1):

        key_dump = self.handle.read(key_offset, key_struct.size)
        try:
            next_key, = key_struct.unpack(key_dump)
        except struct.error:
            next_key = 0

        key_pack = key_struct.pack
        write_file = self.handle.write

        while True:

            if next_key < MAX_KEY:
                next_key += 1
            else:
                next_key = 1    # this should never happen

            write_file(key_offset, key_pack(next_key))
            yield next_key

    # -----------------------------------------------------------

    def _reset_meta_table(self,
                          meta_size=MetaData.size,
                          table_offset=_META_TABLE_OFFSET):

        self.meta_end = table_offset
        self.data_begin = table_offset + meta_size * 1024
        self.data_end = self.data_begin

        self._truncate_file()

    # -----------------------------------------------------------

    def _truncate_file(self,
                       table_header_struct=_META_TABLE_HEADER_STRUCT,
                       table_header_offset=_META_TABLE_HEADER_OFFSET):

        header_dump = table_header_struct.pack(self.data_begin)

        handle = self.handle

        handle.resize(self.data_end)
        handle.write(table_header_offset, header_dump)

        # handle.write( self.meta_end,
        #               bytearray(self.data_begin - self.meta_end) )
        handle.write(self.meta_end, b'\0' * (self.data_begin - self.meta_end))
        handle.flush()

    # -----------------------------------------------------------

    def _init_meta_table(self,
                         table_header_struct=_META_TABLE_HEADER_STRUCT,
                         table_header_offset=_META_TABLE_HEADER_OFFSET,
                         table_header_size=_META_TABLE_HEADER_SIZE,
                         table_begin=_META_TABLE_OFFSET,
                         meta_size=MetaData.size):

        handle = self.handle

        header_dump = handle.read(table_header_offset, table_header_size)

        try:
            data_begin, = table_header_struct.unpack(header_dump)
        except struct.error:
            self._reset_meta_table()
            return

        if (data_begin <= table_begin) or (data_begin > handle.size()):
            self._reset_meta_table()
            return

        table_size = data_begin - table_begin

        if (table_size % meta_size) != 0:
            self._reset_meta_table()
            return

        dump = handle.read(table_begin, table_size)

        if len(dump) < table_size:
            self._reset_meta_table()
            return

        self._load_meta_table(data_begin, dump)

    # -----------------------------------------------------------

    def _load_meta_table(self, data_offset, metas_dump,
                         meta_size=MetaData.size,
                         table_begin=_META_TABLE_OFFSET):

        self.data_begin = data_offset

        file_size = self.handle.size()
        load_meta = MetaData.load

        pos = 0
        dump_size = len(metas_dump)
        while pos < dump_size:
            meta_dump = metas_dump[pos: pos + meta_size]
            try:
                meta = load_meta(meta_dump)

                data_capacity = meta.data_capacity

                if data_capacity == 0:
                    # end of meta table marker
                    break

                meta.offset = pos + table_begin
                meta.data_offset = data_offset

                if (data_offset + meta.data_size) > file_size:
                    raise ErrorDataFileChunkInvalid()

                data_offset += data_capacity

            except Exception:
                self.data_end = data_offset
                self.meta_end = pos + table_begin
                self._truncate_file()
                return

            self.id2data[meta.id] = meta
            if meta.key:
                self.key2id[meta.key] = meta.id

            pos += meta_size

        self.meta_end = pos + table_begin
        self.data_end = data_offset

    # -----------------------------------------------------------

    def _extend_meta_table(self,
                           table_header_struct=_META_TABLE_HEADER_STRUCT,
                           table_header_offset=_META_TABLE_HEADER_OFFSET,
                           table_begin=_META_TABLE_OFFSET):

        data_begin = self.data_begin
        data_end = self.data_end

        table_capacity = data_begin - table_begin
        new_data_begin = data_begin + table_capacity

        handle = self.handle

        handle.move(new_data_begin, data_begin, data_end - data_begin)
        # handle.write( data_begin, bytearray( table_capacity ) )
        handle.write(data_begin, b'\0' * table_capacity)

        header_dump = table_header_struct.pack(new_data_begin)
        handle.write(table_header_offset, header_dump)

        self.data_begin = new_data_begin
        self.data_end += table_capacity

        for meta in self.id2data.values():
            meta.data_offset += table_capacity

    # -----------------------------------------------------------

    def _extend_data(self, meta, oversize):
        new_next_data = meta.data_offset + meta.data_capacity
        next_data = new_next_data - oversize
        rest_size = self.data_end - next_data
        if rest_size > 0:
            self.handle.move(new_next_data, next_data, rest_size)

            for meta in self.id2data.values():
                if meta.data_offset >= next_data:
                    meta.data_offset += oversize

        self.data_end += oversize

    # -----------------------------------------------------------

    def _append(self, key, data_id, data,
                meta_size=MetaData.size):

        meta_offset = self.meta_end
        if meta_offset == self.data_begin:
            self._extend_meta_table()

        data_offset = self.data_end

        meta = MetaData(meta_offset, key, data_id, data_offset, len(data))

        write = self.handle.write

        write(data_offset, data)
        write(meta_offset, meta.dump())

        self.data_end += meta.data_capacity
        self.meta_end += meta_size

        self.id2data[data_id] = meta

    # -----------------------------------------------------------

    def _update(self, meta, data, update_meta):

        data_size = len(data)

        if meta.data_size != data_size:
            update_meta = True
            oversize = meta.resize(data_size)
            if oversize > 0:
                self._extend_data(meta, oversize)

        write = self.handle.write

        if update_meta:
            write(meta.offset, meta.dump())

        write(meta.data_offset, data)

    # -----------------------------------------------------------

    def read(self, data_id):
        try:
            meta = self.id2data[data_id]
        except KeyError:
            return None

        return self.handle.read(meta.data_offset, meta.data_size)

    # -----------------------------------------------------------

    def write(self, data_id, data):

        try:
            meta = self.id2data[data_id]
            self._update(meta, data, update_meta=False)
        except KeyError:
            self._append(0, data_id, data)

    # -----------------------------------------------------------

    def write_with_key(self, data_id, data):

        meta = self.id2data.get(data_id)

        key = next(self.next_key)

        if meta is None:
            self._append(key, data_id, data)
        else:
            try:
                del self.key2id[meta.key]
            except KeyError:
                pass

            meta.key = key
            self._update(meta, data, update_meta=True)

        self.key2id[key] = data_id

        return key

    # -----------------------------------------------------------

    def get_ids(self, keys):
        try:
            return tuple(map(self.key2id.__getitem__, keys))
        except KeyError:
            return None

    # -----------------------------------------------------------

    def get_keys(self, data_ids):
        return map(operator.attrgetter('key'),
                   map(self.id2data.__getitem__, data_ids))

    # -----------------------------------------------------------

    def remove(self, data_ids):

        move = self.handle.move
        meta_size = MetaData.size

        remove_data_ids = frozenset(data_ids)

        metas = sorted(
            self.id2data.values(), key=operator.attrgetter('data_offset'))

        meta_shift = 0
        data_shift = 0

        meta_offset = 0
        data_offset = 0
        last_meta_end = 0
        last_data_end = 0

        remove_data_begin = None
        remove_meta_begin = None

        move_meta_begin = None
        move_data_begin = None

        for meta in metas:

            meta_offset = meta.offset
            last_meta_end = meta_offset + meta_size
            data_offset = meta.data_offset
            last_data_end = data_offset + meta.data_capacity

            if meta.id in remove_data_ids:

                del self.id2data[meta.id]
                if meta.key:
                    del self.key2id[meta.key]

                if move_meta_begin is not None:
                    move(remove_meta_begin, move_meta_begin,
                         meta_offset - move_meta_begin)
                    move(remove_data_begin, move_data_begin,
                         data_offset - move_data_begin)

                    remove_meta_begin = None
                    move_meta_begin = None

                if remove_meta_begin is None:
                    remove_meta_begin = meta_offset - meta_shift
                    remove_data_begin = data_offset - data_shift

            else:
                if remove_meta_begin is not None:
                    if move_meta_begin is None:
                        move_meta_begin = meta_offset
                        move_data_begin = data_offset

                        meta_shift = move_meta_begin - remove_meta_begin
                        data_shift = move_data_begin - remove_data_begin

                if meta_shift:
                    meta.offset -= meta_shift
                    meta.data_offset -= data_shift

        if remove_data_begin is not None:
            if move_meta_begin is None:
                meta_shift = last_meta_end - remove_meta_begin
                data_shift = last_data_end - remove_data_begin
            else:
                move(remove_meta_begin, move_meta_begin,
                     last_meta_end - move_meta_begin)
                move(remove_data_begin, move_data_begin,
                     last_data_end - move_data_begin)

        self.meta_end -= meta_shift
        self.data_end -= data_shift

        # self.handle.write( self.meta_end, bytearray( meta_shift ) )
        self.handle.write(self.meta_end, b'\0' * meta_shift)
        self.handle.resize(self.data_end)

    # -----------------------------------------------------------

    def selfTest(self):

        if self.handle is None:
            return

        file_size = self.handle.size()

        if self.data_begin > file_size:
            raise AssertionError("data_begin(%s) > file_size(%s)" %
                                 (self.data_begin, file_size))

        if self.data_begin > self.data_end:
            raise AssertionError("data_end(%s) > data_end(%s)" %
                                 (self.data_begin, self.data_end))

        if self.meta_end > self.data_begin:
            raise AssertionError("meta_end(%s) > data_begin(%s)" %
                                 (self.meta_end, self.data_begin))

        # -----------------------------------------------------------

        header_dump = self.handle.read(
            self._META_TABLE_HEADER_OFFSET, self._META_TABLE_HEADER_SIZE)

        try:
            data_begin, = self._META_TABLE_HEADER_STRUCT.unpack(header_dump)
        except struct.error:
            self._reset_meta_table()
            return

        if self.data_begin != data_begin:
            raise AssertionError("self.data_begin(%s) != data_begin(%s)" %
                                 (self.data_begin, data_begin))

        # -----------------------------------------------------------

        items = sorted(self.id2data.items(), key=lambda item: item[1].offset)

        last_meta_offset = self._META_TABLE_OFFSET
        last_data_offset = self.data_begin

        for data_id, meta in items:
            if meta.id != data_id:
                raise AssertionError(
                    "meta.id(%s) != data_id(%s)" % (meta.id, data_id))

            if meta.key != 0:
                if self.key2id[meta.key] != data_id:
                    raise AssertionError(
                        "self.key2id[ meta.key ](%s) != data_id(%s)" %
                        (self.key2id[meta.key], data_id))

            if meta.data_capacity < meta.data_size:
                raise AssertionError(
                    "meta.data_capacity(%s) < meta.data_size (%s)" %
                    (meta.data_capacity, meta.data_size))

            if meta.offset >= self.meta_end:
                raise AssertionError("meta.offset(%s) >= self.meta_end(%s)" %
                                     (meta.offset, self.meta_end))

            if meta.offset != last_meta_offset:
                raise AssertionError(
                    "meta.offset(%s) != last_meta_offset(%s)" %
                    (meta.offset, last_meta_offset))

            if meta.data_offset != last_data_offset:
                raise AssertionError(
                    "meta.data_offset(%s) != last_data_offset(%s)" %
                    (meta.data_offset, last_data_offset))

            if meta.data_offset >= self.data_end:
                raise AssertionError(
                    "meta.data_offset(%s) >= self.data_end(%s)" %
                    (meta.data_offset, self.data_end))

            if (meta.data_offset + meta.data_size) > file_size:
                raise AssertionError(
                    "(meta.data_offset + meta.data_size)(%s) > file_size(%s)" %
                    ((meta.data_offset + meta.data_size), file_size))

            last_data_offset += meta.data_capacity
            last_meta_offset += MetaData.size

        # -----------------------------------------------------------

        if last_meta_offset != self.meta_end:
            raise AssertionError("last_meta_offset(%s) != self.meta_end(%s)" %
                                 (last_meta_offset, self.meta_end))

        if last_data_offset != self.data_end:
            raise AssertionError("last_data_offset(%s) != self.data_end(%s)" %
                                 (last_data_offset, self.data_end))

        # -----------------------------------------------------------

        for key, data_id in self.key2id.items():
            if key != self.id2data[data_id].key:
                raise AssertionError(
                    "key(%s) != self.id2data[ data_id ].key(%s)" %
                    (key, self.id2data[data_id].key))

        # -----------------------------------------------------------

        for data_id, meta in self.id2data.items():
            meta_dump = self.handle.read(meta.offset, MetaData.size)
            stored_meta = MetaData.load(meta_dump)

            if meta.key != stored_meta.key:
                raise AssertionError("meta.key(%s) != stored_meta.key(%s)" %
                                     (meta.key, stored_meta.key))

            if meta.id != stored_meta.id:
                raise AssertionError("meta.id(%s) != stored_meta.id(%s)" %
                                     (meta.id, stored_meta.id))

            if meta.data_size != stored_meta.data_size:
                raise AssertionError(
                    "meta.data_size(%s) != stored_meta.data_size(%s)" %
                    (meta.data_size, stored_meta.data_size))

            if meta.data_capacity != stored_meta.data_capacity:
                raise AssertionError(
                    "meta.data_capacity(%s) != stored_meta.data_capacity(%s)" %
                    (meta.data_capacity, stored_meta.data_capacity))
