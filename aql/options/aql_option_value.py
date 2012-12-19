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
  'ErrorOptionValueMergeDifferentOptionTypes'
)

import operator

from aql.utils import toSequence

#//===========================================================================//

class   ErrorOptionValueMergeDifferentOptionTypes( TypeError ):
  def   __init__( self, type1, type2 ):
    msg = "Unable to merge option values of different types: '%s'" % (type1, type2)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorOptionValueMergeNonOptionValue( TypeError ):
  def   __init__( self, value ):
    msg = "Unable to merge option value with non option value: '%s'" % str(type(value))
    super(type(self), self).__init__( msg )

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
  
  def   __call__( self, options, context ):
    if self.condition is not None:
      if not self.condition( options, context ):
        return False
    
    return self.predicate( options, context, *self.args, **self.kw )

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
  
  def   __call__( self, options, context, dest_value ):
    if self.operation is not None:
      dest_value = self.operation( options, context, dest_value )
    
    if self.action is None:
      return dest_value
    
    return self.action( options, context, dest_value, *self.args, **self.kw )

#//===========================================================================//

def   _simpleAction( options, context, dest_value, action, *args, **kw ):
  return action( dest_value, *args, **kw )

def   SimpleOperation( action, *args, **kw ):
  return Operation( None, _simpleAction, action, *args, **kw )

#//===========================================================================//

class   ConditionalValue (object):
  
  __slots__ = (
    'operation',
    'condition',
  )
  
  def   __init__( self, operation, condition = None ):
    self.operation  = operation
    self.condition = condition
  
  #//-------------------------------------------------------//
  
  def   updateValue( self, value, options, context ):
    condition = self.condition
    if (condition is None) or condition( options, context ):
      if self.operation is not None:
        new_value = self.operation( options, context, value )
        value_type = type(value)
        if type(new_value) is not value_type:
          new_value = value_type( new_value )
        
        return new_value
    
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
    
    if self.option_type is not other.option_type:
      raise ErrorOptionValueMergeDifferentOptionTypes( self.option_type, other.option_type )
    
    self.conditional_values += other.conditional_values
    
  #//-------------------------------------------------------//
  
  def   copy( self ):
    return OptionValue( self.option_type, self.conditional_values )
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    return self.copy()
  
  #//-------------------------------------------------------//
  
  def   value( self, options, context = None ):
    
    value = self.option_type()
    
    if context is None:
      context = {}
    else:
      try:
        return context[ self ]
      except KeyError:
        pass
    
    context[ self ] = value
    
    for conditional_value in self.conditional_values:
      value = conditional_value.updateValue( value, options, context )
      context[ self ] = value
    
    return value

  #//-------------------------------------------------------//
  
  def   optionType( self ):
    return self.option_type
