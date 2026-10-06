"""Minimal reader for Minecraft NBT files (the format of the village structure
templates in source/minecraft/).

Why our own parser: it is about 60 lines, needs no pip install, and the
structure files only use a handful of tag types. Every tag type is handled
anyway so an unexpected file fails loudly rather than silently.

Usage from Python:
    from nbt import load
    root = load("plains_small_house_1.nbt")   # returns plain dicts/lists/ints
"""
import gzip
import struct

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = range(7)
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = range(7, 13)


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def take(self, fmt: str):
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, self.data, self.pos)
        self.pos += size
        return value[0] if len(value) == 1 else value

    def string(self) -> str:
        length = self.take(">H")
        raw = self.data[self.pos:self.pos + length]
        self.pos += length
        return raw.decode("utf-8", errors="replace")

    def payload(self, tag: int):
        if tag == TAG_BYTE:
            return self.take(">b")
        if tag == TAG_SHORT:
            return self.take(">h")
        if tag == TAG_INT:
            return self.take(">i")
        if tag == TAG_LONG:
            return self.take(">q")
        if tag == TAG_FLOAT:
            return self.take(">f")
        if tag == TAG_DOUBLE:
            return self.take(">d")
        if tag == TAG_BYTE_ARRAY:
            n = self.take(">i")
            return list(self.take(f">{n}b")) if n else []
        if tag == TAG_STRING:
            return self.string()
        if tag == TAG_LIST:
            item_tag = self.take(">b")
            n = self.take(">i")
            return [self.payload(item_tag) for _ in range(n)]
        if tag == TAG_COMPOUND:
            out = {}
            while True:
                child_tag = self.take(">b")
                if child_tag == TAG_END:
                    return out
                name = self.string()
                out[name] = self.payload(child_tag)
        if tag == TAG_INT_ARRAY:
            n = self.take(">i")
            return list(self.take(f">{n}i")) if n else []
        if tag == TAG_LONG_ARRAY:
            n = self.take(">i")
            return list(self.take(f">{n}q")) if n else []
        raise ValueError(f"unknown NBT tag type {tag} at byte {self.pos}")


def load(path: str):
    """Read a gzipped (or plain) NBT file and return the root compound as a dict."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    reader = _Reader(raw)
    root_tag = reader.take(">b")
    if root_tag != TAG_COMPOUND:
        raise ValueError(f"{path}: root tag is {root_tag}, expected compound")
    reader.string()  # root name, normally empty
    return reader.payload(TAG_COMPOUND)
