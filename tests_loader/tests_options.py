import sys
import os.path
import io

#//===========================================================================//

def  _getExecTests( tests ):
  
  run_tests = set()
  add_tests = set()
  skip_tests = set()
  start_from_tests = set()
  
  for test in tests:
    if test.startswith('+'):
      add_tests.add( test[1:] )
    
    elif test.startswith('-'):
      skip_tests.add( test[1:] )
    
    elif test.startswith('~'):
      start_from_tests.add( test[1:] )
    
    elif test:
      run_tests.add( test )
  
  return (exec_tests, add_tests, skip_tests, start_from_test)

#//===========================================================================//

class _Options( object ):
  
  @staticmethod
  def   _parseArguments():
    
    parser = OptionParser("usage: %prog [OPTIONS] [ARGUMENT=VALUE ...]")
    
    parser.add_option("-c", "--config", dest = "config",
                      help = "Path to config file.", metavar = "FILE PATH")
    
    parser.add_option("-x", "--tests", dest = "tests",
                      help = "Comma separated list of tests which should be executed.", metavar = "TESTS")
    
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
                      help = "Quiet mode.", default = True )
    
    parser.add_option("-k", "--keep-going", action="store_false", dest="keep_going",
                      help = "Keep going even if any test case failed.", default = True )
    
    parser.add_option("-r", "--reset", action="store_true", dest="reset",
                      help = "Reset configuration", default = False )
    
    (options, args) = parser.parse_args()
    print_usage = False
    
    settings = {}
    
    if options.config is not None:
      if not os.path.isfile(options.config):
        logError( "Config file doesn't exist." )
        parser.print_help(); exit()
      else:
        execfile( options.config, {}, settings )
    
    for arg in args:
      name, sep, value = arg.partition('=')
      if not sep:
        logError("Invalid argument.")
        parser.print_help(); exit()
      
      settings[ name.strip() ] = value()
    
    if options.tests is not None:
        settings['tests'] = tests.split(',')
  
  def   __init__(self):
    from optparse import OptionParser
    
    parser = OptionParser("usage: %prog [OPTIONS] [ARGUMENT=VALUE ...]")
    
    parser.add_option("-c", "--config", dest = "config",
                      help = "Path to config file.", metavar = "FILE PATH")
    
    parser.add_option("-x", "--tests", dest = "tests",
                      help = "Comma separated list of tests which should be executed.", metavar = "TESTS")
    
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
                      help = "Quiet mode.", default = True )
    
    parser.add_option("-k", "--keep-going", action="store_false", dest="keep_going",
                      help = "Keep going even if any test case failed.", default = True )
    
    (options, args) = parser.parse_args()
    print_usage = False
    
    settings = {}
    
    if options.config is not None:
      if not os.path.isfile(options.config):
        logError( "Config file doesn't exist." )
        parser.print_help(); exit()
      else:
        execfile( options.config, {}, settings )
    
    for arg in args:
      name, sep, value = arg.partition('=')
      if not sep:
        logError("Invalid argument.")
        parser.print_help(); exit()
      
      settings[ name.strip() ] = value()
    
    if options.tests is not None:
        settings['tests'] = tests.split(',')
    
    self.__dict__ = settings

#//=======================================================//

#//===========================================================================//

def   runTests():
  settings = _Settings()
  
  exec_tests, add_tests, skip_tests, start_from_test = _getExecTests( settings.tests )
  
  #//-------------------------------------------------------//
  
  _runTests( settings, exec_tests, add_tests, skip_tests, start_from_test )

