#!/usr/bin/env python3
"""Generate the two custom tool models used by mod/script/village.lua:

    mod/vox/pickaxe.vox   a 2x2x20 wooden stick with a 10x4x4 iron head
                          across the top
    mod/vox/placer.vox    a 6x6x6 cobblestone-grey cube on a short stick

Materials come from the palette index (blocks.PALETTE_RANGES): the stick is
wood, the pickaxe head metal, the placer cube concrete (cobblestone).
The origin of each model is its bottom centre (vox.write default), i.e. the
end of the handle.

    python3 -I tools/make_tools.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import blocks  # noqa: E402
import vox  # noqa: E402

OUT = Path(__file__).parent.parent / "mod" / "vox"

WOOD = (120, 85, 50)
WOOD_DARK = (95, 66, 38)
IRON = (200, 200, 205)
IRON_DARK = (150, 150, 158)
STONE = (125, 125, 125)
STONE_DARK = (100, 100, 100)


class Palette:
    """Puts each colour at the next free index inside its material's range."""

    def __init__(self):
        self.colours = [(0, 0, 0)] * 255
        self.index = {}
        self.used = {}

    def __call__(self, material, rgb):
        key = (material, rgb)
        if key not in self.index:
            lo, hi = blocks.PALETTE_RANGES[material]
            i = lo + self.used.get(material, 0)
            if i > hi:
                raise ValueError(f"palette range for {material} is full")
            self.used[material] = self.used.get(material, 0) + 1
            self.index[key] = i
            self.colours[i - 1] = rgb
        return self.index[key]


def fill(v, box, idx):
    x0, x1, y0, y1, z0, z1 = box
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                v[(x, y, z)] = idx


def pickaxe():
    pal = Palette()
    v = {}
    W, D, H = 10, 4, 22
    # stick: 2x2 cross-section, 20 tall, centred in x and y
    for z in range(20):
        fill(v, (4, 6, 1, 3, z, z + 1), pal("wood", WOOD if z % 4 else WOOD_DARK))
    # head: 10 wide, 4 deep, 4 tall, across the top of the stick
    fill(v, (0, 10, 0, 4, 18, 22), pal("metal", IRON))
    # darker tips, like the Minecraft sprite
    fill(v, (0, 1, 0, 4, 18, 21), pal("metal", IRON_DARK))
    fill(v, (9, 10, 0, 4, 18, 21), pal("metal", IRON_DARK))
    return (W, D, H), v, pal.colours


def placer():
    pal = Palette()
    v = {}
    W, D, H = 6, 6, 12
    # short stick: 2x2, 6 tall
    fill(v, (2, 4, 2, 4, 0, 6), pal("wood", WOOD))
    # cobblestone cube on top, with a few dark speckles
    fill(v, (0, 6, 0, 6, 6, 12), pal("concrete", STONE))
    dark = pal("concrete", STONE_DARK)
    for (x, y, z) in [(0, 1, 7), (2, 0, 9), (5, 3, 8), (3, 5, 10), (1, 2, 11), (4, 4, 11), (0, 4, 10), (5, 0, 6)]:
        v[(x, y, z)] = dark
    return (W, D, H), v, pal.colours


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in (("pickaxe", pickaxe), ("placer", placer)):
        size, voxels, palette = make()
        path = OUT / f"{name}.vox"
        n = vox.write(str(path), size, voxels, palette, name=name)
        info = vox.read(str(path))
        if tuple(info["size"]) != size or info["count"] != len(voxels):
            raise SystemExit(f"{path}: re-read mismatch {info['size']} {info['count']}")
        mats = sorted({m for m, (lo, hi) in blocks.PALETTE_RANGES.items()
                       for i in info["hist"] if lo <= i <= hi})
        print(f"{path}: size {size}, {len(voxels)} voxels, {n} bytes, materials {mats}")


if __name__ == "__main__":
    main()
