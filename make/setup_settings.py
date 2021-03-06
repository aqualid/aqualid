
from aql import get_aql_info

info = get_aql_info()

SCRIPTS_PATH = 'scripts'
MODULES_PATH = 'modules'
AQL_MODULE_PATH = MODULES_PATH + '/' + info.module

UNIX_SCRIPT_PATH = SCRIPTS_PATH + '/aql'
WINDOWS_SCRIPT_PATH = SCRIPTS_PATH + '/aql.cmd'

MANIFEST = """include {unix_script}
include {win_script}
""".format(unix_script=UNIX_SCRIPT_PATH,
           win_script=WINDOWS_SCRIPT_PATH)


# ==============================================================================
UNIX_SCRIPT = """#!/usr/bin/env python
if __name__ == '__main__':
  import {module}
  import sys
  sys.exit({module}.main())
""".format(module=info.module).replace('\r', '')


# ==============================================================================
WINDOWS_SCRIPT = """@echo off
@echo off

set AQL_ERRORLEVEL=
IF [%AQL_RUN_SCRIPT%] == [YES] goto run

REM Workaround for an interactive prompt "Terminate batch script? (Y/N)"
REM When CTRL+C is pressed
SET AQL_RUN_SCRIPT=YES
CALL %0 %* <NUL
set AQL_ERRORLEVEL=%ERRORLEVEL%
goto exit

:run
SET AQL_RUN_SCRIPT=
SETLOCAL
SET "PATH=%~dp0;%PATH%"
python -O -c "import {module}; import sys; sys.exit({module}.main())" %*
ENDLOCAL & set AQL_ERRORLEVEL=%ERRORLEVEL%

:exit
exit /B %AQL_ERRORLEVEL%
""".format(module=info.module).replace('\r', '').replace('\n', '\r\n')


# ==============================================================================
STANDALONE_WINDOWS_SCRIPT = """@echo off
IF [%AQL_RUN_SCRIPT%] == [YES] (
  SET AQL_RUN_SCRIPT=
  python -O aql %*

) ELSE (
  REM Workaround for an interactive prompt "Terminate batch script? (Y/N)"
  REM When CTRL+C is pressed
  SET AQL_RUN_SCRIPT=YES
  CALL %0 %* <NUL
)
""".replace('\r', '').replace('\n', '\r\n')


# ==============================================================================
def generate_setup_script(long_description):

    setup_script = """
import os
import errno

from distutils.core import setup
from distutils.command.install_scripts import install_scripts

# Work around mbcs bug in distutils.
# http://bugs.python.org/issue10945
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    func = lambda name, enc=ascii: {{True: enc}}.get(name=='mbcs')
    codecs.register(func)


# ==============================================================================
def   _removeFile( file ):
  try:
    os.remove( file )
  except OSError as ex:
    if ex.errno != errno.ENOENT:
      raise

class InstallScripts( install_scripts ):

  def   __getInstallDir(self):

    # use local imports as a workaround for multiprocessing and run_setup
    import os.path
    import site

    install_dir = os.path.normcase( os.path.abspath(self.install_dir) )
    sys_prefix = os.path.normcase( site.USER_BASE )

    if not install_dir.startswith( sys_prefix ):
      return os.path.abspath( os.path.join( self.install_dir, '..' ) )

    return None

  def run(self):
    # use local imports as a workaround for multiprocessing and run_setup
    import os
    from distutils.command.install_scripts import install_scripts

    install_scripts.run( self )

    if os.name == 'nt':
      install_dir = self.__getInstallDir()
      if install_dir:
        for script in self.get_outputs():
          if script.endswith( ('.cmd','.bat') ):
            dest_script = os.path.join(install_dir, os.path.basename(script))
            _removeFile( dest_script )
            self.move_file( script, dest_script )

if os.name == 'nt':
  scripts = [ '{win_script}']
else:
  scripts = [ '{unix_script}']

LONG_DESCRIPTION = \"""
{long_descr}
\"""

setup(
      name              = '{name}',
      version           = '{version}',
      author            = 'Constanine Bozhikov',
      author_email      = 'voidmb@gmail.com',
      description       = '{short_descr}',
      long_description  = LONG_DESCRIPTION,
      url               = '{url}',
      license           = '{license}',
      platforms         = "All platforms",
      scripts           = scripts,
      package_dir       = {{'': '{package_root}'}},
      packages          = ['{modname}'],
      package_data      = {{'{modname}': ['tools/*']}},
      cmdclass          = {{ 'install_scripts' : InstallScripts,}}
)
""".format(short_descr=info.description,
           long_descr=long_description,
           name=info.name,
           modname=info.module,
           version=info.version,
           url=info.url,
           license=info.license,
           package_root=MODULES_PATH,
           unix_script=UNIX_SCRIPT_PATH,
           win_script=WINDOWS_SCRIPT_PATH,
           )

    return setup_script
