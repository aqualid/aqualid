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

from aql.utils import toSequence
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
  __slots__ = ('options', 'setup', 'post_setup', 'builders', 'tool_class' )

#//===========================================================================//

class ToolLoader( object ):
  
  

#//===========================================================================//

class ToolManager( object ):
  
  __slots__ = ('tool_methods', 'tool_classes', 'tool_setup', 'tool_post_setup' )
  
  def   __init__( self ):
    self.tool_methods = set()
    self.tool_classes = {}
    self.tool_setup = {}
    self.tool_post_setup = {}
    self.tool_info = {}
  
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
    
    self.__addToMap( self.tool_classes, names, tool_class )
  
  #//-------------------------------------------------------//
  
  def   addBuilder( self, tool_method ):
    if not hasattr(tool_method, '__call__'):
      raise ErrorToolInvalidBuilderMethod( tool_method )
    
    self.tool_methods.add( tool_method )
    
  #//-------------------------------------------------------//
  
  def   addSetup( self, setup_method, names ):
    if not hasattr(tool_method, '__call__'):
      raise ErrorToolInvalidSetupMethod( tool_method )
    
    self.__addToMap( self.tool_setup, names, setup_method )
  
  #//-------------------------------------------------------//
  
  def   addPostSetup( self, setup_method, names ):
    if not hasattr(setup_method, '__call__'):
      raise ErrorToolInvalidSetupMethod( setup_method )
    
    self.__addToMap( self.tool_post_setup, names, setup_method )
  
  #//-------------------------------------------------------//
  
  def   __getToolBuilders( tool_class ):
    
    all_builders = self.tool_methods
    
    builders = frozenset( instance for instance in tool_class.__dict__.values() if instance in all_builders )
    
    return builders
  
  #//-------------------------------------------------------//
  
  def   getTools( self, name ):
    
    tools_info = []
    tool_classes = self.tool_classes.get( name, () )
    tool_setup = self.tool_setup.get( name, () )
    tool_post_setup = self.tool_post_setup.get( name, () )
    
    for tool_class in tool_classes:
      tool_info = self.tool_info.get( tool_class, None )
      if tool_info is None:
        tool_info = ToolInfo()
        tool_info.tool_class = tool_class
        tool_info.options = tool_class.options()
        tool_info.builders = self.__getToolBuilders( tool_class )
        self.tool_info[ tool_class ] = tool_info
      
      tool_info.setup = tool_setup
      tool_info.post_setup = tool_post_setup
      
      tools_info.append( tool_info )
    
    return tools_info
  
#//===========================================================================//

def   tool( tool_class )
  global _suite_maker
  
  if isinstance( tool_class, type) and issubclass( test_case, unittest.TestCase ):
    _suite_maker.skip_test_classes.add( test_case )
  
  elif hasattr(test_case, '__call__'):
    _suite_maker.skip_test_methods.add( test_case )
  
  return test_case

#//===========================================================================//

def   builder( tool_method ):
  pass

#//===========================================================================//

def   toolSetup( name ):
  pass

#//===========================================================================//

def   toolPostSetup( name ):
  pass

#//===========================================================================//

class SetupTool( object ):
  
  def   setup( self, options ):
    pass
  
  def   postSetup( self, options ):
    pass

#//===========================================================================//

class Tool( object ):
  
  def   __init__( self ):
    pass
  
  @classmethod
  def   options( cls ):
    pass
  
  def   configure( self, options ):
    return True
