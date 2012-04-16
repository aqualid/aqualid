from aql_utils import toSequence
from aql_option_types import OptionType, ListOptionType


#//===========================================================================//

class   Condition(object):
  
  __slots__ = (
    'predicate',
    'args',
    'kw',
  )
  
  def   __init__( self, predicate, *args, **kw ):
    self.predicate = predicate
    self.args = args
    self.kw = kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, options, context ):
    return self.predicate( options, context, *self.args, **self.kw )

#//===========================================================================//

class   OperationValue( object ):
  __slots__ = (
    'value',
  )
  
  def   __init__( self, value ):
    self.value = value
  
  def   __call__( self, options, context ):
    return self.value

#//===========================================================================//

class   OperationOptionValue( OperationValue ):
  def   __call__( self, options, context ):
    return self.value.value( options, context )

#//===========================================================================//

class   Operation( object ):
  __slots__ = (
    'value',
    'operation'
  )
  
  def   __init__( self, value, operation = None ):
    if not isinstance( value, OperationValue):
      value = OperationValue( value )
    
    self.value = value
    self.operation = operation
  
  def   __call__( self, dest_value, options, context ):
    if self.operation is not None:
      dest_value = self.operation( dest_value, options, context )
    
    op_value = self.value( options, context )
    
    return self._exec( dest_value, op_value, options, context )
  
  def   _exec( self, dest_value, op_value, options, context ):
    raise NotImplementedError()

#//===========================================================================//

class   SetValue( Operation ):
  def   _exec( self, dest_value, op_value, options, context ):
    return op_value

#//===========================================================================//

class   AddValue( Operation ):
  def   _exec( self, dest_value, op_value, options, context ):
    dest_value += op_value
    return dest_value

#//===========================================================================//

class   SubValue( Operation ):
  def   _exec( self, dest_value, op_value, options, context ):
    dest_value -= op_value
    return dest_value

#//===========================================================================//

class   CallValue( Operation ):
  def   _exec( self, dest_value, op_value, options, context ):
    return op_value( dest_value )

#//===========================================================================//

class   ConditionalValue (object):
  
  __slots__ = (
    'operation',
    'conditions',
  )
  
  def   __init__( self, operation, conditions = None ):
    self.operation  = operation
    self.conditions = list(toSequence(conditions))
  
  #//-------------------------------------------------------//
  
  def   updateValue( self, value, options, context ):
    for condition in self.conditions:
      if not condition( options, context ):
        return value
    
    if self.operation is not None:
      return self.operation( value, options, context )
    
    return value

#//===========================================================================//

class OptionValue (object):
  
  __slots__ = (
    'option_type',
    'conditions',
  )
  
  def   __init__( self, option_type, conditional_values = None ):
    self.option_type = option_type
    self.conditions = list( toSequence(conditional_values) )
  
  #//-------------------------------------------------------//
  
  def   appendValue( self, conditional_value ):
    self.conditions.append( conditional_value )
  
  #//-------------------------------------------------------//
  
  def   prependValue( self, conditional_value ):
    self.conditions[:0] = [ conditional_value ]
  
  #//-------------------------------------------------------//
  
  def   copy( self ):
    return OptionType( self.option_type, self.conditions )
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    return self.copy()
  
  #//-------------------------------------------------------//
  
  def   value( self, options, context = None ):
    value = self.option_type()
    if context is None:
      context = {}
    
    for condition in self.conditions:
      context[ self ] = value
      value = condition.updateValue( value, options, context )
    
    return value

  #//-------------------------------------------------------//
  
  def   optionType():
    return self.option_type
  
