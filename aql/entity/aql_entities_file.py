#
# Copyright (c) 2011-2014 The developers of Aqualid project
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
  'EntitiesFile',
)

import operator

from aql.util_types import AqlException 
from aql.utils import DataFile, FileLock

from .aql_entity_pickler import EntityPickler

#//===========================================================================//

class   ErrorEntitiesFileUnknownEntity( AqlException ):
  def   __init__( self, entity ):
    msg = "Unknown entity: %s" % (entity, )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class EntitiesFile (object):
  
  __slots__ = (
    
    'data_file',
    'file_lock',
    'cache',
    'pickler',
  )
  
  def   __init__( self, filename, force = False ):
    self.cache = {}
    self.data_file = None
    self.pickler = EntityPickler()
    self.open( filename, force = force )
  
  #//---------------------------------------------------------------------------//
  
  def   __enter__(self):
    return self
  
  #//-------------------------------------------------------//

  #noinspection PyUnusedLocal
  def   __exit__(self, exc_type, exc_entity, traceback):
    self.close()
  
  #//---------------------------------------------------------------------------//
  
  def   open( self, filename, force = False ):
    
    self.file_lock = FileLock( filename )
    self.file_lock.writeLock( wait = False, force = force )
    
    self.data_file = DataFile( filename, force = force )
  
  #//---------------------------------------------------------------------------//
  
  def   close( self ):
    
    if self.data_file is not None:
      self.data_file.close()
      self.data_file = None
    
    self.file_lock.releaseLock()
    
    self.cache.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   findNodeEntity( self, entity ):
    
    entity_id = entity.id
    
    dump = self.data_file.read( entity_id )
    if dump is None:
      return None
    
    try:
      entity = self.pickler.loads( dump )
      entity.id = entity_id
    except Exception:
      self.data_file.remove( (entity_id,) )
      return None
    
    return entity
    
  #//---------------------------------------------------------------------------//
  
  def   addNodeEntity( self, entity ):
    dump = self.pickler.dumps( entity )
    self.data_file.write( entity.id, dump )
  
  #//---------------------------------------------------------------------------//
  
  def   removeNodeEntities( self, entities ):
    entity_ids = map( operator.attrgetter('id'), entities )
    self.data_file.remove( entity_ids )
  
  #//---------------------------------------------------------------------------//
  
  def   _findEntityById( self, entity_id ):
    try:
      return self.cache[ entity_id ]
    except KeyError:
      pass
    
    data = self.data_file.read( entity_id )
    if data is None:
      raise ValueError()
    
    try:
      entity = self.pickler.loads( data )
      entity.id = entity_id
    except Exception:
      self.data_file.remove( (entity_id,) )
      raise ValueError()
    
    self.cache[ entity_id ] = entity
    return entity
  
  #//---------------------------------------------------------------------------//

  def   findEntitiesByKey( self, keys ):
    entity_ids = self.data_file.get_ids( keys )
    if entity_ids is None:
      return None
    
    try:
      return list( map( self._findEntityById, entity_ids ) )
    except Exception:
      return None
  
  #//---------------------------------------------------------------------------//

  def   findEntities( self, entities ):
    try:
      return list( map( self._findEntityById, map( operator.attrgetter('id'), entities ) ) )
    except Exception:
      return None
  
  #//---------------------------------------------------------------------------//
  
  def   addEntities( self, entities ):
    
    keys = []
    entity_ids = []
    key_append = keys.append
    entity_append = entity_ids.append
    
    write = self.data_file.write_with_key
    
    for entity in entities:
      
      entity_id = entity.id
      entity_ids.append( entity_id )
      
      try:
        stored_entity = self._findEntityById( entity_id )
        if stored_entity == entity:
          entity_append( entity_id )
          continue
        
      except Exception:
        pass
      
      dump = self.pickler.dumps( entity )
      key = write( entity_id, dump )
      key_append( key )
    
    keys.extend( self.data_file.get_keys( entity_ids ) )
    
    return keys
  
  #//---------------------------------------------------------------------------//
  
  def   updateEntity( self, entity ):
    
    entity_id = entity.id
    
    data = self.pickler.dumps( entity )
    self.data_file.write_with_key( entity_id, data )
    
    self.cache[ entity_id ] = entity
  
  #//---------------------------------------------------------------------------//
  
  def   removeEntities( self, entities ):
    remove_ids = tuple( map( operator.attrgetter('id'), entities ) )
    
    for entity_id in remove_ids:
      try:
        del self.cache[ entity_id ]
      except KeyError:
        pass
    
    self.data_file.remove( remove_ids )
  
  #//---------------------------------------------------------------------------//
  
  def   clear(self):
    if self.data_file is not None:
      self.data_file.clear()
    
    self.cache.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   selfTest(self, log = False):
    if self.data_file is None:
      if self.cache:
        raise AssertionError("cache is not empty")
      
      return
    
    self.data_file.selfTest()
    
    for entity_id, entity in self.cache.items():
      if log:
        print("entity_id: %s" % (entity_id,))
      
      if entity != entity.id:
        raise AssertionError("entity_id(%s) != entity.id(%s)" % (entity_id, entity.id))
      
      dump = self.data_file.read( entity_id )
      stored_entity = self.pickler.loads( dump )
      
      if stored_entity != entity:
        raise AssertionError("stored_entity(%s) != entity(%s)" % (stored_entity.id, entity.id) )
