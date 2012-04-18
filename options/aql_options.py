from aql_utils import toSequence
from aql_option_types import OptionType, ListOptionType
from aql_option_value import OptionValue

#//===========================================================================//
# raw value
# OptionType
# OptionValue
# OptionValueProxy
# Operation
# ConditionalValue

def   _makeOpValue( value, operation_type, condition = None ):
  
  if operation_type is None:
    raise InvalidOptionType( value )
  
  if isinstance( value, (ConditionalValue, Operation ) ):
    raise InvalidOptionType( value )
  
  if isinstance( value, OptionValue ):
    value = OperationOptionValue( value )
  elif isinstance( value, OptionValueProxy ):
    value = OperationOptionValue( value.option_value )
  
  return ConditionalValue( operation_type( value ), condition )

#//===========================================================================//

def   _makeCondValue( value, operation_type = None, condition = None ):
  if isinstance( value, Operation ):
    return ConditionalValue( value, condition )
  elif isinstance( value, ConditionalValue ):
    return value
  
  return _makeOpValue( value, operation_type, condition )

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
    return self.option_value.value( self.options, context )
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    self.option_value.appendValue( _makeOpValue( other, AddValue ) )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, other ):
    self.option_value.appendValue( _makeOpValue( other, SubValue ) )
    return self
  
  #//-------------------------------------------------------//
  
  def   set( self, value, condition = None ):
    self.option_value.appendValue( _makeCondValue( value, SetValue ), condition )
  
  #//-------------------------------------------------------//
  
  def   __cmp( self, other, op ):
    if isinstance( other, OptionValueProxy ):
      other = other.value()
    elif isinstance( other, OptionValue ):
      other = other.value( self.options )
    
    option_value = self.option_value
    
    value       = option_value.value( self.options )
    other_value = option_value.optionType( other )
    
    return getattr(value, op )( other_value )
  
  def   __eq__( self, other ):  return self.__cmp( other, '__eq__' )
  def   __ne__( self, other ):  return self.__cmp( other, '__ne__' )
  def   __lt__( self, other ):  return self.__cmp( other, '__lt__' )
  def   __le__( self, other ):  return self.__cmp( other, '__le__' )
  def   __gt__( self, other ):  return self.__cmp( other, '__gt__' )
  def   __ge__( self, other ):  return self.__cmp( other, '__ge__' )

#//===========================================================================//

class Options (object):
  
  __slots__ = (
    '__values',
    '__cache',
  )
  
  def     __init__( self ):
      
      self.__values   = {}
      self.__cache    = {}
  
  #//-------------------------------------------------------//
  
  def   __set_value( self, name, value ):
    if isinstance( value, OptionType ):
      value = OptionValue( value )
    
    elif isinstance( value, OptionValueProxy ):
      value = value.option_value
      
    if isinstance( value, OptionValue ):
      opt_value = self.__values.setdefault( name, value )
      if opt_value is value:
        return
      
      value = ConditionalValue( SetValue( OperationOptionValue( value ) ) )
    else:
      try:
        opt_value = self.__values[ name ]
      except KeyError:
        raise InvalidOptionType( value )
      
      value = _makeCondValue( value, SetValue )
    
    opt_value.appendValue( value )
  
  #//-------------------------------------------------------//
  
  def   __setattr__(self, name, value ):
    self.__set_value( name, value )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, name ):
    return OptionValueProxy( self.__values[ name ], self )
  
  #//-------------------------------------------------------//
  
  def     __contains__( self, name ):
    return name in self.__values
  
  #//-------------------------------------------------------//

  def     update( self, args ):
   if isinstance( args, Options ):
     self.__values.update( options.__values )
   
   
      if isString( args ):
          filename = args
          args = {'options':self}
          execfile( filename, {}, args )
          
          if args['options'] is self:
              del args['options']
      
      if isDict( args ):
          set_option = self.__set_option
          
          for key, value in args.iteritems():
              set_option( key, value, update = 1, quiet = quiet )
      else:
          _Error( "Invalid argument: %s" % (str(args)) )

  #//-------------------------------------------------------//
  
  def     __iadd__(self, other ):
      
      self.update( other )
      
      return self
