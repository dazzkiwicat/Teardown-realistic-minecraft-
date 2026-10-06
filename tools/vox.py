"""Write and read MagicaVoxel .vox files (the model format Teardown loads).

Teardown decides a voxel's MATERIAL from its palette index (see PALETTE_RANGES
in blocks.py), so this writer takes a palette of up to 255 RGBA colours and a
dict of voxels keyed by (x, y, z) -> palette index (1..255).

Axes: MagicaVoxel is Z-up. Teardown turns vox Z into world "up" when loading.

The reader below is deliberately separate from the writer so that a written
file can be checked by something that does not share the writer's assumptions
(if the writer mis-sizes a chunk, the reader will fail or report odd counts).
"""
import struct

MAX_SIZE = 256  # MagicaVoxel limit per model axis; Teardown honours it too.


def _chunk(cid: bytes, content: bytes, children: bytes = b"") -> bytes:
    return cid + struct.pack("<ii", len(content), len(children)) + content + children


def _dict(pairs: dict) -> bytes:
    out = struct.pack("<i", len(pairs))
    for k, v in pairs.items():
        for s in (k, v):
            b = s.encode()
            out += struct.pack("<i", len(b)) + b
    return out


def write(path: str, size, voxels, palette: list, emissive: dict | None = None,
          name: str = "model", pivot="bottom-center"):
    """size: (sx, sy, sz).  voxels: {(x,y,z): index} or a numpy uint8 array of
    shape size (0 = empty).  palette: list of up to 255 (r,g,b) or (r,g,b,a);
    palette[i] is palette index i+1.
    emissive: {palette_index: strength} marks indices that glow (torches).

    The file gets a one-model scene graph whose translation puts the model's
    BOTTOM CENTRE at the file origin. Teardown places a vox file's origin at
    the <vox pos=...> you give it, so pos is "where the feet / foundation
    centre goes", the same for every model regardless of its size.

    pivot: "bottom-center" (default, translation (0, 0, sz//2)) or an
    explicit (tx, ty, tz) translation in voxels written into the nTRN _t.
    MagicaVoxel puts the model's centre at _t, so the model spans
    [t - size/2, t + size/2) on each axis and the file origin is the pivot.
    Example: a door of size (16, 3, 32) with pivot (8, 0, 16) spans x 0..16,
    y -1.5..1.5, z 0..32, i.e. the origin is on the hinge edge at the bottom."""
    sx, sy, sz = size
    for axis, n in zip("xyz", size):
        if not 1 <= n <= MAX_SIZE:
            raise ValueError(f"{path}: size {axis}={n} outside 1..{MAX_SIZE}")
    if pivot == "bottom-center":
        tx, ty, tz = 0, 0, sz // 2
    elif isinstance(pivot, str):
        raise ValueError(f"{path}: unknown pivot {pivot!r}")
    else:
        tx, ty, tz = (int(v) for v in pivot)
    if len(palette) > 255:
        raise ValueError(f"{path}: palette has {len(palette)} colours, max 255")

    if hasattr(voxels, "shape"):  # numpy grid fast path
        import numpy as np
        if tuple(voxels.shape) != tuple(size):
            raise ValueError(f"{path}: grid shape {voxels.shape} != size {size}")
        xs, ys, zs = np.nonzero(voxels)
        idxs = voxels[xs, ys, zs]
        count = len(xs)
        arr = np.stack([xs, ys, zs, idxs], axis=1).astype(np.uint8)
        xyzi = struct.pack("<i", count) + arr.tobytes()
    else:
        count = len(voxels)
        xyzi = struct.pack("<i", count)
        for (x, y, z), idx in voxels.items():
            if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
                raise ValueError(f"{path}: voxel {(x, y, z)} outside size {size}")
            if not 1 <= idx <= 255:
                raise ValueError(f"{path}: palette index {idx} outside 1..255")
            xyzi += struct.pack("<4B", x, y, z, idx)

    rgba = b""
    for i in range(256):
        if i < len(palette):
            c = palette[i]
            r, g, b = c[:3]
            a = c[3] if len(c) > 3 else 255
        else:
            r, g, b, a = 0, 0, 0, 255
        rgba += struct.pack("<4B", r, g, b, a)

    body = _chunk(b"SIZE", struct.pack("<iii", sx, sy, sz))
    body += _chunk(b"XYZI", xyzi)
    # Scene graph: root transform -> group -> transform -> shape(model 0).
    # MagicaVoxel puts a model's centre at its transform's _t, so the default
    # _t = (0, 0, sz//2) leaves the horizontal centre at the origin and the
    # base at z=0. An explicit pivot replaces it (see docstring).
    body += _chunk(b"nTRN", struct.pack("<i", 0) + _dict({}) + struct.pack("<iiii", 1, -1, 0, 1) + _dict({}))
    body += _chunk(b"nGRP", struct.pack("<i", 1) + _dict({}) + struct.pack("<ii", 1, 2))
    body += _chunk(b"nTRN", struct.pack("<i", 2) + _dict({"_name": name})
                   + struct.pack("<iiii", 3, -1, 0, 1) + _dict({"_t": f"{tx} {ty} {tz}"}))
    body += _chunk(b"nSHP", struct.pack("<i", 3) + _dict({}) + struct.pack("<i", 1)
                   + struct.pack("<i", 0) + _dict({}))
    body += _chunk(b"RGBA", rgba)
    for idx, strength in (emissive or {}).items():
        # MagicaVoxel material chunk: emissive with flux. Teardown reads these
        # to make voxels glow (used for torches and lanterns).
        body += _chunk(b"MATL", struct.pack("<i", idx) + _dict({
            "_type": "_emit", "_emit": "1", "_flux": str(strength)}))

    data = b"VOX " + struct.pack("<i", 150) + _chunk(b"MAIN", b"", body)
    with open(path, "wb") as fh:
        fh.write(data)
    return len(data)


