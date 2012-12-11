import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import CLIOption, CLIConfig

class TestCLIConfig( AqlTestCase ):
  
  def test_cli_config(self):
    
    usage = "usage: %prog [FLAGS] [[TARGET] [OPTION=VALUE] ...]"

    cli_options = (
      CLIOption( "-j", "--jobs",    "jobs",     int,  1,      "", 'NUMBER' ),
      CLIOption( "-s", "--size",    "size",     int,  256,    "", 'NUMBER' ),
      CLIOption( "-v", "--verbose", "verbose",  bool, False,  "" ),
    )
    
    config = CLIConfig( usage, cli_options, ["-j", "0", "-v", "foo", "-s32", "bv=release"])
    
    config.setDefault( 'jobs', 3 )
    self.assertTrue( config.jobs, 0 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
