
from aql_utils import toSequence
from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue, InvalidOptionType
from aql_simple_types import IgnoreCaseString
from aql_list_types import UniqueList, List, SplitListType, ValueListType

#//===========================================================================//

#~ def   makeValueType( option_type, value_type ):
  #~ class _ValueProxy (value_type):
    
    #~ def   __iadd__( self, other ):      return option_type( super(_Value,cls).__iadd__( cls, value ) )
    #~ def   __isub__( self, other ):      return option_type( super(_Value,cls).__isub__( cls, value ) )
    #~ def   __imul__( self, other ):      return option_type( super(_Value,cls).__imul__( cls, value ) )
    #~ def   __idiv__( self, other ):      return option_type( super(_Value,cls).__idiv__( cls, value ) )
    #~ def   __itruediv__( self, other ):  return option_type( super(_Value,cls).__itruediv__( cls, value ) )
    #~ def   __ifloordiv__( self, other ): return option_type( super(_Value,cls).__ifloordiv__( cls, value ) )
    #~ def   __imod__( self, other ):      return option_type( super(_Value,cls).__imod__( cls, value ) )
    #~ def   __ipow__( self, other ):      return option_type( super(_Value,cls).__ipow__( cls, value ) )
    #~ def   __ilshift__( self, other ):   return option_type( super(_Value,cls).__ilshift__( cls, value ) )
    #~ def   __irshift__( self, other ):   return option_type( super(_Value,cls).__irshift__( cls, value ) )
    #~ def   __iand__( self, other ):      return option_type( super(_Value,cls).__iadd__( cls, value ) )
    #~ def   __ixor__( self, other ):      return option_type( super(_Value,cls).__ixor__( cls, value ) )
    #~ def   __ior__( self, other ):       return option_type( super(_Value,cls).__ior__( cls, value ) )
  
  #~ return _Value

#//===========================================================================//

class   OptionType (object):

  __slots__ = (
    'value_type',
    'description',
    'group',
    'range_help',
  )
  
  #//-------------------------------------------------------//
  
  def     __init__( self, value_type, description = None, group = None, range_help = None ):
    
    self.value_type = value_type
    self.description = description
    self.group = group
    self.range_help = range_help
  
  #//-------------------------------------------------------//
  
  def   __call__( self, value = NotImplemented ):
    """
    Converts a value to options' value
    """
    try:
      if value is NotImplemented:
        return self.value_type()
      
      return self.value_type( value )
    except (TypeError, ValueError):
      raise InvalidOptionValue( self.value_type, value )
  
  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    """
    Returns a description (list of strings) about range of allowed values
    """
    if self.range_help:
      return toSequence( self.range_help )
    
    return ["Value of type %s" % self.value_type]

#//===========================================================================//
#//===========================================================================//

class   BoolOptionType (OptionType):
  
  __slots__ = (
    'true_value',
    'false_value',
    'true_values',
    'false_values',
    'aliases',
  )
  
  class   _Value( int ):
    
    def   __new__( cls, value, str_value ):
      self = super(BoolOptionType._Value, cls).__new__( cls, value )
      self.__value = str(str_value)
      
      return self
    
    def   __str__( self ):
      return self.__value
  
  #//-------------------------------------------------------//
  
  __true_values = ('yes', 'true', 'on', 'enabled', 'y', '1', 't' )
  __false_values = ('no', 'false', 'off', 'disabled', 'n', '0', 'f' )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, description = None, group = None, style = None, true_values = None, false_values = None ):
    
    super(BoolOptionType,self).__init__( BoolOptionType._Value, description, group )
    
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
  
  def   __call__( self, value = NotImplemented ):
    
    if value is NotImplemented:
      value = False
    
    value_str = str(value).lower()
    if value_str in self.true_values:
      value = True
    
    if value_str in self.false_values:
      value =  False
    
    if value:
      value = True
      value_str = self.true_value
    else:
      value = False
      value_str = self.false_value
    
    return self.value_type( value, value_str )
  
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

