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


import binascii
import io

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = (
    'pickleable', 'EntityPickler',
)

# ==============================================================================

_KNOWN_TYPE_NAMES = {}
_KNOWN_TYPE_IDS = {}

# ==============================================================================


class EntityPickler (object):

    __slots__ = ('pickler', 'unpickler', 'buffer')

    def __init__(self):

        membuf = io.BytesIO()

        pickler = pickle.Pickler(membuf, protocol=pickle.HIGHEST_PROTOCOL)
        pickler.fast = True

        unpickler = pickle.Unpickler(membuf)

        pickler.persistent_id = self.persistent_id
        unpickler.persistent_load = self.persistent_load

        self.pickler = pickler
        self.unpickler = unpickler
        self.buffer = membuf

    # -----------------------------------------------------------
    @staticmethod
    def persistent_id(entity, known_type_names=_KNOWN_TYPE_NAMES):

        entity_type = type(entity)
        type_name = _typeName(entity_type)

        try:
            type_id = known_type_names[type_name]

            return type_id, entity.__getnewargs__()
        except KeyError:
            return None

    # -----------------------------------------------------------
    @staticmethod
    def persistent_load(pid, known_type_ids=_KNOWN_TYPE_IDS):

        type_id, new_args = pid

        try:
            entity_type = known_type_ids[type_id]
            return entity_type.__new__(entity_type, *new_args)

        except KeyError:
            raise pickle.UnpicklingError("Unsupported persistent object")

    # -----------------------------------------------------------

    def dumps(self, entity):
        buf = self.buffer
        buf.seek(0)
        buf.truncate(0)
        self.pickler.dump(entity)

        return buf.getvalue()

    # -----------------------------------------------------------

    def loads(self, bytes_object):
        buf = self.buffer
        buf.seek(0)
        buf.truncate(0)
        buf.write(bytes_object)
        buf.seek(0)

        return self.unpickler.load()

# ==============================================================================


def _typeName(entity_type):
    return entity_type.__module__ + '.' + entity_type.__name__

# ==============================================================================


def pickleable(entity_type,
               known_type_names=_KNOWN_TYPE_NAMES,
               known_type_ids=_KNOWN_TYPE_IDS):

    if type(entity_type) is type:
        type_name = _typeName(entity_type)
        type_id = binascii.crc32(type_name.encode("utf-8")) & 0xFFFFFFFF

        other_type = known_type_ids.setdefault(type_id, entity_type)
        if other_type is not entity_type:
            raise Exception(
                "Two different type names have identical CRC32 checksum:"
                " '%s' and '%s'" % (_typeName(other_type), type_name))

        known_type_names[type_name] = type_id

    return entity_type
