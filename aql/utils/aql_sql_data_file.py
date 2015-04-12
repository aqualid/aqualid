#
# Copyright (c) 2015 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = ('SqlDataFile', )

import os
import sqlite3

from .aql_utils import openFile

# //===========================================================================//


class ErrorDataFileFormatInvalid(Exception):

    def __init__(self):
        msg = "Data file format is not valid."
        super(ErrorDataFileFormatInvalid, self).__init__(msg)

# //===========================================================================//


class SqlDataFile (object):

    __slots__ = (
        'id2key',
        'key2id',
        'connection',
    )

    # //-------------------------------------------------------//

    def __init__(self, filename, force=False):

        self.id2key = {}
        self.key2id = {}
        self.connection = None

        self.open(filename, force=force)

    # //-------------------------------------------------------//

    def clear(self):
        with self.connection as conn:
            conn.execute("DELETE FROM items")

        self.id2key.clear()
        self.key2id.clear()

    # //-------------------------------------------------------//

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # //-------------------------------------------------------//

    def _load_ids(self, conn):

        set_key = self.key2id.__setitem__
        set_id = self.id2key.__setitem__

        for key, data_id in conn.execute("SELECT key,id FROM items"):
            set_key(key, data_id)
            set_id(data_id, key)

    # //-------------------------------------------------------//

    def open(self, filename, force=False):

        self.close()

        try:
            conn = self._open_connection(filename)
        except (sqlite3.DataError, sqlite3.IntegrityError):
            os.remove(filename)
            try:
                conn = self._open_connection(filename)
            except Exception:
                raise ErrorDataFileFormatInvalid()

        except sqlite3.DatabaseError:
            if not force and not self._is_aql_db(filename):
                raise ErrorDataFileFormatInvalid()

            os.remove(filename)
            try:
                conn = self._open_connection(filename)
            except Exception:
                raise ErrorDataFileFormatInvalid()

        self._load_ids(conn)

        self.connection = conn

    # //-------------------------------------------------------//

    def close(self):

        if self.connection is not None:
            self.connection.close()
            self.connection = None

        self.id2key.clear()
        self.key2id.clear()

    # //-------------------------------------------------------//

    @staticmethod
    def _is_aql_db(filename):

        MAGIC_TAG = b".AQL.DB."

        with openFile(filename, read=True, binary=True) as f:
            tag = f.read(len(MAGIC_TAG))
            return tag == MAGIC_TAG

    # //-------------------------------------------------------//

    @staticmethod
    def _open_connection(filename):

        conn = None

        try:
            conn = sqlite3.connect(filename)

            with conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS items( key INTEGER PRIMARY KEY AUTOINCREMENT, id blob UNIQUE, data blob NOT NULL)")

        except Exception:
            if conn is not None:
                conn.close()
            raise

        conn.text_factory = str
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA mmap_size=10000000")

        return conn

    # //-------------------------------------------------------//

    def read(self, data_id):

        result = self.connection.execute(
            "SELECT data FROM items where id=?", (data_id,))

        data = result.fetchone()
        if not data:
            return None

        return data[0]

    # //-------------------------------------------------------//

    def write_with_key(self, data_id, data):

        key = self.id2key.pop(data_id, None)
        if key is not None:
            del self.key2id[key]

        with self.connection as conn:
            cur = conn.execute(
                "INSERT OR REPLACE INTO items(id, data) VALUES (?,?)", (data_id, data))

        key = cur.lastrowid
        self.key2id[key] = data_id
        self.id2key[data_id] = key

        return key

    # //-------------------------------------------------------//

    write = write_with_key

    # //-------------------------------------------------------//

    def get_ids(self, keys):
        try:
            return tuple(map(self.key2id.__getitem__, keys))
        except KeyError:
            return None

    # //-------------------------------------------------------//

    def get_keys(self, data_ids):
        return map(self.id2key.__getitem__, data_ids)

    # //-------------------------------------------------------//

    def remove(self, data_ids):
        with self.connection as conn:
            conn.executemany("DELETE FROM items WHERE id=?", zip(data_ids))

        get_key = self.id2key.__getitem__
        del_key = self.key2id.__delitem__
        del_id = self.id2key.__delitem__

        for data_id in data_ids:
            key = get_key(data_id)
            del_key(key)
            del_id(data_id)

    # //-------------------------------------------------------//

    def selfTest(self):
        if self.connection is None:
            if self.id2key:
                raise AssertionError("id2key is not empty")

            if self.key2id:
                raise AssertionError("key2id is not empty")

            return

        key2id = self.key2id.copy()
        id2key = self.id2key.copy()

        for key, data_id in self.connection.execute("SELECT key,id FROM items"):
            if key2id.pop(key, None) is None:
                raise AssertionError("key(%s) not in self.key2id" % (key,))

            if id2key.pop(data_id, None) is None:
                raise AssertionError(
                    "data_id(%s) not in self.id2key" % (data_id,))

        if key2id:
            raise AssertionError("unknown keys: %s" % (key2id,))

        if id2key:
            raise AssertionError("unknown data_ids: %s" % (id2key,))
