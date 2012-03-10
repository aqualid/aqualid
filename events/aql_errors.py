
class   UnknownNodeSourceType (Exception):
  def   __init__( self, node, source ):
    msg = "Internal error: Unable to add unknown source type '%s' to node '%s'" % (type(source), str(node))
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   UnknownNodeDependencyType (Exception):
  def   __init__( self, node, dep ):
    msg = "Internal error: Unable to add unknown dependency type '%s' to node '%s'" % (type(dep), str(node))
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   UnknownAttribute (AttributeError):
  def   __init__( self, obj, attr ):
    msg = "Internal error: Invalid attribute '%s' of object %s (%s)" % (str(attr), str(type(obj)), str(obj))
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   NodeHasCyclicDependency (Exception):
  def   __init__( self, node ):
    msg = "Node has a cyclic dependency: %s" % str(node)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   UnknownNode (Exception):
  def   __init__( self, node ):
    msg = "Unknown node: : %s" % str(node)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   NodeAlreadyExists ( Exception ):
  def   __init__( self, node ):
    msg = "Multiple instances of node: %s" % str(node)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   RemovingNonTailNode ( Exception ):
  def   __init__( self, node ):
    msg = "Removing non-tail node: %s" % str(node)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   UnpickleableValue ( Exception ):
  def   __init__( self, value ):
    msg = "Value '%s' can't be serialized." % type(value).__name__ 
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   InvalidHandlerMethodArgs ( Exception ):
  def   __init__( self, method ):
    msg = "Invalid arguments of handler method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   InvalidBuilderResults( Exception ):
  def   __init__( self, node, values ):
    msg = "Invalid node (%s) builder results: %s" % (node, values )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   EnumOptionAliasIsAlreadySet( Exception ):
  def   __init__( self, option, value, current_value, new_value ):
    msg = "Alias '%s' of Enum Option '%s' can't be changed to '%s' from '%s'" % (value, option, new_value, current_value )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   EnumOptionValueIsAlreadySet( Exception ):
  def   __init__( self, option, value, new_value ):
    msg = "Value '%s' of Enum Option '%s' can't be changed to alias to '%s'" % (value, option, new_value )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   EnumOptionInvalidValue( Exception ):
  def   __init__( self, option, value ):
    msg = "Invalid value '%s' for Enum Option '%s'" % (value, option )
    super(type(self), self).__init__( msg )
