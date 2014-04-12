#
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'ErrorOptionsCyclicallyDependent', 'ErrorOptionsMergeNonOptions'
)

import operator
import weakref

from aql.util_types import toSequence, List, Dict, DictItem
from aql.utils import simplifyValue

from .aql_option_types import OptionType, DictOptionType, autoOptionType
from .aql_option_value import OptionValue, Operation, InplaceOperation, ConditionalValue, Condition,\
                              SetValue, iAddValue, iSubValue, iUpdateValue, SimpleOperation

#//===========================================================================//

class   ErrorOptionsCyclicallyDependent( TypeError ):
  def   __init__( self ):
    msg = "Options are cyclically dependent from each other."
    super(type(self), self).__init__( msg )

class   ErrorOptionsMergeNonOptions( TypeError ):
  def   __init__( self, value ):
    msg = "Type '%s' can't be merged with Options." % (type(value),)
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

class   _OpValueRef( tuple ):
  def   __new__( cls, value ):
    return super(_OpValueRef, cls).__new__( cls, (value.name, value.key ) )
  
  def   get( self, options, context ):
    name, key = self
    
    value = getattr( options, name ).get( context )
    
    if key is not NotImplemented:
      value = value[ key ]
    
    return value

class   _OpValueExRef( tuple ):
  def   __new__( cls, value ):
    return super(_OpValueExRef, cls).__new__( cls, (value.name, value.key, value.options ) )
  
  def   get( self ):
    name, key, options = self
    
    value = getattr( options, name ).get()
    
    if key is not NotImplemented:
      value = value[ key ]
    
    return value

#//===========================================================================//

def   _storeOpValue( options, value ):
  if isinstance( value, DictItem ):
    key, value = value
  else:
    key = NotImplemented
  
  if isinstance( value, OptionValueProxy ):
    value_options = value.options
    
    if (options is value_options) or options._isParent( value_options ):
      value = _OpValueRef( value )
    else:
      value_options._addChild( options )
      value = _OpValueExRef( value )
  
  if key is not NotImplemented:
    value = DictItem( key, value )
  
  return value

#//===========================================================================//

def   _loadOpValue( options, context, value ):
  if isinstance( value, DictItem ):
    key, value = value
  else:
    key = NotImplemented
  
  if isinstance( value, _OpValueRef ):
    value = value.get( options, context )
      
  elif isinstance( value, _OpValueExRef ):
    value = value.get()
  
  value = simplifyValue( value )
  
  if key is not NotImplemented:
    value = DictItem( key, value )
  
  return value

#//===========================================================================//

