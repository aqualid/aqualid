
class AvlMap (object):
    
    class Node (object):
        __slots__ = ( 'top', 'left', 'right', 'key', 'value', 'balance' )
        
        def __init__( self, key, value, top = None ):
            assert (top is None) or (type( top ) is type(self))
            
            self.top = top
            self.left = None
            self.right = None
            self.key = key
            self.value = value
            self.balance = 0
        
        #//-------------------------------------------------------//
        
        def detach( self, node ):
            assert (node is self.left) or (node is self.right)
            
            if self.left is node:
                self.left = None
            else:
                self.right = None
            
            if node is not None:
                node.top = None
        
        #//-------------------------------------------------------//
        
        def replace( self, old_node, new_node ):
            if self.left is old_node:
                self.left = new_node
            else:
                self.right = new_node
            
            if new_node is not None:
                new_node.top = self
        
        #//-------------------------------------------------------//
        
        def __getitem__(self, direction ):
            if direction is -1:
                return self.left
            
            return self.right
        
        #//-------------------------------------------------------//
        
        def __setitem__(self, direction, node ):
            if direction is -1:
                self.left = node
            else:
                self.right = node
            
            if node is not None:
                node.top = self
        
        #//-------------------------------------------------------//
        
        def   __str__(self):
            return str(self.value)
    
    #//=======================================================//
    
    __slots__ = ('head')
    
    def __init__(self, dict = {} ):
        self.head = None
        
        for key, value in dict.iteritems():
            self[ key ] = value
    
    #//-------------------------------------------------------//
    
    def     __rebalance( self, node ):
        assert node is not None
        
        while True:
            top = node.top
            if top is None:
                break
            
            if top.left is node:
                direction = -1
            else:
                direction = 1
            
            balance = direction + top.balance
            top.balance = balance
            if balance is 0:
                break   # rebalance is not needed anymore
            
            elif (balance is not -1) and (balance is not 1):
                self.__rotate( top, direction )
                break
            
            node = top
    
    #//-------------------------------------------------------//
    
    def   __rotate(self, node, direction ):
        if direction is node[direction].balance:
            self.__rotateDirect( node, direction )
        else:
            self.__rotateIndirect( node, direction )
    
    #//-------------------------------------------------------//
    
    def   __rotateDirect( self, node, direction ):
        top = node[direction]
        right = top[-direction]
        node_top = node.top
        
        node[direction] = right
        node.balance = 0
        
        top[ -direction ] = node
        top.balance = 0
        
        if node_top is None:
            self.head = top
            top.top = None
        else:
            node_top.replace( node, top )
    
    #//-------------------------------------------------------//
    
    def   __rotateIndirect( self, node, direction ):
        neg_direction = -direction
        
        node_top = node.top
        left = node[direction]
        top = left[neg_direction]
        top_left = top[direction]
        top_right = top[neg_direction]
        
        left[ neg_direction ] = top_left
        node[ direction ]=  top_right
        
        if top.balance is neg_direction:
            left.balance = direction
            node.balance = 0
        elif top.balance is direction:
            node.balance = neg_direction
            left.balance = 0
        else:
            node.balance = 0
            left.balance = 0
        
        top[ direction ] = left
        top[ neg_direction ] = node
        top.balance = 0
        
        if node_top is None:
            self.head = top
            top.top = None
        else:
            node_top.replace( node, top )
    
    #//-------------------------------------------------------//
    
    def     __find( self, key ):
        head = self.head
        
        while head is not None:
            if key < head.key:
                head = head.left
            elif head.key < key:
                head = head.right
            else:
                return head
        
        return None
    
    #//-------------------------------------------------------//
    
    def     __insert( self, key, value ):
        
        head = self.head
        
        if head is None:
            self.head = AvlMap.Node( key, value )
            return
        
        while True:
            if key < head.key:
                head_left = head.left
                if head_left is None:
                    node = AvlMap.Node( key, value, head )
                    head.left = node
                    self.__rebalance( node )
                    return
                else:
                    head = head_left
            
            elif head.key < key:
                head_right = head.right
                if head_right is None:
                    node = AvlMap.Node( key, value, head )
                    head.right = node
                    self.__rebalance( node )
                    return
                else:
                    head = head_right
            else:
                head.value = value
                return
    
    #//-------------------------------------------------------//
    
    def __str__(self):
        return "<AvlMap object>"
    
    #//-------------------------------------------------------//
    
    def __repr__(self):
        return "<AvlMap object>"
    
    #//-------------------------------------------------------//
    
    def __getitem__(self, key ):
        node = self.__find(key)
        if node is not None:
            return node.value
        
        raise KeyError(str(key))
    
    #//-------------------------------------------------------//
    
    def __setitem__(self, key, value ):
        self.__insert( key, value )
    
    #//-------------------------------------------------------//
    
    def __delitem__(self, key):
        raise KeyError("Not implemented yet")
    
    #//-------------------------------------------------------//
    
    def __contains__(self, key):
        return self.__find( key ) is not None
    
    #//-------------------------------------------------------//
    
    def has_key(self, key):
        return self.__find( key ) is not None
    
    #//-------------------------------------------------------//
    
    def get(self, key, default = None):
        node = self.__find(key)
        if node is not None:
            return node.value
        return default
    
    #//-------------------------------------------------------//
    
    def setdefault( self, key, value = None ):
        node = self.__find( key )
        if node is not None:
            return node.value
        
        self.__insert( key, value )
        return value
