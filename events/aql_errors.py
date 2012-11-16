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


#~ class   UnknownSourceValueType (Exception):
  #~ def   __init__( self, source ):
    #~ msg = "Error: Unable to convert source '%s(%s)' to a value " % (str(source), type(source))
    #~ super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

#~ class   UnknownNodeDependencyType (Exception):
  #~ def   __init__( self, node, dep ):
    #~ msg = "Internal error: Unable to add unknown dependency type '%s' to node '%s'" % (type(dep), str(node))
    #~ super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

#~ class   UnknownAttribute (AttributeError):
  #~ def   __init__( self, obj, attr ):
    #~ msg = "Internal error: Invalid attribute '%s' of object %s (%s)" % (str(attr), str(type(obj)), str(obj))
    #~ super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

#//-------------------------------------------------------//

#~ class   NodeAlreadyExists ( Exception ):
  #~ def   __init__( self, node ):
    #~ msg = "Multiple instances of node: %s" % str(node)
    #~ super(type(self), self).__init__( msg )

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

class   BuildError( Exception ):
  def   __init__( self, out, err ):
    msg = "Build error: '%s'" % str(err)
    super(type(self), self).__init__( msg )

#//-------------------------------------------------------//

class   ProgramNotFound( Exception ):
  def   __init__( self, program, env ):
    msg = "Program '%s' has not been found" % str(program)
    super(type(self), self).__init__( msg )
