from byte_cache import byte_cache

class cache_tree_node:
    def __init__(self) -> None:
        self.left_child: cache_tree_node|None = None   # left child, if any, which receives all keys less than search key
        self.right_child: cache_tree_node|None = None  # right child, if any, which receives all keys greater than or equal to the search key
        self.cache: byte_cache|None = None               # cache that this node represents, if this is a leaf node
        self.search_key: bytes|None = None           # key used to split lookups between children, if this is an internal node
    
    def insert(self, key: bytes, value: bytes) -> None:
        if self.search_key: # if this is an internal node
            if key < self.search_key:
                self.left_child.insert(key, value)
            else:
                self.right_child.insert(key, value)
        else: # if this is a leaf node
            self.cache.cache(key, value)

    def find(self, key: bytes) -> bytes|None:
        if self.search_key: # if this is an internal node
            if key < self.search_key:
                return self.left_child.find(key)
            else:
                return self.right_child.find(key)
        else: # if this is a leaf node
            return self.cache.retrieve(key)
        
    def split(self) -> None:
        lesser, greater = self.cache.split()

        # delete the references to this cache, let gc take care of the underlying
        del self.cache.index
        del self.cache.content
        del self.cache

        # set the search key to be the minimum element in the greater cache
        # (an alternative could be the mean of this and greatest element in the lesser cache)
        self.search_key = greater.index[0]

        self.left_child = lesser
        self.right_child = greater

# implementation of search tree
class cache_tree:
    def __init__(self, split_threshold: int):
        self.root: cache_tree_node = None
        self.split_threshold: int = split_threshold

        self.int_width = 5
        self.index_width = 32
        self.byte_order = 'little'
        