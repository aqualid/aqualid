#
# Copyright (c) 2012,2013 The developers of Aqualid project - http://aqualid.googlecode.com
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
            'ErrorProjectBuilderMethodExists',
            'ErrorProjectBuilderMethodFewArguments',
            'ErrorProjectBuilderMethodUnbound',
            'ErrorProjectBuilderMethodWithKW',
            'ErrorProjectInvalidMethod',
          )

import os
import types

from aql.utils import CLIConfig, CLIOption, getFunctionArgs, finishHandleEvents, execFile, flattenList, findFiles
from aql.util_types import FilePath, FilePaths, SplitListType, toSequence, UniqueList
from aql.values import Value, FileValue
from aql.options import builtinOptions, Options #, optionValueEvaluator
from aql.nodes import BuildManager, Node

from .aql_tools import ToolsManager

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

class   ErrorProjectBuilderMethodExists( Exception ):
  def   __init__( self, method_name ):
    msg = "Builder method '%s' is already added to project" % str(method_name)
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
  
  __slots__ = ('directory', 'makefile', 'targets', 'options' )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, args = None ):
    
    CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"
    
    Paths = SplitListType( FilePaths, ', ' )
    
    CLI_OPTIONS = (
      
      CLIOption( "-C", "--directory",       "directory",      FilePath,   '',           "Change directory before reading the make files.", 'FILE PATH'),
      CLIOption( "-f", "--makefile",        "makefile",       FilePath,   'make.aql',   "Path to a make file.", 'FILE PATH'),
      CLIOption( "-l", "--list-options",    "list_options",   bool,       False,        "List all available options and exit." ),
      CLIOption( "-c", "--config",          "config",         FilePath,   None,         "The configuration file used to read CLI arguments." ),
      CLIOption( "-u", "--up",              "search_up",      bool,       False,        "Search up directory tree for a make file." ),
      
      CLIOption( "-o", "--build-directory", "build_dir",      FilePath,   'output',     "Build output path.", 'FILE PATH'),
      CLIOption( "-I", "--tools-path",      "tools_path",     Paths,      [],           "Path to tools and setup scripts.", 'FILE PATH, ...'),
      CLIOption( "-k", "--keep-going",      "keep_going",     bool,       False,        "Continue build even if any target failed." ),
      CLIOption( "-B", "--always-make",     "build_all",      bool,       False,        "Unconditionally make all targets." ),
      CLIOption( "-j", "--jobs",            "jobs",           int,        None,         "Number of parallel jobs to process targets.", 'NUMBER' ),
      CLIOption( "-v", "--verbose",         "verbose",        bool,       False,        "Verbose mode." ),
      CLIOption( "-q", "--quiet",           "quiet",          bool,       False,        "Quiet mode." ),
    )
    
    cli_config = CLIConfig( CLI_USAGE, CLI_OPTIONS, args )
    
    options = builtinOptions()
    
    config = cli_config.config
    
    if config:
      cli_config.readConfig( config, { 'options', options })
    
    cli_options = {}
    
    ignore_options = {'directory', 'makefile', 'list_options', 'config', 'verbose', 'quiet', 'search_up'}
    for name,value in cli_config.items():
      if (name not in ignore_options) and (value is not None):
        if name == 'tools_path':
          value = map( os.path.abspath, value )
        elif name == 'build_dir':
          value = os.path.abspath( value )

        cli_options[ name ] = value
    
    log_level = 1
    
    if cli_config.verbose:
      log_level += 1
    
    if cli_config.quiet:
      log_level -= 1
    
    cli_options['log_level'] = log_level

    options.update( cli_options )
    print( "options.tools_path: %s" % (options.tools_path,))

    if cli_config.list_options:
      printOptions( options )
    
    self.options = options
    self.directory = cli_config.directory.abs()
    self.makefile = cli_config.makefile
    self.targets = cli_config.targets

#//===========================================================================//

#@optionValueEvaluator
def   _evalNode( value ):
  if isinstance( value, Node ):
    values = value.targets()
  elif isinstance( value, (list, tuple, UniqueList, Value ) ):
    values = toSequence( value )
  else:
    return value

  opt_value = []
  
  for value in values:
    if isinstance( value, Value ):
      value = value.get()
      
    opt_value.append( value )
  
  if len(opt_value) == 1:
    opt_value = opt_value[0]
  
  return opt_value

#//===========================================================================//

