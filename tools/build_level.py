#!/usr/bin/env python3
"""Build the whole mod from the Minecraft templates: vox files, ground tiles,
mod/main.xml, and a preview picture of the village.

    python3 -I tools/build_level.py

World axes are Teardown's: x east, y up, z south (Minecraft z). Ground top is
y = 0. Each structure is placed by the CENTRE of its footprint, because every
vox we write has its origin at its bottom centre (see vox.write).

Templates have their foundation layer at Minecraft y = 0, which in a real
Minecraft village sits flush with the ground. So houses are placed at y = -1
and the metre of ground under each footprint is removed; the template's own
grass, path and cobble blocks fill the hole.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blocks  # noqa: E402
import mc2vox  # noqa: E402
import vox  # noqa: E402
from nbt import load  # noqa: E402
from render import render  # noqa: E402

B = blocks.B
SRC = ROOT / "source/minecraft/village/plains"
MOD = ROOT / "mod"

# ---- the village ------------------------------------------------------------
# (template path relative to SRC, centre x, centre z). All face as authored.
# Kept small on purpose: the mechanics come first, more houses later.
LAYOUT = [
    ("town_centers/plains_fountain_01", 0, 0),
    ("houses/plains_small_house_1", -13, -11),
    ("houses/plains_small_house_2", 13, -11),
    ("houses/plains_small_house_3", -13, 11),
    ("houses/plains_medium_house_1", 15, 13),
    ("houses/plains_small_farm_1", 0, -17),
    ("houses/plains_animal_pen_1", 0, 16),
    ("plains_lamp_1", -7, -7),
    ("plains_lamp_1", 7, -7),
    ("plains_lamp_1", -7, 7),
    ("plains_lamp_1", 7, 7),
]

TILE = 20                   # ground tile edge, metres
GROUND_HALF = 30            # ground covers -30..30 in x and z
DIRT_M, ROCK_M = 2, 1       # ground thickness: 2 m dirt on 1 m unbreakable rock
BOUNDARY = 40               # play area half-size, metres
SPAWN_RING = 27             # zombie spawn ring radius, metres
GRASS_A, GRASS_B = (110, 170, 60), (100, 160, 55)
DIRT = blocks.C["dirt"]
ROCK = (90, 90, 95)


def footprint(info):
    sx, _, sz = info["size_blocks"]
    return sx, sz


def build_structures():
    """Convert every template in LAYOUT. Returns list of dicts with placement."""
    placed = []
    cache = {}
    for name, cx, cz in LAYOUT:
        if name not in cache:
            out = MOD / "vox" / (Path(name).name + ".vox")
            cache[name] = mc2vox.convert(str(SRC / f"{name}.nbt"), str(out))
            print(f"  {name}: {cache[name]['blocks_placed']} blocks -> {out.name}")
        info = cache[name]
        sx, sz = footprint(info)
        placed.append({
            "name": name, "file": f"MOD/vox/{Path(name).name}.vox",
            "cx": cx, "cz": cz, "sx": sx, "sz": sz,
            # footprint in world metres (half-open)
            "x0": cx - sx / 2, "x1": cx + sx / 2, "z0": cz - sz / 2, "z1": cz + sz / 2,
        })
    return placed


def build_ground(placed):
    """Ground tiles with the top metre carved out under each footprint."""
    tiles = []
    thick = (DIRT_M + ROCK_M) * B
    pal = [(0, 0, 0)] * 255
    lo = blocks.PALETTE_RANGES["dirt"][0]
    rock_lo = blocks.PALETTE_RANGES["rock"][0]
    I_GA, I_GB, I_DIRT, I_ROCK = lo, lo + 1, lo + 2, rock_lo
    pal[I_GA - 1], pal[I_GB - 1], pal[I_DIRT - 1], pal[I_ROCK - 1] = GRASS_A, GRASS_B, DIRT, ROCK

    for tx in range(-GROUND_HALF, GROUND_HALF, TILE):
        for tz in range(-GROUND_HALF, GROUND_HALF, TILE):
            n = TILE * B
            g = np.zeros((n, n, thick), dtype=np.uint8)
            g[:, :, :ROCK_M * B] = I_ROCK
            g[:, :, ROCK_M * B:thick - 1] = I_DIRT
            # blocky grass: alternate two greens per Minecraft block
            xi = np.arange(n) // B
            zi = np.arange(n) // B
            checker = (xi[:, None] + zi[None, :]) % 2 == 0
            g[:, :, thick - 1] = np.where(checker, I_GA, I_GB)
            # carve the top metre under every structure footprint
            for p in placed:
                x0 = max(int(round((p["x0"] - tx) * B)), 0)
                x1 = min(int(round((p["x1"] - tx) * B)), n)
                z0 = max(int(round((p["z0"] - tz) * B)), 0)
                z1 = min(int(round((p["z1"] - tz) * B)), n)
                if x0 < x1 and z0 < z1:
                    g[x0:x1, z0:z1, thick - B:thick] = 0
            fname = f"ground_{tx + GROUND_HALF:03d}_{tz + GROUND_HALF:03d}.vox"
            vox.write(str(MOD / "vox" / fname), (n, n, thick), g, pal, name="ground")
            tiles.append({"file": f"MOD/vox/{fname}", "cx": tx + TILE / 2, "cz": tz + TILE / 2,
                          "y": -(DIRT_M + ROCK_M)})
    return tiles


def write_xml(placed, tiles):
    L = []
    L.append('<scene version="1.6.0" shadowVolume="120 60 120">')
    # Daytime look; the script dims these at night. Attribute names follow
    # the Teardown editor's environment node.
    L.append('  <environment template="sunny" skyboxrot="-90" sunBrightness="3.0" '
             'skyboxbrightness="1.0" ambient="1.0" nightlight="false" fogParams="40 100 0.9 2"/>')
    L.append('  <spawnpoint pos="0 0.2 8" rot="0 180 0"/>')
    L.append('  <boundary pad="5">')
    for x, z in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        L.append(f'    <vertex pos="{x * BOUNDARY} {z * BOUNDARY}"/>')
    L.append('  </boundary>')
    L.append('  <script file="MOD/script/village.lua" param0="daylength=240" '
             'param1="maxzombies=4" param2="starttime=0.3"/>')
    import math
    for i in range(8):
        a = i * math.pi / 4
        L.append(f'  <location tags="zombiespawn" pos="{SPAWN_RING * math.cos(a):.1f} 0.5 '
                 f'{SPAWN_RING * math.sin(a):.1f}"/>')
    L.append('  <group name="Ground">')
    for t in tiles:
        L.append(f'    <body><vox file="{t["file"]}" pos="{t["cx"]} {t["y"]} {t["cz"]}"/></body>')
    L.append('  </group>')
    L.append('  <group name="Village">')
    for p in placed:
        L.append(f'    <body name="{Path(p["name"]).name}"><vox file="{p["file"]}" '
                 f'pos="{p["cx"]} -1 {p["cz"]}"/></body>')
    L.append('  </group>')
    L.append('</scene>')
    (MOD / "main.xml").write_text("\n".join(L) + "\n")


def preview_village(placed):
    """One voxel per Minecraft block, whole village, isometric PNG."""
    half = GROUND_HALF
    n = 2 * half
    hmax = 14
    grid = np.zeros((n, n, hmax + 1), dtype=np.uint8)
    colours = {}

    def idx(rgb):
        if rgb not in colours:
            colours[rgb] = len(colours) + 1
        return colours[rgb]

    grid[:, :, 0] = idx(GRASS_A)
    for p in placed:
        root = load(str(SRC / f"{p['name']}.nbt"))
        pal = root.get("palette") or root["palettes"][0]
        for blk in root["blocks"]:
            e = pal[blk["state"]]
            name = (e.get("id") or e.get("Name")).split(":", 1)[-1]
            if name == "jigsaw":
                name = mc2vox.parse_state((blk.get("nbt") or {}).get("final_state", "minecraft:air"))[0]
            entry = blocks.TABLE.get(name)
            if not entry:
                continue
            bx, by, bz = blk["pos"]
            x = int(p["x0"]) + bx + half
            z = int(p["z0"]) + bz + half
            if 0 <= x < n and 0 <= z < n and by <= hmax:
                grid[x, z, by] = idx(blocks.C[entry[2]])
    palette = [(0, 0, 0)] + [rgb for rgb, _ in sorted(colours.items(), key=lambda kv: kv[1])]
    img, faces = render(grid, palette, scale=9)
    out = ROOT / "preview" / "village.png"
    out.parent.mkdir(exist_ok=True)
    img.save(out)
    return out, faces


if __name__ == "__main__":
    (MOD / "vox").mkdir(parents=True, exist_ok=True)
    print("structures:")
    placed = build_structures()
    tiles = build_ground(placed)
    write_xml(placed, tiles)
    (ROOT / "preview").mkdir(exist_ok=True)
    (ROOT / "preview" / "layout.json").write_text(json.dumps({"placed": placed, "tiles": tiles}, indent=1))
    out, faces = preview_village(placed)
    print(f"ground tiles: {len(tiles)}; main.xml written; preview {out.name} ({faces} faces)")
