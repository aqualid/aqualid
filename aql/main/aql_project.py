#
# Copyright (c) 2012-2014 The developers of Aqualid project
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

import os.path
import site
import types
import itertools

from aql.utils import CLIConfig, CLIOption, getFunctionArgs, execFile, flattenList, findFiles, cpuCount, Chdir
from aql.util_types import FilePath, ValueListType, UniqueList, SplitListType, toSequence, AqlException
from aql.values import NullValue, ValueBase, FileTimestampValue, FileChecksumValue, DirValue, SimpleValue
from aql.options import builtinOptions, Options, iUpdateValue
from aql.nodes import BuildManager, Node, BatchNode, NodeTargetsFilter

from .aql_info import getAqlInfo
from .aql_tools import getToolsManager
from .aql_builtin_tools import BuiltinTool


#//===========================================================================//

class   ErrorProjectInvalidMethod( AqlException ):
  def   __init__( self, method ):
    msg = "Invalid project method: '%s'" % (method,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectUnknownTarget( AqlException ):
  def   __init__( self, target ):
    msg = "Unknown build target: '%s'" % (target,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodWithKW( AqlException ):
  def   __init__( self, method ):
    msg = "Keyword arguments are not allowed in builder method: '%s'" % (method,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodUnbound( AqlException ):
  def   __init__( self, method ):
    msg = "Unbound builder method: '%s'" % (method,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodFewArguments( AqlException ):
  def   __init__( self, method ):
    msg = "Too few arguments in builder method: '%s'" % (method,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodInvalidOptions( AqlException ):
  def   __init__( self, value ):
    msg = "Type of 'options' argument must be Options, instead of : '%s'(%s)" % (type(value), value)
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   _getUserConfigDir( info = getAqlInfo() ):
  return os.path.join( os.path.expanduser('~'), '.config', info.module )

#//===========================================================================//

def   _getDefaultToolsPath( info = getAqlInfo() ):
  from distutils.sysconfig import get_python_lib
  python_site = os.path.join( get_python_lib(), info.module )
  
  user_site = os.path.join( site.USER_SITE, info.module )
  
  user_local = _getUserConfigDir()
  
  return [ os.path.join(path, 'tools') for path in (python_site, user_site, user_local) ]

#//===========================================================================//

def   _readConfig( config_file, cli_config, options, tools_path ):
  cli_config.readConfig( config_file, { 'options': options })
  
  if cli_config.tools_path:
    tools_path.extend( cli_config.tools_path )
    cli_config.tools_path = None

#//===========================================================================//

#noinspection PyUnresolvedReferences
class ProjectConfig( object ):
  
  __slots__ = ('directory', 'makefile', 'targets', 'options', 'arguments',
               'verbose', 'no_output', 'jobs', 'keep_going', 'search_up', 'tools_path',
               'build_always', 'clean', 'status', 'list_options', 'list_targets',
               'debug_profile', 'debug_memory', 'debug_explain', 'debug_backtrace',
               'force_lock', 'show_version',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, args = None ):
    
    CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"
    
    Paths = ValueListType( UniqueList, FilePath )
    
    CLI_OPTIONS = (
      
      CLIOption( "-C", "--directory",         "directory",        FilePath,   '',           "Change directory before reading the make files.", 'FILE PATH'),
      CLIOption( "-f", "--makefile",          "makefile",         FilePath,   'make.aql',   "Path to a make file.", 'FILE PATH'),
      CLIOption( "-o", "--list-options",      "list_options",     bool,       False,        "List all available options and exit." ),
      CLIOption( "-t", "--list-targets",      "list_targets",     bool,       False,        "List all available targets and exit." ),
      CLIOption( "-c", "--config",            "config",           FilePath,   None,         "The configuration file used to read CLI arguments." ),
      CLIOption( "-B", "--always",            "build_always",     bool,       False,        "Unconditionally build all targets." ),
      CLIOption( "-R", "--clean",             "clean",            bool,       False,        "Cleans targets." ),
      CLIOption( "-n", "--status",            "status",           bool,       False,        "Print status of targets." ),
      CLIOption( "-u", "--up",                "search_up",        bool,       False,        "Search up directory tree for a make file." ),
                                                                  
      # CLIOption( "-b", "--build-directory",   "build_dir",        FilePath,   'output',     "Build output path.", 'FILE PATH'),
      CLIOption( "-I", "--tools-path",        "tools_path",       Paths,      [],           "Path to tools and setup scripts.", 'FILE PATH, ...'),
      CLIOption( "-k", "--keep-going",        "keep_going",       bool,       False,        "Keep going when some targets can't be built." ),
      CLIOption( "-j", "--jobs",              "jobs",             int,        None,         "Number of parallel jobs to process targets.", 'NUMBER' ),
      CLIOption( "-v", "--verbose",           "verbose",          bool,       False,        "Verbose mode." ),
      CLIOption( "-s", "--no-output",         "no_output",        bool,       False,        "Don't print output streams of builder's commands." ),
      CLIOption( None, "--debug-memory",      "debug_memory",     bool,       False,        "Display memory usage." ),
      CLIOption( None, "--debug-profile",     "debug_profile",    FilePath,   None,         "Run under profiler and save the results in the specified file.", 'FILE PATH' ),
      CLIOption( None, "--debug-explain",     "debug_explain",    bool,       False,        "Show the reasons why targets are being rebuilt" ),
      CLIOption( "--bt", "--debug-backtrace", "debug_backtrace",  bool,       False,        "Show call stack back traces for errors." ),
      CLIOption( None, "--force-lock",        "force_lock",       bool,       False,        "Forces to lock AQL DB file." ),
      CLIOption( "-V", "--version",           "version",          bool,       False,        "Show version and exit." ),
    )
    
    cli_config = CLIConfig( CLI_USAGE, CLI_OPTIONS, args )
    
    options = builtinOptions()
    
    #//-------------------------------------------------------//
    # Add default tools path 
    
    tools_path = _getDefaultToolsPath()
    cli_tools_path = cli_config.tools_path
    cli_config.tools_path = None
    
    #//-------------------------------------------------------//
    # Read a config file from user's home
    
    user_config = os.path.join( _getUserConfigDir(), 'default.cfg' )
    if os.path.isfile( user_config ):
      _readConfig( user_config, cli_config, options, tools_path )
    
    #//-------------------------------------------------------//
    # Read a config file specified from CLI
    
    config = cli_config.config
    if config:
      _readConfig( config, cli_config, options, tools_path )
    
    # add user specified tools_path to the end of search path to override default tools
    if cli_tools_path:
      tools_path.extend( cli_tools_path )
    
    #//-------------------------------------------------------//
    # Apply non-cli arguments to options 
    
    arguments = {}
    
    ignore_options = set( ('list_options', 'config') )
    ignore_options.update( ProjectConfig.__slots__ )
    
    for name,value in cli_config.items():
      if (name not in ignore_options) and (value is not None):
        arguments[ name ] = value
    
    options.update( arguments )
    
    #//-------------------------------------------------------//
    
    self.options          = options
    self.arguments        = arguments
    self.directory        = os.path.abspath( cli_config.directory )
    self.makefile         = cli_config.makefile
    self.search_up        = cli_config.search_up
    self.tools_path       = tools_path
    self.targets          = cli_config.targets
    self.verbose          = cli_config.verbose
    self.show_version     = cli_config.version
    self.no_output        = cli_config.no_output
    self.keep_going       = cli_config.keep_going
    self.build_always     = cli_config.build_always
    self.clean            = cli_config.clean
    self.status           = cli_config.status
    self.list_options     = cli_config.list_options
    self.list_targets     = cli_config.list_targets
    self.jobs             = cli_config.jobs
    self.force_lock       = cli_config.force_lock
    self.debug_profile    = cli_config.debug_profile
    self.debug_memory     = cli_config.debug_memory
    self.debug_explain    = cli_config.debug_explain
    self.debug_backtrace  = cli_config.debug_backtrace

#//===========================================================================//

class BuilderWrapper( object ):
  __slots__ = ( 'project', 'options', 'method', 'arg_names' )
  
  def   __init__( self, method, project, options ):
    self.arg_names  = self.__checkBuilderMethod( method )
    self.method     = method
    self.project    = project
    self.options    = options

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
    sources = []
    deps = []
    
    options = kw.pop("options", None )
    if options is not None:
      if not isinstance( options, Options ):
        raise ErrorProjectBuilderMethodInvalidOptions( options )
    else:
      options = self.options
    
    options = options.override()
    
    for name, value in kw.items():
      if name in ['sources', 'source']:
        sources += toSequence( value )
      else:
        for v in toSequence( value ):
          if isinstance( v, (Node, NodeTargetsFilter, ValueBase) ):
            deps.append( v )
                  
        if name in self.arg_names:
          args_kw[ name ] = value
        else:
          options.appendValue( name, value, iUpdateValue )
    
    return options, deps, sources, args_kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, *args, **kw ):
    
    options, deps, sources, args_kw = self.__getOptionsAndArgs( kw )
    
    sources += args
    sources = flattenList( sources )
    
    builder = self.method( options, **args_kw )
    
    if builder.isBatch() and ((len(sources) > 1) or not builder.canBuild()):
      node = BatchNode( builder, sources )
    else:
      node = Node( builder, sources )

    node.depends( deps )

    self.project.AddNodes( (node,) )
    
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
    
    tools = getToolsManager()
    
    tools.loadTools( self.project.config.tools_path )
    
    self.tools = tools
  
  #//-------------------------------------------------------//
  
  def   _getToolsOptions(self):
    tools_options = {}
    for name, tool in self.tools_cache.items():
      tool = next(iter(tool.values()))
      tools_options.setdefault( tool.options, []).append( name )
    
    return tools_options
  
  #//-------------------------------------------------------//
  
  def   __addTool( self, tool_name, options ):
    
    options_ref = options.getHashRef()
    
    try:
      return self.tools_cache[ tool_name ][options_ref]
    except KeyError:
      pass
    
    tool, tool_names, tool_options = self.tools.getTool( tool_name, options )
    
    tool = ToolWrapper( tool, self.project, tool_options )
    
    attrs = self.__dict__
    
    for name in tool_names:
      attrs.setdefault( name, tool )
      self.tools_cache.setdefault( name, {} )[ options_ref ] = tool
    
    return tool
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    
    options = self.project.options
    
    tool = BuiltinTool( options )
    tool_method = getattr( tool, name, None )
    if tool_method and isinstance( tool_method, (types.FunctionType, types.MethodType) ):
      return BuilderWrapper( tool_method, self.project, options )
    
    return self.__addTool( name, options )
  
  #//-------------------------------------------------------//
  
  def __getitem__( self, name ):
    return getattr( self, name )
  
  #//-------------------------------------------------------//
  
  def   Tools( self, *tool_names, **kw ):
    
    options = kw.pop( 'options', None )
    
    tools_path = kw.pop('tools_path', None )
    if tools_path:
      self.tools.loadTools( tools_path )
    
    if options is None:
      options = self.project.options
    
    if kw:
      options = options.override()
      options.update( kw )
    
    tools = [ self.__addTool( tool_name, options ) for tool_name in tool_names ]
    
    return tools
  
  #//-------------------------------------------------------//
  
  def   Tool( self, tool_name, **kw ):
    return self.Tools( tool_name, **kw )[0]
  
  #//-------------------------------------------------------//
  
  def   AddTool( self, tool_class, tool_names = tuple() ):
    self.tools.addTool( tool_class, tool_names )
    
    return self.__addTool( tool_class, self.project.options )

#//===========================================================================//

def   _textTargets( targets ):
  text = ["","  Targets:", "==================", ""]
  
  max_name = ""
  for names, is_built, description in targets:
    max_name = max( max_name, *names, key = len )
  
  name_format = "{is_built} {name:<%s}" % len(max_name)
  
  for names, is_built, description in targets:
    if len(names) > 1 and text[-1]:
      text.append('')
    
    is_built_mark = "*" if is_built else " "
    
    for name in names:
      text.append( name_format.format( name = name, is_built = is_built_mark ))
    
    text[-1] += ' :  ' + description
    
    if len(names) > 1:
      text.append('')
  
  text.append('')
  return text

#//===========================================================================//

class Project( object ):
  
  def   __init__( self, config ):
    
    self.targets = config.targets
    self.options = config.options
    self.arguments = config.arguments
    self.config = config
    self.scripts_cache = {}
    self.aliases = {}
    self.alias_descriptions = {}
    self.defaults = []
    
    self.build_manager = BuildManager()
    
    self.tools = ProjectTools( self )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'script_locals':
      self.script_locals = self.__getSciptLocals()
      return self.script_locals
    
    raise AttributeError("No attribute '%s'" % (attr,) )
    
  #//-------------------------------------------------------//
  
  def   __getSciptLocals( self ):
    
    script_locals = {
      'options'   : self.options,
      'tools'     : self.tools,
      'Tool'      : self.tools.Tool,
      'Tools'     : self.tools.Tools,
      'AddTool'   : self.tools.AddTool,
      'LoadTools' : self.tools.tools.loadTools,
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
  
  def   FileValue(self, filepath, options = None ):
    if options is None:
      options = self.options
    file_type = FileTimestampValue if options.file_signature == 'timestamp' else FileChecksumValue
    
    return file_type( filepath )
  
  #//-------------------------------------------------------//
  
  def   DirValue( self, filepath ):
    return DirValue( filepath )
  
  #//-------------------------------------------------------//
  
  def   Value( self, data, name = None ):
    return SimpleValue( data = data, name = name )
  
  #//-------------------------------------------------------//
  
  def   _execScript( self, script, script_locals ):
    
    script = os.path.abspath( script )
    
    scripts_cache = self.scripts_cache
    
    script_result = scripts_cache.get( script, None )
    if script_result is not None:
      return script_result

    with Chdir( os.path.dirname( script ) ):
      script_result = execFile( script, script_locals )
      scripts_cache[ script ] = script_result
      return script_result
  
  #//-------------------------------------------------------//
  
  def   ReadOptions( self, options_file, options = None ):
    
    if options is None:
      options = self.options
    
    script_locals = { 'options': options }
    
    script_locals = self._execScript( options_file, script_locals )
    
    # remove overridden options from CLI
    for arg in self.arguments:
      try:
        del script_locals[ arg ]
      except KeyError:
        pass
    
    tools_path = script_locals.pop( 'tools_path', None )
    if tools_path:
      self.tools.tools.loadTools( tools_path )
    
    options.update( script_locals )
  
  #//-------------------------------------------------------//
  
  def   Script( self, makefile ):
    return self._execScript( makefile, self.script_locals )
  
  #//-------------------------------------------------------//
  
  def   AddNodes( self, nodes ):
    self.build_manager.add( nodes )
  
  #//-------------------------------------------------------//
  
  def   SetBuildDir( self, build_dir ):
    self.options.build_dir = os.path.abspath(build_dir)
  
  #//-------------------------------------------------------//
  
  def   Depends( self, nodes, dependencies ):
    dependencies = tuple(toSequence( dependencies ))
    
    for node in toSequence( nodes ):
      node.depends( dependencies )
      self.build_manager.depends( node, node.dep_nodes )
  
  #//-------------------------------------------------------//
  
  def   Requires( self, nodes, dependencies ):
    dependencies = tuple( dep for dep in toSequence( dependencies ) if isinstance( dep, Node ) )
    
    depends = self.build_manager.depends
    for node in toSequence( nodes ):
      depends( node, dependencies )
  
  #//-------------------------------------------------------//
  
  def   RequireModules( self, nodes, dependencies ):
    dependencies = tuple( dep for dep in toSequence( dependencies ) if isinstance( dep, Node ) )
    
    moduleDepends = self.build_manager.moduleDepends
    for node in toSequence( nodes ):
      moduleDepends( node, dependencies )
  
  #//-------------------------------------------------------//
  
  # TODO: It works not fully correctly yet. See test aq_test_sync_modules
  # def   SyncModules( self, nodes ):
  #   nodes = tuple( node for node in toSequence( nodes ) if isinstance( node, Node ) )
  #   self.build_manager.sync( nodes, deep = True)
  
  #//-------------------------------------------------------//
  
  def   Sync( self, *nodes ):
    nodes = flattenList( nodes )
    
    nodes = tuple( node for node in nodes if isinstance( node, Node ) )
    self.build_manager.sync( nodes )
  
  #//-------------------------------------------------------//
  
  def   Alias( self, alias, nodes, description = None ):
    for alias, node in itertools.product( toSequence( alias ), toSequence( nodes ) ):
      self.aliases.setdefault( alias, set()).add( node )
      
      if description:
        self.alias_descriptions[ alias ] = description
    
  #//-------------------------------------------------------//
  
  def   Default( self, nodes ):
    for node in toSequence( nodes ):
      self.defaults.append( node )
  
  #//-------------------------------------------------------//
  
  def   AlwaysBuild( self, nodes ):
    null_value = NullValue()
    for node in toSequence( nodes ):
      node.depends( null_value )
  
  #//=======================================================//
  
  def   _addAliasNodes(self, target_nodes, aliases ):
    try:
      for alias in aliases:
        target_nodes.update( self.aliases[ alias ] )
    except KeyError as ex:
      raise ErrorProjectUnknownTarget( ex.args[0] )
  
  #//=======================================================//
  
  def   _addDefaultNodes( self, target_nodes ):
    for node in self.defaults:
      if isinstance( node, Node ):
        target_nodes.add( node )
      else:
        self._addAliasNodes( target_nodes, (node,) )
  
  #//=======================================================//
  
  def   _getBuildNodes( self ):
    target_nodes = set()
    
    self._addAliasNodes( target_nodes, self.targets )
    
    if not target_nodes:
      self._addDefaultNodes( target_nodes )
    
    if not target_nodes:
      target_nodes = None
    
    return target_nodes
  
  #//=======================================================//
  
  def   Build( self, jobs = None ):
    config = self.config
    
    if jobs is None:
      jobs = config.jobs
    
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
    
    if not self.options.batch_groups.isSet():
      self.options.batch_groups = jobs
    
    build_nodes = self._getBuildNodes()
    
    keep_going     = config.keep_going,
    build_always   = config.build_always
    explain        = config.debug_explain
    with_backtrace = config.debug_backtrace
    force_lock     = config.force_lock
    
    is_ok = self.build_manager.build( jobs = jobs, keep_going = bool(keep_going), nodes = build_nodes,
                                      build_always = build_always, explain = explain,
                                      with_backtrace = with_backtrace, force_lock = force_lock )
    return is_ok
  
  #//=======================================================//
  
  def Clean( self, force_lock = False ):
    build_nodes = self._getBuildNodes()
    
    self.build_manager.clear( nodes = build_nodes, force_lock = force_lock )
  
  #//=======================================================//
  
  def Status( self, explain = False, force_lock = False ):
    build_nodes = self._getBuildNodes()
    
    is_actual = self.build_manager.status( nodes = build_nodes, explain = explain, force_lock = force_lock )
    return is_actual
  
  #//=======================================================//
  
  def ListTargets( self ):
    targets = []
    node2alias = {}
    
    for alias, nodes in self.aliases.items():
      key = frozenset(nodes)
      target_info = node2alias.setdefault( key, [[],""])
      target_info[0].append( alias )
      description = self.alias_descriptions.get( alias, None )
      if description:
        if len(target_info[1]) < len(description):
          target_info[1] = description
    
    build_nodes = self._getBuildNodes()
    
    for nodes, aliases_and_description in node2alias.items():
      
      aliases, description = aliases_and_description
      
      aliases.sort( key = str.lower )
      max_alias = max( aliases, key = len )
      aliases.remove( max_alias )
      aliases.insert( 0, max_alias )
      
      is_built = (build_nodes is None) or nodes.issubset( build_nodes )
      targets.append( (tuple(aliases), is_built, description) )
    
    # sorted list in format: [ (target_names, is_built, description), ... ]
    targets.sort( key = lambda aliases: aliases[0][0].lower() )
    
    return _textTargets(targets)
  
  #//=======================================================//
  
  def   ListOptions( self, brief = False ):
    
    result = self.options.helpText("Builtin options:", brief = brief )
    
    for tools_options, names in self.tools._getToolsOptions().items():
      options_name = "Options of tool: %s" % (', '.join( names ) )
      result += tools_options.helpText( options_name, brief = brief)
    
    result.append("")
    return result