class _ToolBuilderProxy( object ):
  
  def   __init__( self, method, options, args_kw, options_kw ):
    
    self._tool_builder = None
    self._tool_method = method

    if options_kw:
      options = options.override()

    self._tool_options = options
    self._tool_args_kw = args_kw
    self._tool_options_kw = options_kw

  @staticmethod
  def   __evalKW( kw ):
    return { name: _evalNode( value ) for name, value in kw.items() }
  
  def   __getattr__( self, attr ):
    builder = self._tool_builder
    if builder is None:
      args_kw = self.__evalKW( self._tool_args_kw )

      options = self._tool_options

      options_kw = self.__evalKW( self._tool_options_kw )
      if options_kw:
        options.update( options_kw )

      builder = self._tool_method( options, **args_kw )
      self._tool_builder = builder

    return getattr( builder, attr )
  

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
      
      min_args += 1 # add self argument
    
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
          if isinstance( v, (Node, Value)):
            dep_nodes.append( v )
        
        if name in self.arg_names:
          args_kw[ name ] = value
        else:
          options_kw[ name ] = value
    
    if options_kw:
      options = options.override()
    #  options.update( options_kw )
    
    return options, dep_nodes, sources, args_kw, options_kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, *args, **kw ):
    options, dep_nodes, sources, args_kw, options_kw = self.__getOptionsAndArgs( kw )
    sources += args
    sources = flattenList( sources )
    
    builder = _ToolBuilderProxy( self.method, options, args_kw, options_kw )
    
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
    
    tool_options = options.override()
    
    tool, names = self.tools.getTool( tool_name, tool_options )
    
    tool = ToolWrapper( tool, self.project, tool_options )
    
    attrs = self.__dict__
    
    for name in names:
      if name not in attrs:
        attrs[ name ] = tool
        name_tools = self.tools_cache.setdefault( name, {} )
        name_tools[ options_ref ] = tool
    
    return tool
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    return self.__addTool( name, self.project.options )
  
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
    self.files_cache = {}
    
    self.build_manager = BuildManager()
    
    self.tools = ProjectTools( self )
  
  #//-------------------------------------------------------//
  
  def   _override( self ):
    """
    @rtype : Project
    """
    other = super(Project,self).__new__( self.__class__ )
    
    other.targets       = self.targets
    other.files_cache   = self.files_cache
    other.build_manager = self.build_manager
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
    
    script = FilePath( script ).abs()
    
    files_cache = self.files_cache
    
    script_result = files_cache.get( script, None )
    if script_result is not None:
      return script_result

    cur_dir = os.getcwd()

    try:
      os.chdir( script.dir )
      script_result = execFile( script, script_locals )
      files_cache[ script ] = script_result
      return script_result
    finally:
      os.chdir( cur_dir )
  
  #//-------------------------------------------------------//
  
  def   ExecuteMethod( self, method, *args, **kw ):
    raise NotImplementedError()
  
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
  
  def   BuildDir( self, build_dir ):
    self.options.build_dir = FilePath(build_dir).abs()
  
  #//-------------------------------------------------------//
  
  def   Depends( self, node, dependencies ):
    node.depends( dependencies )
    self.build_manager.depends( node, node.dep_nodes )
  
  #//-------------------------------------------------------//
  
  def   Ignore( self, node, dependency ):
    raise NotImplementedError()
  
  def   Alias( self, alias, node ):
    raise NotImplementedError()
  
  def   AlwaysBuild( self, node ):
    raise NotImplementedError()
  
  def   DirName(self, node):
    raise NotImplementedError()
  
  def   BaseName(self, node):
    raise NotImplementedError()
    
    
  #//=======================================================//
  
  def   Build( self ):
    keep_going = self.options.keep_going.get()
    jobs = self.options.jobs.get()
    
    failed_nodes = self.build_manager.build( jobs, keep_going )
    
    finishHandleEvents()
    
    return failed_nodes
  
  #//=======================================================//
  
  def   Clean( self ):
    pass

#//===========================================================================//

"""
  ReadOptions('../../aql.config')
  
  # options
  # tools
  
  libs = Include('src/aql.make')
  
  cpp_paths = ReadLibConfig('config.cfg')
  
  cpp.options.cpp_paths += cpp_paths
  
  
  c, cpp = Tools('c', 'c++')
  
  c.LinkProgram( src_files, libs )
  
  cpp = tools.cpp
  
  objs = cpp.Compile( cpp_files )
  lib = cpp.SharedLibrary( objs )
  objs = cpp.Compile( objs, options = lib.options )
  
  c = Clean( objs )
  
  
  prj = aql.Project( tools_path )
  
  prj.Tool('c').Compile( c_files, optimization = 'size', debug_symbols = False )
  
  cpp = prj.Tool( 'c++' )
  cpp.Compile( cpp_files, optimization = 'speed' )
  
  prj.Tool('c++')
  
  prj.Compile( c_files, optimization = 'size', debug_symbols = False )
  
  prj_c = aql.Project( prj_cfg, tools_path )
  prj_c.Tool( 'c' )
  prj_c.Compile( cpp_files, optimization = 'speed' )
  
  #//-------------------------------------------------------//
  
  prj = aql.Project( prj_cfg, tools_path )
  prj.Tool( 'c++', 'c' )
  
  cpp_objs = prj.CompileCpp( cpp_files, optimization = 'size' )
  c_objs = prj.CompileC( c_files, optimization = 'speed' )
  objs = prj.Compile( c_cpp_files )
  
  cpp_lib = prj.LinkSharedLib( cpp_objs )
  c_lib = prj.LinkLibrary( c_objs )
  
  prog = prj.LinkProgram( [ objs, prj.FilterLibs( cpp_lib ), c_lib ] )
  
  #//-------------------------------------------------------//
  
  prj = aql.Project( prj_cfg, tools_path )
  
  prj.Tools( 'g++', 'gcc' )
  
  cpp_objs = prj.cpp.Compile( cpp_files, optimization = 'size' )
  c_objs = prj.c.Compile( c_files, optimization = 'speed' )
  
  cpp_lib = prj.cpp.LinkSharedLib( cpp_objs )
  c_lib = prj.c.LinkLibrary( c_objs )
  
  prog = prj.cpp.LinkProgram( [ objs, prj.FilterLibs( cpp_lib ), c_lib ] )
  
  
  """
