#!/usr/bin/env python3
"""Convert a Minecraft structure template (.nbt) into Teardown-ready .vox files.

    python3 -I tools/mc2vox.py source/minecraft/village/plains/houses/plains_small_house_1.nbt mod/vox/plains_small_house_1

The second argument is an output STEM (no extension). Writes:
  <stem>.vox                 if the template fits in one chunk, else
  <stem>__<i>_<j>.vox        one per chunk of at most 16 x 16 blocks (x, z),
  <stem>.json                sizes, chunk offsets, doors, palette materials,
  mod/vox/door_oak.vox       the shared door model (once, if missing).

Every block is R x R x R voxels (blocks.R = 16) at <vox scale=blocks.SCALE>.
Geometry comes from blocks.parts, colours from blocks.texture.

Axis change: the grid is built in Minecraft axes (x east, y up, z south) and
transposed to MagicaVoxel's z-up (x, z, y) when a chunk is written.

Doors are not part of the structure: each oak door becomes its own dynamic
body in main.xml (see build_level.door_pose), so it can swing.
"""
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blocks  # noqa: E402
import vox  # noqa: E402
from nbt import load  # noqa: E402

R = blocks.R
FLAME_FLUX = 6           # emissive strength for torch flames
CHUNK_BLOCKS = vox.MAX_SIZE // R   # 16 blocks = 256 voxels per vox model axis
DOOR_FILE = Path(__file__).resolve().parent.parent / "mod" / "vox" / "door_oak.vox"
DOOR_WINDOW = (4, 12, 20, 28)      # x0, x1, z0, z1 voxels left empty in the panel

# Blocks at template y = 0 that fill their cell like ground does. Only these
# cells are carved out of the ground under a structure (so a lamp's fence
# post or a farm's water channel does not leave a 1 m pit).
GROUND_LIKE_KINDS = {"cube", "path", "stairs", "slab"}


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
        rgb = tuple(int(c) for c in rgb)
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

    def lut(self, shades):
        """Lookup table: lut[shade id] -> palette index."""
        return np.array([self.index(m, c) for m, c in shades], dtype=np.uint8)


def parse_state(state: str):
    """'minecraft:oak_stairs[facing=north,half=top]' -> ('oak_stairs', {...})"""
    name, _, rest = state.partition("[")
    props = {}
    if rest:
        for kv in rest.rstrip("]").split(","):
            k, _, v = kv.partition("=")
            props[k] = v
    return name.split(":", 1)[-1], props


def block_list(root):
    """Yield (bx, by, bz, name, props) for every block, jigsaws resolved."""
    palette_list = root.get("palette") or root["palettes"][0]
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
        yield bx, by, bz, name, props


