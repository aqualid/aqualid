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

from aql.util_types import AqlException 
from aql.utils import DataFile, FileLock

from .aql_entity_pickler import EntityPickler

#//===========================================================================//

class   ErrorEntitiesFileUnknownEntity( AqlException ):
  def   __init__( self, entity ):
    msg = "Unknown entity: %s" % (entity, )
    super(type(self), self).__init__( msg )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class EntitiesFile (object):
  
  __slots__ = (
    
    'data_file',
    'file_lock',
    'key2entity',
    'entity2key',
    'pickler',
  )
  
  #//---------------------------------------------------------------------------//
  
  def   getEntityByKey(self, key ):
    return self.key2entity.get(key, None )
  
  #//---------------------------------------------------------------------------//
  
  def   __getKeyByEntityId(self, entity_id ):
    return self.entity2key.get( entity_id, None )
  
  #//---------------------------------------------------------------------------//
  
  def   __addEntityToCache(self, key, entity_id, entity ):
    self.entity2key[ entity_id ] = key
    self.key2entity[ key ] = entity
  
  def   __removeEntityFromCache( self, key, entity_id ):
    del self.entity2key[ entity_id ]
    del self.key2entity[ key ]
  
  #//---------------------------------------------------------------------------//
  
  def   __updateEntityInCache(self, old_key, new_key, entity_id, entity ):
    self.entity2key[ entity_id ] = new_key
    del self.key2entity[ old_key ]
    self.key2entity[ new_key ] = entity
  
  #//---------------------------------------------------------------------------//
  
  def   __clearCache(self ):
    self.entity2key.clear()
    self.key2entity.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   __init__( self, filename, force = False ):
    self.key2entity = {}
    self.entity2key = {}
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
    
    invalid_keys = []
    
    self.file_lock = FileLock( filename )
    self.file_lock.writeLock( wait = False, force = force )
    
    data_file = DataFile( filename, force = force )
    
    self.data_file = data_file
    
    loads = self.pickler.loads
    for key, data in data_file:
      try:
        entity = loads( data )
      except Exception:
        invalid_keys.append( key )
      else:
        entity_id = entity.getId()
        self.__addEntityToCache( key, entity_id, entity )
      
    data_file.remove( invalid_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   close( self ):
    
    if self.data_file is not None:
      self.data_file.close()
      self.data_file = None
    
    self.file_lock.releaseLock()
    
    self.__clearCache()
  
  #//---------------------------------------------------------------------------//
  
  def   findEntityKey( self, entity ):
    return self.__getKeyByEntityId( entity.getId() )
  
  #//---------------------------------------------------------------------------//
  
  def   findEntity( self, entity ):
    key = self.__getKeyByEntityId( entity.getId() )
    if key is None:
      return None
    
    return self.getEntityByKey( key )
  
  #//---------------------------------------------------------------------------//
  
  def   addEntity( self, entity ):
    
    reserve = not entity.IS_SIZE_FIXED
    
    entity_id = entity.getId()
    key = self.__getKeyByEntityId( entity_id )
    
    if key is None:
      data = self.pickler.dumps( entity )
      key = self.data_file.append( data, reserve )
      
      self.__addEntityToCache( key, entity_id, entity )
    
    else:
      val = self.getEntityByKey( key )
      
      if entity != val:
        data = self.pickler.dumps( entity )
        new_key = self.data_file.replace( key, data, reserve )
        
        self.__updateEntityInCache(key, new_key, entity_id, entity )
        
        return new_key
    
    return key
  
  #//---------------------------------------------------------------------------//
  
  def   replaceEntity(self, key, entity ):
    reserve = not entity.IS_SIZE_FIXED
    
    data = self.pickler.dumps( entity )
    new_key = self.data_file.replace( key, data, reserve )
    
    self.__updateEntityInCache(key, new_key, entity.getId(), entity )
  
  #//---------------------------------------------------------------------------//
  
  def   findEntities(self, entities ):
    return tuple( map( self.findEntity, entities ) )
  
  #//---------------------------------------------------------------------------//
  
  def   addEntities( self, entities ):
    return tuple( map( self.addEntity, entities ) )
  
  #//---------------------------------------------------------------------------//
  
  def   removeEntities( self, entities ):
    remove_keys = []
    
    for entity in entities:
      
      key = self.__getKeyByEntityId( entity.getId() )
      
      if key is not None:
        remove_keys.append( key )
    
    self.data_file.remove( remove_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   removeEntityKeys( self, remove_keys ):
    self.data_file.remove( remove_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   getEntitiesByKeys( self, keys ):
    return [ self.getEntityByKey( key ) for key in keys ]
  
  #//---------------------------------------------------------------------------//
  
  def   clear(self):
    if self.data_file is not None:
      self.data_file.clear()
    
    self.__clearCache()
  
  #//---------------------------------------------------------------------------//
  
  def   selfTest(self):
    if self.data_file is not None:
      self.data_file.selfTest()
    
    for key, entity in self.key2entity.items():
      entity_id = entity.getId()  
      
      if entity_id not in self.entity2key:
        raise AssertionError("entity (%s) not in self.entity2key" % (entity_id,))
        
      if key != self.entity2key[ entity_id ]:
        raise AssertionError("key(%s) != self.entity2key[ entity_id(%) ](%s) % (key, entity_id, self.entity2key[ entity_id ])" )
    
    size = len(self.key2entity)
    
    if size != len(self.entity2key):
      raise AssertionError( "size(%s) != len(self.entity2key)(%s)" % (size, len(self.entity2key)) )
    
    data_file_size = len(self.data_file)
    if data_file_size != size:
      raise AssertionError("data_file_size(%s) != size(%s)" % (data_file_size, size))
