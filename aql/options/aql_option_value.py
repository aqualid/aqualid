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
  'Condition', 'Operation', 'InplaceOperation', 'ConditionalValue', 'OptionValue', 'SimpleOperation', 'SimpleInplaceOperation',
  'SetValue', 'iAddValue', 'iSubValue', 'iUpdateValue',
  'ErrorOptionValueMergeNonOptionValue'
)

import operator

from aql.util_types import toSequence, UniqueList, Dict

#//===========================================================================//

class   ErrorOptionValueMergeNonOptionValue( TypeError ):
  def   __init__( self, value ):
    msg = "Unable to merge option value with non option value: '%s'" % (type(value),)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionValueOperationFailed( TypeError ):
  def   __init__( self, op, args, kw, err ):
    
    args_str = ""
    if args:
      args_str += ', '.join( map( str, args ) )
    
    if kw:
      if args_str:
        args_str += ","
      args_str += str( kw )
    
    msg = "Operation %s( %s ) failed with error: %s" % (op, args_str, err)
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   _setOperator( dest_value, value ):
  return value

def   _iAddKeyOperator( dest_value, key, value ):
  dest_value[key] += value
  return dest_value

def   _iSubKeyOperator( dest_value, key, value ):
  dest_value[key] -= value
  return dest_value

#//===========================================================================//

def   _updateOperator( dest_value, value ):
  if isinstance( dest_value, (UniqueList, list) ):
    dest_value += value
    return dest_value
  elif isinstance( dest_value, Dict ):
    dest_value.update( value )
    return dest_value
  else:
    return value

#//===========================================================================//

def   SetValue( value ):
  return SimpleInplaceOperation( _setOperator, value )

def   SetKey( key, value ):
  return SimpleInplaceOperation( operator.setitem, key, value )

def   GetKey( value, key ):
  return SimpleOperation( operator.getitem, value, key )

def   iAddValue( value ):
  return SimpleInplaceOperation( operator.iadd, value )

def   iAddKey( key, value ):
  return SimpleInplaceOperation( _iAddKeyOperator, key, value )

def   iSubKey( key, value ):
  return SimpleInplaceOperation( _iSubKeyOperator, key, value )

def   iSubValue( value ):
  return SimpleInplaceOperation( operator.isub, value )

def   iUpdateValue( value ):
  return SimpleInplaceOperation( _updateOperator, value )

#//===========================================================================//

def   _convertArgs( args, kw, options, converter ):
  tmp_args = []
  for arg in args:
    if isinstance( arg, Operation ):
      arg.convert( options, converter )
    else:
      arg = converter( options, arg )
    
    tmp_args.append( arg )
  
  tmp_kw = {}
  for key,arg in kw.items():
    if isinstance( arg, Operation ):
      arg.convert( options, converter )
    elif converter is not None:
      arg = converter( options, arg )
    
    tmp_kw[ key ] = arg
  
  return tmp_args, tmp_kw

#//===========================================================================//

def   _unconvertArgs( args, kw, options, context, unconverter ):
  
  tmp_args = []
  for arg in args:
    if isinstance( arg, Operation ):
      arg = arg( options, context, unconverter )
    elif unconverter is not None:
      arg = unconverter( options, context, arg )
    
    tmp_args.append( arg )
  
  tmp_kw = {}
  for key,arg in kw.items():
    if isinstance( arg, Operation ):
      arg = arg( options, context, unconverter )
    elif unconverter is not None:
      arg = unconverter( options, context, arg )
    
    tmp_kw[ key ] = arg
  
  return tmp_args, tmp_kw

#//===========================================================================//

class   Condition(object):
  
  __slots__ = (
    'condition',
    'predicate',
    'args',
    'kw',
  )
  
  def   __init__( self, condition, predicate, *args, **kw ):
    self.condition = condition
    self.predicate = predicate
    self.args = args
    self.kw = kw
  
  #//-------------------------------------------------------//
  
  def   convert(self, options, converter ):
    self.args, self.kw = _convertArgs( self.args, self.kw, options, converter )
    
    cond = self.condition
    if cond is not None:
      cond.convert( options, converter )
  
  #//-------------------------------------------------------//
  
  def   __call__( self, options, context, unconverter ):
    if self.condition is not None:
      if not self.condition( options, context, unconverter ):
        return False
    
    args, kw = _unconvertArgs( self.args, self.kw, options, context, unconverter )
    
    return self.predicate( options, context, *args, **kw )

#//===========================================================================//

