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

from aql.utils import cpuCount, CLIConfig, CLIOption, getFunctionArgs, finishHandleEvents, logError, execFile
from aql.types import FilePath, FilePaths, SplitListType, Singleton
from aql.values import Value, NoContent, DependsValue, DependsValueContent
from aql.options import builtinOptions, Options
from aql.nodes import BuildManager, Node

from .aql_tools import ToolsManager

#//===========================================================================//

AQL_CACHE_FILE_NAME = '.aql.cache'

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
      CLIOption( "-I", "--tool-paths",      "tool_paths",     Paths,      [],           "Paths to tools and setup scripts.", 'FILE PATH, ...'),
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
    
    ignore_options = set(['directory', 'makefile', 'list_options', 'config', 'verbose', 'quiet', 'search_up'])
    for name,value in cli_config.items():
      if (name not in ignore_options) and (value is not None):
        cli_options[ name ] = value
    
    log_level = 1
    
    if cli_config.verbose:
      log_level += 1
    
    if cli_config.quiet:
      log_level -= 1
    
    cli_options['log_level'] = log_level
    
    options.update( cli_options )
    
    if cli_config.list_options:
      printOptions( options )
    
    self.options = options
    self.directory = cli_config.directory.abs()
    self.makefile = cli_config.makefile
    self.targets = cli_config.targets

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
    
    options = self.options
    
    for name, value in kw.items():
      if name == "options":
        if not isinstance( value, Options ):
          raise ErrorProjectBuilderMethodInvalidOptions( value )
        options = value
      if name in ['sources', 'source']:
        sources += toSequnece( value )
      else:
        if name in self.arg_names:
          args_kw[ name ] = value
        else:
          options_kw[ name ] = value
    
    if options_kw:
      options = options.override()
      options.update( options_kw )
    
    return options, sources, args_kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, *args, **kw ):
    options, sources, args_kw = self.__getOptionsAndArgs( kw )
    sources += args
    
    builder = self.method( options, **args_kw )
    
    source_values = []
    source_nodes = []
    source_others = []
    
    for source in sources:
      if isinstance( source, Node ):
        source_nodes.append( source )
      elif isinstance( source, Value ):
        source_values.append( source )
      else:
        source_others.append( source )
    
    source_values.extend( builder.makeSourceValues( source_others ) )
    
    node = Node( builder, source_nodes, source_values )
    
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
    tools.loadTools( self.project.options.tool_paths.value() )
    
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
    
    tool_paths = kw.pop('tool_paths', [])
    options = kw.pop( 'options', None )
    
    self.tools.loadTools( tool_paths )
    
    if options is None:
      options = self.project.options
    
    if kw:
      options = options.override()
      options.update( kw )
    
    self.tools.loadTools( options.tool_paths.value() )
    
    tools = [ self.__addTool( tool_name, options ) for tool_name in tool_names ]
    
    return tools[0] if len(tools) == 1 else tools
  
  #//-------------------------------------------------------//
  
  def   AddTool( self, tool_class, tool_names = tuple() ):
    self.tools.addTool( tool_class, tool_names )
    
    return self.__addTool( tool_class, self.project.options )

#//===========================================================================//