def read(path: str):
    """Independent reader. Returns dict with size, voxel count, palette index
    histogram, list of chunk ids and the model's _t translation (the pivot).
    Raises on structural errors."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != b"VOX ":
        raise ValueError("not a vox file")
    version = struct.unpack_from("<i", data, 4)[0]
    pos = 8
    out = {"version": version, "chunks": [], "size": None, "count": 0, "hist": {},
           "translation": None}

    def walk(start, end):
        nonlocal pos
        p = start
        while p < end:
            cid = data[p:p + 4]
            clen, klen = struct.unpack_from("<ii", data, p + 4)
            cstart = p + 12
            out["chunks"].append(cid.decode())
            if cid == b"SIZE":
                out["size"] = struct.unpack_from("<iii", data, cstart)
            elif cid == b"XYZI":
                n = struct.unpack_from("<i", data, cstart)[0]
                out["count"] += n
                if clen != 4 + 4 * n:
                    raise ValueError(f"XYZI claims {n} voxels but chunk is {clen} bytes")
                # numpy for speed (ground tiles hold 200k voxels each); the
                # checks are the same as a per-voxel loop.
                import numpy as np
                arr = np.frombuffer(data, dtype=np.uint8, count=4 * n,
                                    offset=cstart + 4).reshape(n, 4)
                sx, sy, sz = out["size"]
                bad = (arr[:, 0] >= sx) | (arr[:, 1] >= sy) | (arr[:, 2] >= sz)
                if bad.any():
                    x, y, z = (int(v) for v in arr[np.argmax(bad), :3])
                    raise ValueError(f"voxel {(x, y, z)} outside SIZE {out['size']}")
                if (arr[:, 3] == 0).any():
                    raise ValueError("voxel with palette index 0")
                flat = arr[:, 0].astype(np.int64) * sy * sz + arr[:, 1].astype(np.int64) * sz + arr[:, 2]
                if len(np.unique(flat)) != n:
                    raise ValueError("duplicate voxel positions")
                ids, cnt = np.unique(arr[:, 3], return_counts=True)
                for i, c in zip(ids.tolist(), cnt.tolist()):
                    out["hist"][i] = out["hist"].get(i, 0) + c
            elif cid == b"nTRN":
                # node id, attribute dict, child, reserved, layer, frame count,
                # then one frame dict per frame; keep any _t translation.
                q = cstart + 4
                def rdict(q):
                    d = {}
                    k = struct.unpack_from("<i", data, q)[0]; q += 4
                    for _ in range(k):
                        pair = []
                        for _ in range(2):
                            ln = struct.unpack_from("<i", data, q)[0]; q += 4
                            pair.append(data[q:q + ln].decode()); q += ln
                        d[pair[0]] = pair[1]
                    return d, q
                _, q = rdict(q)
                q += 12
                nframes = struct.unpack_from("<i", data, q)[0]; q += 4
                for _ in range(nframes):
                    frame, q = rdict(q)
                    if "_t" in frame:
                        out["translation"] = tuple(int(v) for v in frame["_t"].split())
            walk(cstart + clen, cstart + clen + klen)
            p = cstart + clen + klen
        if p != end:
            raise ValueError("chunk sizes do not add up")

    walk(pos, len(data))
    return out
