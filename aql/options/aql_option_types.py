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

"""
class Proxy(object):
    __slots__ = ["_obj", "__weakref__"]
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)
    
    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_obj"), name)
    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_obj"), name)
    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_obj"), name, value)
    
    def __nonzero__(self):
        return bool(object.__getattribute__(self, "_obj"))
    def __str__(self):
        return str(object.__getattribute__(self, "_obj"))
    def __repr__(self):
        return repr(object.__getattribute__(self, "_obj"))
    
    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__', 
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__', 
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__', 
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__', 
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__', 
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', 
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', 
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__', 
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', 
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__', 
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', 
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__', 
        '__truediv__', '__xor__', 'next',
    ]
    
    @classmethod
    def _create_class_proxy(cls, theclass):
        
        def make_method(name):
            def method(self, *args, **kw):
                return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)
            return method
        
        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
        return type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
    
    def __new__(cls, obj, *args, **kwargs):
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = theclass = cls._create_class_proxy(obj.__class__)
        ins = object.__new__(theclass)
        theclass.__init__(ins, obj, *args, **kwargs)
        return ins
"""


__all__ = (
  'OptionType', 'StrOptionType', 'VersionOptionType', 'PathOptionType', 'BoolOptionType', 
  'EnumOptionType', 'RangeOptionType', 'ListOptionType', 'DictOptionType',
  'ErrorOptionTypeEnumAliasIsAlreadySet', 'ErrorOptionTypeEnumValueIsAlreadySet',
  'ErrorOptionTypeUnableConvertValue', 'ErrorOptionTypeNoEnumValues', 
)


from aql.types import toSequence, IgnoreCaseString, Version, FilePath, UniqueList, List, SplitListType, ValueListType, Dict, SplitDictType, ValueDictType

#//===========================================================================//

class   ErrorOptionTypeEnumAliasIsAlreadySet( Exception ):
  def   __init__( self, option, value, current_value, new_value ):
    msg = "Alias '%s' of Enum Option '%s' can't be changed to '%s' from '%s'" % (value, option, new_value, current_value )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionTypeEnumValueIsAlreadySet( Exception ):
  def   __init__( self, option, value, new_value ):
    msg = "Value '%s' of Enum Option '%s' can't be changed to alias to '%s'" % (value, option, new_value )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionTypeUnableConvertValue( TypeError ):
  def   __init__( self, value_type, value ):
    msg = "Unable to convert value '%s' to type '%s'" % (value, value_type)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionTypeNoEnumValues( TypeError ):
  def   __init__( self, option_type ):
    msg = "Enum option type '%s' doesn't have any values: '%s'" % str(option_type)
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   _ValueTypeProxy( option_type, value_type ):
  
  class   _ValueTypeProxyImpl (object):
    
    __slots__ = ["_value", "__weakref__"]
    
    #//-------------------------------------------------------//
    
    def     __new__( cls, value = NotImplemented ):
      if type(value) is cls:
        return value
      
      value = value_type( option_type._convert( value ) )
      
      self = super(_ValueTypeProxyImpl,cls).__new__( cls )
      super(_ValueTypeProxyImpl, self).__setattr__( "_value", value )
      
      return self
    
    @staticmethod
    def   _getValue( self ):
      return super(_ValueTypeProxyImpl, self).__getattribute__("_value")
    
    def __getattribute__(self, name):
        return getattr(_ValueTypeProxyImpl._getValue( self ), name )
    
    def __delattr__(self, name):
        delattr( _ValueTypeProxyImpl._getValue( self ), name)
    
    def __setattr__(self, name, value):
        setattr(_ValueTypeProxyImpl._getValue( self ), name, value)
    
    def __bool__(self):
        return bool(_ValueTypeProxyImpl._getValue( self ))
    
    def __nonzero__(self):
        return bool(_ValueTypeProxyImpl._getValue( self ))
    
    def __str__(self):
        return option_type._convertToStr(_ValueTypeProxyImpl._getValue( self ))
    
    def __repr__(self):
        return repr(_ValueTypeProxyImpl._getValue( self ))
    
  #//=======================================================//
  
  special_methods = (
      '__call__', '__coerce__', '__hash__',
      '__hex__', '__oct__', '__index__',
      '__int__', '__float__', '__long__', '__complex__', '__round__',
      '__neg__', '__pos__', '__invert__', '__abs__', 
      '__iter__', '__len__', '__reversed__', '__setitem__', '__setslice__', '__next__',
      '__delitem__', '__delslice__', '__getitem__', '__getslice__', 
  )
  
  special_methods_2 = (
      '__add__',        '__iadd__',       '__radd__',
      '__sub__',        '__isub__',       '__rsub__',
      '__mul__',        '__imul__',       '__rmul__',
      '__mod__',        '__imod__',       '__rmod__',
      '__pow__',        '__ipow__',       '__rpow__',
      '__and__',        '__iand__',       '__rand__',
      '__xor__',        '__ixor__',       '__rxor__',
      '__or__',         '__ior__',        '__ror__',
      '__and__',        '__iand__',       '__rand__',
      '__truediv__',    '__itruediv__',   '__rtruediv__',
      '__div__',        '__idiv__',       '__rdiv__',
      '__floordiv__',   '__ifloordiv__',  '__rfloordiv__',
      '__lshift__',     '__ilshift__',    '__rlshift__',
      '__rshift__',     '__irshift__',    '__rrshift__',
      '__divmod__',     '__idivmod__',    '__rdivmod__',
  )
  
  cmp_methods = (
    '__cmp__','__eq__','__ne__','__gt__','__ge__','__lt__','__le__', '__contains__',
  )
  
  def make_method(name):
    def method(self, *args, **kw):
      return getattr( _ValueTypeProxyImpl._getValue( self ), name)(*args, **kw)
    return method
  
  def make_method_2(name):
    def method( self, other ):
      other = _ValueTypeProxyImpl( other )
      other = _ValueTypeProxyImpl._getValue( other )
      value = _ValueTypeProxyImpl._getValue( self )
      return _ValueTypeProxyImpl( getattr( value, name)( other ) )
      
    return method
  
  def make_method_cmp(name):
    def method(self, other ):
      other = _ValueTypeProxyImpl( other )
      other = _ValueTypeProxyImpl._getValue( other )
      value = _ValueTypeProxyImpl._getValue( self )
      return getattr( value, name)( other )
      
    return method
  
  value_type_methods = frozenset( dir(value_type) )
  
  for methods, proxy_method_maker in [  (special_methods,   make_method),
                                        (special_methods_2, make_method_2),
                                        (cmp_methods,       make_method_cmp), ]:
    
    methods = frozenset( methods ) & value_type_methods
    
    for name in methods:
      setattr( _ValueTypeProxyImpl, name, proxy_method_maker( name ) )
  
  return _ValueTypeProxyImpl