class   EnumOptionType (OptionType):
  
  __slots__ = (
    '__values',
  )
  
  def   __init__( self, values, description = None, group = None, value_type = IgnoreCaseString ):
    
    super(EnumOptionType,self).__init__( value_type, description, group )
    
    self.__values = {}
    
    self.addValues( values )
  
  #//-------------------------------------------------------//
  
  def   addValues( self, values ):
    try:
      values = tuple( values.items() )  # convert dictionary to a sequence
    except AttributeError:
      pass
    
    setDefaultValue = self.__values.setdefault
    value_type = self.value_type
    
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
  
  def   __call__( self, value = NotImplemented ):
    try:
      if value is NotImplemented:
        try:
          return next(iter(self.__values.values()))
        except StopIteration:
          raise InvalidOptionType( self )
      
      return self.__values[ self.value_type( value ) ]
    except (KeyError, TypeError):
      raise InvalidOptionValue( self, value )
  
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
      if alias is value:
        values.append( alias )
    
    return values

#//===========================================================================//
#//===========================================================================//

class   RangeOptionType (OptionType):
  
  __slots__ = (
    'min_value',
    'max_value',
    'fix_value',
  )
  
  def   __init__( self, min_value, max_value, description = None, group = None, value_type = int, fix_value = False):
    
    super(RangeOptionType,self).__init__( value_type, description, group )
    
    self.setRange( min_value, max_value, fix_value )
  
  #//-------------------------------------------------------//
  
  def   setRange( self, min_value, max_value, fix_value = None ):
    
    if min_value is not None:
      try:
        self.min_value = self.value_type( min_value )
      except TypeError:
        raise InvalidOptionValue( self, min_value )
    else:
      self.min_value = None
      
    if max_value is not None:
      try:
        self.max_value = self.value_type( max_value )
      except TypeError:
        raise InvalidOptionValue( self, max_value )
    else:
      self.max_value = None
    
    if fix_value is not None:
      self.fix_value = fix_value
    
  #//-------------------------------------------------------//
  
  def   __call__( self, value = NotImplemented):
    try:
      if value is NotImplemented:
        value = self.min_value
      
      value = self.value_type( value )
      
      if value < self.min_value:
        if self.fix_value:
          value = self.min_value
        else:
          raise TypeError()
      
      if value > self.max_value:
        if self.fix_value:
          value = self.max_value
        else:
          raise TypeError()
      
      return value
    
    except TypeError:
      raise InvalidOptionValue( self, value )
  
  #//-------------------------------------------------------//
  
  def   rangeHelp(self):
    return ["%s ... %s" % (self.min_value, self.max_value) ]
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return (self.min_value, self.max_value)

#//===========================================================================//
#//===========================================================================//

#   release_size.flags.value.append( '-Os' )
#   release_size.flags += '-Os'
#   release_size.has( 'flags', '-Os' ).flags -= '-O3'
#   release_size.eq( 'defines', '' ).flags -= '-O3'
#   options.If().cppdefines( 1, '__getitem__', 'DEBUG' )
#   options.If().cppdefines['DEBUG'].eq( 0 ).ccflags += '-O3'
#   options.If().cppdefines['DEBUG'][ 0 ].ccflags += '-O3'
#   options.If().cppdefines['DEBUG'][ 0 ].ccflags += '-O3'

#   options.If().eq( 'cppdefines' ['DEBUG'].eq( 0 ).ccflags += '-O3'

class   ListOptionType (OptionType):
  
  __slots__ = (
    'list_type',
  )
  
  #//=======================================================//
  
  def   __init__( self, value_type, unique = False, separators = ', ', description = None, group = None, range_help = None ):
    
    if isinstance(value_type, OptionType):
      if description is None:
        description = value_type.description
        if description:
          description = "List of: " + description
      
      if group is None:
        group = value_type.group
      
      if range_help is None:
        range_help = value_type.range_help
    
    super(ListOptionType,self).__init__( value_type, description, group, range_help )
    
    if unique:
      list_type = UniqueList
    else:
      list_type = List
    
    list_type = ValueListType( list_type, value_type )
    
    if separators:
      list_type = SplitListType( list_type, separators )
    
    self.list_type = list_type
    
  #//-------------------------------------------------------//
  
  def   __call__( self, values = None ):
    
    try:
      return self.list_type( values )
      
    except (TypeError, ValueError):
      raise InvalidOptionValue( self.value_type, values )

  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    
    if not self.range_help:
      if isinstance(self.value_type, OptionType):
        return self.value_type.rangeHelp()
    
    return super(ListOptionType, self).rangeHelp()
