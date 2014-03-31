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
  'OptionType', 'StrOptionType', 'VersionOptionType', 'PathOptionType', 'BoolOptionType', 
  'EnumOptionType', 'RangeOptionType', 'ListOptionType', 'DictOptionType',
  'autoOptionType',
  'ErrorOptionTypeEnumAliasIsAlreadySet', 'ErrorOptionTypeEnumValueIsAlreadySet',
  'ErrorOptionTypeUnableConvertValue', 'ErrorOptionTypeNoEnumValues', 
)

from aql.util_types import AqlException, toSequence, IgnoreCaseString, Version, FilePath, UniqueList, List, \
                          SplitListType, ValueListType, Dict, SplitDictType, ValueDictType

#//===========================================================================//

class   ErrorOptionTypeEnumAliasIsAlreadySet( AqlException ):
  def   __init__( self, option, value, current_value, new_value ):
    msg = "Alias '%s' of Enum Option '%s' can't be changed to '%s' from '%s'" % (value, option, new_value, current_value )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionTypeEnumValueIsAlreadySet( AqlException ):
  def   __init__( self, option, value, new_value ):
    msg = "Value '%s' of Enum Option '%s' can't be changed to alias to '%s'" % (value, option, new_value )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionTypeUnableConvertValue( TypeError ):
  def   __init__( self, value_type, value ):
    msg = "Unable to convert value '%s(%s)' to type '%s'" % (value, type(value), value_type)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionTypeNoEnumValues( TypeError ):
  def   __init__( self, option_type ):
    msg = "Enum option type '%s' doesn't have any values: '%s'" % str(option_type)
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   autoOptionType( value ):
  
  if isinstance( value, (UniqueList, list, tuple) ):
    value_type = str
    if value:
      try:
        value_type = type(value[0])
      except IndexError:
        pass
    
    return ListOptionType( value_type = value_type )
  
  #//-------------------------------------------------------//
  
  if isinstance( value, dict ):
    return DictOptionType()
  
  if isinstance( value, bool ):
    return BoolOptionType()
  
  return OptionType( value_type = type(value) )


#//===========================================================================//

class   OptionType (object):

  __slots__ = (
    'value_type',
    'description',
    'group',
    'range_help',
  )
  
  #//-------------------------------------------------------//
  
  def     __init__( self, value_type = str, description = None, group = None, range_help = None ):
    
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
      raise ErrorOptionTypeUnableConvertValue( self.value_type, value )
  
  def   toStr( self, value ):
    """
    Converts a value to options' value string
    """
    return str( value )
  
  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    """
    Returns a description (list of strings) about range of allowed values
    """
    if self.range_help:
      return list(toSequence( self.range_help ))
    
    return ["Value of type '%s'" % self.value_type.__name__]

#//===========================================================================//
#//===========================================================================//

class   StrOptionType (OptionType):
  def     __init__( self, ignore_case = False, description = None, group = None, range_help = None ):
    value_type = IgnoreCaseString if ignore_case else str
    super(StrOptionType, self).__init__( value_type, description, group, range_help )

#//===========================================================================//
#//===========================================================================//

class   VersionOptionType (OptionType):
  def     __init__( self, description = None, group = None, range_help = None ):
    super(VersionOptionType, self).__init__( Version, description, group, range_help )

#//===========================================================================//
#//===========================================================================//

class   PathOptionType (OptionType):
  def     __init__( self, description = None, group = None, range_help = None ):
    super(PathOptionType, self).__init__( FilePath, description, group, range_help )

#//===========================================================================//
#//===========================================================================//

