#ifndef AQLDEMO_TOOL_API_HPP_INCLUDED
#define AQLDEMO_TOOL_API_HPP_INCLUDED

#ifdef  WIN32
# ifdef MAKING_LIBRARY
#   define EXPORT_IMPORT_API  __declspec(dllexport)
# else
#   define EXPORT_IMPORT_API __declspec(dllimport)
# endif
#else
# define EXPORT_IMPORT_API
#endif


extern EXPORT_IMPORT_API int   doActionApi( char const *   action );


#endif  // AQLDEMO_TOOL_API_HPP_INCLUDED

