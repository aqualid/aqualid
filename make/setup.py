
import os
import site
import datetime

from distutils.core import setup

from distutils.command.install_lib import install_lib
from distutils.command.install_scripts import install_scripts

#//===========================================================================//

def   isWindowsBuild():
  if os.name == 'nt':
    return True
  
  return False

#//===========================================================================//

AQL_CMD = """
@rem Copyright (c) 2011-{year} the developers of Aqualid project
@echo off

IF [%AQL_RUN_SCRIPT%] == [YES] (
  SET AQL_RUN_SCRIPT=
  python -OO -c "import aqualid; aqualid.main()" %*
    
) ELSE (
  REM Workaround for an interactive prompt "Terminate batch script? (Y/N)" when CTRL+C is pressed
  SET AQL_RUN_SCRIPT=YES
  CALL %0 %* <NUL
)
""".format( year = datetime.date.today().year )

#//===========================================================================//

class   InstallLib( install_lib ):
  def initialize_options(self):
    install_lib.initialize_options( self )
    self.optimize = 2

#//===========================================================================//

class InstallScripts( install_scripts ):
  
  def   __getInstallDir(self):
    
    install_dir = os.path.normcase( os.path.abspath(self.install_dir) )
    sys_prefix = os.path.normcase( site.USER_BASE )
    
    if not install_dir.startswith( sys_prefix ):
      install_dir = os.path.abspath( os.path.join( self.install_dir, '..' ) )
    
    return install_dir
  
  def run(self):
    install_scripts.run( self )
    
    if isWindowsBuild():
      install_dir = self.__getInstallDir()
      cmd_file_name = os.path.join( install_dir, 'aql.cmd')
      with open( cmd_file_name, 'w') as f:
        f.write( AQL_CMD )
      
      # remove Unix scripts
      for file in self.get_outputs():
        os.remove( file )

#//===========================================================================//

LONG_DESCRIPTION = """
General purpose build tool.
Designed be scalable in both ways execution and implementation for any project type.
Build dependency graph is dynamic and it can be changed at any time during the build of a project.
"""

#//===========================================================================//

SETUP_ARGS = {
      'name'              : 'Aqualid',
      'version'           : '1.0',
      'author'            : 'Konstanin Bozhikov',
      'author_email'      : 'voidmb@gmail.com',
      'description'       : 'General purpose build tool.',
      'long_description'  : LONG_DESCRIPTION,
      'url'               : 'https://github.com/menify/aqualid',
      'license'           : "MIT License",
      'platforms'         : "All platforms",
      'scripts'           : ['scripts/aql'],
      'package_dir'       : {'': 'modules'},
      'packages'          : ['aqualid'],
      'package_data'      : {'aqualid': ['tools/*']},
      'cmdclass'          : {
                              'install_lib'     : InstallLib,
                              'install_scripts' : InstallScripts,
                            }
}

setup( **SETUP_ARGS )
