import re

#13.10.3077
#8.00v
#4.1.1
#1.6
#8.42n
#5.5.1

class   Version (str):
  __slots__ = ('__version')
  
    def     __new__(cls, version = None, _ver_re = re.compile(r'[0-9]+[a-zA-Z]*(\.[0-9]+[a-zA-Z]*)*') ):
        
        if isinstance(version, Version):
            return version
        
        if version is None:
            ver_str = ''
        else:
            ver_str = str(version)
        
        match = _ver_re.search( ver_str )
        if match:
            ver_str = match.group()
            ver_list = re.findall(r'[0-9]+|[a-zA-Z]+', ver_str )
        else:
            ver_str = ''
            ver_list = []
        
        self = super(Version, cls).__new__(cls, ver_str)
        
        self.__version = []
        
        append = self.__version.append
        
        for v in ver_list:
            try:
                v = int(v)
            except TypeError:
                pass
            
            append( v )
        
        return self
    
    #//-------------------------------------------------------//
    
    def   __lt__( self, other):       return self.__version < Version( other ).__version
    def   __le__( self, other):       return self.__version <= Version( other ).__version
    def   __eq__( self, other):       return self.__version == Version( other ).__version
    def   __ne__( self, other):       return self.__version != Version( other ).__version
    def   __gt__( self, other):       return self.__version > Version( other ).__version
    def   __ge__( self, other):       return self.__version >= Version( other ).__version
