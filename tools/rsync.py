import os

from aql.utils import Rsync
from aql.util_types import toSequence, FilePaths
from aql.options import Options, BoolOptionType, PathOptionType, StrOptionType
from aql.values import FileValue, DirValue
from aql.nodes import Builder

#//===========================================================================//

def   rsyncOptions():
  
  options = Options()
  
  options.rsync = PathOptionType( description = "File path to rsync program." )
  options.rsync_cygwin = BoolOptionType( description = "Is rsync from Cygwin." )
  
  options.rsync_host = StrOptionType( description = "Rsync remote host." )
  options.rsync_login = StrOptionType( description = "Rsync user's SSH login on the remote host." )
  options.rsync_key_file = PathOptionType( description = "Rsync user's SSH key file for the remote host." )
  
  options.If().rsync.has('cygwin').rsync_cygwin = True
  
  return options

#//===========================================================================//

"""
env.RsyncGet( remote_path = '/work/cp/kh', local_path = src_dir )

prog = env.LinkProgram( target = 'test', obj_files )

env.RsyncPut( prog, local_path = '', remote_path = '/work/cp/bin/' )

"""

class RSyncBuilder (Builder):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  __slots__ = ( 'rsync', 'local_path', 'remote_path', 'exclude' )
  
  def   __init__( self, action, options, local_path, remote_path, exclude = None ):
    do_get = bool(action == 'get')
    
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    host = options.rsync_host.value()
    if host:
      host = RemoteHost( host, options.rsync_login, options.rsync_key_file )
      host_address = host.address
    else:
      host_address = ''
    
    env = options.env.value().copy( value_type = str )
    
    rsync = Rsync( rsync = options.rsync.value(), host = host, cygwin_paths = options.rsync_cygwin.value(), env = env )
    
    self.rsync = rsync
    
    #//-------------------------------------------------------//
    
    if do_get:
      self.local_path = local_path
      self.remote_path = toSequence( remote_path )
    else:
      self.local_path = toSequence( local_path )
      self.remote_path = remote_path
    
    self.exclude = toSequence( exclude )
    
    #//-------------------------------------------------------//
    
    cls = self.__class__
    
    if do_get:
      self.name = '.'.join( [ cls.__module__, cls.__name__, str(local_path) ] )
      self.signature = (host_address + '.' + ','.join( self.remote_path ) + '.' +  ','.join( self.exclude )).encode('utf-8')
    else:
      self.name = '.'.join( [ cls.__module__, cls.__name__, host_address, str( self.remote_path ) ] )
      self.signature = (','.join( self.local_path ) + '.' +  ','.join( self.exclude )).encode('utf-8')
    
    #//-------------------------------------------------------//
    
    if do_get:
      self.build = self.get
      self.buildStr = self.getStr
    else:
      self.build = self.put
      self.buildStr = self.putStr
  
  #//-------------------------------------------------------//
  
  def   get( self, build_manager, vfile, node ):
    
    local_path = self.local_path
    
    self.rsync.get( local_path, self.remote_path, exclude = self.exclude )
    if os.path.isdir( local_path ):
      target = DirValue( local_path )
    else:
      target = FileValue( local_path )
    
    return self.nodeTargets( target )
  
  #//-------------------------------------------------------//
  
  def   getStr( self, node ):
    if self.rsync.host:
      remote_path = ' '.join( map( self.rsync.host.remotePath, self.remote_path ) )
    else:
      remote_path = ' '.join( self.remote_path )
    
    return self.rsync.cmd[0] + ': ' + remote_path + ' > ' + str(self.local_path)
  
  #//-------------------------------------------------------//
  
  def   put( self, build_manager, vfile, node ):
    
    local_files = FilePaths( node.sources() )
    
    local_path = self.local_path
    
    self.rsync.put( local_path, self.remote_path, exclude = self.exclude, local_files = local_files )
    return self.nodeTargets()   # no output targets
  
  #//-------------------------------------------------------//
  
  def   putStr( self, node ):
    host = self.rsync.host
    
    if host:
      local_path = ' '.join( map( host.localPath, self.local_path ) )
    else:
      local_path = ' '.join( self.local_path )
    
    return self.rsync.cmd[0] + ': ' + local_path + ' > ' + str(self.remote_path)

#//===========================================================================//

class RSyncGetBuilder (RSyncBuilder):
  def   __init__( self, options, local_path, remote_path, exclude = None, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    super(RSyncGetBuilder,self).__init__( 'get', options, local_path, remote_path, exclude, scontent_type, tcontent_type )
  
#//===========================================================================//

class RSyncPutBuilder (RSyncBuilder):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  def   __init__( self, options, local_path, remote_path, exclude = None, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    super(RSyncPutBuilder, self).__init__( 'put', options, local_path, remote_path, exclude, scontent_type, tcontent_type )
