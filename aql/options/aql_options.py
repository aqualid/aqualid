#
# Copyright (c) 2011-2013 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'Options', #'optionValueEvaluator',
  'SetValue', 'AddValue', 'SubValue', 'UpdateValue', 'NotValue', 'TruthValue', 'JoinPathValue',
  'ErrorOptionsOperationIsNotSpecified',
  'ErrorOptionsCyclicallyDependent', 'ErrorOptionsMergeNonOptions'
)

import os.path

import operator
import weakref

from aql.util_types import toSequence, UniqueList, List, Dict, DictItem

from .aql_option_types import OptionType, autoOptionType
from .aql_option_value import OptionValue, Operation, ConditionalValue, Condition

#//===========================================================================//

class   ErrorOptionsOperationIsNotSpecified( TypeError ):
  def   __init__( self, value ):
    msg = "Operation type is not set for value: '%s'" % str(value)
    super(type(self), self).__init__( msg )

class   ErrorOptionsCyclicallyDependent( TypeError ):
  def   __init__( self ):
    msg = "Options are cyclically dependent from each other."
    super(type(self), self).__init__( msg )

class   ErrorOptionsMergeNonOptions( TypeError ):
  def   __init__( self, value ):
    msg = "Type '%s' can't be merged with Options." % str(type(value))
    super(type(self), self).__init__( msg )

class   ErrorOptionsMergeDifferentOptions( TypeError ):
  def   __init__( self, name1, name2):
    msg = "Can't merge one an optional value into two different options '%s' and '%s' " % ( name1, name2 )
    super(type(self), self).__init__( msg )

class   ErrorOptionsJoinNoParent( TypeError ):
  def   __init__( self, options ):
    msg = "Can't join options without parent: %s" % ( options, )
    super(type(self), self).__init__( msg )

class   ErrorOptionsJoinParent( TypeError ):
  def   __init__( self, options ):
    msg = "Can't join options with children: %s" % ( options, )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   _OpValue( tuple ):
  def   __new__( cls, value ):
    
    if not isinstance( value, OptionValueProxy ):
      return value
    
    return super(_OpValue, cls).__new__( cls, (value.name, value.key) )
  
  def   get( self, options, context ):
    name, key = self
    
    value = getattr( options, name ).get( context )
    
    if key is not NotImplemented:
      value = value[ key ]
    
    return value

#//===========================================================================//

# _SIMPLE_TYPES = (str,int,float,complex,bool,bytes,bytearray)
# 
# def  _evaluateValue( value, simple_types = _SIMPLE_TYPES ):
#   
#   if isinstance( value, simple_types ):
#     return value
#   
#   if isinstance( value, (list, UniqueList) ):
#     for i,v in enumerate(value):
#       value[i] = _evaluateValue( v )
#     
#     return value
#   
#   if isinstance( value, tuple ):
#     result = []
#     
#     for v in value:
#       result.append( _evaluateValue( v ) )
#     
#     return result
#   
#   try:
#     value = value.get()
#     return value
#   except Exception:
#     pass
#   
#   return value

#//===========================================================================//

def   _evalValue( options, context, other ):
  if isinstance( other, DictItem ):
    key, other = other
  else:
    key = NotImplemented
  
  if isinstance( other, _OpValue ):
    other = other.get( options, context )
  
  elif isinstance( other, OptionValueProxy ):
    if other.options is not options:
      other = other.get( context = None )
    else:
      other = other.get( context )
  
  elif isinstance( other, OptionValue ):
    other = options.value( other, context )
  
  # other = _evaluateValue( other ) # TODO: remove this conversion when added type casts to Values and Node  
  
  if key is not NotImplemented:
    other = DictItem( key, other )
  
  #for evaluator in _evaluators:
  #  other = evaluator( other )
  
  return other

#//===========================================================================//

def   _setOperator( dest_value, value ):
  if isinstance( dest_value, Dict ) and isinstance( value, DictItem ):
    dest_value.update( value )
    return dest_value
  return value

def   _joinPath( dest_value, value ):
  return os.path.join( dest_value, value )

#noinspection PyUnusedLocal
def   _absPath( dest_value, value ):
  return os.path.abspath( value )

#noinspection PyUnusedLocal
def   _notOperator( dest_value, value ):
  return not value

#noinspection PyUnusedLocal
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
  value = _evalValue( options, context, value )
  return op( dest_value, value )

