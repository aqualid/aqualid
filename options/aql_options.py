#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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


import operator
import itertools
import weakref

from aql_utils import toSequence
from aql_list_types import UniqueList, List
from aql_option_types import OptionType, ListOptionType
from aql_option_value import OptionValue, Operation, ConditionalValue, Condition
from aql_errors import InvalidOptions, InvalidOptionValueType, UnknownOptionType, ExistingOptionValue, ForeignOptionValue

#//===========================================================================//

def   _evalValue( other, options, context ):
  if isinstance( other, OptionValueProxy ):
    if other.options is not options:
      return other.value()
    
    return other.value( context )
  
  elif isinstance( other, OptionValue ):
    return options.value( other, context )
  
  return other

#//===========================================================================//

def   _setOperator( dest_value, value ):
  return value

def   _updateOperator( dest_value, value ):
  if isinstance( dest_value, (UniqueList, List) ):
    dest_value += value
    return dest_value
  else:
    return value

def   _doAction( options, context, dest_value, op, value ):
  value = _evalValue( value, options, context )
  return op( dest_value, value )

def   SetValue( value, operation = None ):
  return Operation( operation, _doAction, _setOperator, value )

def   AddValue( value, operation = None ):
  return Operation( operation, _doAction, operator.iadd, value )

def   SubValue( value, operation = None ):
  return Operation( operation, _doAction, operator.isub, value )

def   UpdateValue( value, operation = None ):
  return Operation( operation, _doAction, _updateOperator, value )

#//===========================================================================//

class OptionValueProxy (object):
  
  __slots__ = (
    'option_value',
    'options',
  )
  
  def   __init__( self, option_value, options ):
    self.option_value = option_value
    self.options = options
  
  #//-------------------------------------------------------//
  
  def   value( self, context = None ):
    return self.options.value( self.option_value, context )
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    self.options._appendValue( self.option_value, other, AddValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, other ):
    self.options._appendValue( self.option_value, other, SubValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   set( self, value, operation_type = SetValue, condition = None ):
    self.options._appendValue( self.option_value, value, operation_type, condition )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, cmp_operator, other, context = None ):
    value = self.value( context )
    other = _evalValue( other, self.options, context )
    
    return cmp_operator( value, other )
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return self.cmp( operator.eq, other )
  def   __ne__( self, other ):
    return self.cmp( operator.ne, other )
  def   __lt__( self, other ):
    return self.cmp( operator.lt, other )
  def   __le__( self, other ):
    return self.cmp( operator.le, other )
  def   __gt__( self, other ):
    return self.cmp( operator.gt, other )
  def   __ge__( self, other ):
    return self.cmp( operator.ge, other )
  
  #//-------------------------------------------------------//
  
  def   has( self, other, context = None ):
    return self.cmp( operator.contains, other )
  
  #//-------------------------------------------------------//
  
  def   __contains__( self, other ):
    return self.has( other )
  
  #//-------------------------------------------------------//
  
  def   optionType( self ):
    return self.option_value.option_type
  
#//===========================================================================//

