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

__all__ = ( 'Project', 'ProjectConfig' )

import sys

from aql.utils import cpuCount, CLIConfig, CLIOption
from aql.types import FilePath
from aql.values import Value, NoContent, DependsValue, DependsValueContent
from aql.options import builtinOptions
from aql.nodes import BuildManager

#//===========================================================================//

def   jobsCount( jobs = None ):
  
  if jobs is None:
    jobs = cpuCount()
  
  return max( min( 1, int(jobs) ), 1024 )

#//===========================================================================//

class ProjectConfig( CLIConfig ):
  
  def   __init__( self, args = None ):
    if args is None:
      args = sys.argv
    
    CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"
    
    CLI_OPTIONS = (
      CLIOption( "-j", "--jobs",          "jobs",            jobsCount,  None,          "Number of parallel jobs to process targets.", 'NUMBER' ),
      CLIOption( "-f", "--make-file",     "make_file",       FilePath,   'make.aql',    "Path to main make file", 'FILE PATH'),
      CLIOption( "-t", "--cache-file",    "cache_file",      FilePath,   '.aql.cache',  "Path to cache file of build status.", 'FILE PATH'),
      CLIOption( "-k", "--keep-going",    "keep_going",      bool,       False,         "Continue build even if any target failed." ),
      CLIOption( "-l", "--list-options",  "list_options",    bool,       False,         "List all available options and exit." ),
      CLIOption( "-c", "--clean",         "clean_targets",   bool,       False,         "Clean up actual targets." ),
      CLIOption( "-v", "--verbose",       "verbose",         bool,       False,         "Verbose mode." ),
      CLIOption( "-q", "--quiet",         "quiet",           bool,       False,         "Quiet mode." ),
    )
    
    super(ProjectConfig, self).__init__( CLI_USAGE, CLI_OPTIONS, args )
    
    self._options = builtinOptions()
  
  #//-------------------------------------------------------//
  
  def   readConfig( self, config_file ):
    options = self._options
    locals = { 'options': options }
    super(ProjectConfig, self).readConfig( config_file, locals )
    
    options.update( self )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    if name == 'options':
      return self._options
    
    return super(ProjectConfig, self).__getattr__( name )

#//===========================================================================//

class Project( object ):
  
  __slots__ = (
    'config',
    'options',
    'build_manager',
  )
  
  def   __init__(self, config = None ):
    if config is None:
      config = ProjectConfig()
    
    self.config = config
    
    self.options = config.options.override()
    self.build_manager = BuildManager( config.cache_file, config.jobs, config.keep_going )
  
  #//=======================================================//
  
  def   Tool( self, tools, tool_paths = tuple(), **kw ):
    pass
  
  #//=======================================================//
  
  def   Depends( self, target, dependency ):
    pass
  
  #//=======================================================//
  
  def   Ignore( self, target, dependency ):
    pass
  
  def   Alias( self, alias, target ):
    pass
  
  def   AlwaysBuild( self, target ):
    pass
  
  def   ReadScript( self, scripts ):
    pass
  
  #//=======================================================//
  
  def   Build( self ):
    pass
  
  #//=======================================================//
  
  def   Clean( self ):
    pass

#//===========================================================================//

if __name__ == "__main__":
  
  prj_cfg = aql.ProjectConfiguration()
  prj_cfg.readConfig( config_file )
  
  prj_cfg.options 
  
  prj = aql.Project( )
  prj = aql.Project( prj_cfg )
  
  
