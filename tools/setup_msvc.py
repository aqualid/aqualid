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
# from aql import toolSetup, getShellScriptEnv
# 
# script = r"C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\vcvarsall.bat"
# 
# @toolSetup('msvcpp','msvc++', 'msvc')
# def   setupMsvc32( options ):
#   vc_env = getShellScriptEnv( script, "x86" )
#   options.env.update( vc_env )
#   
# @toolSetup('msvcpp','msvc++', 'msvc')
# def   setupMsvc64( options ):
#   vc_env = getShellScriptEnv( script, "amd64" )
#   options.env.update( vc_env )
# 
# @toolSetup('msvcpp','msvc++', 'msvc')
# def   setupMsvcArm( options ):
#   vc_env = getShellScriptEnv( script, "arm" )
#   options.env.update( vc_env )

