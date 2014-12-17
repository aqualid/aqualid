# Example of user setup script for user's environment
#
# Such scripts could be placed in any of default locations:
# On Windows:
#   X:\PythonXX\Lib\site-packages\aqualid\tools
#   %USERPROFILE%\AppData\Roaming\Python\PythonXX\site-packages\aqualid\tools
#   %USERPROFILE%\.config\aqualid\tools
#
# On Unix:
#   /usr/lib/pythonX.Y/site-packages/aqualid/tools
#   $PYTHONUSERBASE/lib/pythonX.Y/site-packages
#   $HOME/.config/aqualid/tools
#
#
# from aql import toolSetup
#
# @toolSetup('g++', 'gxx', 'gcc')
# def   setupGcc32( options ):
#   options.env['PATH'] = [r"C:\bin\mingw-32\bin"] + options.env['PATH']
#
# @toolSetup('g++', 'gxx', 'gcc')
# def   setupGcc64( options ):
#   options.env['PATH'] = [r"C:\bin\mingw-64\bin"] + options.env['PATH']
