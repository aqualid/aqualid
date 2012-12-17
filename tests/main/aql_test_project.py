import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile
from aql.main import Project, ProjectConfig

#//===========================================================================//

class TestProject( AqlTestCase ):
  
  def test_prj_config(self):
    
    args = "-j 8".split()
    
    with Tempfile() as f:
      cfg = b"""
abc = 123
size = 100
jobs = 4
options.build_variant = "debug"
"""
      f.write( cfg )
      f.flush()
    
      cfg = ProjectConfig( args )
      #~ cfg.readConfig( f.name )
    
    prj = Project( cfg )
    
    bv = prj.options.bv.value()
    
    print( "prj.options.bv: '%s' %s" % (bv, type(bv) ) )
    
    self.assertEqual( bv, 'final' )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
