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

class   InvalidOptionValue( TypeError ):
  def   __init__( self, option, value ):
    msg = "Invalid option value: '%s', option type: '%s'" % (value, option )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   InvalidOptionType( TypeError ):
  def   __init__( self, option ):
    msg = "Invalid option type: '%s'" % (option, )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   InvalidOptionValueType( TypeError ):
  def   __init__( self, option ):
    msg = "Invalid option value type: '%s'" % (option, )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   ExistingOptionValue( TypeError ):
  def   __init__( self, name, value ):
    msg = "Can't create existing option value '%s' to '%s'" % (name, value)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   UnknownOptionType( TypeError ):
  def   __init__( self, name, value ):
    msg = "Unknown option type, attribute: %s, value: %s" % (name, value)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   ForeignOptionValue( TypeError ):
  def   __init__( self, name, value ):
    msg = "Option value is already attached to another options, attribute: %s, value: %s" % (name, value)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   InvalidOptions( TypeError ):
  def   __init__( self, options ):
    msg = "Invalid options: '%s'" % (options, )
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   InvalidSourceValueType( TypeError ):
  def   __init__( self, value ):
    msg = "Invalid source value type: '%s'(%s)" % (type(value), value)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   CommandExecFailed( Exception ):
  def   __init__( self, ex ):
    msg = "Execution failure: '%s'" % str(ex)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   BuildError( Exception ):
  def   __init__( self, msg ):
    msg = "Build error: '%s'" % str(msg)
    super(type(self), self).__init__( msg )
