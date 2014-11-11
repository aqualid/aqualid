#
# Copyright (c) 2011-2014 The developers of Aqualid project
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
  'ErrorOptionsCyclicallyDependent', 'ErrorOptionsMergeNonOptions', 'ErrorOptionsNoIteration',
)

import operator
import weakref

from aql.util_types import toSequence, UniqueList, List, Dict, DictItem
from aql.utils import simplifyValue

from .aql_option_types import OptionType, DictOptionType, autoOptionType, OptionHelpGroup,\
                              ErrorOptionTypeCantDeduce, ErrorOptionTypeUnableConvertValue
from .aql_option_value import OptionValue, Operation, InplaceOperation, ConditionalValue, Condition,\
                              SetValue, iAddValue, iSubValue, iUpdateValue, SimpleOperation

#//===========================================================================//

class   ErrorOptionsCyclicallyDependent( TypeError ):
  def   __init__( self ):
    msg = "Options cyclically depend from each other."
    super(type(self), self).__init__( msg )

class   ErrorOptionsMergeNonOptions( TypeError ):
  def   __init__( self, value ):
    msg = "Type '%s' can't be merged with Options." % (type(value),)
    super(type(self), self).__init__( msg )

class   ErrorOptionsMergeDifferentOptions( TypeError ):
  def   __init__( self, name1, name2):
    msg = "Can't merge one an optional value into two different options '%s' and '%s' " % ( name1, name2 )
    super(type(self), self).__init__( msg )

class   ErrorOptionsMergeChild( TypeError ):
  def   __init__( self ):
    msg = "Can't merge child options into the parent options. Use join() to move child options into its parent."
    super(type(self), self).__init__( msg )

class   ErrorOptionsJoinNoParent( TypeError ):
  def   __init__( self, options ):
    msg = "Can't join options without parent: %s" % ( options, )
    super(type(self), self).__init__( msg )

class   ErrorOptionsJoinParent( TypeError ):
  def   __init__( self, options ):
    msg = "Can't join options with children: %s" % ( options, )
    super(type(self), self).__init__( msg )

class   ErrorOptionsNoIteration( TypeError ):
  def   __init__( self ):
    msg = "Options doesn't support iteration"
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
      value_options._addDependency( options )
      value = _OpValueExRef( value )
  
  elif isinstance( value, dict ):
    value = { k: _storeOpValue( options, v ) for k, v in value.items() }
  
  elif isinstance( value, (list, tuple, UniqueList, set, frozenset) ):
    value = [ _storeOpValue( options, v ) for v in value ]
  
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
    value = simplifyValue( value )
    
  elif isinstance( value, _OpValueExRef ):
    value = value.get()
    value = simplifyValue( value )
  
  elif isinstance( value, dict ):
    value = { k: _loadOpValue( options, context, v ) for k, v in value.items() }
  
  elif isinstance( value, (list, tuple, UniqueList, set, frozenset) ):
    value = [ _loadOpValue( options, context, v ) for v in value ]
  
  else:
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
  
  def   __init__( self, option_value, from_parent, name, options, key = NotImplemented ):
    self.option_value = option_value
    self.from_parent = from_parent
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
    
    v = self.options.evaluate( self.option_value, context, self.name )
    return v if self.key is NotImplemented else v[self.key]
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      other = DictItem(self.key, other)
    
    self.options._appendValue( self.option_value, self.from_parent, other, iAddValue )
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
    
    self.options._appendValue( self.option_value, self.from_parent, other, iSubValue )
    return self
  
  #//-------------------------------------------------------//
  
  def   set( self, value ):
    self.child_ref = None
    
    if self.key is not NotImplemented:
      value = DictItem(self.key, value)
    
    self.options._appendValue( self.option_value, self.from_parent, value, SetValue )
  
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
    
    self.options._appendValue( self.option_value, self.from_parent, value, SetValue )
  
  #//-------------------------------------------------------//
  
  def   __iter__(self):
    raise TypeError()
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, key ):
    if self.key is not NotImplemented:
      raise KeyError( key )
    
    child = OptionValueProxy( self.option_value, self.from_parent, self.name, self.options, key )
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
  
  def   notIn( self, context, others ):
    return not self.oneOf( context, others )
  
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
  def   notIn( self, values ):  return self.cmp( 'notIn',   values )
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