class ConditionGeneratorHelper( object ):
  
  def     __init__( self, name, options, condition  ):
    self.name  = name
    self.options  = options
    self.condition  = condition
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __hasAny( seq, values ):
    for value in toSequence( values ):
      if value in seq:
        return True
    return False
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __hasAll( seq, values ):
    for value in toSequence( values ):
      if value not in seq:
        return False
    return True
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __oneOf( value, values ):
    for v in values:
      if value == v:
        return True
    return False
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __cmpValue( options, context, cmp_operator, name, other ):
    return options[ name ].cmp( cmp_operator, other, context )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def __makeCmpCondition( condition, cmp_operator, name, other ):
    return Condition( condition, ConditionGeneratorHelper.__cmpValue, cmp_operator, name, other )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, cmp_operator, other ):
    condition = self.__makeCmpCondition( self.condition, cmp_operator, self.name, other )
    return ConditionGenerator( self.options, condition )
  
  def   __getitem__( self, other ):
    return self.cmp( operator.eq, other )
  def   eq( self, other ):
    return self.cmp( operator.eq, other )
  def   ne( self, other ):
    return self.cmp( operator.ne, other )
  def   gt( self, other ):
    return self.cmp( operator.gt, other )
  def   ge( self, other ):
    return self.cmp( operator.ge, other )
  def   lt( self, other ):
    return self.cmp( operator.lt, other )
  def   le( self, other ):
    return self.cmp( operator.le, other )
  def   has( self, value ):
    return self.cmp( operator.contains, value )
  def   hasAny( self, values ):
    return self.cmp( self.__hasAny, values )
  def   hasAll( self, values ):
    return self.cmp( self.__hasAll, values )
  def   oneOf( self, values ):
    return self.cmp( self.__oneOf, values )
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, value ):
   self.options.appendValue( self.name, value, AddValue, self.condition )
   return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, value ):
    self.options.appendValue( self.name, value, SubValue, self.condition )
    return self

#//===========================================================================//

class ConditionGenerator( object ):
  
  def     __init__( self, options, condition = None ):
    self.__dict__['__options']  = options
    self.__dict__['__condition']  = condition
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    return ConditionGeneratorHelper( name, self.__dict__['__options'], self.__dict__['__condition'])
  
  #//-------------------------------------------------------//
  
  def     __setattr__(self, name, value):
    if not isinstance(value, ConditionGeneratorHelper):
      self.__dict__['__options'].appendValue( name, value, SetValue, self.__dict__['__condition'] )
  
#//===========================================================================//