#//===========================================================================//

class   OptionType (object):

  __slots__ = (
    'value_type',
    'value_type_proxy',
    'description',
    'group',
    'range_help',
  )
  
  #//-------------------------------------------------------//
  
  def     __init__( self, value_type = str, description = None, group = None, range_help = None ):
    
    self.value_type = value_type
    
    self.value_type_proxy = _ValueTypeProxy( self, value_type )
    
    self.description = description
    self.group = group
    self.range_help = range_help
  
  #//-------------------------------------------------------//
  
  def   __call__( self, value = NotImplemented ):
    return self.value_type_proxy( value )
  
  #//-------------------------------------------------------//
  
  def   _convert( self, value ):
    """
    Converts a value to options' value
    """
    
    try:
      if value is NotImplemented:
        return self.value_type()
      
      return self.value_type( value )
    except (TypeError, ValueError):
      raise ErrorOptionTypeUnableConvertValue( self.value_type, value )
  
  def   _convertToStr( self, value ):
    """
    Converts a value to options' value string
    """
    return str( self._convert( value ))
  
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
  )
  
  #//-------------------------------------------------------//
  
  __true_values = ('yes', 'true', 'on', 'enabled', 'y', '1', 't' )
  __false_values = ('no', 'false', 'off', 'disabled', 'n', '0', 'f' )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, description = None, group = None, style = None, true_values = None, false_values = None ):
    
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
    
    self.addValues( true_values, false_values )
    self.addValues( self.true_value, self.false_value )
  
  #//-------------------------------------------------------//
  
  def   _convert( self, value = NotImplemented ):
    
    if value is NotImplemented:
      value = False
    
    value_str = IgnoreCaseString(value)
    if value_str in self.true_values:
      value = True
    
    if value_str in self.false_values:
      value =  False
    
    if value:
      value = True
    else:
      value = False
    
    return bool( value )
  
  #//-------------------------------------------------------//
  
  def   _convertToStr( self, value ):
    value = self._convert( value )
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
  
  def   _convert( self, value = NotImplemented ):
    try:
      if value is NotImplemented:
        value = self.__default
        if value is not NotImplemented:
          return value
        
        try:
          return next(iter(self.__values.values()))
        except StopIteration:
          raise ErrorOptionTypeNoEnumValues( self )
      
      return self.__values[ self.value_type( value ) ]
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

class   RangeOptionType (OptionType):
  
  __slots__ = (
    'min_value',
    'max_value',
    'auto_correct',
  )
  
  def   __init__( self, min_value, max_value, description = None, group = None, value_type = int, auto_correct = True ):
    
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
  
  def   _convert( self, value = NotImplemented):
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
  
  __slots__ = ('item_type')
  
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
    self.value_type_proxy = list_type
    self.item_type = value_type
  
  #//-------------------------------------------------------//
  
  def   __call__( self, values = None ):
    try:
      if values is NotImplemented:
        values = None
      
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
    
    self.value_types = {}
    
    dict_type = ValueDictType( Dict, key_type, value_type )
    
    if separators:
      dict_type = SplitDictType( dict_type, separators )
    
    super(DictOptionType,self).__init__( dict_type, description, group, range_help )
    self.value_type_proxy = dict_type
  
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
