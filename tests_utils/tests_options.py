import sys
import os.path
import io
import optparse

__all__ = ( 'tests_options' )

#//===========================================================================//

class TestsOptions( object ):
  
  def   __init__( self ):
    opt, args = self.__getOptArgs()
    
    self.__parseConfig( opt.config )
    self.__parseArguments( args )
    self.__parseTests( opt.tests )
    
    self.verbose = opt.verbose
    self.keep_going = opt.keep_going
    self.reset = opt.reset
    self.tests_dir = opt.tests_dir
    
  @staticmethod
  def   __getOptArgs():
    parser = optparse.OptionParser("usage: %prog [OPTIONS] [ARGUMENT=VALUE ...]")
    
    parser.add_option("-d", "--dir", dest = "tests_dir",
                      help = "Tests directory", metavar = "DIR PATH", default = '.' )
    
    parser.add_option("-p", "--prefix", dest = "test_modules_prefix",
                      help = "File name prefix of test modules", metavar = "FILE PATH PREFIX",
                      default = 'test_')
    
    parser.add_option("-m", "--method-prefix", dest = "test_methods_prefix",
                      help = "Test methods prefix", metavar = "TEST METHOD PREFIX",
                      default = 'test')
    
    parser.add_option("-c", "--config", dest = "config",
                      help = "Path to config file.", metavar = "FILE PATH")
    
    parser.add_option("-x", "--tests", dest = "tests",
                      help = "Comma separated list of tests which should be executed.", metavar = "TESTS")
    
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
                      help = "Quiet mode.", default = True )
    
    parser.add_option("-k", "--keep-going", action="store_true", dest="keep_going",
                      help = "Keep going even if any test case failed.", default = False )
    
    parser.add_option("-r", "--reset", action="store_true", dest="reset",
                      help = "Reset configuration", default = False )
    
    opt, args = parser.parse_args()
    
    return (opt, args)

  #//===========================================================================//

  def   __parseArguments( self, args ):
    for arg in args:
      name, sep, value = arg.partition('=')
      if not sep:
        print("Error: Invalid argument.")
        exit()
      
      setattr( self, name.strip(), value.strip() )
  
  #//===========================================================================//
  
  def  __parseTests( self, tests ):
    
    if tests is not None:
      tests = tests.split(',')
    else:
      tests = []
    
    run_tests = None
    add_tests = set()
    skip_tests = set()
    start_from_tests = set()
    
    for test in tests:
      test = test.strip()
      if test.startswith('+'):
        add_tests.add( test[1:] )
      
      elif test.startswith('-'):
        skip_tests.add( test[1:] )
      
      elif test.startswith('~'):
        start_from_tests.add( test[1:] )
      
      elif test:
        if run_tests is None:
          run_tests = set()
        run_tests.add( test )
    
    self.run_tests = run_tests
    self.add_tests = add_tests
    self.skip_tests = skip_tests
    self.start_from_tests = start_from_tests

  #//===========================================================================//

  def   __parseConfig( self, config ):
    if config is not None:
      if not os.path.isfile(config):
        print( "Error: Config file doesn't exist." )
        exit()
      
      settings = {}
      execfile( config, {}, settings )
      
      for key,value in settings:
        setattr( self, key, value )

#//===========================================================================//

tests_options = TestsOptions()

#//===========================================================================//

if __name__ == "__main__":
  import pprint
  
  pprint.pprint( TestsOptions().__dict__ )
  

