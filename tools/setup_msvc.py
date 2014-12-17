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
# def   setupMsvc( options ):
#   
#   cc_name = options.cc_name
#   if cc_name.isSet() and cc_name != 'msvc':
#     return
#   
#   target_arch = options.target_arch
#   
#   if not target_arch.isSet():
#     target = "x86"
#   
#   elif target_arch == 'x86-32':
#     target = "x86"
#   
#   elif target_arch == 'x86-64':
#     target = "amd64"
#   
#   elif target_arch == 'arm':
#     target = "arm"
#   
#   else:
#     raise NotImplementedError()
#   
#   vc_env = getShellScriptEnv( script, target )
#   options.env.update( vc_env )

