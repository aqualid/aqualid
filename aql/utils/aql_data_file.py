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
  
  _HEADER_STRUCT = struct.Struct(">8sL") # big-endian, 8 bytes(MAGIC TAG), 4 bytes (file version)
  _HEADER_SIZE = _HEADER_STRUCT.size
  
  _KEY_STRUCT = struct.Struct(">Q") # 8 bytes (next unique key)
  _KEY_OFFSET = _HEADER_SIZE
  _KEY_SIZE = _KEY_STRUCT.size
  
  _META_TABLE_HEADER_STRUCT = struct.Struct(">L") # 4 bytes (offset of data area)
  _META_TABLE_HEADER_SIZE = _META_TABLE_HEADER_STRUCT.size
  _META_TABLE_HEADER_OFFSET = _KEY_OFFSET + _KEY_SIZE
  
  _META_TABLE_OFFSET = _META_TABLE_HEADER_OFFSET + _META_TABLE_HEADER_SIZE
  
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
  
  def   _get_file_size( self ):
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
    
    header_dump = table_header_struct.pack( self.data_begin )
    
    self._resize_file( self.data_end )
    self._write_file( table_header_offset, header_dump )
    self._write_file( self.meta_end, b'\0' * (self.data_begin - self.meta_end) )
    self._flush_file()
  
  #//-------------------------------------------------------//
  
  def   _load_meta_table( self, items_dump,
                     meta_size = MetaData.size,
                     table_begin = _META_TABLE_OFFSET ):
    
    table_end = self.meta_end
    
    data_offset = self.data_begin
    data_end = self.data_end
    
    load_meta = MetaData.load
    
    meta_offset = 0
    while meta_offset < table_end:
      meta_dump = items_dump[ meta_offset : meta_offset + meta_size ]
      try:
        meta = load_meta( meta_dump )
        
        data_capacity = meta.data_capacity
        
        if data_capacity == 0:
          # end of meta table marker
          break
        
        meta.offset = meta_offset + table_begin
        meta.data_offset = data_offset
        
        if (data_offset + meta.data_size) > data_end:
          raise ErrorDataFileChunkInvalid()
        
        data_offset = data_offset + data_capacity
        
      except Exception:
        self.data_end = data_offset
        self.meta_end = meta_offset
        self._truncate_file()
        return
      
      self.id2data[ meta.id ] = meta
      if meta.key:
        self.key2id[ meta.key ] = meta.id
      
      meta_offset += meta_size
    
    self.data_end = data_offset
        
  #//-------------------------------------------------------//
  
  def   _init_meta_table( self,
                         table_header_struct = _META_TABLE_HEADER_STRUCT,
                         table_header_offset = _META_TABLE_HEADER_OFFSET,
                         table_header_size = _META_TABLE_HEADER_SIZE,
                         table_begin = _META_TABLE_OFFSET,
                         meta_size = MetaData.size ):
    
    header_dump = self._read_file( table_header_offset, table_header_size )
    
    try:
      data_begin, = table_header_struct.unpack( header_dump )
    except struct.error:
      self._reset_meta_table()
      return
    
    self.meta_end = data_begin
    self.data_begin = data_begin
    self.data_end = self._get_file_size()
    
    if (data_begin <= table_begin) or (data_begin > self.data_end):
      self._reset_meta_table()
      return
    
    table_size = data_begin - table_begin
    
    if (table_size % meta_size) != 0:
      self._reset_meta_table()
      return
    
    dump = self._read_file( table_begin, table_size )
    
    if len(dump) < table_size:
      self._reset_meta_table()
      return
    
    self._load_meta_table( dump )
    
  #//-------------------------------------------------------//
  
  def   _extend_meta_table( self,
                            table_header_struct = _META_TABLE_HEADER_STRUCT,
                            table_header_offset = _META_TABLE_HEADER_OFFSET,
                            table_begin = _META_TABLE_OFFSET ):
    
    data_begin = self.data_begin
    data_end = self.data_end
    
    table_capacity = data_begin - table_begin
    new_data_begin = data_begin + table_capacity
    
    self._move_file_data( new_data_begin, data_begin, data_end - data_begin )
    self._write_file( data_begin, b'\0' * table_capacity )
    
    header_dump = table_header_struct.pack( new_data_begin )
    self._write_file( table_header_offset, header_dump )
    
    self.data_begin = new_data_begin
    self.data_end += table_capacity
    
    for meta in self.id2data.values():
      meta.data_offset += table_capacity
  
  #//-------------------------------------------------------//
  
  def   _extend_data( self, meta, oversize ):
    new_next_data = meta.data_offset + meta.data_capacity
    next_data = new_next_data - oversize
    rest_size = self.data_end - next_data
    if rest_size > 0:
      self._move_file_data( new_next_data, next_data, rest_size )
    
      for meta in self.id2data.values():
        if meta.data_offset >= next_data:
          meta.data_offset += oversize
    
    self.data_end += oversize
  
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
  
  def   clear( self ):
    
    self._reset_meta_table()
    
    self.id2data.clear()
    self.key2id.clear()
  
  #//-------------------------------------------------------//
  
  def   _append( self, key, data_id, data,
                 meta_size = MetaData.size ):
    
    meta_offset = self.meta_end
    if meta_offset == self.data_begin:
      self._extend_meta_table()
    
    data_offset = self.data_end
    
    meta = MetaData( meta_offset, key, data_id, data_offset, len(data) )
    
    self._write_file( data_offset, data )
    self._write_file( meta_offset, meta.dump() )
    
    self.data_end += meta.data_capacity
    self.meta_end += meta_size
    
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
  
  def   read( self, data_id ):
    try:
      meta = self.id2data[ data_id ]
    except KeyError:
      return None
    
    return self._read_file( meta.data_offset, meta.data_size )
  
  #//-------------------------------------------------------//
  
  def   read_by_key( self, key ):
    try:
      meta = self.id2data[ self.key2id[key] ]
    except KeyError:
      return None
    
    return self._read_file( meta.data_offset, meta.data_size )
  
  #//-------------------------------------------------------//
  
  def   write( self, data_id, data ):
    
    try:
      meta = self.id2data[ data_id ]
      self._update( meta, data, update_meta = False)
    except KeyError:
      self._append( 0, data_id, data )
  
  #//-------------------------------------------------------//
  
  def   write_with_key( self, data_id, data ):
    
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
  
  def   map_keys(self, keys):
    try:
      return tuple( map( self.key2id.__getitem__, keys ) )
    except KeyError:
      return None
  
  #//-------------------------------------------------------//
  
  def   __delitem__(self, data_id ):
    self.remove( (data_id,) )
  
  #//-------------------------------------------------------//
  
  def   remove( self, data_ids ):
    return
    
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
    
    if self.stream is None:
      return
    
    file_size = self._get_file_size()
    
    if self.data_begin > file_size:
      raise AssertionError("data_begin(%s) > file_size(%s)" % (self.data_begin, file_size))
    
    if self.data_begin > self.data_end:
      raise AssertionError("data_end(%s) > data_end(%s)" % (self.data_begin, self.data_end))
    
    if self.meta_end > self.data_begin:
      raise AssertionError("meta_end(%s) > data_begin(%s)" % (self.meta_end, self.data_begin))
    
    #//-------------------------------------------------------//
    
    header_dump = self._read_file( self._META_TABLE_HEADER_OFFSET, self._META_TABLE_HEADER_SIZE )
    
    try:
      data_begin, = self._META_TABLE_HEADER_STRUCT.unpack( header_dump )
    except struct.error:
      self._reset_meta_table()
      return
    
    # if self.meta_end != meta_end:
    #   raise AssertionError("self.meta_end(%s) != meta_end(%s)" % (self.meta_end, meta_end))
    
    if self.data_begin != data_begin:
      raise AssertionError("self.data_begin(%s) != data_begin(%s)" % (self.data_begin, data_begin))
    
    #//-------------------------------------------------------//
    
    items = sorted( self.id2data.items(), key = lambda item: item[1].offset )
    
    last_meta_offset = self._META_TABLE_OFFSET
    last_data_offset = self.data_begin
    
    for data_id, meta in items:
      if meta.id != data_id:
        raise AssertionError("meta.id(%s) != data_id(%s)" % (meta.id, data_id))
      
      if meta.key != 0:
        if self.key2id[ meta.key ] != data_id:
          raise AssertionError("self.key2id[ meta.key ](%s) != data_id(%s)" % (self.key2id[ meta.key ], data_id))
      
      if meta.data_capacity < meta.data_size:
        raise AssertionError("meta.data_capacity(%s) < meta.data_size (%s)" % (meta.data_capacity, meta.data_size))
      
      if meta.offset >= self.meta_end:
        raise AssertionError("meta.offset(%s) >= self.meta_end(%s)" % (meta.offset, self.meta_end))
      
      if meta.offset != last_meta_offset:
        raise AssertionError("meta.offset(%s) != last_meta_offset(%s)" % (meta.offset, last_meta_offset))
      
      if meta.data_offset != last_data_offset:
        raise AssertionError("meta.data_offset(%s) != last_data_offset(%s)" % (meta.data_offset, last_data_offset))
      
      if meta.data_offset >= self.data_end:
        raise AssertionError("meta.data_offset(%s) >= self.data_end(%s)" % (meta.data_offset, self.data_end))
      
      if (meta.data_offset + meta.data_size) > file_size:
        raise AssertionError("(meta.data_offset + meta.data_size)(%s) > file_size(%s)" % ((meta.data_offset + meta.data_size), file_size))
      
      last_data_offset += meta.data_capacity
      last_meta_offset += MetaData.size
    
    #//-------------------------------------------------------//
    
    if last_data_offset != self.data_end:
      raise AssertionError("last_data_offset(%s) != self.data_end(%s)" % (last_data_offset, self.data_end))
    
    #//-------------------------------------------------------//
    
    for key, data_id in self.key2id.items():
      if key != self.id2data[ data_id ].key:
        raise AssertionError("key(%s) != self.id2data[ data_id ].key(%s)" % (key, self.id2data[ data_id ].key))
    
    #//-------------------------------------------------------//
    
    for data_id, meta in self.id2data.items():
      meta_dump = self._read_file( meta.offset, MetaData.size )
      stored_meta = MetaData.load( meta_dump )
      
      if meta.key != stored_meta.key:
        raise AssertionError("meta.key(%s) != stored_meta.key(%s)" % (meta.key, stored_meta.key))
      
      if meta.id != stored_meta.id:
        raise AssertionError("meta.id(%s) != stored_meta.id(%s)" % (meta.id, stored_meta.id))
      
      if meta.data_size != stored_meta.data_size:
        raise AssertionError("meta.data_size(%s) != stored_meta.data_size(%s)" % (meta.data_size, stored_meta.data_size))
      
      if meta.data_capacity != stored_meta.data_capacity:
        raise AssertionError("meta.data_capacity(%s) != stored_meta.data_capacity(%s)" % (meta.data_capacity, stored_meta.data_capacity))
      
      
