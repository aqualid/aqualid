#
# Copyright (c) 2012-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = ( 'Project', 'ProjectConfig',
            'ErrorProjectBuilderMethodFewArguments',
            'ErrorProjectBuilderMethodUnbound',
            'ErrorProjectBuilderMethodWithKW',
            'ErrorProjectInvalidMethod',
          )

import types
import itertools

from aql.utils import CLIConfig, CLIOption, getFunctionArgs, execFile, flattenList, findFiles, cpuCount, Chdir
from aql.util_types import FilePath, FilePaths, SplitListType, toSequence
from aql.values import NullValue
from aql.options import builtinOptions, Options
from aql.nodes import BuildManager, Node

from .aql_tools import ToolsManager
from .aql_builtin_tools import BuiltinTool

#//===========================================================================//

class   ErrorProjectInvalidMethod( Exception ):
  def   __init__( self, method ):
    msg = "Invalid project method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodWithKW( Exception ):
  def   __init__( self, method ):
    msg = "Keyword arguments are not allowed in builder method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodUnbound( Exception ):
  def   __init__( self, method ):
    msg = "Unbound builder method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodFewArguments( Exception ):
  def   __init__( self, method ):
    msg = "Too few arguments in builder method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodInvalidOptions( Exception ):
  def   __init__( self, value ):
    msg = "Type of 'options' argument must be Options, instead of : '%s'(%s)" % (type(value), value)
    super(type(self), self).__init__( msg )

#//===========================================================================//

#noinspection PyUnresolvedReferences
class ProjectConfig( object ):
  
  __slots__ = ('directory', 'makefile', 'targets', 'options',
               'verbose', 'log_level', 'jobs', 'keep_going', 'rebuild', 'profile', 'memory' )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, args = None ):
    
    CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"
    
    Paths = SplitListType( FilePaths, ', ' )
    
    CLI_OPTIONS = (
      
      CLIOption( "-C", "--directory",       "directory",      FilePath,   '',           "Change directory before reading the make files.", 'FILE PATH'),
      CLIOption( "-f", "--makefile",        "makefile",       FilePath,   'make.aql',   "Path to a make file.", 'FILE PATH'),
      CLIOption( "-l", "--list-options",    "list_options",   bool,       False,        "List all available options and exit." ),
      CLIOption( "-c", "--config",          "config",         FilePath,   None,         "The configuration file used to read CLI arguments." ),
      CLIOption( "-B", "--always",          "always",         bool,       False,        "Unconditionally build all targets." ),
      CLIOption( "-R", "--clear",           "clear",          bool,       False,        "Cleans targets." ),
      CLIOption( "-n", "--status",          "status",         bool,       False,        "Print status of targets." ),
      CLIOption( "-u", "--up",              "search_up",      bool,       False,        "Search up directory tree for a make file." ),
      
      CLIOption( "-b", "--build-directory", "build_dir",      FilePath,   'output',     "Build output path.", 'FILE PATH'),
      CLIOption( "-I", "--tools-path",      "tools_path",     Paths,      [],           "Path to tools and setup scripts.", 'FILE PATH, ...'),
      CLIOption( "-k", "--keep-going",      "keep_going",     bool,       False,        "Keep going when some targets can't be built." ),
      CLIOption( "-r", "--rebuild",         "rebuild",        bool,       False,        "Unconditionally rebuilds all targets." ),
      CLIOption( "-j", "--jobs",            "jobs",           int,        None,         "Number of parallel jobs to process targets.", 'NUMBER' ),
      CLIOption( "-v", "--verbose",         "verbose",        bool,       False,        "Verbose mode." ),
      CLIOption( "-s", "--silent",          "silent",         bool,       False,        "Silent mode." ),
      CLIOption( "-d", "--debug",           "debug",          bool,       False,        "Debug logs." ),
      CLIOption( "-m", "--memory",          "memory",         bool,       False,        "Display memory usage." ),
      CLIOption( "-p", "--profile",         "profile",        FilePath,   None,         "Run under profiler and save the results in the specified file." ),
    )
    
    cli_config = CLIConfig( CLI_USAGE, CLI_OPTIONS, args )
    
    options = builtinOptions()
    
    config = cli_config.config
    
    if config:
      cli_config.readConfig( config, { 'options': options })
    
    cli_options = {}
    
    ignore_options = {'list_options', 'config'}
    ignore_options.update( ProjectConfig.__slots__ )
    
    for name,value in cli_config.items():
      if (name not in ignore_options) and (value is not None):
        cli_options[ name ] = value
    
    options.update( cli_options )
    
    if cli_config.list_options:
      printOptions( options )
    
    #//-------------------------------------------------------//
    
    log_level = 1
    if cli_config.debug:
      log_level = 2
    if cli_config.silent:
      log_level = 0
    
    #//-------------------------------------------------------//
    
    self.options    = options
    self.directory  = cli_config.directory.abspath()
    self.makefile   = cli_config.makefile
    self.targets    = cli_config.targets
    self.verbose    = cli_config.verbose
    self.keep_going = cli_config.keep_going
    self.rebuild    = cli_config.rebuild
    self.jobs       = cli_config.jobs
    self.profile    = cli_config.profile
    self.memory     = cli_config.memory
    self.log_level  = log_level

