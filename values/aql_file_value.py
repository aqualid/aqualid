#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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

import os
import hashlib
import struct
import datetime

from aql_value import Value, NoContent
from aql_value_pickler import pickleable
from aql_utils import fileSignature

_file_content_chache = {}

#//===========================================================================//

@pickleable
class   FileContentChecksum (object):
  
  __slots__ = ( 'signature' )
  
  def   __new__( cls, path = None, signature = None, use_cache = False, file_content_chache = _file_content_chache ):
    
    if use_cache:
      try:
        content = file_content_chache[ path ]
        if type(content) is FileContentChecksum:
          return content
      except KeyError:
        pass
    
    if signature is not None:
      self = super(FileContentChecksum,cls).__new__(cls)
      self.signature = signature
      return self
    
    if path is None:
      return NoContent()
    
    if (cls is FileContentChecksum) and (type(path) is cls):
      return path
    
    try:
      signature = fileSignature( path )
    except (OSError, IOError):
      return NoContent()
    
    self = super(FileContentChecksum,cls).__new__(cls)
    self.signature = signature
    
    file_content_chache[ path ] = self
    return self
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and (self.signature == other.signature)
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  def   __getnewargs__(self):
    return ( None, self.signature )
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass
  def   __str__( self ):
    return str(self.signature)

#//===========================================================================//

@pickleable
class   FileContentTimeStamp (object):
  
  __slots__ = ( 'size', 'modify_time', 'signature' )
  
  def   __new__( cls, path = None, size = None, modify_time = None, use_cache = False, file_content_chache = _file_content_chache ):
    
    if use_cache:
      try:
        content = file_content_chache[ path ]
        if type(content) is FileContentTimeStamp:
          return content
      except KeyError:
        pass
    
    if (size is not None) and (modify_time is not None):
      self = super(FileContentTimeStamp,cls).__new__(cls)
      self.size = size
      self.modify_time = modify_time
      return self
    
    if path is None:
      return NoContent()
    
    if (cls is FileContentTimeStamp) and (type(path) is cls):
      return path
    
    try:
      stat = os.stat( path )
      
      self = super(FileContentTimeStamp,cls).__new__(cls)
      
      self.size = stat.st_size
      self.modify_time = stat.st_mtime
    
    except OSError:
        self = NoContent()
    
    file_content_chache[ path ] = self
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return type(self) == type(other) and (self.size == other.size) and (self.modify_time == other.modify_time)
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  def   __getnewargs__(self):
    return ( None, self.size, self.modify_time )
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass
  def   __str__( self ):
    return str( datetime.datetime.fromtimestamp( self.modify_time ) )
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = self.__signature()
      return self.signature
    
    return super(FileContentTimeStamp,self).__getattr__( attr )
  
  def   __signature( self ):
    return struct.pack( ">Qd", self.size, self.modify_time )

#//===========================================================================//

@pickleable
class   FileName (str):
  def     __new__(cls, path = None, full_path = None ):
    if (cls is FileName) and (type(path) is cls):
      return path
    
    if full_path is None:
      if path is None:
        return super(FileName,cls).__new__(cls)
    
      full_path = os.path.normcase( os.path.abspath( str(path) ) )
    
    return super(FileName,cls).__new__(cls, full_path)
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return (None, super(FileName,self).__getnewargs__()[0] )

#//===========================================================================//

@pickleable
class   FileValue (Value):
  
  def   __new__( cls, name, content = NotImplemented, use_cache = False ):
    
    if isinstance( name, FileValue ):
      other = name
      name = other.name
    
      if content is NotImplemented:
        content = type(other.content)( name )
    else:
      name = FileName( name )
    
    if content is NotImplemented:
      content = FileContentChecksum( name, use_cache = use_cache )
    elif type(content) is type:
      content = content( name, use_cache = use_cache )
    
    return super(FileValue, cls).__new__( cls, name, content )
  
  #//-------------------------------------------------------//
  
  def   actual( self, use_cache = True ):
    content = self.content
    return content == type(content)( self.name, use_cache = use_cache )
  
  #//-------------------------------------------------------//
  
  def   remove( self, os_remove = os.remove ):
    try:
      os_remove( self.name )
    except OSError:
      pass

#//===========================================================================//
