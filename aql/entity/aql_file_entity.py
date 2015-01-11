#
# Copyright (c) 2011-2015 The developers of Aqualid project
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
  'FileEntityBase', 'FileChecksumEntity', 'FileTimestampEntity', 'DirEntity',
)

import os
import errno

from .aql_entity import EntityBase
from .aql_entity_pickler import pickleable

from aql.util_types import AqlException
from aql.utils import fileSignature, fileTimeSignature, absFilePath

#//===========================================================================//

class   ErrorFileEntityNoName( AqlException ):
  def   __init__( self ):
    msg = "Filename is not specified"
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   FileEntityBase (EntityBase):
  
  def   get(self):
    return self.name

  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    tags = self.tags
    if not tags:
      tags = None 
    
    return self.name, self.signature, tags
  
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
class FileChecksumEntity( FileEntityBase ):
  
  IS_SIZE_FIXED = True
  
  def   __new__( cls, name, signature = NotImplemented, tags = None, use_cache = False ):

    if isinstance(name, FileEntityBase):
      name = name.name
    else:
      if isinstance(name, EntityBase):
        name = name.get()
    
    if not name:
      raise ErrorFileEntityNoName()

    name = absFilePath( name )
      
    self = super(FileChecksumEntity, cls).__new__( cls, name, signature, tags = tags )

    if signature is NotImplemented:
      if use_cache:
        del self.signature
      else:
        self.signature = _getFileChecksum( name )

    return self
  
  #//-------------------------------------------------------//

  def   __getattr__(self, attr):
    if attr == 'signature':
      self.signature = signature = _getFileChecksum( self.name, use_cache = True )
      return signature

    raise AttributeError("Unknown attribute: '%s'" % (attr,))

  #//-------------------------------------------------------//

  def   getActual(self):
    name = self.name
    signature = _getFileChecksum( name, use_cache = True )
    return super(FileChecksumEntity, self).__new__( self.__class__, name, signature, self.tags )
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    if not self.signature:
      return False
    
    signature = _getFileChecksum( self.name, use_cache = True )
    
    return self.signature == signature

#//===========================================================================//

@pickleable
class FileTimestampEntity( FileEntityBase ):
  
  IS_SIZE_FIXED = True
  
  def   __new__( cls, name, signature = NotImplemented, tags = None, use_cache = False ):
    if isinstance(name, FileEntityBase):
      name = name.name
    else:
      if isinstance(name, EntityBase):
        name = name.get()
      
      if not name:
        raise ErrorFileEntityNoName()
      
      name = absFilePath( name )
    
    self = super(FileTimestampEntity, cls).__new__( cls, name, signature, tags = tags )

    if signature is NotImplemented:
      if use_cache:
        del self.signature
      else:
        self.signature = _getFileTimestamp( name )

    return self
  
  #//-------------------------------------------------------//

  def   __getattr__(self, attr):
    if attr == 'signature':
      self.signature = signature = _getFileTimestamp( self.name, use_cache = True )
      return signature

    raise AttributeError("Unknown attribute: '%s'" % (attr,))

  #//-------------------------------------------------------//

  def   getActual(self):
    name = self.name
    signature = _getFileTimestamp( name, use_cache = True )
    return super(FileTimestampEntity, self).__new__( self.__class__, name, signature, self.tags )
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    if not self.signature:
      return False
    
    signature = _getFileTimestamp( self.name, use_cache = True )
    
    return self.signature == signature

#//===========================================================================//

@pickleable
class   DirEntity (FileTimestampEntity):
  
  def   remove( self ):
    try:
      os.rmdir( self.name )
    except OSError:
      pass

