from aql_utils import toSequence

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
      self = super(Foo, cls).__new__(cls, value )
      self.__value = str(str_value)
    
    def   __str__( self ):
      return self.__value
  
  #//-------------------------------------------------------//
  
  __true_values = ('yes', 'true', 'on', 'enabled', 'y', '1', 't' )
  __false_values = ('no', 'false', 'off', 'disabled', 'n', '0', 'f' )
  
  __inverted_bool = __invert_true.copy()
  __inverted_bool.update( __invert_false )

  #//-------------------------------------------------------//
  
  def   __init__( self, description = None, group = None, style = None, true_values = None, false_values = None ):
    super(BoolOption,self).__init__( description, group )
    
    if style is None:
      style = ('True', 'False')
    
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
  
  def   convert( self, value ):
    if isinstance( BoolOption.__Value, value ):
      return value
    
    value_str = str(value).lower()
    if value_str in self.true_values:
      value = True
    
    if value_str in self.false_values:
      value =  False
    
    if value:
      return BoolOption.__Value( True, self.true_value )
    
    return BoolOption.__Value( False, self.false_value )
  
  #//-------------------------------------------------------//
  
  def   addValues( self, true_values, false_values ):
    true_values = toSequence( true_values )
    false_values = toSequence( false_values )
    
    self.true_values.update( map( lambda v: str(v).lower(),  true_values  ) )
    self.false_values.update( map( lambda v: str(v).lower(), false_values  ) )
  
  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    return  self.true_value + ': ' + ','.join( sorted( self.true_values ) ) + ' / ' + \
            self.false_value + ': ' + ','.join( sorted( self.false_values ) )