def   _SetDefaultValue( value, operation = None ):
  return Operation( operation, _doAction, _setOperator, value )

def   SetValue( value, operation = None ):
  return Operation( operation, _doAction, _setOperator, value )

def   AddValue( value, operation = None ):
  return Operation( operation, _doAction, operator.iadd, value )

def   SubValue( value, operation = None ):
  return Operation( operation, _doAction, operator.isub, value )

def   JoinPathValue( value, operation = None ):
  return Operation( operation, _doAction, _joinPath, value )

def   AbsPathValue( operation = None ):
  return Operation( operation, _doAction, _absPath, None )

def   UpdateValue( value, operation = None ):
  return Operation( operation, _doAction, _updateOperator, value )

def   NotValue( value, operation = None ):
  return Operation( operation, _doAction, _notOperator, value )

def   TruthValue( value, operation = None ):
  return Operation( operation, _doAction, _notOperator, value )

#//===========================================================================//

#noinspection PyProtectedMember
class OptionValueProxy (object):
  
  def   __init__( self, option_value, name, options, key = NotImplemented ):
    self.option_value = option_value
    self.name = name
    self.options = options
    self.key = key
    self.child_ref = None
  
  #//-------------------------------------------------------//
  
  def   isSet( self ):
    return self.option_value.isSet()
  
  #//-------------------------------------------------------//
  
  def   isSetNotTo( self, value ):
    return self.option_value.isSet() and (self != value)
  
  def   isSetGreater( self, value ):
    return self.option_value.isSet() and (self > value)
  
  def   isSetLess( self, value ):
    return self.option_value.isSet() and (self < value)
  
  #//-------------------------------------------------------//
  
  def   setDefault( self, default_value ):
    if not self.option_value.isSet():
      self.set( default_value, _SetDefaultValue )
      return True
    
    return self == default_value
  
  #//-------------------------------------------------------//
  
  def   get( self, context = None ):
    self.child_ref = None
    
    v = self.options.value( self.option_value, context )
    return v if self.key is NotImplemented else v[self.key]
  
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
  
  def   __setitem__( self, key, value ):
    child_ref = self.child_ref
    if (child_ref is not None) and (child_ref() is value):
      return
    
    self.child_ref = None
    
    self.options._appendValue( self.option_value, DictItem(key, value), SetValue )
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, key ):
    if self.key is not NotImplemented:
      raise KeyError( key )
    
    child = OptionValueProxy( self.option_value, self.name, self.options, key )
    self.child_ref = weakref.ref( child )
    return child
  
  #//-------------------------------------------------------//
  
  def   __bool__(self):
    return bool( self.get( context = None ) )
  
  def   __nonzero__(self):
    return bool( self.get( context = None ) )
  
  def   __str__(self):
    return str( self.get( context = None ) )
  
  #//-------------------------------------------------------//
  
  def   isTrue( self, context ):
    return bool( self.get( context ) )
  
  def   isFalse( self, context ):
    return not bool( self.get( context ) )
  
  #//-------------------------------------------------------//
  
  def   eq( self, context, other ):  return self.cmp( context, operator.eq, other )
  def   ne( self, context, other ):  return self.cmp( context, operator.ne, other )
  def   lt( self, context, other ):  return self.cmp( context, operator.lt, other )
  def   le( self, context, other ):  return self.cmp( context, operator.le, other )
  def   gt( self, context, other ):  return self.cmp( context, operator.gt, other )
  def   ge( self, context, other ):  return self.cmp( context, operator.ge, other )
  
  def   __eq__( self, other ):        return self.eq( None, other )
  def   __ne__( self, other ):        return self.ne( None, other )
  def   __lt__( self, other ):        return self.lt( None, other )
  def   __le__( self, other ):        return self.le( None, other )
  def   __gt__( self, other ):        return self.gt( None, other )
  def   __ge__( self, other ):        return self.ge( None, other )
  def   __contains__( self, other ):  return self.has( None, other )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, context, cmp_operator, other ):
    self.child_ref = None
    
    other = _evalValue( self.options, context, other )
    value = self.get( context )
    
    if not isinstance( value, (Dict, List)) and (self.key is NotImplemented):
      other = self.option_value.option_type( other )
    
    return cmp_operator( value, other )
  
  #//-------------------------------------------------------//
  
  def   has( self, context, other ):
    other = _evalValue( self.options, context, other )
    value = self.get( context )
    
    return other in value
  
  #//-------------------------------------------------------//
  
  def   hasAny( self, context, values ):
    
    value = self.get( context )
    values = _evalValue( self.options, context, values )
    
    for other in toSequence( values ):
      if other in value:
        return True
    return False
  
  #//-------------------------------------------------------//
  
  def   hasAll( self, context, values ):
    
    value = self.get( context )
    values = _evalValue( self.options, context, values )
    
    for other in toSequence( values ):
      if other not in value:
        return False
    return True
  
  #//-------------------------------------------------------//
  
  def   oneOf( self, context, values ):
    
    value = self.get( context )
    values = _evalValue( self.options, context, values )
    
    for other in values:
      other = self.option_value.option_type( other )
      if value == other:
        return True
    return False
  
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
  def   __cmpValue( options, context, cmp_method, name, *args ):
    return getattr( getattr( options, name ), cmp_method )( context, *args )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def __makeCmpCondition( condition, cmp_method, name, *args ):
    return Condition( condition, ConditionGeneratorHelper.__cmpValue, cmp_method, name, *args )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, cmp_method, *args ):
    if self.key is not NotImplemented:
      args = [ DictItem( self.key, *args ) ]
    
    condition = self.__makeCmpCondition( self.condition, cmp_method, self.name, *args )
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
  
  def   eq( self, other ):      return self.cmp( 'eq',      other )
  def   ne( self, other ):      return self.cmp( 'ne',      other )
  def   gt( self, other ):      return self.cmp( 'gt',      other )
  def   ge( self, other ):      return self.cmp( 'ge',      other )
  def   lt( self, other ):      return self.cmp( 'lt',      other )
  def   le( self, other ):      return self.cmp( 'le',      other )
  def   has( self, value ):     return self.cmp( 'has',     value )
  def   hasAny( self, values ): return self.cmp( 'hasAny',  values )
  def   hasAll( self, values ): return self.cmp( 'hasAll',  values )
  def   oneOf( self, values ):  return self.cmp( 'oneOf',   values )
  def   isTrue( self ):         return self.cmp( 'isTrue' )
  def   isFalse( self ):        return self.cmp( 'isFalse' )
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, value ):
    if self.key is not NotImplemented:
      value = DictItem( self.key, value )
    
    self.options.appendValue( self.name, value, AddValue, self.condition )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, value ):
    if self.key is not NotImplemented:
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

