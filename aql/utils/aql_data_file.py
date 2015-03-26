#
# Copyright (c) 2011-2014 The developers of Aqualid project
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

__all__ = ( 'DataFile', )

import os
import struct
import mmap

from aql.util_types import AqlException

from .aql_utils import openFile

#//===========================================================================//

class   ErrorDataFileFormatInvalid( AqlException ):
  def   __init__( self ):
    msg = "Data file format is not valid."
    super(ErrorDataFileFormatInvalid, self).__init__( msg )

#//===========================================================================//

class   ErrorDataFileChunkInvalid( AqlException ):
  def   __init__( self ):
    msg = "Data file chunk format is not valid."
    super(ErrorDataFileChunkInvalid, self).__init__( msg )

#//===========================================================================//

class   ErrorDataFileVersionInvalid( AqlException ):
  def   __init__( self ):
    msg = "Data file version is changed."
    super(ErrorDataFileVersionInvalid, self).__init__( msg )

#//===========================================================================//

class   ErrorDataFileCorrupted( AqlException ):
  def   __init__( self ):
    msg = "Data file is corrupted"
    super(ErrorDataFileCorrupted, self).__init__( msg )

#//===========================================================================//

class   MetaData (object):
  __slots__ = (
    
    'offset',
    'key',
    'id',
    'data_offset',
    'data_size',
    'data_capacity',
  )
  
  _META_STRUCT = struct.Struct(">Q16sLL")   # big-endian, 8 bytes (key), 16 bytes (id), 4 bytes (size), 4 bytes (capacity)
  size = _META_STRUCT.size
  
  #//-------------------------------------------------------//
  
  def   __init__( self, meta_offset, key, data_id, data_offset, data_size ):
    
    self.offset         = meta_offset
    self.key            = key
    self.id             = data_id
    self.data_offset    = data_offset
    self.data_size      = data_size
    self.data_capacity  = data_size + 4
  
  #//-------------------------------------------------------//
  
  def   dump( self, meta_struct = _META_STRUCT ):
    return meta_struct.pack( self.key, self.id, self.data_size, self.data_capacity )
  
  #//-------------------------------------------------------//
  
  @classmethod
  def  load( cls, dump, meta_struct = _META_STRUCT ):
    
    self = cls.__new__(cls)
    
    try:
      self.key, self.id, data_size, data_capacity = meta_struct.unpack( dump )
    except struct.error:
      raise ErrorDataFileChunkInvalid()
    
    if data_capacity < data_size:
      raise ErrorDataFileChunkInvalid()
    
    self.data_size      = data_size
    self.data_capacity  = data_capacity
    
    return self
  
  #//-------------------------------------------------------//
  
  def   resize( self, data_size ):
    
    self.data_size = data_size
    
    capacity = self.data_capacity
    if capacity >= data_size:
      return 0
    
    self.data_capacity = data_size + min( data_size // 4, 128 )
    
    return self.data_capacity - capacity
  
  #//-------------------------------------------------------//
  
  def   __repr__(self):
    return self.__str__()
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    s = []
    for v in self.__slots__:
      s.append( "%s: %s" % (v, getattr( self, v )) ) 
    
    return ", ".join( s )

#//===========================================================================//

class DataFile (object):
  
  __slots__ = (
    'next_key',
    'id2data',
    'key2id',
    'meta_end',
    'data_begin',
    'data_end',
    'stream',
    'memmap',
  )
  
  # +-----------------------------------+
  # |8 bytes (MAGIC TAG)                |
  # +-----------------------------------+
  # |4 bytes (file version)             |
  # +-----------------------------------+
  # |8 bytes (next unique key)          |
  # +-----------------------------------+
  # |4 bytes (meta end)                 |
  # +-----------------------------------+
  # |4 bytes (data offset)              |
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
  
  _HEADER_STRUCT = struct.Struct(">8sL") # big-endian, 8 bytes(MAGIC TAG), 4 bytes (file version)
  _HEADER_SIZE = _HEADER_STRUCT.size
  
  _KEY_STRUCT = struct.Struct(">Q") # 8 bytes (next unique key)
  _KEY_OFFSET = _HEADER_SIZE
  _KEY_SIZE = _KEY_STRUCT.size
  
  _META_TABLE_HEADER_STRUCT = struct.Struct(">LL") # 4 bytes (offset of meta table end), 4 bytes (offset of data area)
  _META_TABLE_HEADER_SIZE = _META_TABLE_HEADER_STRUCT.size
  _META_TABLE_HEADER_OFFSET = _KEY_OFFSET + _KEY_SIZE
  
  _META_TABLE_OFFSET = _META_TABLE_HEADER_OFFSET + _META_TABLE_HEADER_SIZE
  
  #//-------------------------------------------------------//
  
  def   __moveLocations( self, start_offset, shift_size ):
    for location in self.locations.values():
      if location.offset > start_offset:
        location.offset += shift_size
  
  #//-------------------------------------------------------//
  
  def   __init__( self, filename, force = False ):
    
    self.id2data = {}
    self.key2id = {}
    self.meta_end = 0
    self.data_begin = 0
    self.data_end = 0
    self.stream = None
    self.memmap = None
    
    self.open( filename, force = force )
  
  #//-------------------------------------------------------//
  
  def   __enter__(self):
    return self

  def   __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  #//-------------------------------------------------------//
  
  def   _init_header( self, stream, force, header_struct = _HEADER_STRUCT ):
    
    stream.seek(0)
    header = stream.read( header_struct.size )
    
    try:
      tag, version = header_struct.unpack( header )
      
      if tag != self.MAGIC_TAG:
        if not force:
          raise ErrorDataFileFormatInvalid()
      
      elif version == self.VERSION:
        return
      
    except struct.error:
      if header and not force:
        raise ErrorDataFileFormatInvalid()
    
    #//-------------------------------------------------------//
    # init the file
    stream.truncate( 0 )
    header = header_struct.pack( self.MAGIC_TAG, self.VERSION )
    stream.write( header )
    stream.flush()
    
  #//-------------------------------------------------------//
  
  def   _open_file(self, filename, force ):
    stream = openFile( filename, write = True, binary = True, sync = False )
    
    self._init_header( stream, force )
    
    self.stream = stream
    
    try:
      self.memmap = mmap.mmap( stream.fileno(), 0, access = mmap.ACCESS_WRITE )
    except Exception:
      pass
  
  #//-------------------------------------------------------//
  
  def   _read_file( self, offset, size ):
    return self.memmap[ offset : offset + size ]
  
  #//-------------------------------------------------------//
  
  def   _write_file( self, offset, data ):
    memmap = self.memmap
    
    end_offset = offset + len(data)
    if end_offset > memmap.size():
      self._resize_file( end_offset )
    
    memmap[ offset : end_offset ] = data
  
  #//-------------------------------------------------------//
  
  def   _move_file_data( self, dest, src, size ):
    memmap = self.memmap
    end_offset = dest + size
    if end_offset > memmap.size():
      self._resize_file( end_offset )
    
    memmap.move( dest, src, size )
  
  #//-------------------------------------------------------//
  
  def   _resize_file( self, size ):
    page_size = mmap.ALLOCATIONGRANULARITY
    size = ((size + (page_size -1 )) // page_size) * page_size
    if size == 0:
      size = page_size
    self.memmap.resize( size )
  
  #//-------------------------------------------------------//
  
  def   _get_file_size( self, size ):
    return self.memmap.size()
  
  #//-------------------------------------------------------//
  
  def   _flush_file( self ):
    return self.memmap.flush()
  
  #//-------------------------------------------------------//
  
  def   _key_generator( self, key_offset = _KEY_OFFSET, key_struct = _KEY_STRUCT, MAX_KEY = (2 ** 64) - 1 ):
    
    key_dump = self._read_file( key_offset, key_struct.size )
    try:
      next_key, = key_struct.unpack( key_dump )
    except struct.error:
      next_key = 0
    
    key_pack = key_struct.pack
    write_file = self._write_file
    
    while True:
      
      if next_key < MAX_KEY:
        next_key += 1
      else:
        next_key = 1    # this should never happen
      
      write_file( key_offset, key_pack( next_key ) )
      yield next_key
  
  #//-------------------------------------------------------//
  
  def   _reset_meta_table( self,
                      meta_size     = MetaData.size,
                      table_offset  = _META_TABLE_OFFSET ):
    
    self.meta_end = table_offset
    self.data_begin = table_offset + meta_size * 1024
    self.data_end = self.data_begin
    
    self._truncate_file()
  
  #//-------------------------------------------------------//
  
  def   _truncate_file( self,
                        table_header_struct = _META_TABLE_HEADER_STRUCT,
                        table_header_offset = _META_TABLE_HEADER_OFFSET ):
    
    header_dump = table_header_struct.pack( self.meta_end, self.data_end )
    
    self._resize_file( self.data_end )
    self._write_file( table_header_offset, header_dump )
    self._flush_file()
  
  #//-------------------------------------------------------//
  
  def   _load_meta_table( self, items_dump,
                     meta_size = MetaData.size,
                     table_begin = _META_TABLE_OFFSET ):
    
    table_end = self.meta_end
    
    data_offset = self.data_begin
    data_end = self.data_end
    
    load_meta = MetaData.load
    
    meta_offset = table_begin
    while meta_offset < table_end:
      meta_dump = items_dump[meta_offset:meta_size]
      try:
        meta = load_meta( meta_dump )
        
        meta.offset = meta_offset
        meta.data_offset = data_offset
        
        if (data_offset + meta.data_size) > data_end:
          raise ErrorDataFileChunkInvalid()
        
        data_offset = data_offset + meta.data_capacity
        
      except Exception:
        break
      
      self.id2data[ meta.id ] = meta
      if meta.key:
        self.key2id[ meta.key ] = meta.id
      
      meta_offset += meta_size
    
    self.data_end = data_offset
    
    if meta_offset < table_end:
      self.meta_end = meta_offset
      self._truncate_file()
        
  #//-------------------------------------------------------//
  
  def   _init_meta_table( self,
                         table_header_struct = _META_TABLE_HEADER_STRUCT,
                         table_header_offset = _META_TABLE_HEADER_OFFSET,
                         table_header_size = _META_TABLE_HEADER_SIZE,
                         table_begin = _META_TABLE_OFFSET,
                         meta_size = MetaData.size ):
    
    header_dump = self._read_file( table_header_offset, table_header_size )
    
    try:
      table_end, data_begin = table_header_struct.unpack( header_dump )
    except struct.error:
      self._reset_meta_table()
      return
    
    self.meta_end = table_end
    self.data_begin = data_begin
    self.data_end = self._get_file_size()
    
    if (table_end > data_begin) or (data_begin > self.data_end):
      self._reset_meta_table()
      return
    
    table_size = table_end - table_begin
    reserved_size = data_begin - table_end
    
    if ((table_size % meta_size) != 0) or ((reserved_size % meta_size) != 0):
      self._reset_meta_table()
      return
    
    dump = self._read_file( table_begin, table_size )
    
    if len(dump) < table_size:
      self._reset_meta_table()
      return
    
    self._load_meta_table( dump )
    
  #//-------------------------------------------------------//
  
  def   _extend_meta_table( self,
                            table_begin = _META_TABLE_OFFSET ):
    
    data_begin = self.data_begin
    data_end = self.data_end
    
    table_capacity = data_begin - table_begin
    new_data_begin = data_begin + table_capacity
    
    self._move_file_data( new_data_begin, data_begin, data_end - data_begin )
    
    for meta in self.id2data.values():
      meta.data_offset += table_capacity
  
  #//-------------------------------------------------------//
  
  def   _extend_data( self, meta, oversize ):
    next_data = meta.data_offset + meta.data_capacity
    offset = self.data_end - next_data
    self._move_file_data( next_data + oversize, next_data, offset )
    
    for meta in self.id2data.values():
      if meta.data_offset >= next_data: 
        meta.data_offset += offset
  
  #//-------------------------------------------------------//
  
  def  open( self, filename, force = False ):
    self.close()
    
    self._open_file( filename, force )
    self.next_key = self._key_generator()
    
    self._init_meta_table()
    
  #//-------------------------------------------------------//
  
  def   close(self):
    
    mem = self.memmap
    if mem is not None:
      mem.flush()
      mem.close()
      self.memmap = None
    
    stream = self.stream
    if stream is not None:
      stream.flush()
      stream.close()
      self.stream = None
      
      self.id2data.clear()
      self.key2id.clear()
      self.meta_end = 0
      self.data_begin = 0
      self.data_end = 0
  
  #//-------------------------------------------------------//
  
  def   clear( self, header_size = _HEADER_SIZE ):
    
    stream = self.stream
    if stream is None:
      return
      
    memmap = self.memmap
    if memmap is not None:
      memmap.close()
    
    stream.truncate( header_size )
    stream.flush()
    stream.seek( 0, os.SEEK_END )
    
    self.memmap = mmap.mmap( stream.fileno(), 0 )
    
    self.id2data.clear()
    self.key2id.clear()
  
  #//-------------------------------------------------------//
  
  def   _append( self, key, data_id, data,
                 meta_size = MetaData.size ):
    
    meta_offset = self.meta_end
    if meta_offset == self.data_begin:
      self._extend_meta_table()
    
    self.meta_end += meta_size
    
    data_offset = self.data_end
    
    meta = MetaData( meta_offset, key, data_id, data_offset, len(data) )
    
    self._write_file( data_offset, data )
    self._write_file( meta_offset, meta.dump() )
    
    self.data_end += meta.data_capacity
    self.meta_end += meta_offset + meta_size
    
    self.id2data[ data_id ] = meta
  
  #//-------------------------------------------------------//
  
  def   _update( self, meta, data, update_meta ):
    
    data_size = len(data)
    
    if meta.data_size != data_size:
      update_meta = True
      oversize = meta.resize( data_size )
      if oversize > 0:
        self._extend_data( meta, oversize )
    
    if update_meta:
      self._write_file( meta.offset, meta.dump() )
    
    self._write_file( meta.data_offset, data )
  
  #//-------------------------------------------------------//
  
  def   store( self, data_id, data ):
    
    meta = self.id2data.get( data_id )
    if meta is None:
      self._append( 0, data_id, data )
    else:
      self._update( meta, data, update_meta = False)
  
  #//-------------------------------------------------------//
  
  def   store_with_key( self, data_id, data ):
    
    meta = self.id2data.get( data_id )
    
    key = next(self.next_key)
    
    if meta is None:
      self._append( key, data_id, data )
    else:
      try:
        del self.key2id[ meta.key ]
      except KeyError:
        pass
      
      meta.key = key
      
      self._update( meta, data, update_meta = True )
      
      self.key2id[ key ] = data_id
    
    return key
  
  #//-------------------------------------------------------//
  
  def   get_ids_by_keys(self, keys):
    try:
      return tuple( map( self.key2id.__getitem__, keys ) )
    except KeyError:
      return None
  
  #//-------------------------------------------------------//
  
  def   get_data( self, data_id ):
    try:
      meta = self.id2data[ data_id ]
    except KeyError:
      return None
    
    return self._read_file( meta.data_offset, meta.data_size )
  
  #//-------------------------------------------------------//
  
  def   __delitem__(self, key):
    self.remove( (key,) )
  
  #//-------------------------------------------------------//
  
  def   remove( self, data_ids ):
    
    del_keys = frozenset( del_keys )
    
    start_offset = self.__findMinOffset( del_keys )
    if start_offset == -1:
      return
    
    rest_locations = self.__findRestLocations( start_offset, del_keys )
    
    rest_chunks = self.__readAndMoveRestLocations( rest_locations, start_offset )
    
    stream = self.stream
    
    stream.truncate( start_offset )
    stream.seek( start_offset )
    stream.write( rest_chunks )
    
    self.file_size = start_offset + len( rest_chunks )
    
    locations = self.locations
    for key in del_keys:
      del locations[ key ]
    
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    
    if self.stream is not None:
      file_size = self.file_header.size()
    else:
      file_size = 0
    
    next_key = self.file_header.uid
    
    for key,location in self.locations.items():
      
      if key >= next_key:
        raise AssertionError("location.key (%s) >= next key (%s)" % (key, next_key))
      
      if location.capacity < location.size:
        raise AssertionError("location.capacity(%s) < location.size (%s)" % (location.capacity, location.size))
      
      file_size += location.space()
    
    if file_size != self.file_size:
      raise AssertionError("file_size (%s) != self.file_size (%s)" % (file_size, self.file_size) )
    
    ordered_location = sorted( self.locations.values(), key = lambda loc: loc.offset )
    
    if self.stream is not None:
      real_file_size = self.stream.seek( 0, os.SEEK_END )
      if ordered_location:
        
        last_location = ordered_location[-1]
        last_data_offset = last_location.offset + last_location.header_size
        
        if real_file_size < (last_data_offset + last_location.size) or \
           real_file_size > (last_data_offset + last_location.capacity) :
          raise AssertionError("Invalid real_file_size(%s), last_location: %s" % (real_file_size, last_location) )
      
      else:
        if (file_size != real_file_size) and (real_file_size != 0 or file_size != self.file_header.size()):
          raise AssertionError("file_size(%s) != real_file_size(%s)" % (file_size, real_file_size))
    
    prev_location = None
    for location in ordered_location:
      if prev_location is not None:
        if (prev_location.offset + prev_location.capacity + prev_location.header_size) != location.offset:
          raise AssertionError("Messed locations: [%s] [%s]" % (prev_location, location))
      
      prev_location = location
    
    #//-------------------------------------------------------//
    
    if self.stream is not None:
      file_header = DataFileHeader()
      file_header.load( self.stream )
      
      if self.file_header != file_header:
        raise AssertionError("self.file_header != file_header")
      
      offset = file_header.size()
      
      while True:
        key, location, size = DataFileChunk.load( self.stream, offset )
        if key == -1:
          break
        
        l = self.locations[key]

        #noinspection PyUnresolvedReferences
        if (l.size != location.size) or (l.capacity != location.capacity):
          raise AssertionError("self.locations[%s] (%s) != location (%s)" % (key, l, location))
        
        offset += size
