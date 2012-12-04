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
)

from aql.utils import toSequence, eventStatus, logInfo
from aql.values import Value, NoContent, DependsValue, DependsValueContent
from aql.options import builtinOptions



#//===========================================================================//

def   _getOptParser():
  parser = optparse.OptionParser("usage: %prog [OPTIONS] [[TARGET] [OPTION=VALUE] ...]")
  
  parser.add_option("-f", "--cache-file", dest = "cache_file",
                      help = "Tests directory", metavar = "FILE PATH" )
  
  parser.add_option("-k", "--keep-going", action="store_true", dest="keep_going",
                      help = "Keep going even if any target failed." )
  
  parser.add_option("-o", "--list_options", action="store_true", dest="list_options",
                      help = "List options and exit." )
  
  parser.add_option("-c", "--clean", action="store_true", dest="clean_targets",
                      help = "Clean targets." )
  
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help = "Verbose mode." )
  
  parser.add_option("-q", "--quiet", action="store_true", dest="quiet", help = "Quiet mode." )
  
  return parser

#//===========================================================================//

def   _parseOptions( parser ):
  opt, args = parser.parse_args()
  
  for opt in options.items()

#//===========================================================================//

class Project( object ):
  
  __slots__ = (
    'options',
    'build_manager',
  )
  
  def   __init__(self, cache_file = None ):
    self.options = builtinOptions()
    self.build_manager = BuildManager( datafilename, 4, True )
  
  def   Depends( self, target, dependency ):
    pass
  
  def   Ignore( self, target, dependency ):
    pass
  
  def   Alias( self, alias, target ):
    pass
  
  def   AlwaysBuild( self, target ):
    pass
  
  def   ReadScript( self, scripts ):
    pass
  
  def   Tool( self, tools, tool_paths = tuple(), **kw ):
    pass
  
