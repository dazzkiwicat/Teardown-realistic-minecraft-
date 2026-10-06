#!/usr/bin/env python3
"""Generate the zombie model: mod/vox/zombie.vox.

Classic Minecraft zombie proportions at 1 voxel = 0.1 m: 0.5 m head, 0.6 m
wide, arms out in front. Height 1.7 m. Made of WOOD so a sledgehammer, a
shotgun or a car can break it (that is how you kill one), and so it never
gets stuck inside hard material.

The model's origin is its bottom centre, which keeps the maths in
mod/script/village.lua simple: the body position is the zombie's feet.

    python3 -I tools/make_zombie.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import blocks  # noqa: E402
import vox  # noqa: E402

SKIN = (44, 140, 76)
SKIN_DARK = (30, 100, 54)
SHIRT = (0, 150, 150)
TROUSERS = (58, 58, 136)
EYES = (20, 20, 20)
BOOT = (40, 40, 90)

# Palette: all wood (57-72) so the whole zombie is one soft material.
LO = blocks.PALETTE_RANGES["wood"][0]
palette = [(0, 0, 0)] * 255
colours = {}


def idx(rgb):
    if rgb not in colours:
        colours[rgb] = LO + len(colours)
        palette[colours[rgb] - 1] = rgb
    return colours[rgb]


# Model space: x = left/right (width 6), y = front/back (depth 9 with arms),
# z = up (17). Front of the zombie faces +y.
W, D, H = 6, 9, 17
v = {}


def fill(x0, x1, y0, y1, z0, z1, rgb):
    i = idx(rgb)
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                v[(x, y, z)] = i


# legs: two 2x3 columns, 6 tall, body depth is y 1..4
fill(0, 2, 1, 4, 0, 1, BOOT)
fill(4, 6, 1, 4, 0, 1, BOOT)
fill(0, 2, 1, 4, 1, 6, TROUSERS)
fill(4, 6, 1, 4, 1, 6, TROUSERS)
# torso 6 wide, 3 deep, 6 tall
fill(0, 6, 1, 4, 6, 12, SHIRT)
# arms out front: 2x2 cross-section, 6 long along +y from the shoulders
fill(0, 2, 3, 9, 10, 12, SKIN)
fill(4, 6, 3, 9, 10, 12, SKIN)
# head 5x5x5, centred, slightly forward
fill(0, 5, 0, 5, 12, 17, SKIN)
# face: eyes and a dark mouth on the front face (+y side at y=4)
v[(1, 4, 15)] = idx(EYES)
v[(3, 4, 15)] = idx(EYES)
fill(1, 4, 4, 5, 13, 14, SKIN_DARK)

# Shift x so width 6 is centred (head is 5 wide -> offset by 0.5 is not
# possible in voxels, so the head sits flush left; fine for a zombie).
out = Path(__file__).parent.parent / "mod" / "vox" / "zombie.vox"
out.parent.mkdir(parents=True, exist_ok=True)
n = vox.write(str(out), (W, D, H), v, palette)
print(f"{out}: {len(v)} voxels, {n} bytes, palette {sorted(colours.values())}")
