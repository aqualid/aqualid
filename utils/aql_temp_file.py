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

class Tempfile (object):
  
  __slots__ = ('__handle', 'name')
  
  def   __init__(self, prefix = 'tmp', suffix = ''):
    self.__handle = tempfile.NamedTemporaryFile( mode = 'w+b', suffix = suffix, prefix = prefix, delete = False )
    self.name = self.__handle.name
  
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
    self.__handle.flush()
  
  def close( self ):
    self.__handle.close()
    return self
  
  def remove( self ):
    self.__handle.close()
    try:
      os.remove( self.name )
    except OSError:
      pass
    
    return self

#//===========================================================================//

class Tempfiles( object ):
  __slots__ = ('tmpfilenames')
  
  def   __init__(self, tmpfilenames = None ):
    
    if isinstance( tmpfilenames, str ):
      tmpfilenames = [ tmpfilenames ]
    else:
      try:
        iter( tmpfilenames )
      except TypeError:
        tmpfilenames = [ tmpfilenames ]
    
    self.tmpfilenames = lsist( map( str, tmpfilenames ) )
  
  def   __enter__(self):
    return self
  
  def   __exit__(self, exc_type, exc_value, traceback):
    self.remove()
  
  def remove( self ):
    for tmpfname in self.tmpfilenames:
      try:
        os.remove( self.name )
      except OSError:
        pass

