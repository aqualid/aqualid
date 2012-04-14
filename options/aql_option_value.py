from aql_utils import toSequence
from aql_option_types import OptionType, ListOptionType


#//===========================================================================//

class   OptionCondition(object):
  
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

class   ValueOperation( object ):
  __slots__ = (
    'value',
    'operation'
  )
  
  def   __init__( self, value, operation = None ):
    self.value = value
    self.operation = operation
  
  def   __call__( self, dest_value, options, context ):
    if self.operation is not None:
      dest_value = self.operation( dest_value, options, context )
    
    return self._exec( dest_value, options, context )
  
  def   _exec( self, dest_value ):
    raise NotImplementedError()

#//===========================================================================//

class   AddValue( ValueOperation ):
  def   _exec( self, dest_value, options, context ):
    dest_value += self.value
    return dest_value

#//===========================================================================//

class   SubValue( ValueOperation ):
  def   _exec( self, dest_value, options, context ):
    dest_value -= self.value
    return dest_value

#//===========================================================================//

class   CallValue( ValueOperation ):
  def   _exec( self, dest_value, options, context ):
    return self.value( dest_value )

#//===========================================================================//

class   ValueValue( ValueOperation ):
  def   _exec( self, dest_value, options, context ):
    return dest_value.value( options, context )

#//===========================================================================//

class   OptionConditionalValue (object):
  
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
  
