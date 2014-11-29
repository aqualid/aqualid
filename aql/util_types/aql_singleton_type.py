#
# Copyright (c) 2013 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = ( 'Singleton', )

#noinspection PyProtectedMember
class Singleton( object ):
  
  @staticmethod
  def   getInstance( cls ):
    try:
      instance = cls._instance
    except AttributeError:
      instance = cls._instance = __import__('__main__').__dict__.setdefault( (cls.__module__, cls.__name__ ), [None] )

    return instance[0]

  @staticmethod
  def   setInstance( cls, instance ):
    cls._instance[0] = instance

  @classmethod
  def   instance( cls, *args, **kw ):
    instance = Singleton.getInstance( cls )
    if instance is not None:
      return instance
    
    self = cls( *args, **kw )
    
    Singleton.setInstance( cls, self )

    return self
