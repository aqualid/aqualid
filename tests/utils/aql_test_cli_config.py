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
    config.setDefault( 'size', 10 )
    config.setDefault( 'new_size', 2 )
    self.assertTrue( config.jobs, 0 )
    self.assertTrue( config.size, 32 )
    self.assertTrue( config.new_size, 2 )
    self.assertTrue( config.targets, ['foo'] )
    self.assertTrue( config.values['bv'], 'release' )
    
    config.jobs = 10
    self.assertTrue( config.jobs, 10 )
    config.size = 20
    self.assertTrue( config.size, 20 )
    config.new_size = 1
    self.assertTrue( config.new_size, 1 )
    
    config.setDefault( 'new_size', 30 )
    self.assertTrue( config.new_size, 1 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
