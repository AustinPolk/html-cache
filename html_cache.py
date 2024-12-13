import hashlib
import blosc2
import sys

# custom implementation of a database table with two columns, url and html
# the url will be hashed and used as a search key on the table, which will be sorted by hash value (hashing done with SHA256)
# the html will be compressed bytes that are decompressed when fetched (compression done thru blosc2)
class html_cache:
    def __init__(self):
        self.index: list[bytes] = []    # index of cache, will be hashes of known urls
        self.content: list[bytes] = []  # cache content, bytes representing compressed html

        # constants
        self._int_width: int = 5
        self._byteorder: str = sys.byteorder
        self._hash_width: int = 32

    def _hash_url(self, url: str) -> bytes:
        return hashlib.sha256(url.encode('utf-8')).digest()
    
    def _compress(self, html_content: bytes) -> bytes:
        return blosc2.compress(html_content)
    
    def _decompress(self, compressed: bytes) -> bytes:
        return blosc2.decompress(compressed)
    
    # find the index of this hash in the table index list or where this hash would be inserted,
    # return that index and a boolean indicating whether the hash exists at this index
    def _find_index(self, hashed: bytes) -> int:
        if not self.index:
            return 0, False

        L = 0
        R = len(self.index) - 1
        mid = lambda: (R - L) // 2 + L

        while L <= R:
            m = mid()
            if self.index[m] < hashed:
                L = m + 1
            elif self.index[m] > hashed:
                R = m - 1
            else:
                return m, True

        return L, False
    
    # check if this url has cached html data
    def is_cached(self, url: str) -> bool:
        hashed = self._hash_url(url)
        _, in_cache = self._find_index(hashed)
        return in_cache
    
    # cache this html_content using the url as a key.
    # will update the content if the url already exists as a key
    def cache(self, url: str, html_content: bytes) -> None:
        hashed = self._hash_url(url)
        compressed = self._compress(html_content)
        idx, in_cache = self._find_index(hashed)
        if in_cache:
            self.content[idx] = compressed
        else:
            # TODO: do I need to do idx + 1 or just idx
            self.index.insert(idx, hashed)
            self.content.insert(idx, compressed)

    # get a cached value if it exists, otherwise return None
    def retrieve(self, url: str) -> bytes | None:
        hashed = self._hash_url(url)
        idx, in_cache = self._find_index(hashed)
        if not in_cache:
            return None
        compressed = self.content[idx]
        decompressed = self._decompress(compressed)
        return decompressed
    
    # save the cache to a binary file
    # file format of saved file:
    # integer signifying the number of entries in the index (5 byte integer)
    # bytes of each hash value in the index, in order (32 bytes each)
    # for each content:
    #   integer signifying the length of the compressed content (5 byte integer)
    #   bytes in compressed content (variable byte length)
    def save(self, filepath: str) -> None:
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
    def load(self, filepath: str) -> None:
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
