import sys
import os.path
import pickle
import unittest

_search_paths = [ '.', 'tests_utils', 'tools' ]
sys.path[:0] = map( lambda p: os.path.abspath( os.path.join( os.path.dirname( __file__ ), '..', p) ), _search_paths )

from tests_utils import TestCaseBase, skip, runTests, runLocalTests, TestsOptions
from aql.types import FilePaths
from aql.values import NoContent

#//===========================================================================//

SRC_FILE_TEMPLATE = """
#include <cstdio>
#include "%s.h"

void  %s()
{}
"""

HDR_FILE_TEMPLATE = """
#ifndef HEADER_%s_INCLUDED
#define HEADER_%s_INCLUDED

extern void  %s();

#endif
"""

#//===========================================================================//

class AqlTestCase( TestCaseBase ):
  
  def _testSaveLoad( self, value ):
    data = pickle.dumps( ( value, ), protocol = pickle.HIGHEST_PROTOCOL )
    
    loaded_values = pickle.loads( data )
    loaded_value = loaded_values[0]
    
    self.assertEqual( value.name, loaded_value.name )
    if value.content:
      self.assertEqual( value.content, loaded_value.content )
    else:
      self.assertFalse( loaded_value.content )
  
  #//===========================================================================//

  def   generateCppFile( self, dir, name ):
    src_content = SRC_FILE_TEMPLATE % ( name, 'foo_' + name )
    hdr_content = HDR_FILE_TEMPLATE % ( name.upper(), name.upper(), 'foo_' + name )
    
    src_file = dir.join( name + '.cpp' )
    hdr_file = dir.join( name + '.h' )
    
    with open( src_file, 'w' ) as f:
      f.write( src_content )
    
    with open( hdr_file, 'w' ) as f:
      f.write( hdr_content )
    
    return src_file, hdr_file

  #//===========================================================================//

  def   generateCppFiles( self, dir, name, count ):
    src_files = FilePaths()
    hdr_files = FilePaths()
    for i in range( count ):
      src_file, hdr_file = self.generateCppFile( dir, name + str(i) )
      src_files.append( src_file )
      hdr_files.append( hdr_file )
    
    return src_files, hdr_files
  
#//===========================================================================//

if __name__ == '__main__':
  
  options = TestsOptions.instance()
  options.setDefault( 'test_modules_prefix', 'aql_test_' )
  
  runTests()