def   _evalCmpValue( value ):
  if isinstance( value, DictItem ):
    key, value = value
  else:
    key = NotImplemented
  
  if isinstance( value, OptionValueProxy ):
    value = value.get()
  
  value = simplifyValue( value )  
  
  if key is not NotImplemented:
    value = DictItem( key, value )
  
  return value

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
  
  def   get( self, context = None ):
    self.child_ref = None
    
    v = self.options.evaluate( self.option_value, context )
    return v if self.key is NotImplemented else v[self.key]
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      other = DictItem(self.key, other)
    
    self.options._appendValue( self.option_value, other, iAddValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   __add__( self, other ):
    return SimpleOperation( operator.add, self, other )
  
  #//-------------------------------------------------------//
  
  def   __radd__( self, other ):
    return SimpleOperation( operator.add, other, self )
  
  #//-------------------------------------------------------//
  
  def   __sub__( self, other ):
    return SimpleOperation( operator.sub, self, other )
  
  #//-------------------------------------------------------//
  
  def   __rsub__( self, other ):
    return SimpleOperation( operator.sub, other, self )
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, other ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      other = DictItem(self.key, other)
    
    self.options._appendValue( self.option_value, other, iSubValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   set( self, value, as_default = False ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      value = DictItem(self.key, value)
    
    self.options._appendValue( self.option_value, value, SetValue )
  
  #//-------------------------------------------------------//
  
  def   __setitem__( self, key, value ):
    child_ref = self.child_ref
    if (child_ref is not None) and (child_ref() is value):
      return
    
    if self.key is not NotImplemented:
      raise KeyError( key )
    
    option_type = self.option_value.option_type
    
    if isinstance( option_type, DictOptionType ):
      if isinstance( value, OptionType ) or (type(value) is type):
        option_type.setValueType( key, value )
        return
    
    value = DictItem( key, value )
    
    self.child_ref = None
    
    self.options._appendValue( self.option_value, value, SetValue )
  
  #//-------------------------------------------------------//
  
  def   __iter__(self):
    raise TypeError()
  
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
  
  def   eq( self, context, other ):   return self.cmp( context, operator.eq, other )
  def   ne( self, context, other ):   return self.cmp( context, operator.ne, other )
  def   lt( self, context, other ):   return self.cmp( context, operator.lt, other )
  def   le( self, context, other ):   return self.cmp( context, operator.le, other )
  def   gt( self, context, other ):   return self.cmp( context, operator.gt, other )
  def   ge( self, context, other ):   return self.cmp( context, operator.ge, other )
  
  def   __eq__( self, other ):        return self.eq( None,   _evalCmpValue( other ) )
  def   __ne__( self, other ):        return self.ne( None,   _evalCmpValue( other ) )
  def   __lt__( self, other ):        return self.lt( None,   _evalCmpValue( other ) )
  def   __le__( self, other ):        return self.le( None,   _evalCmpValue( other ) )
  def   __gt__( self, other ):        return self.gt( None,   _evalCmpValue( other ) )
  def   __ge__( self, other ):        return self.ge( None,   _evalCmpValue( other ) )
  def   __contains__( self, other ):  return self.has( None,  _evalCmpValue( other ) )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, context, cmp_operator, other ):
    self.child_ref = None
    
    value = self.get( context )
    
    if not isinstance( value, (Dict, List)) and (self.key is NotImplemented):
      other = self.option_value.option_type( other )
    
    return cmp_operator( value, other )
  
  #//-------------------------------------------------------//
  
  def   has( self, context, other ):
    value = self.get( context )
    
    return other in value
  
  #//-------------------------------------------------------//
  
  def   hasAny( self, context, others ):
    
    value = self.get( context )
    
    for other in toSequence( others ):
      if other in value:
        return True
    return False
  
  #//-------------------------------------------------------//
  
  def   hasAll( self, context, others ):
    
    value = self.get( context )
    
    for other in toSequence( others ):
      if other not in value:
        return False
    return True
  
  #//-------------------------------------------------------//
  
  def   oneOf( self, context, others ):
    
    value = self.get( context )
    
    for other in others:
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
  
  def   __iter__(self):
    raise TypeError()
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, key ):
    if self.key is not NotImplemented:
      raise KeyError( key )
    
    return ConditionGeneratorHelper( self.name, self.options, self.condition, key )
  
  #//-------------------------------------------------------//
  
  def   __setitem__( self, key, value ):
    if not isinstance(value, ConditionGeneratorHelper):
      
      value = DictItem(key, value)
      
      self.options.appendValue( self.name, value, SetValue, self.condition )
  
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
    
    self.options.appendValue( self.name, value, iAddValue, self.condition )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, value ):
    if self.key is not NotImplemented:
      value = DictItem( self.key, value )
    
    self.options.appendValue( self.name, value, iSubValue, self.condition )
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
      
      condition  = self.__dict__['__condition']
      
      self.__dict__['__options'].appendValue( name, value, SetValue, condition )
  
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
  
  def   _addChild(self, child ):
    
    children = self.__dict__['__children']
    
    for child_ref in children:
      if child_ref() is child:
        return
    
    if child._isChild( self ):
      raise ErrorOptionsCyclicallyDependent()
    
    children.append( weakref.ref( child ) )
  
  #//-------------------------------------------------------//
  
  def   _isParent( self, other ):
    
    if other is None:
      return False
    
    parent = self.__dict__['__parent']
    
    while parent is not None:
      if parent is other:
        return True
      
      parent = parent.__dict__['__parent']
    
    return False
  
  #//-------------------------------------------------------//
  
  def   _isChild(self, other ):
    
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
    for name, value in kw.items():
      opt_value = self._get_value( name, raise_ex = False )
      if opt_value is not None:
        opt_value = OptionValueProxy( opt_value, name, self )
        if opt_value.isSet() and (opt_value != value):
          return True
    
    return False
  
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
  
  def   __setitem__( self, name, value ):
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
  
  def   __getitem__( self, name ):
    return self.__getattr__( name )
  
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
    return opt_value not in self.__dict__['__opt_values']
  
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
        value = options.evaluate( value, context = None )
      
      self.__set_value( name, value, iUpdateValue )
  
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
  
  def   evaluate( self, option_value, context  ):
    try:
      if context is not None:
        return context[ option_value ]
    except KeyError:
      pass
    
    cache = self.__dict__['__cache']
    
    try:
      value = cache[ option_value ]
    except KeyError:
      value = option_value.get( self, context, _loadOpValue )
      cache[ option_value ] = value
    
    return value
  
  #//-------------------------------------------------------//
  
  def   _storeValue( self, value ):
    if isinstance( value, Operation ):
      value.convert( self, _storeOpValue )
    else:
      value = _storeOpValue( self, value )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   _loadValue( self, value ):
    if isinstance( value, Operation ):
      return value( self, {}, _loadOpValue )
    else:
      value = _loadOpValue( self, {}, value )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   _makeCondValue( self, value, operation_type, condition = None ):
    if isinstance(value, ConditionalValue ):
      return value
    
    if not isinstance( value, InplaceOperation ):
      value = operation_type( value )
    
    value = ConditionalValue( value, condition )
    
    value.convert( self, _storeOpValue )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   appendValue( self, name, value, operation_type, condition = None ):
    opt_value = self._get_value( name, raise_ex = True )
    self._appendValue( opt_value, value, operation_type, condition )
  
  #//-------------------------------------------------------//
  
  def   _appendValue( self, opt_value, value, operation_type, condition = None ):
    
    value = self._makeCondValue( value, operation_type, condition )
    
    self.clearCache()
    
    if self._isParentValue( opt_value ):
      names = self._valueNames( opt_value )
      opt_value = opt_value.copy()
      self.__set_opt_value( opt_value, names )
    
    opt_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   clearCache( self ):
    self.__dict__['__cache'].clear()
    self.__clearChildrenCache()
  
  #//-------------------------------------------------------//
  
  def   If( self ):
    return ConditionGenerator( self )
