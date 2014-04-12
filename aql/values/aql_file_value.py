#
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'FileValueBase', 'FileChecksumValue', 'FileTimestampValue', 'DirValue',
)

import os
import errno

from .aql_value import ValueBase
from .aql_value_pickler import pickleable

from aql.util_types import AqlException
from aql.utils import fileSignature, fileTimeSignature

#//===========================================================================//

class   ErrorFileValueNoName( AqlException ):
  def   __init__( self ):
    msg = "Filename is not specified"
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   _normFileName( name ):
  if not name:
    raise ErrorFileValueNoName()
  
  return os.path.normcase( os.path.abspath( name ) )


#//===========================================================================//

class   FileValueBase (ValueBase):
  
  def   __new__( cls, name, signature = None ):
    return super(FileValueBase, cls).__new__( cls, name, signature )
  
  #//-------------------------------------------------------//

  def   get(self):
    return self.name

  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return self.name, self.signature
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return bool(self.signature)
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    try:
      os.remove( self.name )
    except OSError:
      pass

#//===========================================================================//

# noinspection PyDefaultArgument
def   _getFileChecksum( path, use_cache = False, _cache = {} ):
  if use_cache:
    try:
      return _cache[ path ]
    except KeyError:
      pass
  
  try:
    signature = fileSignature( path )
  except (OSError, IOError) as err:
    if err.errno != errno.EISDIR:
      return None
    
    try:
      signature = fileTimeSignature( path )
    except (OSError, IOError):
      return None
  
  _cache[ path ] = signature
  return signature

#//===========================================================================//

# noinspection PyDefaultArgument
def   _getFileTimestamp( path, use_cache = False, _cache = {} ):
  if use_cache:
    try:
      return _cache[ path ]
    except KeyError:
      pass
  
  try:
    signature = fileTimeSignature( path )
  except (OSError, IOError):
    return None
  
  _cache[ path ] = signature
  return signature

#//===========================================================================//

@pickleable
class FileChecksumValue( FileValueBase ):
  
  IS_SIZE_FIXED = True
  
  def   __new__( cls, name, signature = NotImplemented, use_cache = False ):
    
    if isinstance(name, FileValueBase):
      name = name.name
    else:
      if isinstance(name, ValueBase):
        name = name.get()
    
    name = _normFileName( name )
      
    if signature is NotImplemented:
      signature = _getFileChecksum( name, use_cache = use_cache )
    
    return super(FileChecksumValue, cls).__new__( cls, name, signature )
  
  #//-------------------------------------------------------//
  
  def   getActual(self):
    name = self.name
    signature = _getFileChecksum( name, use_cache = True )
    return super(FileChecksumValue, self).__new__( self.__class__, name, signature )
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    if not self.signature:
      return False
    
    signature = _getFileChecksum( self.name, use_cache = True )
    
    return self.signature == signature

#//===========================================================================//

@pickleable
class FileTimestampValue( FileValueBase ):
  
  IS_SIZE_FIXED = True
  
  def   __new__( cls, name, signature = NotImplemented, use_cache = False ):
    if isinstance(name, FileValueBase):
      name = name.name
    else:
      if isinstance(name, ValueBase):
        name = name.get()
      
      name = _normFileName( name )
    
    if signature is NotImplemented:
      signature = _getFileTimestamp( name, use_cache = use_cache )
    
    self = super(FileTimestampValue, cls).__new__( cls, name, signature )
    return self
  
  #//-------------------------------------------------------//
  
  def   getActual(self):
    name = self.name
    signature = _getFileTimestamp( name, use_cache = True )
    return super(FileTimestampValue, self).__new__( self.__class__, name, signature )
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    if not self.signature:
      return False
    
    signature = _getFileTimestamp( self.name, use_cache = True )
    
    return self.signature == signature

#//===========================================================================//

@pickleable
class   DirValue (FileTimestampValue):
  
  def   remove( self ):
    try:
      os.rmdir( self.name )
    except OSError:
      pass