#//===========================================================================//

class BuilderWrapper( object ):
  __slots__ = ( 'project', 'options', 'method', 'arg_names')
  
  def   __init__( self, method, project, options):
    self.arg_names = self.__checkBuilderMethod( method )
    self.method = method
    self.project = project
    self.options = options

  #//-------------------------------------------------------//
  
  @staticmethod
  def   __checkBuilderMethod( method ):
    if not hasattr(method, '__call__'):
      raise ErrorProjectInvalidMethod( method )
    
    f_args, f_varargs, f_kw, f_defaults = getFunctionArgs( method )
    
    if f_kw:
      raise ErrorProjectBuilderMethodWithKW( method )
    
    min_args = 1  # at least one argument: options
    
    if isinstance( method, types.MethodType ):
      if method.__self__ is None:
        raise ErrorProjectBuilderMethodUnbound( method )
      
    if len(f_args) < min_args:
      raise ErrorProjectBuilderMethodFewArguments( method )
    
    return frozenset( f_args )
  
  #//-------------------------------------------------------//
  
  def   __getOptionsAndArgs( self, kw ):
    args_kw = {}
    options_kw = {}
    sources = []
    dep_nodes = []
    
    options = self.options
    
    for name, value in kw.items():
      if name == "options":
        if not isinstance( value, Options ):
          raise ErrorProjectBuilderMethodInvalidOptions( value )
        options = value
      if name in ['sources', 'source']:
        sources += toSequence( value )
      else:
        for v in toSequence( value ):
          if isinstance( v, Node):
            dep_nodes.append( v )
        
        if name in self.arg_names:
          args_kw[ name ] = value
        else:
          options_kw[ name ] = value
    
    return options, dep_nodes, sources, args_kw, options_kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, *args, **kw ):
    options, dep_nodes, sources, args_kw, options_kw = self.__getOptionsAndArgs( kw )
    sources += args
    sources = flattenList( sources )
    
    builder = self.method( options, **args_kw )
    builder.setOptionsKw( options_kw )
    
    node = Node( builder, sources )
    node.depends( dep_nodes )
    
    self.project.AddNodes( node )
    
    return node

#//===========================================================================//

class ToolWrapper( object ):
  
  def   __init__( self, tool, project, options ):
    self.project = project
    self.options = options
    self.tool = tool
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    method = getattr( self.tool, attr )
    
    if attr.startswith('_') or not isinstance( method, types.MethodType ):
      return method
    
    builder = BuilderWrapper( method, self.project, self.options )
    
    setattr( self, attr, builder )
    return builder

#//===========================================================================//

class ProjectTools( object ):
  
  def   __init__( self, project ):
    self.project = project
    self.tools_cache = {}
    
    tools = ToolsManager.instance()
    tools.loadTools( self.project.options.tools_path.get() )
    
    self.tools = tools
  
  #//-------------------------------------------------------//
  
  def   _override( self, project ):
    other = super(ProjectTools,self).__new__( self.__class__ )
    
    other.project = project
    other.tools = self.tools
    other.tools_cache = self.tools_cache
    
    return other
  
  #//-------------------------------------------------------//
  
  def   __addTool( self, tool_name, options ):
    
    options_ref = options.getHashRef()
    
    try:
      return self.tools_cache[ tool_name ][ options_ref ]
    except KeyError:
      pass
    
    tool, tool_names, tool_options = self.tools.getTool( tool_name, options )
    
    tool = ToolWrapper( tool, self.project, tool_options )
    
    attrs = self.__dict__
    
    for name in tool_names:
      if name not in attrs:
        attrs[ name ] = tool
        name_tools = self.tools_cache.setdefault( name, {} )
        name_tools[ options_ref ] = tool
    
    return tool
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    
    options = self.project.options
    
    tool_method = getattr( BuiltinTool( options ), name, None )
    if tool_method and isinstance( tool_method, (types.FunctionType, types.MethodType ) ):
      return BuilderWrapper( tool_method, self.project, options )
    
    return self.__addTool( name, options )
  
  #//-------------------------------------------------------//
  
  def __getitem__( self, name ):
    return getattr( self, name )
  
  #//-------------------------------------------------------//
  
  def   Tools( self, *tool_names, **kw ):
    
    tools_path = kw.pop('tools_path', [])
    options = kw.pop( 'options', None )
    
    self.tools.loadTools( tools_path )
    
    if options is None:
      options = self.project.options
    
    if kw:
      options = options.override()
      options.update( kw )
    
    self.tools.loadTools( options.tools_path.get() )
    
    tools = [ self.__addTool( tool_name, options ) for tool_name in tool_names ]
    
    return tools[0] if len(tools) == 1 else tools
  
  #//-------------------------------------------------------//
  
  def   AddTool( self, tool_class, tool_names = tuple() ):
    self.tools.addTool( tool_class, tool_names )
    
    return self.__addTool( tool_class, self.project.options )

