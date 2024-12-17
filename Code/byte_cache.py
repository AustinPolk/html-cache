import hashlib
import brotli
import sys

# custom implementation of a database table with two columns, url and html
# the url will be hashed and used as a search key on the table, which will be sorted by hash value (hashing done with SHA256)
# the html will be compressed bytes that are decompressed when fetched (compression done thru blosc2)
class byte_cache:
    def __init__(self, cache_file: str, cache_index: int) -> None:
        self.index: list[bytes] = []            # index of cache, will be hashes of known urls
        self.content: list[bytes] = []          # cache content, bytes representing compressed html
        self.cache_file: str = cache_file       # filepath where contents are saved to and loaded from
        self.cache_index: int = 0               # index of this cache, appended to cache_file to form a filename

    # find the index of this key in the table index list or where this key would be inserted,
    # return that index and a boolean indicating whether the key actually exists at this index
    def _find_index(self, key: bytes) -> int:
        if not self.index:
            return 0, False

        L = 0
        R = len(self.index) - 1
        mid = lambda: (R - L) // 2 + L

        while L <= R:
            m = mid()
            if self.index[m] < key:
                L = m + 1
            elif self.index[m] > key:
                R = m - 1
            else:
                return m, True

        return L, False
    
    # check if this url has cached html data
    def is_cached(self, key: bytes) -> bool:
        _, in_cache = self._find_index(key)
        return in_cache
    
    # cache this html_content using the url as a key.
    # will update the content if the url already exists as a key
    def cache(self, key: bytes, content: bytes) -> None:
        idx, in_cache = self._find_index(key)
        if in_cache:
            self.content[idx] = content
        else:
            self.index.insert(idx, key)
            self.content.insert(idx, content)

    # get a cached value if it exists, otherwise return None
    def retrieve(self, key: bytes) -> bytes | None:
        idx, in_cache = self._find_index(key)
        if not in_cache:
            return None
        return self.content[idx]
        
    # save the cache to a binary file
    # file format of saved file:
    # integer signifying the number of entries in the index
    # bytes of each hash value in the index, in order
    # for each content:
    #   integer signifying the length of the compressed content
    #   bytes in compressed content (variable byte length)
    def save(self, int_width: int, byte_order: str) -> None:
        filepath = f'{self.cache_file}-{self.cache_index}'
        with open(filepath, 'wb+') as f:
            index_size = len(self.index)
            index_size_bytes = index_size.to_bytes(self._int_width, self._byteorder)
            f.write(index_size_bytes)
            for hashed in self.index:
                f.write(hashed)
            for content in self.content:
                content_size = len(content)
                content_size_bytes = content_size.to_bytes(self._int_width, self._byteorder)
                f.write(content_size_bytes)
                f.write(content)

    # load the cache from a binary file, following the same spec used in the save method
    def load(self, index_width: int, int_width: int, byte_order: str) -> None:
        filepath = f'{self.cache_file}-{self.cache_index}'
        with open(filepath, 'rb') as f:
            index_size_bytes = f.read(self._int_width)
            index_size = int.from_bytes(index_size_bytes, self._byteorder)
            for _ in range(index_size):
                hashed = f.read(self._hash_width)
                self.index.append(hashed)
            for _ in range(index_size):
                content_size_bytes = f.read(self._int_width)
                content_size = int.from_bytes(content_size_bytes, self._byteorder)
                content = f.read(content_size)
                self.content.append(content)

    # load only the index from a binary file
    def load_index(self, index_width: int, int_width: int, byte_order: str) -> None:
        filepath = f'{self.cache_file}-{self.cache_index}'
        with open(filepath, 'rb') as f:
            index_size_bytes = f.read(self._int_width)
            index_size = int.from_bytes(index_size_bytes, self._byteorder)
            for _ in range(index_size):
                hashed = f.read(self._hash_width)
                self.index.append(hashed)

    # split this cache into two separate caches, distribute half of the elements to each cache,
    # return a tuple of the two new caches
    def split(self) -> tuple:
        lesser = byte_cache(self.cache_file, 2 * self.cache_index)
        greater = byte_cache(self.cache_file, 2 * self.cache_index + 1)

        midpoint = len(self.index) // 2
        lesser.index = self.index[:midpoint]
        lesser.content = self.content[:midpoint]
        greater.index = self.index[midpoint:]
        greater.content = self.index[midpoint:]

        return (lesser, greater)
