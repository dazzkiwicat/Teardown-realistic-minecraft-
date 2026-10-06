#!/usr/bin/env python3
"""Build the whole mod from the Minecraft templates: vox files, ground tiles,
mod/main.xml, layout.json and a preview picture of the village.

    python3 -I tools/build_level.py

World axes are Teardown's: x east, y up, z = Minecraft z (south). Ground top
is y = 0. Every structure vox has its origin at its bottom centre (see
vox.write), so a chunk is placed by the centre of its footprint.

Templates have their foundation layer at Minecraft y = 0, which in a real
Minecraft village replaces the top block of the terrain. So every structure
chunk sits at y = -1 and the ground is carved away under the cells that the
template's own foundation fills.

Layout: a 5 x 5 grid of plots, pitch 18 m. The fountain is the centre (and
the crossing); two roads of street tiles run north-south and east-west
through it; the 16 corner plots get one structure each; four lamps stand
around the fountain. Every oak door is its own dynamic body (door_pose).
"""
import json
import math
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

R = blocks.R
SRC = ROOT / "source/minecraft/village/plains"
MOD = ROOT / "mod"
VOXDIR = MOD / "vox"
PREVIEW = ROOT / "preview"

# Files in mod/vox that this build does not make but must keep.
KEEP = {"zombie.vox"}           # written by tools/make_zombie.py, used by village.lua

# ---- the village ------------------------------------------------------------
PITCH = 18                      # plot pitch, metres
PLOT_MAX = 16                   # a structure must fit in 16 x 16 blocks
CENTRE = "town_centers/plains_fountain_01"
STREET = "streets/straight_01"  # its dirt_path strip runs along Minecraft z
LAMP = "plains_lamp_1"

# The 16 plots that are not the centre or a road, one structure each.
# Inner ring first (small houses near the fountain), farms on the corners.
HOUSES = {
    (-1, -1): "houses/plains_small_house_1",
    (1, -1): "houses/plains_small_house_2",
    (-1, 1): "houses/plains_small_house_3",
    (1, 1): "houses/plains_small_house_4",
    (-2, -1): "houses/plains_medium_house_1",
    (2, -1): "houses/plains_medium_house_2",
    (-2, 1): "houses/plains_big_house_1",
    (2, 1): "houses/plains_library_1",
    (-1, -2): "houses/plains_temple_4",
    (1, -2): "houses/plains_butcher_shop_1",
    (-1, 2): "houses/plains_armorer_house_1",
    (1, 2): "houses/plains_tool_smith_1",
    (-2, -2): "houses/plains_small_farm_1",
    (2, -2): "houses/plains_large_farm_1",
    (-2, 2): "houses/plains_animal_pen_1",
    (2, 2): "houses/plains_stable_1",
}
# Templates whose footprint is over 16 x 16 blocks, and what replaces them.
# plains_library_1 is 11 x 17 blocks (17 > 16); plains_library_2 (8 x 9) is
# the other library in the set.
SWAPS = {"houses/plains_library_1": "houses/plains_library_2"}

# ---- ground -----------------------------------------------------------------
TILE = 20                       # ground tile edge, metres (every layer)
MARGIN = 12                     # ground beyond the layout bounding box, metres
BUDGET_MB = 90                  # keep mod/vox under this
ROCK = (90, 90, 95)
PATH_SHADES = [c for _, c in blocks.texture("dirt_path")[1]]
# z-road path strip (world x cells) and x-road strip (world z cells), from
# straight_01: path at template x 6..8 of 16. See road_cells().

# ---- world placement --------------------------------------------------------
BOUNDARY = 62                   # play area half-size, metres
SPAWN_RING = 52                 # zombie spawn ring radius, metres
SPAWN_COUNT = 12

