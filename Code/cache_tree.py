from html_cache import cache

class cache_tree_node:
    def __init__(self) -> None:
        self.left_child: cache_tree_node|None = None   # left child, if any, which receives all keys less than search key
        self.right_child: cache_tree_node|None = None  # right child, if any, which receives all keys greater than or equal to the search key
        self.cache: cache|None = None               # cache that this node represents, if this is a leaf node
        self.search_key: bytes|None = None           # key used to split lookups between children, if this is an internal node
    
    def insert(self, key: bytes, value: bytes) -> None:
        if self.search_key: # if this is an internal node
            if key < self.search_key:
                self.left_child.insert(key, value)
            else:
                self.right_child.insert(key, value)
        else:
            self.cache.cache()

# implementation of a search tree that stores 
class cache_tree:
    def __init__(self):
        self.Root: cache_tree_node = None
        self.Spl