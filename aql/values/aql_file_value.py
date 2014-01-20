#
# Copyright (c) 2011-2013 The developers of Aqualid project - http://aqualid.googlecode.com
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

from .aql_value import Value, ContentBase, NoContent
from .aql_value_pickler import pickleable

from aql.utils import fileSignature, fileTimeSignature


#//===========================================================================//

class   ErrorFileValueNoName( Exception ):
  def   __init__( self ):
    msg = "Filename is not specified"
    super(type(self), self).__init__( msg )

class   ErrorFileValueInvalidContentType( Exception ):
  def   __init__( self, content_type ):
    msg = "Content type must inherited from ContentBase. Invalid content type: '%s'" % (content_type, )
    super(type(self), self).__init__( msg )


#//===========================================================================//
_file_content_cache = {}

#noinspection PyAttributeOutsideInit
class   FileContentBase( ContentBase ):
  
  FIXED_SIZE = True
  
  __slots__ = ('path', 'signature')
  
  def   __new__( cls, path = None, signature = None, use_cache = False ):
    
    if isinstance(path, ContentBase):
      return path
    
    if not signature and (path is None):
      return NoContent
    
    self = super(FileContentBase,cls).__new__(cls)
    
    if signature:
      self.signature = signature
    else:
      if not use_cache:
        self.signature = self._getSignature( path )
      else:
        self.path = path
    
    return self
  
  #//-------------------------------------------------------//

  def   _getSignature( self, path, use_cache = False ):

    cache = _file_content_cache.setdefault( self.__class__, {})
    
    if use_cache:
      try:
        return cache[ path ]
      except KeyError:
        pass
    
    try:
      signature = self._sign( path )
      cache[ path ] = signature
    except (OSError, IOError):
      signature = bytearray()
    
    return signature
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      signature = self._getSignature( self.path, use_cache = True )
      self.signature = signature
      del self.path
      
      return signature
    
    return super(FileContentBase, self).__getattr__( attr )
    
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return bool(self.signature)
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and self.signature and (self.signature == other.signature)
  
  def   __getnewargs__(self):
    return None, self.signature
  
  def   __str__( self ):
    return str(self.signature)

#//===========================================================================//

@pickleable
class   FileContentChecksum (FileContentBase):

  #noinspection PyMethodMayBeStatic
  def   _sign( self, path ):
    return fileSignature( path )

#//===========================================================================//

@pickleable
class   FileContentTimeStamp (FileContentBase):
  
  #noinspection PyMethodMayBeStatic
  def   _sign( self, path ):
    return fileTimeSignature( path )

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
    return None, super(FileName,self).__getnewargs__()[0]

#//===========================================================================//

@pickleable
class   FileValue (Value):
  
  def   __new__( cls, content = NotImplemented, name = None, use_cache = False ):
    
    file_content = NotImplemented
    file_name = None
    content_type = FileContentChecksum
    
    if isinstance( name, ContentBase):
      file_content = name
    
    elif type(name) is type:
      content_type = name
    
    else:
      file_name = name
    
    if isinstance( content, FileValue ):
      file_name = content.name
      content_type = type(content.content)
    
    elif isinstance( content, ContentBase ) or (content is None):
      file_content = content
    
    elif type(content) is type:
      content_type = content
    
    elif content is not NotImplemented:
      file_name = content
    
    if file_name:
      file_name = FileName( file_name )
    else:
      raise ErrorFileValueNoName()
    
    if file_content is NotImplemented:
      if not issubclass( content_type, ContentBase ):
        raise ErrorFileValueInvalidContentType( content_type )
      
      file_content = content_type( file_name, use_cache = use_cache )
    
    # if __debug__:
    #   print( "FileValue(): content: %s, name: %s" % (type(file_content), type(file_name)) )

    self = super(FileValue, cls).__new__( cls, content = file_content, name = file_name )
    
    # if __debug__:
    #   print( "FileValue(): content: %s, name: %s" % (type(self.content), type(self.name)) )
    
    return self
  
  #//-------------------------------------------------------//

  def   get(self):
    return self.name

  #//-------------------------------------------------------//

  def   actual( self ):
    content = self.content
    
    if not content:
      # if __debug__:
      #   print( "FileValue.actual(): no content of file %s" % (self.name,))
      return False
    
    # if __debug__:
    #   print("type(content): %s " % (type(content),) )
    
    result = (content == type(content)( self.name, use_cache = True ))
    # if __debug__:
    #   if not result:
    #     print( "FileValue.actual(): non-actual content of file %s" % (self.name,))
    
    return result
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    try:
      os.remove( self.name )
    except OSError:
      pass

#//===========================================================================//

@pickleable
class   DirValue (FileValue):
  
  def   __new__( cls, content = NotImplemented, name = None, use_cache = False ):
    
    if content is NotImplemented:
      content = FileContentTimeStamp
    
    return super(DirValue, cls).__new__( cls, name = name, content = content, use_cache = use_cache )
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    try:
      os.rmdir( self.name )
    except OSError:
      pass

#//===========================================================================//
