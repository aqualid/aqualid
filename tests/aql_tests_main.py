import re
import imp
import os.path

from aql_tests import runTests
from aql_logging import logInfo

#//===========================================================================//

def  _findTestModules( path = None ):
  test_case_re = re.compile(r"^aql_test_.+\.py$")
  
  test_case_modules = []
  if path is None:
    path = os.path.normpath( os.path.dirname( __file__ ) )
  
  for root, dirs, files in os.walk( path ):
    for file_name in files:
      if test_case_re.match( file_name ):
        test_case_modules.append( os.path.join(root, file_name))
    dirs[:] = filter( lambda d: not d.startswith('.') or d.startswith('__'), dirs )
  
  return test_case_modules

#//===========================================================================//

def   _loadTestModules( test_modules ):
  
  for module_file in test_modules:
    
    module_dir = os.path.normpath( os.path.dirname( module_file ) )
    module_name = os.path.splitext( os.path.basename( module_file ) )[0]
    
    fp, pathname, description = imp.find_module( module_name, [ module_dir ] )
    
    with fp:
      user_mod = imp.load_module( module_name, fp, pathname, description )
      
      logInfo( "Loaded module: %s", user_mod.__file__ )

#//===========================================================================//

def   _isIterable( obj ):
  return hasattr( obj, '__iter__') or hasattr( obj, '__getitem__')

#//===========================================================================//

def   _importTestModules( path = None ):
  if _isIterable(path):
    module_files = path
  elif (path is not None) and os.path.isfile( path ):
    module_files = ( path, )
  else:
    module_files = _findTestModules( path )
  
  _loadTestModules( module_files )


#//===========================================================================//
#//===========================================================================//

if __name__ == "__main__":
  _importTestModules()
  runTests()