class   Operation( object ):
  __slots__ = (
    'action',
    'kw',
    'args',
  )
  
  def   __init__( self, action, *args, **kw ):
    self.action = action
    self.args = args
    self.kw = kw
  
  #//-------------------------------------------------------//
  
  def   convert( self, options, converter ):
    self.args, self.kw = _convertArgs( self.args, self.kw, options, converter )
  
  #//-------------------------------------------------------//
  
  def   _callAction(self, options, context, args, kw ):
    return self.action( options, context, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   __call__( self, options, context, unconverter ):
    args, kw = _unconvertArgs( self.args, self.kw, options, context, unconverter )
    
    try:
      result = self._callAction( options, context, args, kw )
    except Exception as ex:
      raise ErrorOptionValueOperationFailed( self.action, args, kw, ex )
    
    return result

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

#//===========================================================================//

class SimpleOperation( Operation ):
  def   _callAction(self, options, context, args, kw ):
    return self.action( *args, **kw )

#//===========================================================================//

class   InplaceOperation( object ):
  __slots__ = (
    'action',
    'kw',
    'args',
  )
  
  def   __init__( self, action, *args, **kw ):
    
    self.action = action
    self.args = args
    self.kw = kw
  
  def   convert(self, options, converter ):
    self.args, self.kw = _convertArgs( self.args, self.kw, options, converter )
      
  def   _callAction(self, options, context, dest_value, args, kw ):
    return self.action( options, context, dest_value, *args, **kw )
  
  def   __call__( self, options, context, dest_value, value_type, unconverter ):
    if self.action is None:
      return dest_value
    
    args, kw = _unconvertArgs( self.args, self.kw, options, context, unconverter )
    
    try:
      result = self._callAction( options, context, dest_value, args, kw )
    except Exception as ex:
      raise ErrorOptionValueOperationFailed( self.action, args, kw, ex )
    
    if result is None:
      result = dest_value
    
    dest_value = value_type( result )
    return dest_value

#//===========================================================================//

class SimpleInplaceOperation( InplaceOperation ):
  def   _callAction(self, options, context, dest_value, args, kw ):
    return self.action( dest_value, *args, **kw )

#//===========================================================================//

class   ConditionalValue (object):
  
  __slots__ = (
    'ioperation',
    'condition',
  )
  
  def   __init__( self, ioperation, condition = None ):
    self.ioperation  = ioperation
    self.condition  = condition
  
  #//-------------------------------------------------------//
  
  def   convert(self, options, converter ):
    condition = self.condition
    if isinstance( condition, Condition ):
      condition.convert( options, converter )
    
    ioperation = self.ioperation
    if isinstance( ioperation, InplaceOperation ):
      ioperation.convert( options, converter )
  
  #//-------------------------------------------------------//
  
  def   evaluate( self, value, value_type, options, context, unconverter ):
    condition = self.condition
    if (condition is None) or condition( options, context, unconverter ):
      if self.ioperation is not None:
        value = self.ioperation( options, context, value, value_type, unconverter )
    
    return value

#//===========================================================================//

class OptionValue (object):
  
  __slots__ = (
    'option_type',
    'conditional_values',
  )
  
  def   __init__( self, option_type, conditional_values = None ):
    self.option_type = option_type
    self.conditional_values = list( toSequence(conditional_values) )
  
  #//-------------------------------------------------------//
  
  def   isSet( self ):
    return bool(self.conditional_values)
  
  #//-------------------------------------------------------//
  
  def   isToolKey( self ):
    return self.option_type.is_tool_key
  
  #//-------------------------------------------------------//
  
  def   appendValue( self, conditional_value ):
    self.conditional_values.append( conditional_value )
  
  #//-------------------------------------------------------//
  
  def   prependValue( self, conditional_value ):
    self.conditional_values[:0] = [ conditional_value ]
  
  #//-------------------------------------------------------//
  
  def   merge( self, other ):
    if self is other:
      return
    
    if not isinstance( other, OptionValue ):
      raise ErrorOptionValueMergeNonOptionValue( other )
    
    values = self.conditional_values
    other_values = other.conditional_values
    
    diff_index = 0
    for value1, value2 in zip( values, other_values ):
      if value1 is not value2:
        break
      
      diff_index += 1
    
    if self.option_type.is_auto and not other.option_type.is_auto:
      self.option_type = other.option_type
    
    self.conditional_values += other_values[ diff_index: ]
    
  #//-------------------------------------------------------//
  
  def   reset( self ):
    self.conditional_values = []
  
  #//-------------------------------------------------------//
  
  def   copy( self ):
    return OptionValue( self.option_type, self.conditional_values )
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    return self.copy()
  
  #//-------------------------------------------------------//
  
  def   get( self, options, context, evaluator = None ):
    
    if context is None:
      context = {}
    else:
      try:
        return context[ self ]
      except KeyError:
        pass
    
    value_type = self.option_type
    
    value = value_type()
    context[ self ] = value
    
    for conditional_value in self.conditional_values:
      value = conditional_value.evaluate( value, value_type, options, context, evaluator )
      context[ self ] = value
    
    return value
