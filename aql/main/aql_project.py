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

import sys
import types

from aql.utils import cpuCount, CLIConfig, CLIOption, getFunctionArgs
from aql.types import FilePath, FilePaths, SplitListType
from aql.values import Value, NoContent, DependsValue, DependsValueContent
from aql.options import builtinOptions, Options
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

class ProjectConfig( CLIConfig ):
  
  def   __init__( self, args = None ):
    if args is None:
      args = sys.argv
    
    CLI_USAGE = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"
    
    Paths = SplitListType( FilePaths, ', ')
    
    CLI_OPTIONS = (
      CLIOption( "-j", "--jobs",          "jobs",           jobsCount,  None,               "Number of parallel jobs to process targets.", 'NUMBER' ),
      CLIOption( "-f", "--make-file",     "make_file",      FilePath,   'build.aql',        "Path to main make file", 'FILE PATH'),
      CLIOption( "-s", "--state-file",    "state_file",     FilePath,   'build.aql.state',  "File path to store information of previous builds.", 'FILE PATH'),
      CLIOption( "-t", "--tools-path",    "tools_path",     Paths,      [],                 "Paths to tools", 'FILE PATH, ...'),
      CLIOption( "-p", "--setup-path",    "setup_path",     Paths,      [],                 "Paths to setup scripts to preconfigure tools", 'FILE PATH, ...'),
      CLIOption( "-k", "--keep-going",    "keep_going",     bool,       False,              "Continue build even if any target failed." ),
      CLIOption( "-l", "--list-options",  "list_options",   bool,       False,              "List all available options and exit." ),
      CLIOption( "-c", "--clean",         "clean_targets",  bool,       False,              "Clean up actual targets." ),
      CLIOption( "-v", "--verbose",       "verbose",        bool,       False,              "Verbose mode." ),
      CLIOption( "-q", "--quiet",         "quiet",          bool,       False,              "Quiet mode." ),
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

class BuilderWrapper( object ):
  __slots__ = ( 'project', 'method', 'arg_names')
  
  def   __init__( self, project, method ):
    self.arg_names = self.__checkBuilderMethod( method )
    self.method = method
    self.project = project
  
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
    options = self.project.options
    
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

class Project( object ):
  
  def   __init__(self, config = None ):
    if config is None:
      config = ProjectConfig()
    
    self.config = config
    
    self.options = config.options.override()
    self.build_manager = BuildManager( config.state_file, config.jobs, config.keep_going )
    self.tools_manager = ToolsManager()
  
  #//=======================================================//
  
  def   Tool( self, tools, tool_paths = None ):
    tools_manager = self.tools_manager
    tools_manager.loadTools( tool_paths )
    
    options = self.options
    
    for tool_name in toSequence( tools ):
      tool = tools_manager.getTool( tool_name, options )
      
      for builder in tool.getBuilders():
        self.AddBuilder( builder )
  
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
  
  def   AddBuilder( self, builder_method, name = None ):
    
    method_wrapper = BuilderWrapper( self, builder_method )
    
    if not name:
      name = builder_method.__name__
    
    if hasattr( self, name ):
      raise ErrorProjectBuilderMethodExists( builder_method )
    
    setattr( self, name, method_wrapper )
  
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
  
  prj_cfg = aql.ProjectConfig()
  prj_cfg.readConfig( config_file )
  
  prj = aql.Project()
  prj = aql.Project( prj_cfg )
  prj.Tool( 'c++', tool_paths )
  prj.CompileC( c_files, optimization = 'size', debug_symbols = False )
  prj.CompileCpp( cpp_files, optimization = 'speed' )
  
  """
  1. kw - args
  
  """
  
  
