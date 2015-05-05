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


import os
import sqlite3
import binascii

from .aql_utils import open_file

__all__ = ('SqlDataFile', )

# ==============================================================================


class ErrorDataFileFormatInvalid(Exception):

    def __init__(self, filename):
        msg = "Invalid format of data file: %s" % (filename,)
        super(ErrorDataFileFormatInvalid, self).__init__(msg)


class ErrorDataFileCorrupted(Exception):

    def __init__(self, filename):
        msg = "Corrupted format of data file: %s" % (filename,)
        super(ErrorDataFileCorrupted, self).__init__(msg)

# ==============================================================================


def _bytes_to_blob_stub(value):
    return value


def _many_bytes_to_blob_stub(values):
    return values


def _blob_to_bytes_stub(value):
    return value

# ----------------------------------------------------------


def _bytes_to_blob_buf(value):
    return buffer(value)        # noqa


def _many_bytes_to_blob_buf(values):
    return map(buffer, values)  # noqa


def _blob_to_bytes_buf(value):
    return bytes(value)


try:
    buffer
except NameError:
    _bytes_to_blob = _bytes_to_blob_stub
    _many_bytes_to_blob = _many_bytes_to_blob_stub
    _blob_to_bytes = _blob_to_bytes_stub

else:
    _bytes_to_blob = _bytes_to_blob_buf
    _many_bytes_to_blob = _many_bytes_to_blob_buf
    _blob_to_bytes = _blob_to_bytes_buf

# ==============================================================================


class SqlDataFile (object):

    __slots__ = (
        'id2key',
        'key2id',
        'connection',
    )

    # -----------------------------------------------------------

    def __init__(self, filename, force=False):

        self.id2key = {}
        self.key2id = {}
        self.connection = None

        self.open(filename, force=force)

    # -----------------------------------------------------------

    def clear(self):
        with self.connection as conn:
            conn.execute("DELETE FROM items")

        self.id2key.clear()
        self.key2id.clear()

    # -----------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # -----------------------------------------------------------

    def _load_ids(self, conn, blob_to_bytes=_blob_to_bytes):

        set_key = self.key2id.__setitem__
        set_id = self.id2key.__setitem__

        for key, data_id in conn.execute("SELECT key,id FROM items"):
            data_id = blob_to_bytes(data_id)
            set_key(key, data_id)
            set_id(data_id, key)

    # -----------------------------------------------------------

    def open(self, filename, force=False):

        self.close()

        try:
            conn = self._open_connection(filename)
        except ErrorDataFileCorrupted:
            os.remove(filename)
            conn = self._open_connection(filename)

        except ErrorDataFileFormatInvalid:
            if not force and not self._is_aql_db(filename):
                raise

            os.remove(filename)
            conn = self._open_connection(filename)

        self._load_ids(conn)

        self.connection = conn

    # -----------------------------------------------------------

    def close(self):

        if self.connection is not None:
            self.connection.close()
            self.connection = None

        self.id2key.clear()
        self.key2id.clear()

    # -----------------------------------------------------------

    @staticmethod
    def _is_aql_db(filename):

        magic_tag = b".AQL.DB."

        with open_file(filename, read=True, binary=True) as f:
            tag = f.read(len(magic_tag))
            return tag == magic_tag

    # -----------------------------------------------------------

    @staticmethod
    def _open_connection(filename):

        conn = None

        try:
            conn = sqlite3.connect(filename,
                                   detect_types=sqlite3.PARSE_DECLTYPES)

            with conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS items("
                    "key INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "id BLOB UNIQUE,"
                    "data BLOB NOT NULL"
                    ")")

        except (sqlite3.DataError, sqlite3.IntegrityError):
            if conn is not None:
                conn.close()
            raise ErrorDataFileCorrupted(filename)

        except sqlite3.DatabaseError:
            if conn is not None:
                conn.close()
            raise ErrorDataFileFormatInvalid(filename)

        conn.execute("PRAGMA synchronous=OFF")

        return conn

    # -----------------------------------------------------------

    def read(self, data_id,
             bytes_to_blob=_bytes_to_blob,
             blob_to_bytes=_blob_to_bytes):

        result = self.connection.execute("SELECT data FROM items where id=?",
                                         (bytes_to_blob(data_id),))

        data = result.fetchone()
        if not data:
            return None

        return blob_to_bytes(data[0])

    # -----------------------------------------------------------

    def write_with_key(self, data_id, data,
                       bytes_to_blob=_bytes_to_blob):

        key = self.id2key.pop(data_id, None)
        if key is not None:
            del self.key2id[key]

        with self.connection as conn:
            cur = conn.execute(
                "INSERT OR REPLACE INTO items(id, data) VALUES (?,?)",
                (bytes_to_blob(data_id), bytes_to_blob(data)))

        key = cur.lastrowid
        self.key2id[key] = data_id
        self.id2key[data_id] = key

        return key

    # -----------------------------------------------------------

    write = write_with_key

    # -----------------------------------------------------------

    def get_ids(self, keys):
        try:
            return tuple(map(self.key2id.__getitem__, keys))
        except KeyError:
            return None

    # -----------------------------------------------------------

    def get_keys(self, data_ids):
        return map(self.id2key.__getitem__, data_ids)

    # -----------------------------------------------------------

    def remove(self, data_ids, many_bytes_to_blob=_many_bytes_to_blob):

        with self.connection as conn:
            conn.executemany("DELETE FROM items WHERE id=?",
                             zip(many_bytes_to_blob(data_ids)))

        get_key = self.id2key.__getitem__
        del_key = self.key2id.__delitem__
        del_id = self.id2key.__delitem__

        for data_id in data_ids:
            key = get_key(data_id)
            del_key(key)
            del_id(data_id)

    # -----------------------------------------------------------

    def self_test(self, blob_to_bytes=_blob_to_bytes):  # noqa
        if self.connection is None:
            if self.id2key:
                raise AssertionError("id2key is not empty")

            if self.key2id:
                raise AssertionError("key2id is not empty")

            return

        key2id = self.key2id.copy()
        id2key = self.id2key.copy()

        items = self.connection.execute("SELECT key,id FROM items")

        for key, data_id in items:

            data_id = blob_to_bytes(data_id)

            d = key2id.pop(key, None)

            if d is None:
                raise AssertionError("key(%s) not in key2id" % (key,))

            if d != data_id:
                raise AssertionError("data_id(%s) != d(%s)" %
                                     (binascii.hexlify(data_id),
                                      binascii.hexlify(d)))

            k = id2key.pop(data_id, None)

            if k is None:
                raise AssertionError("data_id(%s) not in id2key" %
                                     (binascii.hexlify(data_id),))

            if k != key:
                raise AssertionError("key(%s) != k(%s)" % (key, k))

        if key2id:
            raise AssertionError("unknown keys: %s" % (key2id,))

        if id2key:
            raise AssertionError("unknown data_ids: %s" % (id2key,))
