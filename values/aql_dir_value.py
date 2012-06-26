#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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


import os
import hashlib
import datetime

from aql_value import Value

#//===========================================================================//

class   _Unpickling(object):
    pass

#//===========================================================================//

#//===========================================================================//

class   DirContentChecksum (object):
    
    __slots__ = ( 'size', 'checksum' )
    
    def   __new__( cls, path = None ):
        
        if isinstance( path, _Unpickling):
            return super(DirContentChecksum,self).__new__(cls)
        
        if path is None:
            return NoFileContent()
        
        try:
            size = os.stat( path ).st_size
            
            checksum = hashlib.md5()
            
            with open( path, mode = 'rb' ) as f:
                for chunk in f:
                    checksum.update( chunk )
            
            self = super(DirContentChecksum,self).__new__(cls)
            
            self.checksum = checksum.hexdigest()
            self.size = size
            
            return self
        
        except OSError:
            return NoFileContent()
    
    #//-------------------------------------------------------//
    
    def   __eq__( self, other ):
        return (type(self) == type(other)) and \
               (self.size == other.size) and \
               (self.checksum == other.checksum)
    
    def   __ne__( self, other ):        return not self.__eq__( other )
    
    def     __getnewargs__(self):       return ( _Unpickling(), )

    def   __getstate__( self ):         return { 'size': self.size, 'checksum': self.checksum }
    def   __setstate__( self, state ):  self.size = state['size']; self.checksum = state['checksum']
    
    def   __str__( self ):              return self.checksum

#//===========================================================================//

class   FileContentTimeStamp (object):
    
    __slots__ = ( 'size', 'modify_time' )
    
    def   __new__( cls, path = None ):
        
        if isinstance( path, _Unpickling):
            return super(DirContentChecksum,self).__new__(cls)
        
        if path is None:
            return NoFileContent()
        
        try:
            stat = os.stat( path )
            
            self = super().__new__(cls)
            
            self.size = stat.st_size
            self.modify_time = stat.st_mtime
            
            return self
        
        except OSError:
            return NoFileContent()

    #//-------------------------------------------------------//
    
    def   __eq__( self, other ):        return type(self) == type(other) and (self.size == other.size) and (self.modify_time == other.modify_time)
    def   __ne__( self, other ):        return not self.__eq__( other )
    
    def     __getnewargs__(self):       return ( _Unpickling(), )
    def   __getstate__( self ):         return { 'size': self.size, 'modify_time': self.modify_time }
    def   __setstate__( self, state ):  self.size = state['size']; self.modify_time = state['modify_time']
    
    def   __str__( self ):              return str( datetime.datetime.fromtimestamp( self.modify_time ) )
    

#//===========================================================================//

class   FileName (str):
    def     __new__(cls, path = None, str_new_args = None ):
        if isinstance( path, FileName ):
            return path
        
        if isinstance( path, _Unpickling ):
            return super().__new__(cls, *str_new_args )
        
        if path is None:
            return super().__new__(cls)
        
        full_path = os.path.normcase( os.path.normpath( os.path.abspath( str(path) ) ) )
        
        return super().__new__(cls, full_path )
    
    #//-------------------------------------------------------//
    
    def     __getnewargs__(self):
        return ( _Unpickling(), super().__getnewargs__() )

#//===========================================================================//

class   FileValue (Value):
    
    def   __init__( self, name, content = FileContentChecksum ):
        super().__init__( name, content )
    
    def   exists( self ):
        return type(self.content) is not NoFileContent


#//===========================================================================//
