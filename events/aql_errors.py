
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