def   _itemsByValue( items ):
  
  values = {}
  
  for name, value in items:
    try:
      values[ value ].add( name )
    except KeyError:
      values[ value ] = {name}
  
  return values

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
  
  def   _addDependency(self, child ):
    
    children = self.__dict__['__children']
    
    for child_ref in children:
      if child_ref() is child:
        return
    
    if child._isDependency( self ):
      raise ErrorOptionsCyclicallyDependent()
    
    children.append( weakref.ref( child ) )
  
  #//-------------------------------------------------------//
  
  def   _isDependency(self, other ):
    
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
  
  def   __copyParentOption(self, opt_value ):
    parent = self.__dict__['__parent']
    items = parent._valuesMapByName().items()
    names = [ name for name, value in items if value is opt_value ]
    opt_value = opt_value.copy()
    self.__set_opt_value( opt_value, names )
    
    return opt_value
  
  #//-------------------------------------------------------//
  
  def   getHashRef( self ):
    if self.__dict__['__opt_values']:
      return weakref.ref( self )
    
    parent = self.__dict__['__parent']
    
    if parent is None:
      return weakref.ref( self )
    
    return parent.getHashRef()
  
  #//-------------------------------------------------------//
  
  def   hasChangedKeyOptions(self):
    
    parent = self.__dict__['__parent']
    
    for name, opt_value in self.__dict__['__opt_values'].items():
      if not opt_value.isToolKey() or not opt_value.isSet():
        continue
      
      parent_opt_value, from_parent = parent._get_value( name, raise_ex = False )
      if parent_opt_value is None:
        continue
      
      if parent_opt_value.isSet():
        value = self.evaluate( opt_value, None, name )
        parent_value = parent.evaluate( parent_opt_value, None, name )
        if value != parent_value:
          return True
    
    return False
  
  #//-------------------------------------------------------//
  
  def   __set_value( self, name, value, operation_type = SetValue ):
    
    opt_value, from_parent = self._get_value( name, raise_ex = False )
    
    if opt_value is None:
      self.clearCache()
      
      if isinstance( value, OptionType ):
        opt_value = OptionValue( value )
      
      elif isinstance( value, OptionValueProxy ):
        if value.options is self:
          if not value.from_parent:
            opt_value = value.option_value
          else:
            opt_value = self.__copyParentOption( value.option_value )

        elif self._isParent( value.options ):
          opt_value = self.__copyParentOption( value.option_value )
        
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
      
      self._appendValue( opt_value, from_parent, value, operation_type )
  
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
      return self.__dict__['__opt_values'][ name ], False
    except KeyError:
      parent = self.__dict__['__parent']
      if parent is not None:
        value, from_parent = parent._get_value( name, False )
        if value is not None:
          return value, True
      
      if raise_ex:
        raise AttributeError( "Options '%s' instance has no option '%s'" % (type(self), name) )
      
      return None, False
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, name ):
    return self.__getattr__( name )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    opt_value, from_parent = self._get_value( name, raise_ex = True )
    return OptionValueProxy( opt_value, from_parent, name, self )
  
  #//-------------------------------------------------------//
  
  def   __contains__( self, name ):
    return self._get_value( name, raise_ex = False )[0] is not None
  
  #//-------------------------------------------------------//
  
  def   __iter__( self ):
    raise ErrorOptionsNoIteration()
  
  #//-------------------------------------------------------//
  
  def   _valuesMapByName( self, result = None ):
    
    if result is None:
      result = {}
          
    parent = self.__dict__['__parent']
    if parent is not None:
      parent._valuesMapByName( result = result )
    
    result.update( self.__dict__['__opt_values'] )
    
    return result
  
  #//-------------------------------------------------------//
  
  def   _valuesMapByValue( self ):
    items = self._valuesMapByName().items()
    return _itemsByValue( items )
  
  #//-------------------------------------------------------//
  
  def   help( self, with_parent = False, hidden = False ):
    
    if with_parent:
      options_map = self._valuesMapByName()
    else:
      options_map = self.__dict__['__opt_values']

    options2names = _itemsByValue( options_map.items() )
    
    result = {}
    for option, names in options2names.items():
      help = option.option_type.help()
      
      if help.isHidden() and not hidden:
        continue
      
      help.names = names
      
      try:
        help.current_value = self.evaluate( option, {}, names )
      except Exception:
        pass
      
      group_name = help.group if help.group else ""
      
      try:
        group = result[ group_name ]
      except KeyError:
        group = result[ group_name ] = OptionHelpGroup( group_name )
      
      group.append( help )
    
    return sorted( result.values(), key = operator.attrgetter('name') )
        
  #//-------------------------------------------------------//
  
  def   helpText( self, title, with_parent = False, hidden = False, brief = False ):
    
    border = "=" * len(title)
    result = ["", title, border, ""]
    
    for group in self.help( with_parent = with_parent, hidden = hidden ):
      text = group.text( brief = brief, indent = 2 )
      if result[-1]:
        result.append("")
      result.extend( text )
    
    return result
  
  #//-------------------------------------------------------//
  
  def   setGroup( self, group ):
    opt_values = self._valuesMapByName().values()
    
    for opt_value in opt_values:
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
    
    if isinstance( other, Options ):
      self.merge( other )
    
    else:
      for name, value in other.items():
        if isinstance( value, (ConditionGeneratorHelper, ConditionGenerator, Options) ):
          continue
        
        try:
          self.__set_value( name, value, iUpdateValue )
        except ErrorOptionTypeCantDeduce:
          pass
  
  #//-------------------------------------------------------//
  
  def   __merge( self, self_names, other_names, move_values = False ):
    
    self.clearCache()
    
    other_values = _itemsByValue( other_names.items() )
    
    self_names_set = set(self_names)
    self_values = _itemsByValue( self_names.items() )
    
    for value, names in other_values.items():
      same_names = names & self_names_set
      if same_names:
        self_value_name   = next(iter(same_names))
        self_value        = self_names[ self_value_name ]
        self_values_names = self_values[ self_value ]
        self_other_names  = same_names - self_values_names
        if self_other_names:
          raise ErrorOptionsMergeDifferentOptions( self_value_name, self_other_names.pop() )
        else:
          new_names = names - self_values_names
          self_value.merge( value )
      else:
        if move_values:
          self_value = value
        else:
          self_value = value.copy()
        
        new_names = names
      
      self.__set_opt_value( self_value, new_names )
        
  #//-------------------------------------------------------//
  
  def   merge( self, other ):
    if not other:
      return
    
    if self is other:
      return
    
    if not isinstance( other, Options ):
      raise ErrorOptionsMergeNonOptions( other )
    
    if other._isParent( self ):
      raise ErrorOptionsMergeChild()
    
    self.__merge( self._valuesMapByName(), other._valuesMapByName() )
    
  #//-------------------------------------------------------//
  
  def   join( self ):
    parent = self.__dict__['__parent']
    if parent is None:
      raise ErrorOptionsJoinNoParent( self )
    
    if self.__dict__['__children']:
      raise ErrorOptionsJoinParent( self )
    
    parent.__merge( parent.__dict__['__opt_values'],
                    self.__dict__['__opt_values'],
                    move_values = True )
    
    self.clear()
  
  #//-------------------------------------------------------//
  
  def   unjoin( self ):
    parent = self.__dict__['__parent']
    if parent is None:
      return
    
    self.__merge( self.__dict__['__opt_values'], parent._valuesMapByName() )
    
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
    
    for opt_value, names in self._valuesMapByValue().items():
      other.__set_opt_value( opt_value.copy(), names )
    
    return other
  
  #//-------------------------------------------------------//
  
  def   _evaluate( self, option_value, context ):
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
  
  def   evaluate( self, option_value, context, name ):
    try:
      return self._evaluate( option_value, context )
    except ErrorOptionTypeUnableConvertValue as err:
      if not name:
        raise
      
      option_help = err.option_help
      if option_help.names:
        raise
    
    option_help.names = tuple( toSequence( name ) )
    
    raise ErrorOptionTypeUnableConvertValue( option_help, err.invalid_value )
  
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
    opt_value, from_parent = self._get_value( name, raise_ex = True )
    self._appendValue( opt_value, from_parent, value, operation_type, condition )
  
  #//-------------------------------------------------------//
  
  def   _appendValue( self, opt_value, from_parent, value, operation_type, condition = None ):
    
    value = self._makeCondValue( value, operation_type, condition )
    
    self.clearCache()
    
    if from_parent:
      opt_value = self.__copyParentOption( opt_value )
    
    opt_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   clearCache( self ):
    self.__dict__['__cache'].clear()
    self.__clearChildrenCache()
  
  #//-------------------------------------------------------//
  
  def   If( self ):
    return ConditionGenerator( self )
