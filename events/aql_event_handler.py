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


import traceback

from aql_logging import logInfo,logWarning,logError

#//===========================================================================//

info_events     = set()
debug_events    = set()
status_events   = set()
warning_events  = set()

def   _info( event_method ):    info_events.add( event_method.__name__ );     return event_method
def   _debug( event_method ):   debug_events.add( event_method.__name__ );    return event_method
def   _status( event_method ):  status_events.add( event_method.__name__ );   return event_method
def   _warning( event_method ): warning_events.add( event_method.__name__ );  return event_method

#//===========================================================================//

class EventHandler( object ):
  
  #//-------------------------------------------------------//
  @_warning
  def   eventDataFileIsNotSync( self, filename ):
    """
    Inconsistency state of Data file. Either internal error or external corruption.
    """
    logWarning("Internal error: DataFile '%s' is unsynchronized" % str(filename) )
  
  #//-------------------------------------------------------//
  @_warning
  def   eventDepValueIsCyclic( self, value ):
    logWarning("Internal error: Cyclic dependency value: %s" % value )
  
  #//-------------------------------------------------------//
  @_warning
  def   eventUnknownValue( self, value ):
    logWarning("Internal error: Unknown value: %s " % value )
  
  #//-------------------------------------------------------//
  
  @_info
  def   eventOutdatedNode( self, node ):
    """
    Node needs to be rebuilt.
    """
    logInfo("Outdated node: %s" % node )
  
  #//-------------------------------------------------------//
  
  @_info
  def   eventActualNode( self, node ):
    """
    Node needs to be rebuilt.
    """
    logInfo("Actual node: %s" % node )
  
  #//-------------------------------------------------------//
  
  @_warning
  def   eventTargetIsBuiltTwiceByNodes( self, value, node1, node2 ):
    logWarning("Target '%s' is built by different nodes: '%s', '%s' " % ( value.name, node1, node2 ) )
  
  #//-------------------------------------------------------//
  
  @_status
  def   eventBuildingNodes( self, total_nodes ):
    logInfo("Building %s nodes" % total_nodes )
  
  #//-------------------------------------------------------//
  
  @_status
  def   eventBuildingNode( self, node ):
    logInfo("Building node: %s" % str(node) )
  
  #//-------------------------------------------------------//
  
  @_status
  def   eventBuildingNodeFinished( self, node ):
    logInfo("Finished node: %s" % str(node) )
  
  @_status
  def   eventRebuildNode( self, node ):
    logInfo("Rebuild node: %s" % str(node) )
  
  @_status
  def   eventFailedNode( self, node, error ):
    logError("Failed node: %s" % str(node) )
    logError("Error: %s" % str(error) )
    traceback.print_tb( error.__traceback__ )


#//===========================================================================//

info_events     = frozenset( info_events )
debug_events    = frozenset( debug_events )
status_events   = frozenset( status_events )
warning_events  = frozenset( warning_events )
all_events      = frozenset( warning_events | info_events | debug_events | status_events )
