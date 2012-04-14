from aql_utils import toSequence
from aql_option_types import OptionType, ListOptionType
from aql_option_value import OptionValue

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
  
  def   value( self ):
    return self.option_value.value( self.options )
  
  #//-------------------------------------------------------//
  
  def   __makeValue( self, value, operation_type ):
    if isinstance( value, ValueOperation ):
      return OptionConditionalValue( value )
    
    if isinstance( value OptionValue ):
    
    if not isinstance( value, OptionConditionalValue ):
      return OptionConditionalValue( operation_type( value ) )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    other = self.__makeValue( other, AddValue )
    self.option_value.appendValue( other )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__( self, other ):
    other = self.__makeValue( other, SubValue )
    self.option_value.appendValue( other )
    return self


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
      if opt_value is not value:
        opt_value
    else:
      try:
        opt_value = self.__values[ name ]
      except KeyError:
        raise InvalidOptionType( value )
  
  #//-------------------------------------------------------//
  
  def     __setattr__(self, name, value ):
    self.__set_value( name, value )
  
  #//-------------------------------------------------------//
  
  def     __getattr__( self, name ):
    return OptionValueProxy( self.__values[ name ], self )
  
  #//-------------------------------------------------------//
  
  def     __contains__( self, name ):
    return self.__get_option( name )
  
  #//-------------------------------------------------------//

  def     move( self, options ):
    
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

  def     update( self, args ):
      
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