class   BoolOptionType (OptionType):
  
  __slots__ = (
    'true_value',
    'false_value',
    'true_values',
    'false_values',
    'aliases',
    'default',
  )
  
  #//-------------------------------------------------------//
  
  __true_values = ('yes', 'true', 'on', 'enabled', 'y', '1', 't' )
  __false_values = ('no', 'false', 'off', 'disabled', 'n', '0', 'f' )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, description = None, group = None, style = None, true_values = None, false_values = None, default = False ):
    
    #noinspection PyTypeChecker
    super(BoolOptionType,self).__init__( bool, description, group )
    
    if style is None:
      style = ('True', 'False')
    else:
      style = map(IgnoreCaseString, style)
    
    if true_values is None:
      true_values = self.__true_values
    else:
      true_values = toSequence( true_values )
    
    if false_values is None:
      false_values = self.__false_values
    else:
      false_values = toSequence( false_values )
    
    self.true_value, self.false_value = style
    self.true_values  = set()
    self.false_values = set()
    self.default = default
    
    self.addValues( true_values, false_values )
    self.addValues( self.true_value, self.false_value )
  
  #//-------------------------------------------------------//
  
  def   __call__( self, value = NotImplemented ):
    
    if type(value) is bool:
      return value
    
    if value is NotImplemented:
      value = self.default
    
    value_str = IgnoreCaseString(value)
    if value_str in self.true_values:
      return True
    
    if value_str in self.false_values:
      return  False
    
    return True if value else False
  
  #//-------------------------------------------------------//
  
  def   toStr( self, value ):
    return self.true_value if value else self.false_value
  
  #//-------------------------------------------------------//
  
  def   addValues( self, true_values, false_values ):
    true_values = toSequence( true_values )
    false_values = toSequence( false_values )
    
    self.true_values.update( map( lambda v: IgnoreCaseString(v),  true_values  ) )
    self.false_values.update( map( lambda v: IgnoreCaseString(v), false_values  ) )
  
  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    return  [ ', '.join( sorted( self.true_values ) ),
              ', '.join( sorted( self.false_values ) ) ]

#//===========================================================================//
#//===========================================================================//

class   EnumOptionType (OptionType):
  
  __slots__ = (
    '__values',
    '__default',
  )
  
  def   __init__( self, values, description = None, group = None, value_type = IgnoreCaseString, default = NotImplemented ):
    
    super(EnumOptionType,self).__init__( value_type, description, group )
    
    self.__values = {}
    
    if default is not NotImplemented:
      self.addValues( default )
      self.__default = value_type( default )
    else:
      self.__default = NotImplemented
    
    self.addValues( values )
  
  #//-------------------------------------------------------//
  
  def   addValues( self, values ):
    try:
      values = tuple( values.items() )  # convert dictionary to a sequence
    except AttributeError:
      pass
    
    set_default_value = self.__values.setdefault
    value_type = self.value_type
    
    for value in toSequence(values):
      
      it = iter( toSequence( value ) )
      
      value = value_type( next( it ) )
      
      value = set_default_value( value, value )
      
      for alias in it:
        alias = value_type(alias)
        
        v = set_default_value( alias, value )
        if v != value:
          if alias == v:
            raise ErrorOptionTypeEnumValueIsAlreadySet( self, alias, value )
          else:
            raise ErrorOptionTypeEnumAliasIsAlreadySet( self, alias, v, value )
  
  #//-------------------------------------------------------//
  
  def   __call__( self, value = NotImplemented ):
    
    try:
      if value is NotImplemented:
        value = self.__default
        if value is not NotImplemented:
          return value
        
        try:
          value = next(iter(self.__values.values()))
          return value
        except StopIteration:
          raise ErrorOptionTypeNoEnumValues( self )
      
      value = self.__values[ self.value_type( value ) ]
      return value
      
    except (KeyError, TypeError):
      raise ErrorOptionTypeUnableConvertValue( self, value )
  
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
  
  def   range( self ):
    values = []
    
    for alias, value in self.__values.items():
      if alias is value:
        values.append( alias )
    
    return values

