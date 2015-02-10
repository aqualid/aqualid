#include <string>
#include <iostream>
#include <fstream>
#include <algorithm>
#include <locale>

//===========================================================================//

static char const   HEADER_TEMPLATE[] = 
"\
#ifndef HEADER_{header}_INCLUDED                  \n\
#define HEADER_{header}_INCLUDED                  \n\
                                                  \n\
#include <cstdlib>                                \n\
                                                  \n\
class Rectangle                                   \n\
{                                                 \n\
  size_t  width_;                                 \n\
  size_t  height_;                                \n\
                                                  \n\
public:                                           \n\
  Rectangle( size_t width, size_t height )        \n\
  : width_(width)                                 \n\
  , height_(height)                               \n\
  {}                                              \n\
                                                  \n\
  virtual ~Rectangle()                            \n\
  {}                                              \n\
                                                  \n\
                                                  \n\
  size_t  getWigth() const                        \n\
  {                                               \n\
    return width_;                                \n\
  }                                               \n\
                                                  \n\
  size_t  getHeight() const                       \n\
  {                                               \n\
    return height_;                               \n\
  }                                               \n\
                                                  \n\
  size_t  getPerimeter() const                    \n\
  {                                               \n\
    return (width_ + height_) * 2;                \n\
  }                                               \n\
                                                  \n\
  size_t  getSpace() const                        \n\
  {                                               \n\
    return width_ * height_;                      \n\
  }                                               \n\
};                                                \n\
                                                  \n\
#endif  //  #ifndef HEADER_{header}_INCLUDED  //  \n\
";

//===========================================================================//

template <typename charT>
static charT  toUpper( charT  c )
{
  std::locale const  loc;
  
  return std::toupper( c, loc );
}

//===========================================================================//

static void  getHeader(
  
  std::string &   header,
  char const *    header_path
)
{
  header.assign( header_path );
  
  size_t const    sep_pos = header.find_last_of( "/\\" );
  
  if (sep_pos != std::string::npos)
  {
    header.erase( 0, sep_pos + 1 );
  }
  
  std::replace( header.begin(), header.end(), '.', '_' );
  
  std::transform( header.begin(), header.end(), header.begin(), toUpper<std::string::value_type> );
}

//===========================================================================//

static void   trimContent( std::string &  content )
{
  std::string const   empty;
  size_t              pos = 0;
  
  while (pos < content.size())
  {
    pos = content.find( '\n', pos );
    if (pos == std::string::npos)
    {
      pos = content.size();
    }
    
    if (pos > 0)
    {
      size_t const  line_end = content.find_last_not_of( ' ', pos - 1);
      if (line_end == std::string::npos)
      {
        content.replace( 0, pos - 1, empty );
      }
      else
      {
        content.replace( line_end + 1, pos - 1 - line_end, empty );
      }
      ++pos;
    }
  }
}

//===========================================================================//

static void  getContent(
  
  std::string &   content,
  char const *    header_path
)
{
  std::string  header;
  getHeader( header, header_path );
  
  content.assign( HEADER_TEMPLATE );
  
  std::string const   marker( "{header}" );
  
  size_t  pos = 0;
  
  for (;;)
  {
    pos = content.find( marker, pos );
    if (pos == std::string::npos)
    {
      break;
    }
    
    content.replace( pos, marker.size(), header );
    
    pos += marker.size();
  }
  
  trimContent( content );
}

//===========================================================================//

static void   saveContent( char const *    header_path )
{
  std::string  content;
  getContent( content, header_path );
  
  std::ofstream   file( header_path, std::ofstream::out | std::ofstream::binary | std::ofstream::trunc );
  
  file.write( content.c_str(), content.size() );
}

//===========================================================================//

int main( int argc, char *argv[] )
{
  if (argc < 2)
  {
    std::cerr << "Header names has not been specified." << std::endl;
    return 1;
  }
  
  char const * const  header_name = argv[1];
  
  saveContent( header_name );
  
  return 0;
}