def write_door_model(path=DOOR_FILE):
    """The one shared oak door: vox size (R, 3, 2R) = 16 wide, 3 thick, 32
    tall, planks texture, with a small window. Pivot (R//2, 0, R) puts the
    file origin on the HINGE edge at the bottom, so the model spans x 0..16
    (panel extends along +x), y -1.5..1.5, z 0..32."""
    vol, shades = blocks.texture("planks")      # Minecraft axes (x, y up, z)
    pal = Palette()
    lut = pal.lut(shades)
    t = blocks.DOOR_T
    # vox (x, y=thickness, z=up) <- texture (x, z slice, y tiled twice)
    tex = np.concatenate([vol, vol], axis=1)[:, :, :t]   # (R, 2R, t): x, up, thick
    grid = lut[np.transpose(tex, (0, 2, 1))]               # (R, t, 2R)
    x0, x1, z0, z1 = DOOR_WINDOW
    grid[x0:x1, :, z0:z1] = 0
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    vox.write(str(path), grid.shape, grid, pal.colours, name="door_oak", pivot=(R // 2, 0, R))
    return int(np.count_nonzero(grid))


def chunk_ranges(n):
    """Split n blocks into runs of at most CHUNK_BLOCKS: [(start, length), ...]."""
    return [(s, min(CHUNK_BLOCKS, n - s)) for s in range(0, n, CHUNK_BLOCKS)]


def convert(nbt_path: str, out_stem: str, seed: int = 1):
    root = load(nbt_path)
    sx, sy, sz = root["size"]
    rng = random.Random(seed)
    pal = Palette()
    luts = {}
    grid = np.zeros((sx * R, sy * R, sz * R), dtype=np.uint8)   # Minecraft axes
    emissive = {}
    missing = set()
    doors = []
    ground_cells = set()
    block_count = 0

    for bx, by, bz, name, props in block_list(root):
        if name == "oak_door":
            if props.get("half", "lower") == "lower":
                doors.append({"bx": bx, "by": by, "bz": bz,
                              "facing": props.get("facing", "north"),
                              "hinge": props.get("hinge", "left"),
                              "open": props.get("open", "false") == "true"})
                block_count += 1
                if by == 0:
                    # A door standing in the foundation layer: carve the
                    # ground under it so the dynamic door body is free.
                    ground_cells.add((bx, bz))
            continue
        try:
            parts = list(blocks.parts(name, props, rng))
        except KeyError:
            missing.add(name)
            continue
        if not parts:
            continue
        block_count += 1
        if by == 0 and blocks.TABLE[name][0] in GROUND_LIKE_KINDS:
            ground_cells.add((bx, bz))
        ox, oy, oz = bx * R, by * R, bz * R
        for boxes, tex in parts:
            if tex not in luts:
                vol, shades = blocks.texture(tex)
                lut = pal.lut(shades)
                for (m, _), idx in zip(shades, lut):
                    if m == "unphysical":
                        emissive[int(idx)] = FLAME_FLUX
                luts[tex] = (vol, lut)
            vol, lut = luts[tex]
            for x0, x1, y0, y1, z0, z1 in boxes:
                grid[ox + x0:ox + x1, oy + y0:oy + y1, oz + z0:oz + z1] = lut[vol[x0:x1, y0:y1, z0:z1]]

    if missing:
        raise ValueError(f"{nbt_path}: unmapped block names {sorted(missing)}; "
                         f"add them to blocks.TABLE")

    stem = Path(out_stem)
    if stem.suffix == ".vox":
        stem = stem.with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)
    xr, zr = chunk_ranges(sx), chunk_ranges(sz)
    single = len(xr) * len(zr) == 1
    chunks = []
    total = 0
    nbytes = 0
    for i, (bx0, csx) in enumerate(xr):
        for j, (bz0, csz) in enumerate(zr):
            part = grid[bx0 * R:(bx0 + csx) * R, :, bz0 * R:(bz0 + csz) * R]
            n = int(np.count_nonzero(part))
            if n == 0:
                continue
            v = np.ascontiguousarray(np.transpose(part, (0, 2, 1)))  # MC (x,y,z) -> vox (x,z,y)
            fname = f"{stem.name}.vox" if single else f"{stem.name}__{i}_{j}.vox"
            nbytes += vox.write(str(stem.parent / fname), v.shape, v, pal.colours, emissive,
                                name=fname[:-4])
            chunks.append({"file": fname, "bx0": bx0, "bz0": bz0, "sx": csx, "sz": csz,
                           "voxels": n})
            total += n

    door_written = False
    if doors and not DOOR_FILE.exists():
        write_door_model()
        door_written = True

    info = {
        "source": str(nbt_path),
        "size_blocks": [sx, sy, sz],
        "blocks_placed": block_count,
        "voxels": total,
        "bytes": nbytes,
        "chunks": chunks,
        "doors": doors,
        "ground_cells": sorted([list(c) for c in ground_cells]),
        "materials": {str(i): m for i, m in sorted(pal.material_of.items())},
        "emissive_indices": sorted(emissive),
        "door_model_written": door_written,
    }
    (stem.parent / f"{stem.name}.json").write_text(json.dumps(info, indent=1))
    return info


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    info = convert(sys.argv[1], sys.argv[2])
    print(f"{info['source']} -> {sys.argv[2]}: {info['blocks_placed']} blocks, "
          f"{info['voxels']} voxels in {len(info['chunks'])} chunk(s), "
          f"{len(info['doors'])} door(s), {info['bytes']} bytes")