# Teardown's rot="0 <yaw> 0" turns the model about world y. With YAW_SIGN = +1
# we assume the right-hand rule (y up): local +x goes to world
# (cos yaw, 0, -sin yaw), so yaw 90 points local +x to world -z (north) and
# local +z to world +x. If doors and the east-west road come out mirrored in
# the game, set YAW_SIGN = -1: every yaw and swing below follows it.
YAW_SIGN = +1


def yaw_dir(yaw_deg):
    """World (x, z) direction that the model's local +x points to."""
    a = math.radians(yaw_deg)
    return math.cos(a), -YAW_SIGN * math.sin(a)


def rotate_xz(dx, dz, yaw_deg):
    """Rotate a local (x, z) offset by yaw about world y."""
    ux, uz = yaw_dir(yaw_deg)            # where local +x goes
    vx, vz = yaw_dir(yaw_deg - 90 * YAW_SIGN)   # where local +z goes
    return dx * ux + dz * vx, dx * uz + dz * vz


# ---- doors ------------------------------------------------------------------
LEFT_OF = {"north": "west", "south": "east", "east": "north", "west": "south"}
PANEL_HALF = blocks.DOOR_T / R / 2       # half the panel thickness: 0.09375 m


def door_pose(x0, z0, by, door):
    """Where the shared door model goes for one Minecraft door.

    The model (mod/vox/door_oak.vox) has its origin on the HINGE edge at the
    bottom, the panel extending along local +x for 1 m, 3 voxels thick
    centred on the origin, 2 m tall.

    In world metres (x east, z = Minecraft z south), the door's cell is
    [cx, cx+1) x [cz, cz+1) with cx = x0 + bx, cz = z0 + bz, bottom y = -1 + by.

      closed panel: against the cell side OPPOSITE to `facing`, its centre
                    line PANEL_HALF in from that side:
                      facing north -> z = cz + 1 - 0.09375 (south edge)
                      facing south -> z = cz + 0.09375     (north edge)
                      facing east  -> x = cx + 0.09375     (west edge)
                      facing west  -> x = cx + 1 - 0.09375 (east edge)
      hinge=left:   the hinge is on the LEFT looking in the facing direction:
                      facing north -> west end  (x = cx)
                      facing south -> east end  (x = cx + 1)
                      facing east  -> north end (z = cz)
                      facing west  -> south end (z = cz + 1)
      hinge=right:  the other end of the same panel.
      yaw:          turns local +x onto the direction hinge -> free end
                    (see yaw_dir / YAW_SIGN for the rotation sense):
                      panel towards east  -> yaw 0
                      panel towards north -> yaw 90
                      panel towards west  -> yaw 180
                      panel towards south -> yaw -90
      swing:        +1 if increasing yaw moves the free end towards `facing`
                    (Minecraft doors open into the facing direction), else -1.
      open=true:    the closed pose turned 90 degrees in the swing direction.
    """
    facing = door["facing"]
    fx, fz = blocks.DIR[facing]
    cx, cz = x0 + door["bx"], z0 + door["bz"]
    hinge_side = LEFT_OF[facing] if door["hinge"] == "left" else blocks.OPPOSITE[LEFT_OF[facing]]
    hx, hz = blocks.DIR[hinge_side]
    if fz:   # facing north/south: panel runs along x
        px = cx + 0.5 + 0.5 * hx
        pz = cz + 0.5 - fz * (0.5 - PANEL_HALF)
    else:    # facing east/west: panel runs along z
        px = cx + 0.5 - fx * (0.5 - PANEL_HALF)
        pz = cz + 0.5 + 0.5 * hz
    dx, dz = -hx, -hz                                   # hinge -> free end
    yaw = math.degrees(math.atan2(-YAW_SIGN * dz, dx))  # inverse of yaw_dir
    a = math.radians(yaw)
    tx, tz = -math.sin(a), -YAW_SIGN * math.cos(a)      # d/dyaw of yaw_dir
    swing = 1 if tx * fx + tz * fz > 0 else -1
    if door.get("open"):
        yaw += 90 * swing
    yaw = (yaw + 180) % 360 - 180
    if abs(yaw + 180) < 1e-9:
        yaw = 180.0
    return (px, -1 + by, pz), round(yaw, 6) + 0.0, swing


