#
# Copyright (c) 2012 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'FilePath',
)

import os.path

from .aql_simple_types import String, IgnoreCaseString

#//===========================================================================//

if os.path.normcase('ABC') == os.path.normcase('abc'):
  FilePathBase = IgnoreCaseString
else:
  FilePathBase = String

try:
  _splitunc = os.path.splitunc
except AttributeError:
  def _splitunc( path ):
    return str(), path

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class   FilePath (FilePathBase):
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    #noinspection PyRedundantParentheses
    return (str(self), )
  
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass
  
  #//-------------------------------------------------------//
  
  def   __add__(self, other):
    return FilePath( super(FilePath,self).__add__( other ) )
  
  def   __iadd__(self, other):
    return FilePath( super(FilePath,self).__add__( other ) )
  
  #//-------------------------------------------------------//
  
  def   __hash__( self ):
    return super(FilePath, self).__hash__()
  
  #//-------------------------------------------------------//
  
  def   abspath(self):
    return FilePath( os.path.abspath(self) )
  
  def   normpath(self):
    return FilePath( os.path.normpath(self) )
  
  def   filename(self):
    return FilePath( os.path.basename(self) )
  
  def   dirname(self):
    return FilePath( os.path.dirname(self) )
  
  def   ext(self):
    return FilePathBase( os.path.splitext(self)[1] )
  
  def   name(self):
    return FilePathBase( os.path.splitext(self.filename())[0] )
  
  def   drive(self):
    drive, path = os.path.splitdrive( self )
    if not drive:
      drive, path = _splitunc( path )
    
    return FilePathBase( drive )
  
  #//-------------------------------------------------------//
  
  def   change( self, dirname = None, name = None, ext = None, prefix = None ):
    
    self_dirname, self_filename = os.path.split( self )
    self_name, self_ext = os.path.splitext( self_filename )
    
    if dirname is None: dirname = self_dirname
    if name is None: name = self_name
    if ext is None: ext = self_ext
    if prefix: name = prefix + name
    
    return FilePath( os.path.join( dirname, name + ext ) )
  
  #//-------------------------------------------------------//
  
  def   join( self, *paths ):
    return FilePath( os.path.join( self, *paths ) )
  
