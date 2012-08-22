import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import fileChecksum, printStacks
from aql_temp_file import Tempfile, Tempdir
from aql_path_types import FilePath, FilePaths
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_builtin_options import builtinOptions

from gcc import GccCompileCppBuilder, gccOptions

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

def   _generateSrcFile( dir, name ):
  src_content = SRC_FILE_TEMPLATE % ( name, 'foo_' + name )
  hdr_content = HDR_FILE_TEMPLATE % ( name.upper(), name.upper(), 'foo_' + name )
  
  src_file = dir.join( name + '.cpp' )
  hdr_file = dir.join( name + '.h' )
  
  with open( src_file, 'wb' ) as f:
    f.write( src_content )
  
  with open( hdr_file, 'wb' ) as f:
    f.write( hdr_content )
  
  return src_file, hdr_file

#//===========================================================================//

def   _generateSrcFiles( dir, name, count ):
  src_files = FilePaths()
  for i in range( count ):
    src_file = _generateSrcFile( dir, name + str(i) )[0]
    src_files.append( src_file )
  
  return src_files

#//===========================================================================//

class TestToolGcc( AqlTestCase ):

  def test_gcc_compile(self):
    
      event_manager.setHandlers( EventHandler() )
    
    #~ with Tempdir() as tmp_dir:
      tmp_dir = Tempdir()
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      src_files = _generateSrcFiles( src_dir, 'foo', 5 )
      
      options = builtinOptions()
      options.update( gccOptions() )
      
      options.cxx = "C:\\MinGW32\\bin\\g++.exe"
      
      options.build_dir_prefix = build_dir
      
      cpp_compiler = GccCompileCppBuilder( None, options )
      
      vfilename = Tempfile( dir = root_dir, suffix = '.aql.values' ).name
      
      vfile = ValuesFile( vfilename )
      
      obj = Node( cpp_compiler, map( FileValue, src_files ) )
      obj.build( None, vfile )
      
      obj = Node( cpp_compiler, map( FileValue, src_files ) )
      print( obj.actual( vfile ) )
  
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
