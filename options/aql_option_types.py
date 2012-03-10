
from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, EnumOptionInvalidValue
from aql_utils import toSequence
from aql_simple_types import IgnoreCaseString

#//===========================================================================//
#//===========================================================================//

class   OptionBase (object):

  __slots__ = (
    'description',
    'group',
    'allowed_operations',
  )

  #//-------------------------------------------------------//
  
  def     __init__( self, description = None, group = None, allowed_operations = '=' ):
    
    self.group = group
    self.description = description
    self.allowed_operations = allowed_operations
  
  #//-------------------------------------------------------//
  
  def   convert( self, value ):
    """
    Converts a value to options' value
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    """
    Returns a description (list of strings) about range of allowed values
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )

#//===========================================================================//
#//===========================================================================//

class   BoolOption (OptionBase):
  
  __slots__ = (
    'true_value',
    'false_value',
    'true_values',
    'false_values',
    'aliases',
  )
  
  class   __Value( int ):
    
    def __new__( cls, value, str_value ):
      self = super(cls, cls).__new__( cls, value )
      self.__value = str(str_value)
      
      return self
    
    def   __str__( self ):
      return self.__value
  
  #//-------------------------------------------------------//
  
  __true_values = ('yes', 'true', 'on', 'enabled', 'y', '1', 't' )
  __false_values = ('no', 'false', 'off', 'disabled', 'n', '0', 'f' )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, description = None, group = None, style = None, true_values = None, false_values = None ):
    super(BoolOption,self).__init__( description, group )
    
    if style is None:
      style = ('True', 'False')
    else:
      style = map(str, style)
    
    if true_values is None:
      true_values = self.__true_values
    else:
      true_values = toSequence( true_values )
    
    if false_values is None:
      false_values = self.__false_values
    else:
      false_values = toSequence( false_values )
    
    self.true_value, self.false_value = style
    self.true_values  = set( map( lambda v: str(v).lower(), true_values  ) )
    self.false_values = set( map( lambda v: str(v).lower(), false_values ) )
  
  #//-------------------------------------------------------//
  
  def   convert( self, value, _BoolValue = __Value):
    if isinstance( value, _BoolValue ):
      return value
    
    value_str = str(value).lower()
    if value_str in self.true_values:
      value = True
    
    if value_str in self.false_values:
      value =  False
    
    if value:
      return _BoolValue( True, self.true_value )
    
    return _BoolValue( False, self.false_value )
  
  #//-------------------------------------------------------//
  
  def   addValues( self, true_values, false_values ):
    true_values = toSequence( true_values )
    false_values = toSequence( false_values )
    
    self.true_values.update( map( lambda v: str(v).lower(),  true_values  ) )
    self.false_values.update( map( lambda v: str(v).lower(), false_values  ) )
  
  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    return  [ self.true_value + ': [' + ', '.join( sorted( self.true_values ) ) + ']',
              self.false_value + ': [' + ', '.join( sorted( self.false_values ) ) + ']' ]

#//===========================================================================//
#//===========================================================================//

class   EnumOption (OptionBase):
  
  __slots__ = (
    '__values',
    '__value_type',
  )
  
  def   __init__( self, description = None, group = None, values = None, value_type = IgnoreCaseString ):
    
    super(EnumOption,self).__init__( description, group )
    
    self.__values = {}
    self.__value_type = value_type
    
    self.addValues( values );
  
  #//-------------------------------------------------------//
  
  def   addValues( self, values ):
    try:
      values = tuple( values.items() )  # convert dictionary to a sequence
    except AttributeError:
      pass
    
    setDefaultValue = self.__values.setdefault
    value_type = self.__value_type
    
    for value in values:
      it = iter( toSequence( value ) )
      
      value = value_type( next( it ) )
      
      value = setDefaultValue( value, value )
      
      for alias in it:
        alias = value_type(alias)
        
        v = setDefaultValue( alias, value )
        if v != value:
          if alias == v:
            raise EnumOptionValueIsAlreadySet( self, alias, value )
          else:
            raise EnumOptionAliasIsAlreadySet( self, alias, v, value )
    
  #//-------------------------------------------------------//
  
  def   convert( self, value ):
    try:
      return self.__values[ self.__value_type( value ) ]
    except KeyError:
      raise EnumOptionInvalidValue( self, value )
  
  #//-------------------------------------------------------//
  
  def   rangeHelp(self):
    
    values = {}
    
    for alias, value in self.__values.items():
      if alias is value:
        values.setdefault( alias, [] )
      else:
        values.setdefault( value, [] ).append( alias )
    
    help_str = []
    
    for value, aliases in values.items():
      s = str(value)
      if aliases:
        s += ' (or ' + ', '.join( map( str, aliases ) ) + ')'
      
      help_str.append( s )
    
    return help_str
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    values = []
    
    for alias, value in self.__values.items():
      if value is value:
        values.append( alias )
    
    return values