# ---- structures -------------------------------------------------------------
def plan():
    """[(template, cx, cz, yaw)] for the whole village."""
    items = [(CENTRE, 0, 0, 0)]
    for k in (1, 2):
        for s in (-1, 1):
            items.append((STREET, 0, s * k * PITCH, 0))     # north-south road: as authored
            items.append((STREET, s * k * PITCH, 0, 90))    # east-west road: turned
    for (i, j), name in HOUSES.items():
        items.append((SWAPS.get(name, name), i * PITCH, j * PITCH, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            items.append((LAMP, sx * 6, sz * 6, 0))
    return items


def build_structures():
    placed, cache = [], {}
    for name, cx, cz, yaw in plan():
        stem = Path(name).name
        if name not in cache:
            info = mc2vox.convert(str(SRC / f"{name}.nbt"), str(VOXDIR / stem))
            cache[name] = info
            print(f"  {name}: {info['blocks_placed']} blocks, {info['voxels']} voxels, "
                  f"{len(info['chunks'])} chunk(s), {len(info['doors'])} door(s)")
        info = cache[name]
        sx, sy, sz = info["size_blocks"]
        if sx > PLOT_MAX or sz > PLOT_MAX:
            raise SystemExit(f"{name} is {sx} x {sz} blocks, over {PLOT_MAX} x {PLOT_MAX}; "
                             f"add it to SWAPS")
        if yaw and info["doors"]:
            raise SystemExit(f"{name}: doors on a turned structure are not supported")
        x0, z0 = cx - sx // 2, cz - sz // 2      # integer, so cells align with the ground
        mx, mz = x0 + sx / 2, z0 + sz / 2        # footprint centre = turning point
        chunks = []
        for c in info["chunks"]:
            ox = x0 + c["bx0"] + c["sx"] / 2 - mx
            oz = z0 + c["bz0"] + c["sz"] / 2 - mz
            rx, rz = rotate_xz(ox, oz, yaw)
            chunks.append({"file": f"MOD/vox/{c['file']}", "x": mx + rx, "z": mz + rz})
        cells = set()
        for bx, bz in info["ground_cells"]:
            rx, rz = rotate_xz(bx + 0.5 - sx / 2, bz + 0.5 - sz / 2, yaw)
            cells.add((math.floor(mx + rx), math.floor(mz + rz)))
        doors = []
        for d in info["doors"]:
            pos, dyaw, swing = door_pose(x0, z0, d["by"], d)
            doors.append({**d, "pos": pos, "yaw": dyaw, "swing": swing})
        # footprint after turning (a square street tile keeps its rectangle)
        fx, fz = (sz, sx) if yaw % 180 else (sx, sz)
        placed.append({
            "name": name, "cx": cx, "cz": cz, "yaw": yaw,
            "x0": mx - fx / 2, "z0": mz - fz / 2, "sx": fx, "sz": fz, "sy": sy,
            "chunks": chunks, "doors": doors, "ground_cells": sorted(cells),
        })
    return placed


def road_cells(placed):
    """Ground cells painted as dirt path so the roads run unbroken between the
    street tiles and the fountain (tiles are 16 m on an 18 m pitch)."""
    # The path strip of the street tile, located from the placed tiles' own
    # carved path cells: the x cells used by the north-south tiles and the z
    # cells used by the east-west ones.
    xs, zs = set(), set()
    for p in placed:
        if p["name"] != STREET:
            continue
        for wx, wz in p["ground_cells"]:
            # the strip is 3 cells next to the tile centre; jigsaw grass
            # cells further out are not part of it
            if p["yaw"] % 180 == 0 and abs(wx + 0.5 - p["cx"]) < 2.5:
                xs.add(wx)
            elif p["yaw"] % 180 and abs(wz + 0.5 - p["cz"]) < 2.5:
                zs.add(wz)
    reach = 2 * PITCH + PLOT_MAX // 2
    cells = set()
    for t in range(-reach, reach):
        cells |= {(x, t) for x in xs} | {(t, z) for z in zs}
    return cells


# ---- ground -----------------------------------------------------------------
def ground_extent(placed):
    x0 = min(p["x0"] for p in placed) - MARGIN
    x1 = max(p["x0"] + p["sx"] for p in placed) + MARGIN
    z0 = min(p["z0"] for p in placed) - MARGIN
    z1 = max(p["z0"] + p["sz"] for p in placed) + MARGIN
    r = lambda v, f: int(f(v / TILE) * TILE)  # noqa: E731
    return r(x0, math.floor), r(x1, math.ceil), r(z0, math.floor), r(z1, math.ceil)


def build_ground(placed, top_voxels=5):
    """Three layers of 20 m tiles. Returns (tiles, files written).

    1. top:  scale 1 (0.1 m), top_voxels thick, grass speckle on the top row,
             dirt speckle below, path speckle on road cells. Carved.
    2. mid:  scale 2 (0.2 m), 3 voxels (0.6 m), dirt speckle. Carved.
    3. rock: scale 4 (0.4 m), 3 voxels (1.2 m), unbreakable rock. One file
             shared by every tile (they are identical).
    Carving removes the Minecraft cells that a template's foundation fills
    (mc2vox ground_cells), not whole rectangles: most templates fill only
    part of their rectangle at y = 0 (a street tile fills 53 of 256 cells).
    """
    gx0, gx1, gz0, gz1 = ground_extent(placed)
    carved = set()
    for p in placed:
        carved |= set(p["ground_cells"])
    roads = road_cells(placed)

    top_h = top_voxels * 0.1
    y_top, y_mid = -top_h, -top_h - 0.6
    y_rock = y_mid - 1.2

    dirt_lo = blocks.PALETTE_RANGES["dirt"][0]
    pal = [(0, 0, 0)] * 255
    shades = blocks.DIRT_SHADES + blocks.GRASS_SHADES + PATH_SHADES
    for k, c in enumerate(shades):
        pal[dirt_lo - 1 + k] = c
    I_DIRT = dirt_lo + np.arange(3)
    I_GRASS = dirt_lo + 3 + np.arange(3)
    I_PATH = dirt_lo + 6 + np.arange(3)
    rock_pal = [(0, 0, 0)] * 255
    rock_i = blocks.PALETTE_RANGES["rock"][0]
    rock_pal[rock_i - 1] = ROCK

    rng = np.random.RandomState(7)
    tiles, files = [], []
    rock_file = "ground_rock.vox"
    vox.write(str(VOXDIR / rock_file), (50, 50, 3), np.full((50, 50, 3), rock_i, np.uint8),
              rock_pal, name="ground_rock")
    files.append(rock_file)

    for ix, tx in enumerate(range(gx0, gx1, TILE)):
        for iz, tz in enumerate(range(gz0, gz1, TILE)):
            # cell masks for this tile, 1 m resolution
            cut = np.zeros((TILE, TILE), bool)
            path = np.zeros((TILE, TILE), bool)
            for (wx, wz) in carved:
                if tx <= wx < tx + TILE and tz <= wz < tz + TILE:
                    cut[wx - tx, wz - tz] = True
            for (wx, wz) in roads:
                if tx <= wx < tx + TILE and tz <= wz < tz + TILE:
                    path[wx - tx, wz - tz] = True

            n = TILE * 10
            top = I_DIRT[rng.randint(0, 3, (n, n, top_voxels))].astype(np.uint8)
            path10 = np.repeat(np.repeat(path, 10, 0), 10, 1)
            surface = np.where(path10, I_PATH[rng.randint(0, 3, (n, n))],
                               I_GRASS[rng.randint(0, 3, (n, n))])
            top[:, :, -1] = surface
            top[np.repeat(np.repeat(cut, 10, 0), 10, 1)] = 0
            fname = f"ground_top_{ix}_{iz}.vox"
            vox.write(str(VOXDIR / fname), top.shape, top, pal, name="ground_top")
            files.append(fname)

            m = TILE * 5
            mid = I_DIRT[rng.randint(0, 3, (m, m, 3))].astype(np.uint8)
            mid[np.repeat(np.repeat(cut, 5, 0), 5, 1)] = 0
            fname_m = f"ground_mid_{ix}_{iz}.vox"
            vox.write(str(VOXDIR / fname_m), mid.shape, mid, pal, name="ground_mid")
            files.append(fname_m)

            cx, cz = tx + TILE / 2, tz + TILE / 2
            tiles += [
                {"layer": "top", "file": f"MOD/vox/{fname}", "x": cx, "y": y_top, "z": cz, "scale": 1,
                 "voxels": int(np.count_nonzero(top))},
                {"layer": "mid", "file": f"MOD/vox/{fname_m}", "x": cx, "y": y_mid, "z": cz, "scale": 2,
                 "voxels": int(np.count_nonzero(mid))},
                {"layer": "rock", "file": f"MOD/vox/{rock_file}", "x": cx, "y": y_rock, "z": cz, "scale": 4,
                 "voxels": 50 * 50 * 3},
            ]
    return tiles, files, (gx0, gx1, gz0, gz1)


# ---- main.xml ---------------------------------------------------------------
def f(v):
    """Compact number for XML."""
    s = f"{v:.5f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def write_xml(placed, tiles, extent):
    gx0, gx1, gz0, gz1 = extent
    span = max(gx1 - gx0, gz1 - gz0) + 10
    L = []
    L.append(f'<scene version="1.6.0" shadowVolume="{span} 60 {span}">')
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
    for i in range(SPAWN_COUNT):
        a = i * 2 * math.pi / SPAWN_COUNT
        L.append(f'  <location tags="zombiespawn" pos="{f(SPAWN_RING * math.cos(a))} 0.5 '
                 f'{f(SPAWN_RING * math.sin(a))}"/>')
    L.append('  <group name="Ground">')
    for t in tiles:
        L.append(f'    <body><vox file="{t["file"]}" pos="{f(t["x"])} {f(t["y"])} {f(t["z"])}" '
                 f'scale="{t["scale"]}"/></body>')
    L.append('  </group>')
    L.append('  <group name="Village">')
    for p in placed:
        L.append(f'    <body name="{Path(p["name"]).name}">')
        rot = f' rot="0 {p["yaw"]} 0"' if p["yaw"] else ""
        for c in p["chunks"]:
            L.append(f'      <vox file="{c["file"]}" pos="{f(c["x"])} -1 {f(c["z"])}"{rot} '
                     f'scale="{f(blocks.SCALE)}"/>')
        L.append('    </body>')
    L.append('  </group>')
    L.append('  <group name="Doors">')
    for p in placed:
        for d in p["doors"]:
            x, y, z = d["pos"]
            sw = "+1" if d["swing"] > 0 else "-1"
            L.append(f'    <body dynamic="true" tags="door swing={sw}"><vox file="MOD/vox/door_oak.vox" '
                     f'pos="{f(x)} {f(y)} {f(z)}" rot="0 {f(d["yaw"])} 0" scale="{f(blocks.SCALE)}"/></body>')
    L.append('  </group>')
    L.append('</scene>')
    (MOD / "main.xml").write_text("\n".join(L) + "\n")


# ---- preview ----------------------------------------------------------------
def preview_village(placed, extent, roads):
    """One voxel per Minecraft block, whole ground area, isometric PNG."""
    gx0, gx1, gz0, gz1 = extent
    nx, nz = gx1 - gx0, gz1 - gz0
    hmax = max(p["sy"] for p in placed)
    grid = np.zeros((nx, nz, hmax), dtype=np.uint8)   # vox axes: x, z(world), up
    colours = {}

    def idx(rgb):
        rgb = tuple(int(c) for c in rgb)
        if rgb not in colours:
            colours[rgb] = len(colours) + 1
        return colours[rgb]

    grid[:, :, 0] = idx(blocks.GRASS_SHADES[0])
    for wx, wz in roads:
        if gx0 <= wx < gx1 and gz0 <= wz < gz1:
            grid[wx - gx0, wz - gz0, 0] = idx(PATH_SHADES[0])
    for p in placed:
        root = load(str(SRC / f"{p['name']}.nbt"))
        sx, _, sz = root["size"]
        mx, mz = p["x0"] + p["sx"] / 2, p["z0"] + p["sz"] / 2
        for bx, by, bz, name, _ in mc2vox.block_list(root):
            if name not in blocks.PREVIEW_COLOUR:
                continue
            # PREVIEW_COLOUR takes a texture's first shade, which for
            # grass_block is the dirt underneath; show its top instead.
            rgb = blocks.GRASS_SHADES[0] if name == "grass_block" else blocks.PREVIEW_COLOUR[name]
            rx, rz = rotate_xz(bx + 0.5 - sx / 2, bz + 0.5 - sz / 2, p["yaw"])
            x = math.floor(mx + rx) - gx0
            z = math.floor(mz + rz) - gz0
            if 0 <= x < nx and 0 <= z < nz and by < hmax:
                grid[x, z, by] = idx(rgb)
    palette = [(0, 0, 0)] + sorted(colours, key=colours.get)
    img, faces = render(grid, palette, scale=7)
    out = PREVIEW / "village.png"
    img.save(out)
    return out, faces


# ---- main -------------------------------------------------------------------
def dir_mb():
    return sum(p.stat().st_size for p in VOXDIR.iterdir() if p.is_file()) / 1e6


def main():
    VOXDIR.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    print("structures:")
    placed = build_structures()
    tiles, ground_files, extent = build_ground(placed)

    # the files this build owns; anything else in mod/vox is stale
    produced = set(ground_files) | {"door_oak.vox"} | KEEP
    for p in placed:
        stem = Path(p["name"]).name
        produced.add(f"{stem}.json")
        produced |= {Path(c["file"]).name for c in p["chunks"]}
    removed = []
    for fpath in sorted(VOXDIR.iterdir()):
        if fpath.is_file() and fpath.name not in produced:
            fpath.unlink()
            removed.append(fpath.name)

    top_note = "top ground layer 0.5 m"
    if dir_mb() > BUDGET_MB:
        tiles, ground_files, extent = build_ground(placed, top_voxels=4)
        top_note = f"OVER {BUDGET_MB} MB at 0.5 m: top ground layer reduced to 0.4 m"
    write_xml(placed, tiles, extent)

    roads = road_cells(placed)
    (PREVIEW / "layout.json").write_text(json.dumps(
        {"extent": extent, "placed": placed, "tiles": tiles}, indent=1))
    out, faces = preview_village(placed, extent, roads)

    n_doors = sum(len(p["doors"]) for p in placed)
    n_chunks = sum(len(p["chunks"]) for p in placed)
    files = {Path(c["file"]).name for p in placed for c in p["chunks"]}
    print(f"structures placed: {len(placed)} ({len({p['name'] for p in placed})} templates)")
    print(f"chunks placed: {n_chunks} ({len(files)} distinct vox files)")
    print(f"doors: {n_doors}")
    print(f"ground: {len(tiles)} tiles ({len(tiles) // 3} per layer), extent x {extent[0]}..{extent[1]}, "
          f"z {extent[2]}..{extent[3]}; {top_note}")
    if removed:
        print(f"removed stale files: {', '.join(removed)}")
    print(f"mod/vox total: {dir_mb():.1f} MB (budget {BUDGET_MB} MB)")
    print(f"main.xml written; preview {out.relative_to(ROOT)} ({faces} faces)")


if __name__ == "__main__":
    main()