class Project( object ):
  
  def   __init__( self, options, targets ):
    
    self.targets = targets
    self.options = options
    self.files_cache = {}
    
    self.build_manager = BuildManager()
    
    self.tools = ProjectTools( self )
  
  #//-------------------------------------------------------//
  
  def   _override( self ):
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
    
    raise AttributeError("No attribute '%s'" % str(atrr) )
    
  #//-------------------------------------------------------//
  
  def   __getSciptLocals( self ):
    
    locals = {
      'options' : self.options,
      'tools'   : self.tools,
      'Tool'    : self.tools.Tools,
      'Tools'   : self.tools.Tools,
      'AddTool' : self.tools.AddTool,
    }
    
    for name in dir(self):
      if name.startswith('_'):
        continue
      
      member = getattr( self, name )
      if isinstance( member, types.MethodType ):
        locals.setdefault( name, member )
    
    return locals
  
  #//-------------------------------------------------------//
  
  def   _execScript( self, script, script_locals ):
    
    script = FilePath( script ).abs()
    
    files_cache = self.files_cache
    
    locals = files_cache.get( script, None )
    if locals is not None:
      return locals
    
    self.files_cache.setdefault( script, {} )
    
    try:
      cur_dir = os.getcwd()
      os.chdir( script.dir )
      return execFile( script, script_locals )
    finally:
      os.chdir( cur_dir )
  
  #//-------------------------------------------------------//
  
  def   ReadOptions( self, options_file ):
    
    script_locals = { 'options': self.options }
    
    locals = self._execScript( options_file, script_locals )
    
    options.update( locals )
  
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
  
  def   Depends( self, node, dependency ):
    pass
  
  #//-------------------------------------------------------//
  
  def   Ignore( self, node, dependency ):
    pass
  
  def   Alias( self, alias, node ):
    pass
  
  def   AlwaysBuild( self, node ):
    pass
  
  #//=======================================================//
  
  def   Build( self ):
    keep_going = self.options.keep_going.value()
    jobs = self.options.jobs.value()
    
    failed_nodes = self.build_manager.build( jobs, keep_going )
    
    finishHandleEvents()
    
    return failed_nodes
  
  #//=======================================================//
  
  def   Clean( self ):
    pass

#//===========================================================================//

if __name__ == "__main__":
  ReadOptions('../../aql.config')
  
  # options
  # tools
  
  libs = Include('src/aql.make')
  
  
  c, cpp = Tools('c', 'c++')
  
  c.LinkProgram( src_files, libs )
  
  cpp = tools.cpp
  
  objs = cpp.Compile( cpp_files )
  lib = cpp.SharedLibrary( objs )
  objs = cpp.Compile( objs, options = lib.options )
  
  c = Clean( objs )
  
  
  prj = aql.Project( tool_paths )
  
  prj.Tool('c').Compile( c_files, optimization = 'size', debug_symbols = False )
  
  cpp = prj.Tool( 'c++' )
  cpp.Compile( cpp_files, optimization = 'speed' )
  
  prj.Tool('c++')
  
  prj.Compile( c_files, optimization = 'size', debug_symbols = False )
  
  prj_c = aql.Project( prj_cfg, tool_paths )
  prj_c.Tool( 'c' )
  prj_c.Compile( cpp_files, optimization = 'speed' )
  
  #//-------------------------------------------------------//
  
  prj = aql.Project( prj_cfg, tool_paths )
  prj.Tool( 'c++', 'c' )
  
  cpp_objs = prj.CompileCpp( cpp_files, optimization = 'size' )
  c_objs = prj.CompileC( c_files, optimization = 'speed' )
  objs = prj.Compile( c_cpp_files )
  
  cpp_lib = prj.LinkSharedLib( cpp_objs )
  c_lib = prj.LinkLibrary( c_objs )
  
  prog = prj.LinkProgram( [ objs, prj.FilterLibs( cpp_lib ), c_lib ] )
  
  #//-------------------------------------------------------//
  
  prj = aql.Project( prj_cfg, tool_paths )
  
  prj.Tools( 'g++', 'gcc' )
  
  cpp_objs = prj.cpp.Compile( cpp_files, optimization = 'size' )
  c_objs = prj.c.Compile( c_files, optimization = 'speed' )
  
  cpp_lib = prj.cpp.LinkSharedLib( cpp_objs )
  c_lib = prj.c.LinkLibrary( c_objs )
  
  prog = prj.cpp.LinkProgram( [ objs, prj.FilterLibs( cpp_lib ), c_lib ] )
  
  
  """
  1. kw - args
  
  """
  
  
