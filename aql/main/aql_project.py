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

class   CLIOption( object ):
  __slots__ = (
    'cli_name', 'cli_long_name', 'opt_name', 'action', 'default', 'help', 'metavar'
  )
  
  def   __init__( self, cli_name, cli_long_name, opt_name, action, default, metavar = None ):
    self.cli_name = cli_name
    self.cli_long_name = cli_long_name
    self.opt_name = opt_name
    self.action = action
    self.default = default
    self.help = help
    self.metavar = metavar

#//===========================================================================//

CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"

CLI_OPTIONS = (
  CLIOption( "-j", "--jobs",         "jobs",            'store',      defaultJobs(),  "Cache file of targets build status.", 'NUMBER' ),
  CLIOption( "-m", "--make-file",    "make_file",       'store',      'make.aql',  "Cache file of targets build status.", 'FILE PATH'),
  CLIOption( "-t", "--cache-file",   "cache_file",      'store',      '.aql.values',  "Cache file of targets build status.", 'FILE PATH'),
  CLIOption( "-k", "--keep-going",   "keep_going",      'store_true',  False,         "Continue build even if any target failed." ),
  CLIOption( "-l", "--list-options", "list_options",    'store_true',  False,         "List all available options and exit." ),
  CLIOption( "-c", "--clean",        "clean_targets",   'store_true',  False,         "Clean up actual targets." ),
  CLIOption( "-v", "--verbose",      "verbose",         'store_true',  False,         "Verbose mode." ),
  CLIOption( "-q", "--quiet",        "quiet",           'store_true',  False,         "Quiet mode." ),
)

#//===========================================================================//

class   Configuration( object ):
  
  #//-------------------------------------------------------//
  
  def   __init__( self, cli_options, args ):
    
    self._args = {}
    self.values = {}
    self.targets = []
    
    self.__parseArguments( args )
    
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __getArgsParser():
    parser = optparse.OptionParser( CLI_USAGE )
    
    for opt in CLI_OPTIONS:
      args = (opt.cli_name, opt.cli_long_name)
      kw = { 'dest': opt.opt_name, 'help': opt.help }
      if opt.metavar:
        kw['metavar'] = opt.metavar
      parser.add_option( *args, **kw )
    
    return parser
  
  #//-------------------------------------------------------//
  
  def __parseValues( self, args ):
    values = self.values
    targets = self.targets
    
    for arg in args:
      name, sep, value = arg.partition('=')
      name = name.strip()
      if sep:
        values[name] = value.strip()
      else:
        targets.append( name )
  
  #//-------------------------------------------------------//
  
  def __parseOptions( self, opts ):
    flags = self.flags
    
    for opt in CLI_OPTIONS:
      name = opt.opt_name
      value = getattr( opts, name )
      if value is not None:
        setattr( self, name, value )
  
  #//-------------------------------------------------------//
  
  def   __parseArguments( self, cli_args ):
    parser = self.__getArgsParser()
    flags, args = parser.parse_args( cli_args )
    
    self.__parseValues( flags )
    self.__parseOptions( args )
  
  def __getattr__(self, name):
    value = getattr( opts, name )

#//===========================================================================//

def   readConfingFile( config_file, )

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
  
