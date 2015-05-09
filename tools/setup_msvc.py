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
# from aql import tool_setup, get_shell_script_env
#
# script=r"C:\Program Files (x86)\Microsoft Visual Studio 12\VC\vcvarsall.bat"
#
# @tool_setup('msvcpp','msvc++', 'msvc')
# def   setup_msvc(cls, options):
#
#   if options.cc_name.is_set_not_to('msvc'):
#     return
#
#   target_arch = options.target_arch
#
#   if not target_arch.is_set() or (target_arch == 'x86-32'):
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
#   vc_env = get_shell_script_env( script, target )
#   options.env.update( vc_env )
