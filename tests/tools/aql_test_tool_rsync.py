import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import findProgram
from aql_temp_file import Tempfile, Tempdir
from aql_path_types import FilePath, FilePaths
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_builtin_options import builtinOptions

from rsync import Rsync, rsyncOptions, RemotePathMapping

#//===========================================================================//

class TestToolRsync( AqlTestCase ):
  
  @classmethod
  def   setUpClass( cls ):
    event_manager.setHandlers( EventHandler() )
  
  #//-------------------------------------------------------//

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
