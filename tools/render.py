#!/usr/bin/env python3
"""Draw an isometric PNG preview of one or more .vox files.

    python3 -I tools/render.py mod/vox/plains_small_house_1.vox preview/house1.png [pixels_per_voxel]

Why: we cannot run Teardown in this container, so this is how we look at a
build before Darren loads it. Colours come from the vox palette; the three
visible faces are shaded top / right / left so shapes read clearly.
"""
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import vox  # noqa: E402


def load_grid(path):
    """Return (grid[x,y,z] of palette index, palette list of rgb)."""
    with open(path, "rb") as fh:
        data = fh.read()
    size = None
    grid = None
    palette = [(0, 0, 0)] * 256
    p = 8

    def walk(start, end):
        nonlocal size, grid, palette
        q = start
        while q < end:
            cid = data[q:q + 4]
            clen, klen = struct.unpack_from("<ii", data, q + 4)
            c = q + 12
            if cid == b"SIZE":
                size = struct.unpack_from("<iii", data, c)
                grid = np.zeros(size, dtype=np.uint8)
            elif cid == b"XYZI":
                n = struct.unpack_from("<i", data, c)[0]
                arr = np.frombuffer(data, dtype=np.uint8, count=4 * n, offset=c + 4).reshape(n, 4)
                grid[arr[:, 0], arr[:, 1], arr[:, 2]] = arr[:, 3]
            elif cid == b"RGBA":
                raw = np.frombuffer(data, dtype=np.uint8, count=1024, offset=c).reshape(256, 4)
                palette = [(int(r), int(g), int(b)) for r, g, b, _ in raw]
                palette = [(0, 0, 0)] + palette[:-1]  # RGBA[i] is index i+1
            walk(c + clen, c + clen + klen)
            q = c + clen + klen

    walk(p, len(data))
    return grid, palette


def render(grid, palette, scale=4.0, background=(30, 34, 40)):
    sx, sy, sz = grid.shape
    filled = grid > 0
    pad = np.zeros((sx + 1, sy + 1, sz + 1), dtype=bool)
    pad[:sx, :sy, :sz] = filled
    top = filled & ~pad[:sx, :sy, 1:sz + 1]
    xf = filled & ~pad[1:sx + 1, :sy, :sz]
    yf = filled & ~pad[:sx, 1:sy + 1, :sz]

    cos30, sin30 = 0.8660254, 0.5

    # Camera above the (+x, +y) corner looking down towards the origin, so
    # the visible faces are top, +x and +y (the three masks above) and a
    # larger x + y + z is nearer (drawn later). Screen right is (y - x) so
    # the picture is not mirrored: vox axes are right-handed, z up.
    def proj(x, y, z):
        return ((y - x) * cos30 * scale, ((x + y) * sin30 - z) * scale)

    # image bounds
    corners = [proj(*c) for c in [(0, 0, 0), (sx, 0, 0), (0, sy, 0), (sx, sy, 0),
                                  (0, 0, sz), (sx, 0, sz), (0, sy, sz), (sx, sy, sz)]]
    minu = min(c[0] for c in corners); maxu = max(c[0] for c in corners)
    minv = min(c[1] for c in corners); maxv = max(c[1] for c in corners)
    W, H = int(maxu - minu) + 4, int(maxv - minv) + 4
    img = Image.new("RGB", (W, H), background)
    draw = ImageDraw.Draw(img)

    def P(x, y, z):
        u, v = proj(x, y, z)
        return (u - minu + 2, v - minv + 2)

    faces = []  # (depth, polygon, colour)
    for mask, shade, kind in ((yf, 0.62, "y"), (xf, 0.82, "x"), (top, 1.0, "t")):
        xs, ys, zs = np.nonzero(mask)
        for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
            r, g, b = palette[grid[x, y, z]]
            col = (int(r * shade), int(g * shade), int(b * shade))
            if kind == "t":
                poly = [P(x, y, z + 1), P(x + 1, y, z + 1), P(x + 1, y + 1, z + 1), P(x, y + 1, z + 1)]
            elif kind == "x":
                poly = [P(x + 1, y, z), P(x + 1, y + 1, z), P(x + 1, y + 1, z + 1), P(x + 1, y, z + 1)]
            else:
                poly = [P(x, y + 1, z), P(x + 1, y + 1, z), P(x + 1, y + 1, z + 1), P(x, y + 1, z + 1)]
            faces.append((x + y + z, poly, col))
    faces.sort(key=lambda f: f[0])
    for _, poly, col in faces:
        draw.polygon(poly, fill=col)
    return img, len(faces)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
    grid, palette = load_grid(sys.argv[1])
    img, nfaces = render(grid, palette, scale)
    img.save(sys.argv[2])
    print(f"{sys.argv[2]}: {img.size[0]}x{img.size[1]} px, {nfaces} faces drawn")
