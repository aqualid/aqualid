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

from aql.utils import cpuCount
from aql.values import Value, NoContent, DependsValue, DependsValueContent
from aql.options import builtinOptions


#//===========================================================================//

def   defaultJobs():
  return max( min( 1, cpuCount(), 1024 ) )

#//===========================================================================//

CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"

CLI_OPTIONS = (
  CLIOption( "-j", "--jobs",         "jobs",            int,      defaultJobs(),  "Cache file of targets build status.", 'NUMBER' ),
  CLIOption( "-m", "--make-file",    "make_file",       FilePath, 'make.aql',     "Cache file of targets build status.", 'FILE PATH'),
  CLIOption( "-t", "--cache-file",   "cache_file",      FilePath, '.aql.values',  "Cache file of targets build status.", 'FILE PATH'),
  CLIOption( "-k", "--keep-going",   "keep_going",      bool,     False,          "Continue build even if any target failed." ),
  CLIOption( "-l", "--list-options", "list_options",    bool,     False,          "List all available options and exit." ),
  CLIOption( "-c", "--clean",        "clean_targets",   bool,     False,          "Clean up actual targets." ),
  CLIOption( "-v", "--verbose",      "verbose",         bool,     False,          "Verbose mode." ),
  CLIOption( "-q", "--quiet",        "quiet",           bool,     False,          "Quiet mode." ),
)

#//===========================================================================//

class Project( object ):
  
  __slots__ = (
    'options',
    'flags',
    'build_manager',
  )
  
  def   __init__(self, flags, options ):
    self.flags = flags
    self.options = options
    self.build_manager = BuildManager( flags.cache_file, flags.jobs, flags.keep_going )
  
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
  

if __name__ == "__main__":
  
  options = aql.CLIOptions( )
  options.include( )
  
  prj_cfg = aql.ProjectConfiguration()
  prj_cfg.readConfig( config_file )
  
  prj_cfg.options 
  
  prj = aql.Project( prj_cfg )
  
  
