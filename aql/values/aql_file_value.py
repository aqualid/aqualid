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

__all__ = (
  'FileContentChecksum', 'FileContentTimeStamp', 'FileName',
  'FileValue', 'DirValue',
)

import os

from .aql_value import Value, NoContent
from .aql_value_pickler import pickleable

from aql.utils import fileSignature, fileTimeSignature

_file_content_cache = {}

#//===========================================================================//

class   FileContentBase(object):
  
  __slots__ = ( 'path', 'exists', 'signature' )
  
  def   __new__( cls, path = None, signature = None, exists = False, use_cache = False, file_content_cache = _file_content_cache ):
    
    if use_cache:
      try:
        content = _file_content_cache[ path ]
        if type(content) is cls:
          return content
      except KeyError:
        pass
    
    if signature is not None:
      self = super(FileContentBase,cls).__new__(cls)
      self.signature = signature
      self.exists = exists
      return self
    
    if path is None:
      return NoContent
    
    if type(path) is cls:
      return path
    
    self = super(FileContentBase,cls).__new__(cls)
    self.path = path
    
    file_content_cache[ path ] = self
    return self
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr in ('signature', 'exists'):
      try:
        signature = self._sign()
        exists = True
      except (OSError, IOError):
        signature = bytearray()
        exists = False
      
      self.exists = exists
      self.signature = signature
      del self.path
      
      return signature if (attr == 'signature') else exists
    
    return super(FileContentBase, self).__getattr__( attr )
    
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and self.exists and other.exists and (self.signature == other.signature)
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  def   __getnewargs__(self):
    return ( None, self.signature, self.exists )
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass
  def   __str__( self ):
    return str(self.signature)

#//===========================================================================//

@pickleable
class   FileContentChecksum (FileContentBase):
  
  def   _sign( self ):
    return fileSignature( self.path )

#//===========================================================================//

@pickleable
class   FileContentTimeStamp (FileContentBase):
  
  def   _sign( self ):
    return fileTimeSignature( self.path )

#//===========================================================================//

@pickleable
class   FileName (str):
  def     __new__(cls, path = None, full_path = None ):
    if type(path) is cls:
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
        content = type(other.content)
    else:
      name = FileName( name )
    
    if content is NotImplemented:
      content = FileContentChecksum( name, use_cache = use_cache )
    elif type(content) is type:
      content = content( name, use_cache = use_cache )
    
    return super(FileValue, cls).__new__( cls, name, content )
  
  #//-------------------------------------------------------//
  
  def   actual( self ):
    content = self.content
    return content == type(content)( self.name, use_cache = True )
  
  #//-------------------------------------------------------//
  
  def   exists( self ):
    return self.content.exists
  
  #//-------------------------------------------------------//
  
  def   remove( self, os_remove = os.remove ):
    try:
      os_remove( self.name )
    except OSError:
      pass

#//===========================================================================//

@pickleable
class   DirValue (FileValue):
  
  def   __new__( cls, name, content = NotImplemented, use_cache = False ):
    
    if content is NotImplemented:
      content = FileContentTimeStamp
    
    return super(DirValue, cls).__new__( cls, name, content, use_cache = use_cache )
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    try:
      os.rmdir( self.name )
    except OSError:
      pass

#//===========================================================================//
