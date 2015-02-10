#include <iostream>

#include "rect.hpp"

class MyBox: public Rectangle
{
public:
  MyBox( size_t width, size_t height )
  : Rectangle( width, height )
  {}
};

int main()
{
  MyBox const box( 5, 7 );
  
  std::cout << "Perimeter: " << box.getPerimeter() << std::endl;
  std::cout << "Space: " << box.getSpace() << std::endl;
  return 0;
}
