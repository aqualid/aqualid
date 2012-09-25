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
import tempfile
import errno
import shutil

class Tempfile (object):
  
  __slots__ = ('__handle', 'name')
  
  def   __init__(self, prefix = 'tmp', suffix = '', dir = None, mode = 'w+b'):
    self.__handle = tempfile.NamedTemporaryFile( mode = mode, suffix = suffix, prefix = prefix, dir = dir, delete = False )
    self.name = self.__handle.name
  
  def   __str__(self):
    return self.name
  
  def   __enter__(self):
    return self
  
  def   __exit__(self, exc_type, exc_value, traceback):
    self.remove()
  
  def write( self, buffer ):
    self.__handle.write( buffer )
  
  def read( self, buffer ):
    self.__handle.read( buffer )
  
  def seek( self, offset, whence = os.SEEK_SET ):
    self.__handle.seek( offset )
  
  def tell( self ):
    return self.__handle.tell()
  
  def flush( self ):
    if self.__handle is not None:
      self.__handle.flush()
  
  def close( self ):
    if self.__handle is not None:
      self.__handle.close()
      self.__handle = None
    return self
  
  def remove( self ):
    self.close()
    try:
      os.remove( self.name )
    except OSError as ex:
      if ex.errno != errno.ENOENT:
        raise
    
    return self

#//===========================================================================//

class Tempdir( object ):
  __slots__ = ('path')
  
  def   __init__( self, prefix = 'tmp', suffix = '', dir = None, name = None ):
    
    if dir is not None:
      if not os.path.isdir( dir ):
        os.makedirs( dir )
    
    if name is None:
      self.path = tempfile.mkdtemp( prefix = prefix, suffix = suffix, dir = dir )
    else:
      if dir is not None:
        name = os.path.join( dir, name )
      
      name = os.path.absname( name )
      
      if not os.path.isdir( name ):
        os.makedirs( name )
      
      self.path = name
  
  def   __str__(self):
    return self.path
  
  def   __enter__(self):
    return self
  
  def   __exit__(self, exc_type, exc_value, traceback):
    self.remove()
  
  def remove( self ):
    shutil.rmtree( self.path, ignore_errors = False )
