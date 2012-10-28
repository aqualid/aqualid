import os

from aql_builder import Builder
from aql_utils import toSequence
from aql_options import Options
from aql_option_types import BoolOptionType, PathOptionType, StrOptionType

from aql_rsync import Rsync
from aql_file_value import FileValue, DirValue

#//===========================================================================//

def   rsyncOptions():
  
  options = Options()
  
  options.rsync = PathOptionType( description = "File path to rsync program." )
  options.rsync_cygwin = BoolOptionType( description = "Is rsync from Cygwin." )
  
  options.rsync_host = StrOptionType( description = "Rsync remote host." )
  options.rsync_login = StrOptionType( description = "Rsync user's SSH login on the remote host." )
  options.rsync_key_file = PathOptionType( description = "Rsync user's SSH key file for the remote host." )
  
  options.rsync = 'rsync'
  options.If().rsync.has('cygwin').rsync_cygwin = True
  
  return options

#//===========================================================================//

"""
env.RsyncGet( remote_path = '/work/cp/kh', local_path = src_dir )

prog = env.LinkProgram( target = 'test', obj_files )

env.RsyncPut( prog, local_path = '', remote_path = '/work/cp/bin/' )

"""

class RSyncGetBuilder (Builder):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  __slots__ = ( 'rsync', 'local_path', 'remote_path', 'exclude' )
  
  def   __init__( self, options, local_path, remote_path, exclude = None, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    rsync_prog = options.rsync.value()
    
    host = options.rsync_host.value()
    if host:
      host = RemoteHost( host, options.rsync_log, options.rsync_key_file )
      host_address = host.address
    else:
      host_address = ''
    
    rsync = Rsync( rsync_prog, host, cygwin_paths = options.rsync_cygwin.value(), env = options.env.value() )
    
    self.rsync = rsync
    self.local_path = local_path
    self.remote_path = toSequence( remote_path )
    self.exclude = toSequence( exclude )
    
    cls = self.__class__
    self.name = '.'.join( [ cls.__module__ , cls.__name__ , host_address , str(local_path) ] )
    self.signature = (','.join( self.remote_path ) + '.' +  ','.join( self.exclude )).encode('utf-8')
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    local_path = self.local_path
    
    self.rsync.get( local_path, self.remote_path, exclude = self.exclude )
    if os.path.isdir( local_path ):
      target = DirValue( local_path )
    else:
      target = FileValue( local_path )
    
    return self.nodeTargets( target )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    if self.rsync.host:
      remote_path = ' '.join( map( self.rsync.host.remotePath, self.remote_path ) )
    else:
      remote_path = ' '.join( self.remote_path )
    
    return self.rsync.cmd[0] + ': ' + remote_path + ' > ' + str(self.local_path)
