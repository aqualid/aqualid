#include <iostream>

#include "tool_api.hpp"

int main( int argc, char * argv[] )
{
  if (argc < 2)
  {
    std::cerr << "Action has not been specified." << std::endl;
    return -1;
  }
  
  int const   status = doActionApi( argv[1] );
  
  std::cout << "Action status: " << status << std::endl;
  
  return status;
}
