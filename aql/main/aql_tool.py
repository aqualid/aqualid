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

from aql.utils import toSequence, logWarning
from aql.types import FilePath
from aql.values import Value, NoContent, DependsValue, DependsValueContent
from aql.options import builtinOptions

"""
1. Tool('c++')
  1.1 Select first c++ tool
  1.2 Get tool's options
  1.3 Setup tool's options
  1.4 Create tool
  1.5 Post setup tool
  1.6 Add tool's builders
"""

#//===========================================================================//

class   ErrorToolInvalid( Exception ):
  def   __init__( self, tool_class ):
    msg = "Invalid tool type: '%s'" % str(tool_class)
    super(type(self), self).__init__( msg )

class   ErrorToolInvalidBuilderMethod( Exception ):
  def   __init__( self, method ):
    msg = "Invalid tool builder method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

class   ErrorToolInvalidSetupMethod( Exception ):
  def   __init__( self, method ):
    msg = "Invalid tool setup method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class ToolInfo( object ):
  __slots__ = (
    'tool_class',
    'options',
    'setup',
    'post_setup',
    'builders',
  )
  
  def   __getattr__( self, attr ):
    if attr == 'options':
      self.options = self.tool_class.options()
      return self.options
    
    raise AttributeError( attr )

#//===========================================================================//

class ToolManager( object ):
  
  __slots__ = (
    'builders',
    'classes',
    'setup',
    'post_setup',
    'loaded_paths'
  )
  
  _instance = __import__('__main__').__dict__.setdefault( '__ToolManager_instance', [None] )
  
  def   __new__( cls ):
    
    instance = ToolManager._instance
    
    if instance[0] is not None:
      return instance[0]
    
    self = super(ToolManager,cls).__new__(cls)
    instance[0] = self
    
    self.builders = set()
    self.classes = {}
    self.setup = {}
    self.post_setup = {}
    self.tool_info = {}
    self.loaded_paths = set()
    
    return self
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __addToMap( values_map, names, value ):
    setdefault = values_map.setdefault
    for name in toSequence( names ):
      setdefault( name, [] ).append( value )
  
  #//-------------------------------------------------------//
  
  def   addTool( self, tool_class, names ):
    if not isinstance( tool_class, type ) or not issubclass( test_case, Tool ):
      raise ErrorToolInvalid( tool_class )
    
    self.__addToMap( self.classes, names, tool_class )
  
  #//-------------------------------------------------------//
  
  def   addBuilder( self, tool_method ):
    if not hasattr(tool_method, '__call__'):
      raise ErrorToolInvalidBuilderMethod( tool_method )
    
    self.builders.add( tool_method )
    
  #//-------------------------------------------------------//
  
  def   addSetup( self, setup_method, names ):
    if not hasattr(tool_method, '__call__'):
      raise ErrorToolInvalidSetupMethod( tool_method )
    
    self.__addToMap( self.setup, names, setup_method )
  
  #//-------------------------------------------------------//
  
  def   addPostSetup( self, setup_method, names ):
    if not hasattr(setup_method, '__call__'):
      raise ErrorToolInvalidSetupMethod( setup_method )
    
    self.__addToMap( self.post_setup, names, setup_method )
  
  #//-------------------------------------------------------//
  
  def   __getToolBuilders( tool_class ):
    
    all_builders = self.builders
    
    builders = frozenset( instance for instance in tool_class.__dict__.values() if instance in all_builders )
    
    return builders
  
  #//-------------------------------------------------------//
  
  def   loadTools( self, paths ):
    paths = set( map( lambda path: os.path.normcase( os.path.abspath( path ) ), toSequence( paths ) ) )
    paths -= self.loaded_paths
    
    module_files = findFiles( paths, suffixes = ".py" )
    
    for module_file in module_files:
      try:
        loadModule( module_file, update_sys_path = False )
      except Exception as ex:
        logWarning( "Unable to load module: %s, error: %s" % (module_file, ex) )
    
    self.loaded_paths |= paths
    
  #//-------------------------------------------------------//
  
  def   getTools( self, name ):
    
    tools_info = []
    empty_list = tuple()
    classes = self.classes.get( name, empty_list )
    setup = self.setup.get( name, empty_list )
    post_setup = self.post_setup.get( name, empty_list )
    
    for tool_class in classes:
      tool_info = self.tool_info.get( tool_class, None )
      if tool_info is None:
        tool_info = ToolInfo()
        tool_info.tool_class = tool_class
        tool_info.builders = self.__getToolBuilders( tool_class )
        self.tool_info[ tool_class ] = tool_info
      
      tool_info.setup = setup
      tool_info.post_setup = post_setup
      
      tools_info.append( tool_info )
    
    return tools_info
  
#//===========================================================================//

_tool_manager = ToolManager()

def   tool( *tool_names ):
  def   _tool( tool_class ):
    _tool_manager.addTool( tool_class, tool_names )
    return tool_class
  
  return _tool

#//===========================================================================//

def   builder( tool_method ):
  _tool_manager.addBuilder( tool_method )
  return tool_method

#//===========================================================================//

def   toolSetup( *tool_names ):
  def   _tool_setup( setup_method ):
    _tool_manager.addSetup( setup_method, tool_names )
    return setup_method
  
  return _tool_setup

#//===========================================================================//

def   toolPostSetup( *tool_names ):
  def   _tool_post_setup( setup_method ):
    _tool_manager.addPostSetup( setup_method, tool_names )
    return setup_method
  
  return _tool_post_setup

#//===========================================================================//

class Tool( object ):
  
  def   __init__( self ):
    pass
  
  @staticmethod
  def   options( cls ):
    pass
  
  @staticmethod
  def   signature( options ):
    pass
  
  def   configure( self, options ):
    return True
