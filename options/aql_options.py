import itertools
import weakref

from aql_utils import toSequence
from aql_option_types import OptionType, ListOptionType
from aql_option_value import OptionValue
from aql_errors import InvalidOptions, InvalidOptionValueType

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
    option_value = self.option_value
    options = self.options
    
    try:
      value = options.getCached( option_value )
    except KeyError:
      value = option_value.value( self.options, context )
      options.setCached( option_value, value )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    options = self.options
    options.clearCache()
    self.option_value.appendValue( options._makeOpValue( other, AddValue ) )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, other ):
    self.options.clearCache()
    self.option_value.appendValue( options._makeOpValue( other, SubValue ) )
    return self
  
  #//-------------------------------------------------------//
  
  def   set( self, value, operation_type = SetValue, condition = None ):
    value = self.options._makeCondValue( value, operation_type, condition )
    self.options.clearCache()
    self.option_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   cmp( self, other, op, context = None ):
    if isinstance( other, OptionValueProxy ):
      other = other.value()
    elif isinstance( other, OptionValue ):
      other = other.value( self.options, context )
    
    value       = self.value( context )
    other_value = self.option_value.optionType( other )
    
    return getattr(value, op )( other_value )
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):  return self.__cmp( other, '__eq__' )
  def   __ne__( self, other ):  return self.__cmp( other, '__ne__' )
  def   __lt__( self, other ):  return self.__cmp( other, '__lt__' )
  def   __le__( self, other ):  return self.__cmp( other, '__le__' )
  def   __gt__( self, other ):  return self.__cmp( other, '__gt__' )
  def   __ge__( self, other ):  return self.__cmp( other, '__ge__' )

#//===========================================================================//

class Options (object):
  
  __slots__ = (
    '__opt_values',
    '__cache',
    '__parent',
    '__children',
  )
  
  def     __init__( self, parent = None ):
    self.__opt_values   = {}
    self.__cache        = {}
    self.__parent       = parent
    self.__children     = []
    
    if parent is not None:
      parent.__children.append( weakref.proxy( self ) )
  
  #//-------------------------------------------------------//
  
  #//===========================================================================//
  # raw value
  # OptionType
  # OptionValue
  # OptionValueProxy
  # Operation
  # ConditionalValue

  def   _makeOpValue( self, value, operation_type, condition = None ):
    
    if operation_type is None:
      raise InvalidOptionValueType( value )
    
    if isinstance( value, (ConditionalValue, Operation ) ):
      raise InvalidOptionValueType( value )
    
    if isinstance( value, OptionValue ):
      raise InvalidOptionValueType( value )
    
    if isinstance( value, OptionValueProxy ):
      if value.options is not self:
        raise InvalidOptionValueType( value )
      
      value = OperationOptionValue( value.option_value )
    
    return ConditionalValue( operation_type( value ), condition )

  #//===========================================================================//

  def   _makeCondValue( self, value, operation_type = None, condition = None ):
    if isinstance( value, Operation ):
      return ConditionalValue( value, condition )
    elif isinstance( value, ConditionalValue ):
      return value
    
    return self._makeOpValue( value, operation_type, condition )

  
  #//-------------------------------------------------------//
  
  def   __set_value( self, name, value, operation_type = SetValue ):
    
    opt_value, from_parent = self._get_value( name )
    
    if isinstance( value, OptionType ):
      value = OptionValue( value )
    
    elif isinstance( value, OptionValueProxy ):
      if value.options is not self:
        raise InvalidOptionValueType( value )
      
      if opt_value is value.option_value:
        return
      
      if opt_value is None:
        self.__opt_values[ name ] = value.option_value
        return
      
      value = ConditionalValue( operation_type( OperationOptionValue( value ) ) )
    
    else:
      value = self._makeCondValue( value, operation_type )
    
    if from_parent:
      opt_value = opt_value.copy()
      self.__opt_values[ name ] = opt_value
    
    opt_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   __setattr__( self, name, value ):
    self.__set_value( name, value )
    self.clearCache()
  
  #//-------------------------------------------------------//
  
  def   _get_value( self, name ):
    try:
      return (self.__opt_values[ name ], False)
    except KeyError as e:
      try:
        return (self.__parent._get_value( name ), True )
      except AttributeError:
        return None, False
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    return OptionValueProxy( self._get_value( name )[0], self )
  
  #//-------------------------------------------------------//
  
  def   __contains__( self, name ):
    return self._get_value( name )[0] is None
  
  #//-------------------------------------------------------//
  
  def   __iter__( self ):
    return iter(self.keys())
  
  #//-------------------------------------------------------//
  
  def   keys( self ):
    names = set( self.__opt_values )
    parent = self.__parent
    if parent:
      names.update( parent.keys() )
    
    return names
  
  #//-------------------------------------------------------//
  
  def   items( self ):
    for name in self.keys():
      yield ( name, self._get_value( name )[0] )
  
  #//-------------------------------------------------------//
  
  def     __nonzero__( self ):
    return bool(self.__opt_values) or bool(self.__parent)
  
  def     __bool__( self ):
    return bool(self.__opt_values) or bool(self.__parent)
  
  #//-------------------------------------------------------//

  def     update( self, other ):
    if not other:
      return
    
    self.clearCache()
    
    for name, value in other.items():
      try:
        self.__set_value( name, value, UpdateValue )
      except KeyError:
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
      new_opt_value = opt_value.copy()
      for name in names:
        setattr( other, name, new_opt_value )
  
  #//-------------------------------------------------------//
  
  def   getCached( self, option_value ):
    return self.__cache[ option_value ]
  
  #//-------------------------------------------------------//
  
  def   setCached( self, option_value, value ):
    self.__cache[ option_value ] = value
  
  #//-------------------------------------------------------//
  
  def   clearCache( self ):
    self.__cache.clear()
    
    for child in self.__children:
      try:
        child.clearCache()
      except ReferenceError:
        pass
