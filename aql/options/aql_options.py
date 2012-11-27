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

__all__ = (
  'Options',
  'ErrorOptionsOperationIsNotSpecified', 'ErrorOptionsOptionValueExists',
  'ErrorOptionsNewValueTypeIsNotOption', 'ErrorOptionsForeignOptionValue',
)

import operator
import itertools
import weakref

from aql.utils import toSequence, UniqueList, List, Dict, DictItem

from aql_option_types import OptionType, ListOptionType
from aql_option_value import OptionValue, Operation, ConditionalValue, Condition

#//===========================================================================//

class   ErrorOptionsOperationIsNotSpecified( TypeError ):
  def   __init__( self, value ):
    msg = "Operation type is not set for value: '%s'" % str(value)
    super(type(self), self).__init__( msg )

class   ErrorOptionsOptionValueExists( TypeError ):
  def   __init__( self, value_name, option_type ):
    msg = "Unable to set option type '%s' to existing value '%s'" % (option_type, value_name)
    super(type(self), self).__init__( msg )

class   ErrorOptionsNewValueTypeIsNotOption( TypeError ):
  def   __init__( self, name, value ):
    msg = "Type of the new value '%s' must be OptionType or OptionValue, value's type: %s" % (name, type(value))
    super(type(self), self).__init__( msg )

class   ErrorOptionsForeignOptionValue( TypeError ):
  def   __init__( self, value ):
    msg = "Can't assign OptionValue owned by other options: %s" % str(value)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   OptionalValueItem( tuple ):
  def   __new__( cls, key, opt_value ):
    return super(OptionalValueItem, cls).__new__( cls, (key, opt_value ) )
  
  def   value( self, options, context ):
    key, opt_value = self
    return options.value( opt_value, context )[ key ]

#//===========================================================================//

def   _evalValue( other, options, context ):
  if isinstance( other, DictItem ):
    key, other = other
  else:
    key = NotImplemented
  
  if isinstance( other, OptionValueProxy ):
    if other.options is not options:
      return other.value()
    
    other = other.value( context )
  
  elif isinstance( other, OptionValue ):
    other = options.value( other, context )
  
  elif isinstance( other, OptionalValueItem ):
    other = other.value( options, context )
  
  if key is not NotImplemented:
    other = DictItem( key, other )
  
  return other

#//===========================================================================//

def   _setOperator( dest_value, value ):
  if isinstance( dest_value, Dict ) and isinstance( value, DictItem ):
    dest_value.update( value )
    return dest_value
  return value

def   _notOperator( dest_value, value ):
  return not value

def   _truthOperator( dest_value, value ):
  return bool(value)

def   _updateOperator( dest_value, value ):
  if isinstance( dest_value, (UniqueList, List) ):
    dest_value += value
    return dest_value
  elif isinstance( dest_value, Dict ):
    dest_value.update( value )
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

def   NotValue( value, operation = None ):
  return Operation( operation, _doAction, _notOperator, value )

def   TruthValue( value, operation = None ):
  return Operation( operation, _doAction, _notOperator, value )

#//===========================================================================//

class OptionValueProxy (object):
  
  def   __init__( self, option_value, options, key = NotImplemented ):
    self.option_value = option_value
    self.options = options
    self.key = key
    self.child_ref = None
  
  #//-------------------------------------------------------//
  
  def   value( self, context = None ):
    self.child_ref = None
    
    v = self.options.value( self.option_value, context )
    return v if self.key is NotImplemented else v[self.key]
  
  #//-------------------------------------------------------//
  
  def   valueForCondition( self ):
    if self.key is NotImplemented:
      return self.option_value
    
    return OptionalValueItem( self.key, self.option_value )
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      other = DictItem(self.key, other)
    
    self.options._appendValue( self.option_value, other, AddValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, other ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      other = DictItem(self.key, other)
    
    self.options._appendValue( self.option_value, other, SubValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   set( self, value, operation_type = SetValue, condition = None ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      value = DictItem(self.key, value)
    
    self.options._appendValue( self.option_value, value, operation_type, condition )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, cmp_operator, other, context = None ):
    self.child_ref = None
    
    value = self.value( context )
    other = _evalValue( other, self.options, context )
    
    return cmp_operator( value, other )
  
  #//-------------------------------------------------------//
  
  def   __setitem__( self, key, value ):
    child_ref = self.child_ref
    if (child_ref is not None) and (child_ref() is value):
      return
    
    self.child_ref = None
    
    self.options._appendValue( self.option_value, DictItem(key, value), SetValue, None )
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, key ):
    if self.key is not NotImplemented:
      raise KeyError( key )
    
    child = OptionValueProxy( self.option_value, self.options, key )
    self.child_ref = weakref.ref( child )
    return child
  
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
  
  def   __bool__(self):
    return bool( self.value() )
  
  def   __nonzero__(self):
    return bool( self.value() )
  
  def   __str__(self):
    return str( self.value() )
  
  #//-------------------------------------------------------//
  
  def   has( self, other, context = None ):
    return self.cmp( operator.contains, other )
  
  #//-------------------------------------------------------//
  
  def   __contains__( self, other ):
    return self.has( other )
  
  #//-------------------------------------------------------//
  
  def   optionType( self ):
    self.child_ref = None
    return self.option_value.option_type
  
#//===========================================================================//

class ConditionGeneratorHelper( object ):
  
  __slots__ = ('name', 'options', 'condition', 'key')
  
  def     __init__( self, name, options, condition, key = NotImplemented ):
    self.name = name
    self.options = options
    self.condition = condition
    self.key = key
  
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
    return getattr( options, name ).cmp( cmp_operator, other, context )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def __makeCmpCondition( condition, cmp_operator, name, other ):
    return Condition( condition, ConditionGeneratorHelper.__cmpValue, cmp_operator, name, other )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, cmp_operator, other ):
    if self.key is not None:
      other = DictItem( self.key, other )
    
    condition = self.__makeCmpCondition( self.condition, cmp_operator, self.name, other )
    return ConditionGenerator( self.options, condition )
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, key ):
    if self.key is not NotImplemented:
      raise KeyError( key )
    
    return ConditionGeneratorHelper( self.name, self.options, self.condition, key )
  
  #//-------------------------------------------------------//
  
  def   __setitem__( self, key, value ):
    if not isinstance(value, ConditionGeneratorHelper):
      self.options.appendValue( self.name, DictItem(key, value), SetValue, self.condition )
  
  #//-------------------------------------------------------//
  
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
    if self.key is not None:
      value = DictItem( self.key, value )
    
    self.options.appendValue( self.name, value, AddValue, self.condition )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, value ):
    if self.key is not None:
      value = DictItem( self.key, value )
    
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
      raise ErrorOptionsOperationIsNotSpecified( value )
    
    if isinstance( value, DictItem ):
      key, value = value
    else:
      key = NotImplemented
    
    if isinstance( value, OptionValueProxy ):
      if value.options is not self:
        raise ErrorOptionsForeignOptionValue( value )
      
      value = value.valueForCondition()
    
    if key is not NotImplemented:
      value = DictItem( key, value )
    
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
          raise ErrorOptionsForeignOptionValue( value )
        
        value = value.option_value
      
      elif not isinstance( value, OptionValue):
        raise ErrorOptionsNewValueTypeIsNotOption( name, value )
      
      self.__dict__['__opt_values'][ name ] = value
    
    #//-------------------------------------------------------//
    #// Existing option
    else:
      if isinstance( value, OptionType ):
        raise ErrorOptionsOptionValueExists( name, value )
      
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
      except ErrorOptionsNewValueTypeIsNotOption:
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
