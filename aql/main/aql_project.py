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

__all__ = ( 'Project', 'ProjectConfig',
            'ErrorProjectBuilderMethodExists',
            'ErrorProjectBuilderMethodFewArguments',
            'ErrorProjectBuilderMethodResultInvalid',
            'ErrorProjectBuilderMethodUnbound',
            'ErrorProjectBuilderMethodWithKW',
            'ErrorProjectInvalidMethod',
          )

import types

from aql.utils import cpuCount, CLIConfig, CLIOption, getFunctionArgs, finishHandleEvents, logError
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

class   ErrorProjectBuilderMethodResultInvalid( Exception ):
  def   __init__( self, method, result ):
    msg = "Builder method '%s' must return a Node object, actual result: '%s'" % (method, result)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProjectBuilderMethodInvalidOptions( Exception ):
  def   __init__( self, value ):
    msg = "Type of 'options' argument must be Options, instead of : '%s'(%s)" % (type(value), value)
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   jobsCount( jobs = None ):
  
  if jobs is None:
    jobs = cpuCount()
  
  return min( max( 1, int(jobs) ), 1024 )

#//===========================================================================//

class ProjectConfig( Singleton ):
  
  __slots__ = ('cli_options', 'options' )
  
  _instance = []
  
  #//-------------------------------------------------------//
  
  def   __init__( cls, args = None ):
    
    CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"
    
    Paths = SplitListType( FilePaths, ', ' )
    
    CLI_OPTIONS = (
      CLIOption( "-j", "--jobs",          "jobs",           jobsCount,  None,               "Number of parallel jobs to process targets.", 'NUMBER' ),
      CLIOption( "-f", "--make-file",     "make_file",      FilePath,   'aql.make',         "Path to main make file", 'FILE PATH'),
      CLIOption( "-o", "--output",        "output",         FilePath,   'output',           "Build output path", 'FILE PATH'),
      CLIOption( "-p", "--tool-paths",    "tool_paths",     Paths,      [],                 "Paths to tools and setup scripts", 'FILE PATH, ...'),
      CLIOption( "-k", "--keep-going",    "keep_going",     bool,       False,              "Continue build even if any target failed." ),
      CLIOption( "-l", "--list-options",  "list_options",   bool,       False,              "List all available options and exit." ),
      CLIOption( "-c", "--clean",         "clean_targets",  bool,       False,              "Clean up actual targets." ),
      CLIOption( "-v", "--verbose",       "verbose",        bool,       False,              "Verbose mode." ),
      CLIOption( "-q", "--quiet",         "quiet",          bool,       False,              "Quiet mode." ),
    )
    
    sel.cli_options = CLIConfig( CLI_USAGE, CLI_OPTIONS, args )
    self.options = builtinOptions()
  
  #//-------------------------------------------------------//
  
  def   __init__(self, args = None):
    pass
  
  #//-------------------------------------------------------//
  
  def   Update( self, config_file ):
    locals = { 'options': self.options }
    self.cli_options.readConfig( config_file, locals )
    
    options.update( self.cli_options )
  
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
    
    min_args = 2  # at least two arguments: for project and for options
    
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
    
    options = self.options
    
    for name, value in kw.items():
      if name == "options":
        if not isinstance( value, Options ):
          raise ErrorProjectBuilderMethodInvalidOptions( value )
        options = value
      
      if name in self.arg_names:
        args_kw[ name ] = value
      else:
        options_kw[ name ] = value
    
    if options_kw:
      options = options.override()
      options.update( options_kw )
    
    return options, args_kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, *args, **kw ):
    options, args_kw = self.__getOptionsAndArgs( kw )
    
    node = self.method( self.project, options, *args, **args_kw )
    
    if not isinstance( node, Node ):
      raise ErrorProjectBuilderMethodResultInvalid( self.method, node )
    
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

class Project( object ):
  
  def   __init__( self, tool_paths = None ):
    
    config = ProjectConfig.instance()
    
    self.options = config.options.override()
    self.build_manager = BuildManager( config.aql_db, config.jobs, config.keep_going )
    
    tools_manager = ToolsManager.instance()
    tools_manager.loadTools( config.tool_paths )
    tools_manager.loadTools( tool_paths )
    
    self.tools_manager = tools_manager
  
  #//=======================================================//
  
  def   __addTool( self, tool_name, options ):
    tool_options = options.override()
    
    tool, names = self.tools_manager.getTool( tool_name, self, tool_options )
    
    tool = ToolWrapper( tool, self, tool_options )
    
    attrs = self.__dict__
    
    for name in names:
      if name not in attrs:
        attrs[ name] = tool
    
    return tool
  
  #//=======================================================//
  
  def   __getattr__( self, name ):
    if not self.tools_manager.hasTool( name ):
      raise AttributeError( "%s instance has no attribute '%s'" % (type(self), name) )
    
    return self.__addTool( name, self.options )
  
  #//=======================================================//
  
  def __getitem__( self, name ):
    return getattr( self, name )
  
  #//=======================================================//
  
  def   Tools( self, *tool_names, **kw ):
    
    tool_paths = kw.get('tool_paths', [] )
    options = kw.get( 'options', None )
    
    tools_manager = self.tools_manager
    tools_manager.loadTools( tool_paths )
    
    if options is None:
      options = self.options
    
    for tool_name in tool_names:
      self.__addTool( tool_name, options )
  
  #//=======================================================//
  
  def   Tool( self, tool_class, tool_names = tuple() ):
    self.tools_manager.addTool( tool_class, tool_names )
    
    return self.__addTool( tool_class, self.options )
  
  #//=======================================================//
  
  def   AddMethod( self, method, name = None ):
    if not hasattr(tool_method, '__call__'):
      raise ErrorProjectInvalidMethod( method )
    
    if not name:
      name = method.__name__
    
    def   methodWrapper( *args, **kw ):
      return method( self, *args, **kw )
    
    setattr( self, name, methodWrapper )
  
  #//=======================================================//
  
  def   AddBuilder( self, builder, name = None ):
    
    builder_wrapper = BuilderWrapper( builder, self, self.options )
    
    if not name:
      name = builder.__name__
    
    if hasattr( self, name ):
      raise ErrorProjectBuilderMethodExists( builder )
    
    setattr( self, name, builder_wrapper )
  
  #//=======================================================//
  
  def   AddNodes( self, nodes ):
    self.build_manager.add( nodes )
  
  #//=======================================================//
  
  def   Depends( self, node, dependency ):
    pass
  
  #//=======================================================//
  
  def   Ignore( self, node, dependency ):
    pass
  
  def   Alias( self, alias, node ):
    pass
  
  def   AlwaysBuild( self, node ):
    pass
  
  def   Include( self, scripts ):
    pass
  
  #//=======================================================//
  
  def   Build( self ):
    failed_nodes = self.build_manager.build()
    finishHandleEvents()
    
    return failed_nodes
  
  #//=======================================================//
  
  def   Clean( self ):
    pass

#//===========================================================================//

if __name__ == "__main__":
  
  aql.CONFIG.Update( 'aql.cfg' )
  
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
  
  
