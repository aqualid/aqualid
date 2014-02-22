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
  'Condition', 'Operation', 'ConditionalValue', 'OptionValue', 'SimpleOperation',
  'SetValue', 'AddValue', 'SubValue', 'UpdateValue', 'NotValue', 'TruthValue', 'JoinPathValue',
  'ErrorOptionValueMergeNonOptionValue'
)

import os.path
import operator

from aql.util_types import toSequence, UniqueList, List, Dict, DictItem

#//===========================================================================//

class   ErrorOptionValueMergeNonOptionValue( TypeError ):
  def   __init__( self, value ):
    msg = "Unable to merge option value with non option value: '%s'" % str(type(value))
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   _setOperator( options, context, dest_value, value ):
  if isinstance( dest_value, Dict ) and isinstance( value, DictItem ):
    dest_value.update( value )
    return dest_value
  return value

def   _joinPath( options, context, dest_value, value ):
  return os.path.join( dest_value, value )

def   _absPath( options, context, dest_value, value ):
  return os.path.abspath( value )

def   _notOperator( options, context, dest_value, value ):
  return not value

def   _truthOperator( options, context, dest_value, value ):
  return bool(value)

def   _updateOperator( options, context, dest_value, value ):
  if isinstance( dest_value, (UniqueList, List) ):
    dest_value += value
    return dest_value
  elif isinstance( dest_value, Dict ):
    dest_value.update( value )
    return dest_value
  else:
    return value

#noinspection PyUnusedLocal
def   _simpleAction( options, context, dest_value, action, *args, **kw ):
  return action( dest_value, *args, **kw )

def   SimpleOperation( action, *args, **kw ):
  return Operation( None, _simpleAction, action, *args, **kw )

def   SetValue( value, operation = None ):
  return Operation( operation, _setOperator, value )

def   AddValue( value, operation = None ):
  return Operation( operation, _simpleAction, operator.iadd, value )

def   SubValue( value, operation = None ):
  return Operation( operation, _simpleAction, operator.isub, value )

def   JoinPathValue( value, operation = None ):
  return Operation( operation, _joinPath, value )

def   AbsPathValue( operation = None ):
  return Operation( operation, _absPath, None )

def   UpdateValue( value, operation = None ):
  return Operation( operation, _updateOperator, value )

def   NotValue( value, operation = None ):
  return Operation( operation, _notOperator, value )

def   TruthValue( value, operation = None ):
  return Operation( operation, _truthOperator, value )

#//===========================================================================//

def   _convertArgs( args, kw, options, convertor ):
  if convertor is not None:
    args = tuple( convertor(options, arg ) for arg in args )
    kw = dict( (key, convertor(options, value)) for key, value in kw.items() )
  
  return args, kw

def   _unconvertArgs( args, kw, options, context, unconvertor ):
  if unconvertor is not None:
    args = tuple( unconvertor(options, context, arg ) for arg in args )
    kw = dict( (key, unconvertor(options, context, value)) for key, value in kw.items() )
  
  return args, kw

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
  
  def   convert(self, options, convertor ):
    self.args, self.kw = _convertArgs( self.args, self.kw, options, convertor )
    
    cond = self.condition
    if cond is not None:
      cond.convert( options, convertor )
  
  #//-------------------------------------------------------//
  
  def   __call__( self, options, context, unconvertor ):
    if self.condition is not None:
      if not self.condition( options, context ):
        return False
    
    args, kw = _unconvertArgs( self.args, self.kw, options, context, unconvertor )
    
    return self.predicate( options, context, *args, **kw )

#//===========================================================================//

class   Operation( object ):
  __slots__ = (
    'action',
    'kw',
    'args',
    'operation'
  )
  
  def   __init__( self, operation, action, *args, **kw ):
    
    self.operation = operation
    self.action = action
    self.args = args
    self.kw = kw
  
  def   convert(self, options, convertor ):
    self.args, self.kw = _convertArgs( self.args, self.kw, options, convertor )
    
    op = self.operation
    if op is not None:
      op.convert( options, convertor )
  
  def   __call__( self, options, context, dest_value, value_type, unconvertor ):
    if self.operation is not None:
      dest_value = self.operation( options, context, dest_value, value_type, unconvertor )
    
    if self.action is None:
      return dest_value
    
    args, kw = _unconvertArgs( self.args, self.kw, options, context, unconvertor )
    
    dest_value = self.action( options, context, dest_value, *args, **kw )
    dest_value = value_type( dest_value )
    return dest_value

#//===========================================================================//

class   ConditionalValue (object):
  
  __slots__ = (
    'operation',
    'condition',
  )
  
  def   __init__( self, operation, condition = None ):
    self.operation  = operation
    self.condition  = condition
  
  #//-------------------------------------------------------//
  
  def   convert(self, options, convertor ):
    condition = self.condition
    if isinstance( condition, Condition ):
      condition.convert( options, convertor )
    
    operation = self.operation
    if isinstance( operation, Operation ):
      operation.convert( options, convertor )
  
  #//-------------------------------------------------------//
  
  def   evaluate( self, value, value_type, options, context, unconvertor ):
    condition = self.condition
    if (condition is None) or condition( options, context, unconvertor ):
      if self.operation is not None:
        value = self.operation( options, context, value, value_type, unconvertor )
    
    return value

#//===========================================================================//

class OptionValue (object):
  
  __slots__ = (
    'option_type',
    'default_conditional_value',
    'conditional_values',
  )
  
  def   __init__( self, option_type, default_conditional_value = None, conditional_values = None ):
    self.option_type = option_type
    self.default_conditional_value = default_conditional_value
    self.conditional_values = list( toSequence(conditional_values) )
  
  #//-------------------------------------------------------//
  
  def   isSet( self ):
    return bool(self.conditional_values)
  
  #//-------------------------------------------------------//
  
  def   setDefault( self, conditional_value ):
    self.default_conditional_value = conditional_value
  
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
    
    self.option_type = other.option_type
    
    diff_index = 0
    for conditional_value1, conditional_value2 in zip( self.conditional_values, other.conditional_values ):
      if conditional_value1 is not conditional_value2:
        break
      
      diff_index += 1
    
    self.default_conditional_value = other.default_conditional_value
    
    self.conditional_values += other.conditional_values[ diff_index: ]
    
  #//-------------------------------------------------------//
  
  def   reset( self ):
    self.conditional_values = []
  
  #//-------------------------------------------------------//
  
  def   copy( self ):
    return OptionValue( self.option_type, self.default_conditional_value, self.conditional_values )
  
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
    
    if (not self.conditional_values) and (self.default_conditional_value is not None):
        value = self.default_conditional_value.evaluate( value, value_type, options, context, evaluator )
        context[ self ] = value
        return value
    
    for conditional_value in self.conditional_values:
      value = conditional_value.evaluate( value, value_type, options, context, evaluator )
      context[ self ] = value
    
    return value
