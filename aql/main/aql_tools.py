#
# Copyright (c) 2012, 2013 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = ( 'Tool', 'tool', 'toolSetup', 'ToolsManager')

import os

from aql.util_types import toSequence, Singleton, AqlException
from aql.utils import logWarning, loadModule, findFiles, eventWarning

#noinspection PyStatementEffect
"""
1. Tool('c++')
  1.1 Select first c++ tool
  1.2 Get tool's options
  1.3 Setup tool's options
  1.4 Create tool
  1.5 Add tool's builders
"""

#//===========================================================================//

@eventWarning
def   eventToolsUnableLoadModule( module, err ):
  logWarning( "Unable to load module: %s, error: %s" % (module, err) )

#//===========================================================================//

@eventWarning
def   eventToolsToolFailed( tool_class, err ):
  logWarning( "Tool init failed: %s - %s" % (tool_class, err))

#//===========================================================================//

def   _toolSetupStub( options ):
  pass

#//===========================================================================//

class   ErrorToolInvalid( AqlException ):
  def   __init__( self, tool_class ):
    msg = "Invalid tool type: '%s'" % (tool_class,)
    super(type(self), self).__init__( msg )

class   ErrorToolInvalidSetupMethod( AqlException ):
  def   __init__( self, method ):
    msg = "Invalid tool setup method: '%s'" % (method,)
    super(type(self), self).__init__( msg )

class   ErrorToolNotFound( AqlException ):
  def   __init__( self, tool_name ):
    msg = "Tool '%s' has not been found" % (tool_name,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class   ToolInfo( object ):
  __slots__ = (
    'tool_class',
    'options',
    'setup_methods',
  )
  
  def   __getattr__( self, attr ):
    if attr == 'options':
      self.options = self.tool_class.options()
      return self.options
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )

#//===========================================================================//

class ToolsManager( Singleton ):
  
  __slots__ = (
    'tool_classes',
    'tool_names',
    'tool_info',
    'all_setup_methods',
    'loaded_paths'
  )
  
  #//-------------------------------------------------------//
  
  _instance = []
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    
    self.tool_classes = {}
    self.tool_names = {}
    self.all_setup_methods = {}
    self.tool_info = {}
    self.loaded_paths = set()
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __addToMap( values_map, names, value ):
    setdefault = values_map.setdefault
    for name in toSequence( names ):
      setdefault( name, [] ).append( value )
  
  #//-------------------------------------------------------//
  
  def   addTool( self, tool_class, names ):
    if not issubclass( tool_class, Tool ):
      raise ErrorToolInvalid( tool_class )
    
    if names:
      self.tool_names.setdefault( tool_class, set() ).update( toSequence( names ) )
      self.__addToMap( self.tool_classes, names, tool_class )
  
  #//-------------------------------------------------------//
  
  def   addSetup( self, setup_method, names ):
    if not hasattr(setup_method, '__call__'):
      raise ErrorToolInvalidSetupMethod( setup_method )
    
    self.__addToMap( self.all_setup_methods, names, setup_method )
  
  #//-------------------------------------------------------//
  
  def   loadTools( self, paths ):
    
    if not paths:
      return
    
    paths = set( map( lambda path: os.path.normcase( os.path.abspath( path ) ), toSequence( paths ) ) )
    paths -= self.loaded_paths
    
    module_files = findFiles( paths, suffixes = ".py" )
    
    for module_file in module_files:
      try:
        loadModule( module_file, update_sys_path = False )
      except Exception as ex:
        eventToolsUnableLoadModule( module_file, ex )
    
    self.loaded_paths |= paths
  
  #//-------------------------------------------------------//
  
  def   __getToolInfoList( self, name ):
    
    tools_info = []
    empty_list = tuple()
    
    if (type(name) is type) and issubclass( name, Tool ):
      tool_classes = ( name, )
    else:
      tool_classes = self.tool_classes.get( name, empty_list )
    
    for tool_class in tool_classes:
      tool_info = self.tool_info.get( tool_class, None )
      if tool_info is None:
        tool_info = ToolInfo()
        tool_info.tool_class = tool_class
        self.tool_info[ tool_class ] = tool_info
        
        setup_methods = set()
        tool_info.setup_methods = setup_methods
        
        for name in self.tool_names.get( tool_class, [] ):
          setup_methods.update( self.all_setup_methods.get( name, [] ) )
        else:
          setup_methods.add( _toolSetupStub )
      
      tools_info.append( tool_info )
    
    return tools_info
  
  #//=======================================================//
  
  def   getTool( self, tool_name, options ):
    
    tool_info_list = self.__getToolInfoList( tool_name )
    
    for tool_info in tool_info_list:
      
      tool_options = options.override()
      
      tool_options.merge( tool_info.options )
      
      for setup in tool_info.setup_methods:
        setup_options = tool_options.override()

        try:
          setup( setup_options )
          
          env = setup_options.env.get().dump()
          
          tool_info.tool_class.setup( setup_options, env )
          
          options_kw = dict( setup_options.items( with_parent = False ) )
          
          if tool_options.checkToolKeys( **options_kw ):
            raise NotImplementedError()
          
          tool_options.update( options_kw )
          
          tool_obj = tool_info.tool_class( tool_options )
          
        except NotImplementedError:
          setup_options.clear()
          tool_options.clear()
        except Exception as err:
            eventToolsToolFailed( tool_info.tool_class, err )
            raise
        else:
          setup_options.join()
          tool_names = self.tool_names.get( tool_info.tool_class, tuple() )
          return tool_obj, tool_names, tool_options
    
    raise ErrorToolNotFound( tool_name )
  
  #//=======================================================//
  
  def   hasTool( self, tool_name ):
    return tool_name in self.tool_classes

#//===========================================================================//

def   tool( *tool_names ):
  def   _tool( tool_class ):
    ToolsManager.instance().addTool( tool_class, tool_names )
    return tool_class
  
  return _tool

#//===========================================================================//

def   toolSetup( *tool_names ):
  def   _tool_setup( setup_method ):
    ToolsManager.instance().addSetup( setup_method, tool_names )
    return setup_method
  
  return _tool_setup

#//===========================================================================//

class Tool( object ):
  
  def   __init__( self, options ):
    pass
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   setup( options, env ):
    pass
  
  @staticmethod
  def   options():
    return None
