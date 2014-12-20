#include <iostream>

#include "tool.hpp"
#include "tool_api.hpp"

int   doActionApi( char const *   action )
{
  std::cout << "Calling toolAction() from static library" << std::endl;
  doAction( action );
  
  return 0;
}

