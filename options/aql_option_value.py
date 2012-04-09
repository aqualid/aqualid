#~ from aql_utils import toSequence
#~ from aql_option_types import OptionType


#//===========================================================================//

class   OptionCondition(object):
  
  __slots__ = (
    'predicate',
    'args',
    'kw',
  )
  
  def   __init__( self, predicate, args, kw ):
    self.predicate = predicate
    self.args = args
    self.kw = kw
  
  #//-------------------------------------------------------//
  
  def   __call__( self, options, context ):
    return self.predicate( options, context, *self.args, **self.kw )

#//===========================================================================//

class   OptionConditionalValue (object):
  
  __slots__ = (
    'value',
    'operation',
    'conditions',
  )
  
  def   __init__( self, value, operation, conditions = None ):
    self.value      = value
    self.operation  = operation
    self.conditions = list(toSequence(conditions))
  
  #//-------------------------------------------------------//
  
  def   updateValue( self, value, options, context ):
    for condition in self.conditions:
      if not condition( options, context ):
        return
    
    if self.operation is not None:
      return self.operation( value, self.value )
    
    return None

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
  
  def   value( self, options ):
    value = self.option_type()
    context = {}
    
    for condition in self.conditions:
      context[ self ] = value
      value = condition.updateValue( value, options, context )
    
    return value

  #//-------------------------------------------------------//
  
  def   optionType():
    return self.option_type
  
