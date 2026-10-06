#!/usr/bin/env python3
"""Convert a Minecraft structure template (.nbt) into a Teardown-ready .vox.

    python3 -I tools/mc2vox.py source/minecraft/village/plains/houses/plains_small_house_1.nbt mod/vox/plains_small_house_1.vox

Also writes <out>.json next to the vox with the block size, voxel count and the
palette-index -> material map, so the result can be checked without Teardown.

Axis change: Minecraft is (x east, y up, z south). MagicaVoxel is z-up, so a
Minecraft voxel (x, y, z) is stored as vox (x, z, y).
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import blocks  # noqa: E402
import vox  # noqa: E402
from nbt import load  # noqa: E402

B = blocks.B
FLAME_FLUX = 6  # emissive strength for torch flames


class Palette:
    """Hands out palette indices inside the Teardown range for each material.
    Same (material, colour) always gets the same index. If a material's range
    fills up, the nearest existing colour in that range is reused."""

    def __init__(self):
        self.colours = [(0, 0, 0)] * 255  # index i+1 -> rgb
        self.used = {}  # (material, rgb) -> index
        self.next_free = {m: lo for m, (lo, hi) in blocks.PALETTE_RANGES.items()}
        self.material_of = {}  # index -> material

    def index(self, material, rgb):
        key = (material, rgb)
        if key in self.used:
            return self.used[key]
        lo, hi = blocks.PALETTE_RANGES[material]
        idx = self.next_free[material]
        if idx > hi:
            # range full: reuse nearest colour already allocated to this material
            cands = [(sum((a - b) ** 2 for a, b in zip(rgb, c)), i)
                     for (m, c), i in self.used.items() if m == material]
            idx = min(cands)[1]
            self.used[key] = idx
            return idx
        self.next_free[material] = idx + 1
        self.colours[idx - 1] = rgb
        self.used[key] = idx
        self.material_of[idx] = material
        return idx


def parse_state(state: str):
    """'minecraft:oak_stairs[facing=north,half=top]' -> ('oak_stairs', {...})"""
    name, _, rest = state.partition("[")
    props = {}
    if rest:
        for kv in rest.rstrip("]").split(","):
            k, _, v = kv.partition("=")
            props[k] = v
    return name.split(":", 1)[-1], props


def convert(nbt_path: str, out_path: str, seed: int = 1):
    root = load(nbt_path)
    palette_list = root.get("palette") or root["palettes"][0]
    sx, sy, sz = root["size"]
    rng = random.Random(seed)
    pal = Palette()
    voxels = {}
    emissive = {}
    missing = set()
    block_count = 0

    for blk in root["blocks"]:
        entry = palette_list[blk["state"]]
        name = (entry.get("id") or entry.get("Name")).split(":", 1)[-1]
        props = entry.get("properties") or entry.get("Properties") or {}
        if name == "jigsaw":
            # Jigsaw blocks mark where streets join; the template says what
            # block should replace them when placed in a real world.
            final = (blk.get("nbt") or {}).get("final_state", "minecraft:air")
            name, props = parse_state(final)
        bx, by, bz = blk["pos"]
        placed = False
        try:
            for coords, material, rgb in blocks.parts(name, props, rng):
                idx = pal.index(material, rgb)
                if material == "unphysical":
                    emissive[idx] = FLAME_FLUX
                for (x, y, z) in coords:
                    # Minecraft (x, y up, z) -> vox (x, z, y up)
                    voxels[(bx * B + x, bz * B + z, by * B + y)] = idx
                placed = True
        except KeyError as e:
            missing.add(name)
        if placed:
            block_count += 1

    if missing:
        raise SystemExit(f"{nbt_path}: unmapped blocks {sorted(missing)}")

    size = (sx * B, sz * B, sy * B)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    nbytes = vox.write(str(out), size, voxels, pal.colours, emissive)

    info = {
        "source": nbt_path,
        "size_blocks": [sx, sy, sz],
        "size_voxels_xyz_vox": list(size),
        "blocks_placed": block_count,
        "voxels": len(voxels),
        "bytes": nbytes,
        "materials": {str(i): m for i, m in sorted(pal.material_of.items())},
        "emissive_indices": sorted(emissive),
    }
    out.with_suffix(".json").write_text(json.dumps(info, indent=1))
    return info


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    info = convert(sys.argv[1], sys.argv[2])
    print(f"{info['source']} -> {sys.argv[2]}: {info['blocks_placed']} blocks, "
          f"{info['voxels']} voxels, {info['bytes']} bytes")