#noinspection PyProtectedMember
class Options (object):
  
  def     __init__( self, parent = None ):
    self.__dict__['__parent']       = parent
    self.__dict__['__cache']        = {}
    self.__dict__['__opt_values']   = {}
    self.__dict__['__children']     = []
    
    if parent is not None:
      parent.__dict__['__children'].append( weakref.ref( self ) )
  
  #//-------------------------------------------------------//
  
  def   addChild(self, child ):
    
    children = self.__dict__['__children']
    
    for child_ref in children:
      if child_ref() is child:
        return
    
    if child.__isChild( self ):
      raise ErrorOptionsCyclicallyDependent()
    
    self.__dict__['__children'].append( weakref.ref( child ) )
  
  #//-------------------------------------------------------//
  
  def   __isChild(self, other ):
    
    children = list(self.__dict__['__children'])
    
    while children:
      
      child_ref = children.pop()
      child = child_ref()
      
      if child is None:
        continue
      
      if child is other:
        return True
      
      children += child.__dict__['__children']
    
    return False
  
  #//-------------------------------------------------------//
  
  def   getHashRef( self ):
    if self.__dict__['__opt_values']:
      return weakref.ref( self )
    
    parent = self.__dict__['__parent']
    
    if parent is None:
      return weakref.ref( self )
    
    return parent.getHashRef()
    
  
  #//-------------------------------------------------------//
  
  def   conflictsWith( self, **kw ):
    for key, value in kw.items():
      opt_value = self._get_value( key, raise_ex = False )
      if opt_value is not None:
        opt_value = OptionValueProxy( opt_value, key, self )
        if opt_value.isSetNotTo( value ):
          return True
    
    return False
  
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
      if value.options is self:
        value = _OpValue( value )
      else:
        value.options.addChild( self )
    
    if key is not NotImplemented:
      value = DictItem( key, value )
    
    return ConditionalValue( operation_type( value ), condition )
  
  #//-------------------------------------------------------//
  
  def   __set_value( self, name, value, operation_type = SetValue ):
    
    opt_value = self._get_value( name, raise_ex = False )
    
    if opt_value is None:
      self.clearCache()
      
      if isinstance( value, OptionType ):
        opt_value = OptionValue( value )
      
      elif isinstance( value, OptionValueProxy ):
        if value.options is self:
          opt_value = value.option_value
        else:
          opt_value = value.option_value.copy()
          opt_value.reset()
          value = self._makeCondValue( value, SetValue )
          opt_value.appendValue( value )
      
      elif not isinstance( value, OptionValue ):
        opt_value = OptionValue( autoOptionType( value ) )
        value = self._makeCondValue( value, SetValue )
        opt_value.appendValue( value )
      
      self.__dict__['__opt_values'][ name ] = opt_value
    
    else:
      if isinstance( value, OptionType ):
        opt_value.option_type = value
        return
      
      elif isinstance( value, OptionValueProxy ):
        if value.option_value is opt_value:
          return
      
      elif value is opt_value:
        return
      
      self._appendValue( opt_value, value, operation_type )
  
  #//-------------------------------------------------------//
  
  def   __set_opt_value( self, opt_value, names ):
    opt_values = self.__dict__['__opt_values']
    for name in names:
      opt_values[ name ] = opt_value
  
  #//-------------------------------------------------------//
  
  def   __setattr__( self, name, value ):
    self.__set_value( name, value )
  
  #//-------------------------------------------------------//
  
  def   _get_value( self, name, raise_ex ):
    try:
      return self.__dict__['__opt_values'][ name ]
    except KeyError:
      parent = self.__dict__['__parent']
      if parent is not None:
        value = parent._get_value( name, False )
        if value is not None:
          return value
      
      if raise_ex:
        raise AttributeError( "Options '%s' instance has no option '%s'" % (type(self), name) )
      
      return None
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    opt_value = self._get_value( name, raise_ex = True )
    return OptionValueProxy( opt_value, name, self )
  
  #//-------------------------------------------------------//
  
  def   __contains__( self, name ):
    return self._get_value( name, raise_ex = False ) is not None
  
  #//-------------------------------------------------------//
  
  def   __iter__( self ):
    return iter(self.keys())
  
  #//-------------------------------------------------------//
  
  def   _itemsDict( self, with_parent = True ):
    
    parent = self.__dict__['__parent']
    its = parent._itemsDict() if (parent is not None) and with_parent else {}
      
    its.update( self.__dict__['__opt_values'] )
    
    return its
  
  #//-------------------------------------------------------//
  
  def   keys( self ):
    for opt_value, names  in self._itemsByValue():
      yield next(iter(names))
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    for opt_value, names  in self._itemsByValue():
      name = next(iter(names))
      yield OptionValueProxy( opt_value, name, self )
  
  #//-------------------------------------------------------//
  
  def   items( self, with_parent = True ):
    for opt_value, names  in self._itemsByValue( with_parent = with_parent ):
      name = next(iter(names))
      yield name, OptionValueProxy( opt_value, name, self )
  
  #//-------------------------------------------------------//
  
  def   _itemsByValue( self, with_parent = True ):
    
    values = {}
    
    for name, value in self._itemsDict( with_parent = with_parent ).items():
      try:
        values[ value ].add( name )
      except KeyError:
        values[ value ] = {name}
    
    return values.items()
  
  #//-------------------------------------------------------//
  
  def   _isParentValue( self, opt_value ):
    parent = self.__dict__['__parent']
    return parent and (opt_value in parent._itemsDict().values() )
  
  #//-------------------------------------------------------//
  
  def   _valueNames( self, opt_value ):
    return set( name for name, value in self._itemsDict().items() if value is opt_value )
  
  #//-------------------------------------------------------//
  
  def   setGroup( self, group, opt_values = None ):
    if opt_values is None:
      opt_values = set(self._itemsDict().values())
    
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
    
    options = other if isinstance( other, Options ) else self
    
    for name, value in other.items():
      
      if isinstance( value, OptionValueProxy ):
        value = value.get( context = None )
      
      elif isinstance( value, OptionValue ):
        value = value.get( options, context = None )
      
      self.__set_value( name, value, UpdateValue )
  
  #//-------------------------------------------------------//
  
  def   __getMergeValueNames( self, names ):
    
    for name in names:
      value = self._get_value( name, raise_ex = False )
      if value is not None:
        value_names = self._valueNames( value )
        
        new_names = (names - value_names)
        for new_name in new_names:
          if self._get_value( new_name, raise_ex = False ) is not None:
            raise ErrorOptionsMergeDifferentOptions( new_name, value_names.pop() )
        
        if self._isParentValue( value ):
          value = value.copy()
          new_names = names | value_names
        
        return value, new_names
    
    return None, names
  
  #//-------------------------------------------------------//
  
  def   merge( self, other ):
    if not other:
      return
    
    if self is other:
      return
    
    if not isinstance( other, Options ):
      raise ErrorOptionsMergeNonOptions( other )
    
    self.clearCache()
    
    for value, names in other._itemsByValue():
      self_value, new_names = self.__getMergeValueNames( names )
      
      if self_value is None:
        self_value = value.copy()
      else:
        self_value.merge( value )
      
      self.__set_opt_value( self_value, new_names )
  
  #//-------------------------------------------------------//
  
  def   join( self ):
    parent = self.__dict__['__parent']
    if parent is None:
      raise ErrorOptionsJoinNoParent( self )
    
    if self.__dict__['__children']:
      raise ErrorOptionsJoinParent( self )
    
    parent.merge( self )
    self.clear()
  
  #//-------------------------------------------------------//
  
  def   unjoin( self ):
    parent = self.__dict__['__parent']
    if parent is None:
      return
    
    self.merge( parent )
    
    self.__dict__['__parent'] = None
  
  #//-------------------------------------------------------//
  
  def   __unjoinChildren( self ):
    
    children = self.__dict__['__children']
    
    for child_ref in children:
      child = child_ref()
      if child is not None:
        child.unjoin()
    
    del children[:]
  
  #//-------------------------------------------------------//
  
  def   __clearChildrenCache( self ):
    
    def   _clearChildCache( ref ):
      child = ref()
      if child is not None:
        child.clearCache()
        return True
      
      return False
    
    self.__dict__['__children'] = list( filter( _clearChildCache, self.__dict__['__children'] ) )
  
  #//-------------------------------------------------------//
  
  def   __removeChild( self, child ):
    
    def   _filterChild( child_ref, removed_child = child ):
      filter_child = child_ref()
      return (filter_child is not None) and (filter_child is not removed_child)
    
    self.__dict__['__children'] = list( filter( _filterChild, self.__dict__['__children'] ) )
  
  #//-------------------------------------------------------//
  
  def   clear( self ):
    parent = self.__dict__['__parent']
    
    self.__unjoinChildren()
    
    if parent is not None:
      parent.__removeChild( self )
    
    self.__dict__['__parent'] = None
    self.__dict__['__cache'].clear()
    self.__dict__['__opt_values'].clear()
  
  #//-------------------------------------------------------//

  def   override( self, **kw ):
    other = Options( self )
    other.update( kw )
    return other
  
  #//-------------------------------------------------------//
  
  def     copy( self ):
    
    other = Options()
    
    for opt_value, names in self._itemsByValue():
      other.__set_opt_value( opt_value.copy(), names )
    
    return other
  
  #//-------------------------------------------------------//
  
  def   value( self, option_value, context  ):
    try:
      if context is not None:
        return context[ option_value ]
    except KeyError:
      pass
    
    cache = self.__dict__['__cache']
    
    try:
      value = cache[ option_value ]
    except KeyError:
      value = option_value.get( self, context )
      cache[ option_value ] = value
    
    return value
  
  #//-------------------------------------------------------//
  
  def   appendValue( self, name, value, operation_type = None, condition = None ):
    opt_value = self._get_value( name, raise_ex = True )
    self._appendValue( opt_value, value, operation_type, condition )
  
  #//-------------------------------------------------------//
  
  def   _appendValue( self, opt_value, value, operation_type = None, condition = None ):
    value = self._makeCondValue( value, operation_type, condition )
    
    self.clearCache()
    
    if self._isParentValue( opt_value ):
      names = self._valueNames( opt_value )
      opt_value = opt_value.copy()
      self.__set_opt_value( opt_value, names )
    
    if operation_type is _SetDefaultValue:
      opt_value.setDefault( value )
    else:
      opt_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   clearCache( self ):
    self.__dict__['__cache'].clear()
    self.__clearChildrenCache()
  
  #//-------------------------------------------------------//
  
  def   If( self ):
    return ConditionGenerator( self )
