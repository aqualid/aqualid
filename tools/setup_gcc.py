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
# from aql import tool_setup
#
# @tool_setup('g++', 'gxx', 'gcc')
# def   setup_gcc(cls, options):
#   if options.cc_name.is_set_not_to( 'gcc' ):
#     return
#
#   target_arch = options.target_arch
#
#   if not target_arch.is_set() or target_arch == 'x86-32':
#     if options.cc_ver == '4.6':
#       path = r"C:\MinGW32\bin"
#     else:
#       path = r"C:\bin\mingw-32\bin"
#
#   elif target_arch == 'x86-64':
#     path = r"C:\bin\mingw-32\bin"
#
#   else:
#     raise NotImplementedError()
#
#   options.env['PATH'] = [ path ] + options.env['PATH']
