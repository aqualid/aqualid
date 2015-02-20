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

class   DataFileChunk (object):
  __slots__ = \
  (
    'offset',
    'capacity',
    'size',
  )
  
  header_struct = struct.Struct(">QLL") # big-endian, 8 bytes (key), 4 bytes (capacity), 4 bytes (size)
  header_size = header_struct.size
  
  #//-------------------------------------------------------//
  
  def   __init__(self, offset ):
    
    self.offset = offset
    self.capacity = 0
    self.size = 0
  
  #//-------------------------------------------------------//
  
  @classmethod
  def  load( cls, stream, offset, header_size = header_size, header_struct = header_struct ):
    
    stream.seek( offset )
    header = stream.read( header_size )
    
    if len(header) < header_size:
      return -1, None, 0
    
    key, capacity, size = header_struct.unpack( header )
    
    if capacity < size:
      raise ErrorDataFileChunkInvalid()
    
    self = cls.__new__(cls)
    self.offset = offset
    self.capacity = capacity
    self.size = size
    
    return key, self, header_size + capacity
  
  #//-------------------------------------------------------//
  
  def   pack( self, key, data, reserve = True, header_struct = header_struct ):
    
    size = len(data)
    
    oversize = 0
    
    capacity = self.capacity
    if capacity < size:
      self.capacity = size + (min( size // 4, 64 ) if reserve else 4)
      
      oversize = self.capacity - capacity
    
    self.size = size
    
    header = header_struct.pack( key, self.capacity, size )
    
    chunk = bytearray(header)
    chunk += data
    
    return chunk, oversize
  
  #//-------------------------------------------------------//
  
  def   data( self, stream, header_size = header_size ):
    stream.seek( self.offset + header_size )
    return stream.read( self.size )
  
  #//-------------------------------------------------------//
  
  def   chunk( self, stream, header_size = header_size ):
    stream.seek( self.offset )
    return stream.read( header_size + self.size ) + bytearray( self.capacity - self.size )
  
  #//-------------------------------------------------------//
  
  def   chunkSize( self, header_size = header_size ):
    return header_size + self.capacity
  
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

class DataFileHeader( object ):
  
  __slots__ = \
  (
    'uid',
  )
  
  MAGIC_TAG = b".AQL.DB."
  VERSION = 0
  MAX_UID = (2 ** 64) - 1
  
  header_struct = struct.Struct(">8sLQ") # big-endian, 8 bytes(MAGIC TAG), 4 bytes (file version), 8 bytes (next unique ID)
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self.uid = 0
  
  #//-------------------------------------------------------//
  def   __eq__(self, other):
    return self.uid == other.uid
  
  #//-------------------------------------------------------//
  
  def   __ne__(self, other):
    return self.uid != other.uid
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   size( header_struct = header_struct ):
    return header_struct.size
  
  #//-------------------------------------------------------//
  
  def   load(self, stream, header_struct = header_struct ):
    stream.seek(0)
    header = stream.read( header_struct.size )
    
    if header:
      try:
        tag, version, self.uid = header_struct.unpack( header )
      except struct.error:
        raise ErrorDataFileFormatInvalid()
      
      if tag != self.MAGIC_TAG:
        raise ErrorDataFileFormatInvalid()
      
      if version != self.VERSION:
        raise ErrorDataFileVersionInvalid()
  
  #//-------------------------------------------------------//
  
  def   save( self, stream, header_struct = header_struct ):
    header = header_struct.pack( self.MAGIC_TAG, self.VERSION, self.uid )
    stream.seek(0)
    stream.write( header )
  
  #//-------------------------------------------------------//
  
  def   nextKey( self, stream, max_uid = MAX_UID ):
    key = self.uid
    
    if key < max_uid:
      self.uid += 1
    else:
      self.uid = 0    # it should never happen
    
    self.save( stream )
    
    return key
    
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
  
  __slots__ = \
  (
    'locations',
    'file_header',
    'file_size',
    'stream',
  )
  
  #//-------------------------------------------------------//
  
  def   __moveLocations( self, start_offset, shift_size ):
    for location in self.locations.values():
      if location.offset > start_offset:
        location.offset += shift_size
  
  #//-------------------------------------------------------//
  
  def   __init__( self, filename, force = False ):
    
    self.locations = {}
    self.file_header = DataFileHeader()
    self.file_size = 0
    self.stream = None
    
    self.open( filename, force = force )
  
  #//-------------------------------------------------------//
  
  def   __enter__(self):
    return self

  #noinspection PyUnusedLocal
  def   __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  #//-------------------------------------------------------//
  
  def  open( self, filename, force = False ):
    self.close()
    
    stream = openFile( filename, write = True, binary = True, sync = False )
    
    self.stream = stream
    
    try:
      self.file_header.load( stream )
    except ErrorDataFileVersionInvalid:
      self.clear()
      return
    except ErrorDataFileFormatInvalid:
      if not force:
        raise
      
      self.clear()
      return
    
    offset = self.file_header.size()
    stream = self.stream
    locations = self.locations
    
    file_size = stream.seek( 0, os.SEEK_END )
    
    next_key = self.file_header.uid
    
    invalid_keys = []
    
    try:
      while True:
        key, location, size = DataFileChunk.load( stream, offset )
        
        if location is None:
          break
        
        if (offset + location.size) > file_size:
          raise ErrorDataFileChunkInvalid()
        
        if key >= next_key:
          invalid_keys.append( key )
        
        locations[ key ] = location
        offset += size
    
    except ErrorDataFileChunkInvalid:
      stream.truncate( offset )
      stream.flush()
    
    if invalid_keys:
      self.remove( invalid_keys )
    
    self.file_size = offset
  
  #//-------------------------------------------------------//
  
  def   __truncate( self, size ):
    stream = self.stream
    if stream is not None:
      stream.seek( size )
      stream.truncate( size )
      stream.flush()
  
  #//-------------------------------------------------------//
  
  def   flush(self):
    stream = self.stream
    if stream is not None:
      stream.flush()
  
  #//-------------------------------------------------------//
  
  def   close(self):
    stream = self.stream
    if stream is not None:
      stream.flush()
      stream.close()
      self.stream = None
      
      self.locations.clear()
      self.file_size = 0
  
  #//-------------------------------------------------------//
  
  def   clear(self):
    
    file_header = DataFileHeader()
    
    stream = self.stream
    if stream is not None:
      stream.truncate( 0 )
      file_header.save( stream )
      stream.flush()
          
    self.file_header = file_header
    self.locations.clear()
    self.file_size = file_header.size()

    
  
  #//-------------------------------------------------------//
  
  def append( self, data ):
    
    stream  = self.stream
    key     = self.file_header.nextKey( stream )
    offset  = self.file_size
    
    location = DataFileChunk( offset )
    
    chunk, oversize = location.pack( key, data, reserve = False )
    
    stream.seek( offset )
    stream.write( chunk )
    
    self.file_size += location.chunkSize()
    self.locations[key] = location
    
    return key
  
  #//-------------------------------------------------------//
  
  def   modify(self, key, data ):
    
    stream = self.stream
    
    locations = self.locations
    location = locations[ key ]
    
    tail_offset = location.offset + location.chunkSize()
    chunk, oversize = location.pack( key, data, reserve = True )
    
    if oversize > 0:
      chunk += bytearray( location.capacity - location.size )
      
      stream.seek( tail_offset ); chunk += stream.read()
      
      self.file_size += oversize
      self.__moveLocations( location.offset, oversize )
      
    stream.seek( location.offset )
    stream.write( chunk )
  
  #//-------------------------------------------------------//
  
  def   replace(self, key, data ):
    
    stream = self.stream
    
    locations = self.locations
    location = locations[ key ]
    del locations[ key ]
    
    key = self.file_header.nextKey( stream )
    locations[ key ] = location
    
    tail_offset = location.offset + location.chunkSize()
    chunk, oversize = location.pack( key, data, reserve = True )
    
    if oversize > 0:
      chunk += bytearray( location.capacity - location.size )
      
      stream.seek( tail_offset ); chunk += stream.read()
      
      self.file_size += oversize
      self.__moveLocations( location.offset, oversize )
      
    stream.seek( location.offset )
    stream.write( chunk )
    
    return key
  
  #//-------------------------------------------------------//
  
  def   __delitem__(self, key):
    self.remove( (key,) )
  
  #//-------------------------------------------------------//
  
  def   __findMinOffset( self, keys ):
    start_offset = -1
    
    locations = self.locations
    
    for key in keys:
      try:
        location = locations[ key ]
        if (start_offset == -1) or (start_offset > location.offset):
          start_offset = location.offset
      except KeyError:
        pass
      
    return start_offset
    
  #//-------------------------------------------------------//
  
  def   __findRestLocations( self, start_offset, del_keys ):
    
    locations = []
    
    for key, location in self.locations.items():
      if key not in del_keys:
        if location.offset > start_offset:
          locations.append( location )
    
    return locations
  
  #//-------------------------------------------------------//
  
  def   __readAndMoveRestLocations( self, locations, start_offset ):
    
    chunks = bytearray()
    
    stream = self.stream
    
    for location in locations:
      chunk = location.chunk( stream )
      location.offset = start_offset
      start_offset += len( chunk )
      chunks += chunk
    
    return chunks
    
  #//-------------------------------------------------------//
  
  def   remove(self, del_keys ):
    
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
  
  def   __getitem__(self, key ):
    return self.locations[ key ].data( self.stream )
  
  #//-------------------------------------------------------//
  
  def   __iter__(self):
    stream = self.stream
    for key, location in self.locations.items():
      yield key, location.data( stream )
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len( self.locations )
  
  #//-------------------------------------------------------//
  
  def   __bool__(self):
    return bool(self.locations)
  
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
      
      file_size += location.chunkSize()
    
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