#//===========================================================================//
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class   RangeOptionType (OptionType):
  
  __slots__ = (
    'min_value',
    'max_value',
    'auto_correct',
  )

  def   __init__( self, min_value, max_value, description = None, group = None, value_type = int, auto_correct = True ):
    
    #noinspection PyTypeChecker
    super(RangeOptionType,self).__init__( value_type, description, group )
    
    self.setRange( min_value, max_value, auto_correct )
  
  #//-------------------------------------------------------//
  
  def   setRange( self, min_value, max_value, auto_correct = True ):
    
    if min_value is not None:
      try:
        min_value = self.value_type( min_value )
      except (TypeError, ValueError):
        raise ErrorOptionTypeUnableConvertValue( self.value_type, min_value )
    else:
      min_value = self.value_type()
      
    if max_value is not None:
      try:
        max_value = self.value_type( max_value )
      except (TypeError, ValueError):
        raise ErrorOptionTypeUnableConvertValue( self.value_type, max_value )
    else:
      max_value = self.value_type()
    
    self.min_value = min_value
    self.max_value = max_value
    
    if auto_correct is not None:
      self.auto_correct = auto_correct
    
  #//-------------------------------------------------------//
  
  def   __call__( self, value = NotImplemented):
    try:
      min_value = self.min_value
      
      if value is NotImplemented:
        return min_value
      
      value = self.value_type( value )
      
      if value < min_value:
        if self.auto_correct:
          value = min_value
        else:
          raise TypeError()
      
      max_value = self.max_value
      
      if value > max_value:
        if self.auto_correct:
          value = max_value
        else:
          raise TypeError()
      
      return value
    
    except TypeError:
      raise ErrorOptionTypeUnableConvertValue( self.value_type, value )
  
  #//-------------------------------------------------------//
  
  def   rangeHelp(self):
    return ["%s ... %s" % (self.min_value, self.max_value) ]
  
  #//-------------------------------------------------------//
  
  def   range( self ):
    return [self.min_value, self.max_value]

#//===========================================================================//
#//===========================================================================//

class   ListOptionType (OptionType):
  
  __slots__ = ('item_type',)
  
  #//=======================================================//
  
  def   __init__( self, value_type = str, unique = False, separators = ', ', description = None, group = None, range_help = None ):
    
    if isinstance(value_type, OptionType):
      if description is None:
        description = value_type.description
        if description:
          description = "List of: " + description
      
      if group is None:
        group = value_type.group
      
      if range_help is None:
        range_help = value_type.range_help
    
    if unique:
      list_type = UniqueList
    else:
      list_type = List
    
    list_type = ValueListType( list_type, value_type )
    
    if separators:
      list_type = SplitListType( list_type, separators )
    
    super(ListOptionType,self).__init__( list_type, description, group, range_help )
    self.item_type = value_type
  
  #//-------------------------------------------------------//
  
  def   __call__( self, values = None ):
    try:
      if values is NotImplemented:
        values = []
      
      return self.value_type( values )
      
    except (TypeError, ValueError):
      raise ErrorOptionTypeUnableConvertValue( self.value_type, values )

  #//-------------------------------------------------------//
  
  def     rangeHelp( self ):
    
    if self.range_help:
      return list(toSequence( self.range_help ))
    
    if isinstance(self.item_type, OptionType):
      return self.item_type.rangeHelp()
    
    return ["List of type '%s'" % self.item_type.__name__]

#//===========================================================================//

class   DictOptionType (OptionType):
  
  #//=======================================================//
  
  def   __init__( self, key_type = str, value_type = None, separators = ', ', description = None, group = None, range_help = None ):
    
    if isinstance(value_type, OptionType):
      if description is None:
        description = value_type.description
        if description:
          description = "List of: " + description
      
      if group is None:
        group = value_type.group
      
      if range_help is None:
        range_help = value_type.range_help
    
    dict_type = ValueDictType( Dict, key_type, value_type )
    
    if separators:
      dict_type = SplitDictType( dict_type, separators )
    
    super(DictOptionType,self).__init__( dict_type, description, group, range_help )
  
  #//-------------------------------------------------------//
  
  def   setValueType( self, key, value_type ):
    if isinstance( value_type, OptionType ):
      value_type = value_type.value_type
    self.value_type.setValueType( key, value_type )
  
  #//-------------------------------------------------------//
  
  def   __call__( self, values = None ):
    try:
      if values is NotImplemented:
        values = None
      
      return self.value_type( values )
      
    except (TypeError, ValueError):
      raise ErrorOptionTypeUnableConvertValue( self.value_type, values )

  #//-------------------------------------------------------//
  
  def   rangeHelp( self ):
    if self.range_help:
      return list(toSequence( self.range_help ))
    
    return ["Dictionary of values"]