#//===========================================================================//

#noinspection PyProtectedMember,PyAttributeOutsideInit
class Project( object ):
  
  def   __init__( self, options, targets ):
    
    self.targets = targets
    self.options = options
    self.scripts_cache = {}
    self.aliases = {}
    self.defaults = []
    
    self.build_manager = BuildManager()
    
    self.tools = ProjectTools( self )
  
  #//-------------------------------------------------------//
  
  def   _override( self ):
    """
    @rtype : Project
    """
    other = super(Project,self).__new__( self.__class__ )
    
    other.targets       = self.targets
    other.scripts_cache = self.scripts_cache
    other.build_manager = self.build_manager
    other.aliases       = self.aliases
    other.defaults      = self.defaults
    other.options       = self.options.override()
    other.tools         = self.tools._override( other )
    
    return other
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'script_locals':
      self.script_locals = self.__getSciptLocals()
      return self.script_locals
    
    raise AttributeError("No attribute '%s'" % str(attr) )
    
  #//-------------------------------------------------------//
  
  def   __getSciptLocals( self ):
    
    script_locals = {
      'options'   : self.options,
      'tools'     : self.tools,
      'Tool'      : self.tools.Tools,
      'Tools'     : self.tools.Tools,
      'AddTool'   : self.tools.AddTool,
      'FindFiles' : findFiles
    }
    
    for name in dir(self):
      if name.startswith('_'):
        continue
      
      member = getattr( self, name )
      if isinstance( member, types.MethodType ):
        script_locals.setdefault( name, member )
    
    return script_locals
  
  #//-------------------------------------------------------//
  
  def   _execScript( self, script, script_locals ):
    
    script = FilePath( script ).abspath()
    
    scripts_cache = self.scripts_cache
    
    script_result = scripts_cache.get( script, None )
    if script_result is not None:
      return script_result

    with Chdir( script.dirname() ):
      script_result = execFile( script, script_locals )
      scripts_cache[ script ] = script_result
      return script_result
  
  #//-------------------------------------------------------//
  
  def   ReadOptions( self, options_file ):
    
    script_locals = { 'options': self.options }
    
    script_locals = self._execScript( options_file, script_locals )
    
    self.options.update( script_locals )
  
  #//-------------------------------------------------------//
  
  def   Include( self, makefile ):
    
    other = self._override()
    return other._execScript( makefile, self.script_locals )
  
  #//-------------------------------------------------------//
  
  def   AddNodes( self, nodes ):
    self.build_manager.add( nodes )
  
  #//-------------------------------------------------------//
  
  def   SetBuildDir( self, build_dir ):
    self.options.build_dir = FilePath(build_dir).abspath()
  
  #//-------------------------------------------------------//
  
  def   Depends( self, node, dependencies ):
    node.depends( dependencies )
    self.build_manager.depends( node, node.dep_nodes )
  
  #//-------------------------------------------------------//
  
  def   Alias( self, alias, node ):
    for alias, node in itertools.product( toSequence( alias ), toSequence( node ) ):
      self.aliases.setdefault( alias, []).append( node )
    
  #//-------------------------------------------------------//
  
  def   Default( self, node ):
    for node in toSequence( node ):
      self.defaults.append( node )
  
  #//-------------------------------------------------------//
  
  def   AlwaysBuild( self, node ):
    null_value = NullValue()
    for node in toSequence( node ):
      node.depends( null_value )
  
  #//=======================================================//
  
  def   _getBuildNodes( self ):
    target_nodes = []
    
    for alias in self.targets:
      target_nodes += self.aliases.get( alias, [] )
    
    if not target_nodes:
      target_nodes = self.defaults
    
    if not target_nodes:
      target_nodes = None
    
    return target_nodes
  
  #//=======================================================//
  
  def   Build( self, jobs = None, keep_going = False, verbose = False ):
    brief = not verbose
    
    if not jobs:
      jobs = 0
    else:
      jobs = int(jobs)
    
    if not jobs:
      jobs = cpuCount()
    
    if jobs < 0:
      jobs = 1
    
    elif jobs > 32:
      jobs = 32
    
    build_nodes = self._getBuildNodes()
    
    is_ok = self.build_manager.build( jobs = jobs, keep_going = bool(keep_going), nodes = build_nodes, brief = brief )
    return is_ok
  
  #//=======================================================//
  
  def   PrintFails(self):
    self.build_manager.printFails()
  
  #//=======================================================//
  
  def   Clean( self ):
    pass

#//===========================================================================//
