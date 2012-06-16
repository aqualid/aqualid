import operator

from aql_utils import toSequence
from aql_list_types import UniqueList, List


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

def   _setOperator( dest_value, value ):
  return value

def   _doAction( options, context, dest_value, op, value ):
  if isinstance( value, OptionValue ):
    value = value.value( options, context )
  return op( dest_value, value )

def   SetValue( value, operation = None ):
  return Operation( operation, _doAction, _setOperator, value )

def   AddValue( value, operation = None ):
  return Operation( operation, _doAction, operator.iadd, value )

def   SubValue( value, operation = None ):
  return Operation( operation, _doAction, operator.isub, value )

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