class Options (object):
  
  def     __init__( self, parent = None ):
    self.__dict__['__parent']       = parent
    self.__dict__['__cache']        = {}
    self.__dict__['__opt_values']   = {}
    self.__dict__['__children']     = []
    
    if parent is not None:
      parent.__dict__['__children'].append( weakref.proxy( self ) )
  
  #//-------------------------------------------------------//
  
  def   _makeCondValue( self, value, operation_type = None, condition = None ):
    if isinstance( value, Operation ):
      return ConditionalValue( value, condition )
    
    elif isinstance( value, ConditionalValue ):
      return value
    
    if operation_type is None:
      raise InvalidOptionValueType( value )
    
    if isinstance( value, OptionValueProxy ):
      if value.options is not self:
        raise ForeignOptionValue( None, value )
      
      value = value.option_value
    
    return ConditionalValue( operation_type( value ), condition )
  
  #//-------------------------------------------------------//
  
  def   __set_value( self, name, value, operation_type = SetValue ):
    
    opt_value, from_parent = self._get_value( name )
    
    #//-------------------------------------------------------//
    #// New option
    if opt_value is None:
      if isinstance( value, OptionType ):
        value = OptionValue( value )
      
      elif isinstance( value, OptionValueProxy ):
        if value.options is not self:
          raise ForeignOptionValue( name, value )
        
        value = value.option_value
      
      elif not isinstance( value, OptionValue):
        raise UnknownOptionType( name, value )
      
      self.__dict__['__opt_values'][ name ] = value
    
    #//-------------------------------------------------------//
    #// Existing option
    else:
      if isinstance( value, OptionType ):
        raise ExistingOptionValue( name, value )
      
      elif isinstance( value, OptionValueProxy ):
        if value.option_value is opt_value:
          return
      
      elif value is opt_value:
        return
      
      value = self._makeCondValue( value, operation_type )
      
      if from_parent:
        opt_value = opt_value.copy()
        self.__dict__['__opt_values'][ name ] = opt_value
      
      opt_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   __setattr__( self, name, value ):
    self.__set_value( name, value )
    self.clearCache()
  
  #//-------------------------------------------------------//
  
  def   __setitem__( self, name, value ):
    self.__setattr__( name, value )
  
  #//-------------------------------------------------------//
  
  def   _get_value( self, name ):
    try:
      return (self.__dict__['__opt_values'][ name ], False)
    except KeyError as e:
      try:
        return ( self.__dict__['__parent']._get_value( name )[0], True )
      except AttributeError:
        return (None, False)
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    opt_value = self._get_value( name )[0]
    if opt_value is None:
      raise AttributeError( name )
    
    return OptionValueProxy( opt_value, self )
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, name ):
    return self.__getattr__( name )
  
  #//-------------------------------------------------------//
  
  def   __contains__( self, name ):
    return self._get_value( name )[0] is not None
  
  #//-------------------------------------------------------//
  
  def   __iter__( self ):
    return iter(self.keys())
  
  #//-------------------------------------------------------//
  
  def   keys( self ):
    names = set( self.__dict__['__opt_values'] )
    parent = self.__dict__['__parent']
    if parent:
      names.update( parent.keys() )
    
    return names
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    values = set( self.__dict__['__opt_values'].values() )
    parent = self.__dict__['__parent']
    if parent:
      values.update( parent.values() )
    
    return values
  
  #//-------------------------------------------------------//
  
  def   items( self ):
    for name in self.keys():
      yield ( name, self._get_value( name )[0] )
  
  #//-------------------------------------------------------//
  
  def   setGroup( self, group, opt_values = None ):
    if opt_values is None:
      opt_values = self.values()
    
    for opt_value in toSequence(opt_values):
      #~ print("setGroup: opt_value: %s" % str(opt_value))
      if isinstance( opt_value, OptionValueProxy ):
        opt_value = opt_value.option_value
      
      opt_value.option_type.group = group
  
  #//-------------------------------------------------------//
  
  def   __nonzero__( self ):
    return bool(self.__dict__['__opt_values']) or bool(self.__dict__['__parent'])
  
  def   __bool__( self ):
    return bool(self.__dict__['__opt_values']) or bool(self.__dict__['__parent'])
  
  #//-------------------------------------------------------//
  
  def   update( self, other ):
    if not other:
      return
    
    if self is other:
      return
    
    self.clearCache()
    
    for name, value in other.items():
      
      if isinstance( value, OptionValue ):
        value = value.copy()
      
      elif isinstance( value, OptionValueProxy ):
        value = value.option_value.copy()
      
      try:
        self.__set_value( name, value, UpdateValue )
      except UnknownOptionType:
        pass
  
  #//-------------------------------------------------------//
  
  def     __iadd__(self, other ):
    self.update( other )
    return self

  #//-------------------------------------------------------//

  def     override( self ):
    return Options( self )
  
  #//-------------------------------------------------------//
  
  def     copy( self ):
    
    val_names = {}
    for name, opt_value in self.items():
      val_names.setdefault( opt_value, [] ).append( name )
    
    other = Options()
    
    for opt_value, names in val_names.items():
      new_opt_value = OptionValueProxy( opt_value.copy(), other )
      for name in names:
        setattr( other, name, new_opt_value )
    
    return other
  
  #//-------------------------------------------------------//
  
  def   value( self, option_value, context = None ):
    try:
      if context is not None:
        return context[ option_value ]
    except KeyError:
      pass
    
    cache = self.__dict__['__cache']
    
    try:
      value = cache[ option_value ]
    except KeyError:
      value = option_value.value( self, context )
      cache[ option_value ] = value
    
    return value
  
  #//-------------------------------------------------------//
  
  def   appendValue( self, name, value, operation_type = None, condition = None ):
    option_value = getattr( self, name ).option_value
    self._appendValue( option_value, value, operation_type, condition )
  
  #//-------------------------------------------------------//
  
  def   _appendValue( self, option_value, value, operation_type = None, condition = None ):
    value = self._makeCondValue( value, operation_type, condition )
    self.clearCache()
    option_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   clearCache( self ):
    self.__dict__['__cache'].clear()
    
    for child in self.__dict__['__children']:
      try:
        child.clearCache()
      except ReferenceError:
        pass
  
  #//-------------------------------------------------------//
  
  def   If( self ):
    return ConditionGenerator( self )
