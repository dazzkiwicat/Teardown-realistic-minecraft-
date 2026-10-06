"""Minecraft block -> Teardown voxel geometry, texture and material.

One Minecraft block is 1 metre and is built from R x R x R voxels (R = 16,
matching Minecraft's 16-pixel textures). Teardown voxels are 0.1 m by
default, so the vox shapes carry scale = 10 / R = 0.625 to make a block one
metre again. Partial blocks (stairs, slabs, fences, doors, panes, torches)
are built from boxes using Minecraft's own pixel measurements.

Coordinates inside this file are MINECRAFT axes: x east, y up, z south.
mc2vox.py swaps to MagicaVoxel's z-up when it writes.

TEXTURES: every block type has a texture volume, an R x R x R array of shade
numbers, generated once from noise or a pattern (cobble cells, plank rows,
brick courses, grass speckle). Each shade is a (material, colour). The
geometry decides which voxels exist, the texture decides their colour.

MATERIAL is what the zombies care about. Teardown reads it from the palette
index of the voxel (PALETTE_RANGES). Zombies bite with MakeHole using only
the soft radius, so they eat glass, grass, dirt, wood, plaster and plastic
but not concrete (cobblestone), brick or metal.
"""
import numpy as np

R = 16                 # voxels per block edge
SCALE = 10 / R         # Teardown <vox scale=...> so that a block is 1 m

# Teardown material by MagicaVoxel palette index (1-based, inclusive),
# read off the official teardown_palette.vox in the modding docs.
# SOFT: glass, foliage(grass), dirt, plastic, wood, plaster.
# MEDIUM: concrete, brick, metal(weak). HARD: hardmasonry, hardmetal.
# UNBREAKABLE: rock, heavymetal.
PALETTE_RANGES = {
    "glass":       (1, 8),
    "foliage":     (9, 24),
    "dirt":        (25, 40),
    "rock":        (41, 56),
    "wood":        (57, 72),
    "concrete":    (73, 88),
    "brick":       (89, 104),
    "plaster":     (105, 120),
    "metal":       (121, 136),
    "heavymetal":  (137, 152),
    "plastic":     (153, 168),
    "hardmetal":   (169, 176),
    "hardmasonry": (177, 184),
    "unphysical":  (225, 240),
}

DIR = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


# =============================================================================
# Geometry: functions return a list of boxes (x0, x1, y0, y1, z0, z1),
# half-open, in voxels 0..R, Minecraft axes.
# =============================================================================
def cube():
    return [(0, R, 0, R, 0, R)]


def side_slab(direction, thickness, y0=0, y1=R):
    dx, dz = DIR[direction]
    if dx == 1:
        return [(R - thickness, R, y0, y1, 0, R)]
    if dx == -1:
        return [(0, thickness, y0, y1, 0, R)]
    if dz == 1:
        return [(0, R, y0, y1, R - thickness, R)]
    return [(0, R, y0, y1, 0, thickness)]


def half_towards(direction, y0, y1):
    dx, dz = DIR[direction]
    h = R // 2
    if dx == 1:
        return (h, R, y0, y1, 0, R)
    if dx == -1:
        return (0, h, y0, y1, 0, R)
    if dz == 1:
        return (0, R, y0, y1, h, R)
    return (0, R, y0, y1, 0, h)


def stairs(props):
    """Full lower half; upper half on the `facing` side. half=top flips."""
    facing = props.get("facing", "north")
    h = R // 2
    if props.get("half") == "top":
        return [(0, R, h, R, 0, R), half_towards(facing, 0, h)]
    return [(0, R, 0, h, 0, R), half_towards(facing, h, R)]


def slab(props):
    t = props.get("type", "bottom")
    h = R // 2
    if t == "double":
        return cube()
    if t == "top":
        return [(0, R, h, R, 0, R)]
    return [(0, R, 0, h, 0, R)]


def arm(direction, y0, y1, half_width=1):
    """A rail from the centre out to one side, 2*half_width voxels wide."""
    dx, dz = DIR[direction]
    c0, c1 = R // 2 - half_width, R // 2 + half_width
    h = R // 2
    if dx == 1:
        return (h, R, y0, y1, c0, c1)
    if dx == -1:
        return (0, h, y0, y1, c0, c1)
    if dz == 1:
        return (c0, c1, y0, y1, h, R)
    return (c0, c1, y0, y1, 0, h)


def fence(props):
    out = [(6, 10, 0, R, 6, 10)]  # 4x4 post, Minecraft's exact size
    for d in DIR:
        if props.get(d) == "true":
            out += [arm(d, 6, 9), arm(d, 12, 15)]
    return out


def fence_gate(props):
    facing = props.get("facing", "north")
    across = ("east", "west") if facing in ("north", "south") else ("north", "south")
    out = []
    for d in across:
        out += [arm(d, 6, 9), arm(d, 12, 15)]
        dx, dz = DIR[d]
        px = 0 if dx == -1 else R - 2 if dx == 1 else R // 2 - 1
        pz = 0 if dz == -1 else R - 2 if dz == 1 else R // 2 - 1
        out.append((px, px + 2, 0, R, pz, pz + 2))
    return out


def wall(props):
    out = [(4, 12, 0, R, 4, 12)]  # 8x8 post
    for d in DIR:
        v = props.get(d, "none")
        if v in ("low", "tall", "true"):
            h = R if v == "tall" else R - 2
            dx, dz = DIR[d]
            if dx:
                out.append((R // 2 if dx == 1 else 0, R if dx == 1 else R // 2, 0, h, 5, 11))
            else:
                out.append((5, 11, 0, h, R // 2 if dz == 1 else 0, R if dz == 1 else R // 2))
    return out


DOOR_T = 3  # door thickness in voxels (Minecraft: 3 px)


def door_closed_side(props):
    """Which side of the cell a closed door panel sits against: opposite the
    facing direction (the panel is at the back of the cell as you look in)."""
    return OPPOSITE[props.get("facing", "north")]


def door(props):
    if props.get("open") == "true":
        hinge_left = props.get("hinge", "left") == "left"
        order = ["north", "east", "south", "west"]
        i = order.index(props.get("facing", "north"))
        side = order[(i - 1) % 4] if hinge_left else order[(i + 1) % 4]
        return side_slab(side, DOOR_T)
    return side_slab(door_closed_side(props), DOOR_T)


def trapdoor(props):
    if props.get("open") == "true":
        return side_slab(props.get("facing", "north"), 3)
    if props.get("half") == "top":
        return [(0, R, R - 3, R, 0, R)]
    return [(0, R, 0, 3, 0, R)]


def pane(props):
    out = [(7, 9, 0, R, 7, 9)]
    connected = [d for d in DIR if props.get(d) == "true"] or list(DIR)
    for d in connected:
        dx, dz = DIR[d]
        if dx:
            out.append((R // 2 if dx == 1 else 0, R if dx == 1 else R // 2, 0, R, 7, 9))
        else:
            out.append((7, 9, 0, R, R // 2 if dz == 1 else 0, R if dz == 1 else R // 2))
    return out


def torch_parts(props, on_wall):
    """Returns (stick boxes, flame boxes)."""
    if on_wall:
        dx, dz = DIR[props.get("facing", "north")]  # points away from the wall
        cx = R // 2 - 1 - dx * 5
        cz = R // 2 - 1 - dz * 5
        return [(cx, cx + 2, 4, 12, cz, cz + 2)], [(cx, cx + 2, 12, 15, cz, cz + 2)]
    return [(7, 9, 0, 10, 7, 9)], [(7, 9, 10, 13, 7, 9)]


# =============================================================================
# Textures: shade volumes. Each returns (volume[R,R,R] of shade ids,
# shades = [(material, (r,g,b)), ...]).
# =============================================================================
_tex_cache = {}


def _rng(name):
    return np.random.RandomState(abs(hash(name)) % (2 ** 31))


def _speckle(name, material, colours, weights=None):
    rng = _rng(name)
    k = len(colours)
    p = weights or [1 / k] * k
    vol = rng.choice(k, size=(R, R, R), p=p).astype(np.uint8)
    return vol, [(material, c) for c in colours]


def _voronoi(name, material, stone_shades, mortar):
    """Stone cells with mortar between them. Cells are 3D so every face reads
    as stonework."""
    rng = _rng(name)
    n = 10
    pts = rng.rand(n, 3) * R
    coords = np.stack(np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij"), -1) + 0.5
    d = np.linalg.norm(coords[..., None, :] - pts[None, None, None, :, :], axis=-1)
    order = np.argsort(d, axis=-1)
    d1 = np.take_along_axis(d, order[..., :1], -1)[..., 0]
    d2 = np.take_along_axis(d, order[..., 1:2], -1)[..., 0]
    cell = order[..., 0]
    shade = (cell % len(stone_shades)).astype(np.uint8)
    vol = np.where(d2 - d1 < 1.1, len(stone_shades), shade).astype(np.uint8)
    return vol, [(material, c) for c in stone_shades] + [(material, mortar)]


def _planks(name, material, base, dark, light):
    """Horizontal boards 4 voxels tall with dark seams; staggered board ends."""
    rng = _rng(name)
    x, y, z = np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij")
    vol = np.zeros((R, R, R), dtype=np.uint8)
    grain = rng.rand(R, R, R) < 0.12
    vol[grain] = 2
    seam_y = (y % 4 == 0)
    row = y // 4
    seam_x = ((x + row * 8) % 16 == 0)
    seam_z = ((z + row * 8) % 16 == 0)
    vol[seam_y | seam_x | seam_z] = 1
    return vol, [(material, base), (material, dark), (material, light)]


def _log(name, material, bark, bark_dark, end, ring):
    """Bark on the sides, growth rings on the top and bottom layer."""
    rng = _rng(name)
    x, y, z = np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij")
    streak = rng.rand(R, 1, R) < 0.35  # vertical streaks: same for all y
    vol = np.where(np.broadcast_to(streak, (R, R, R)), 1, 0).astype(np.uint8)
    r = np.sqrt((x - 7.5) ** 2 + (z - 7.5) ** 2)
    rings = np.where((r.astype(int) % 2 == 0), 2, 3).astype(np.uint8)
    cap = (y == 0) | (y == R - 1)
    vol[cap] = rings[cap]
    return vol, [(material, bark), (material, bark_dark), (material, end), (material, ring)]


def _bricks(name, material, brick_a, brick_b, mortar):
    x, y, z = np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij")
    course = y // 4
    mortar_mask = (y % 4 == 0) | ((x + course * 4) % 8 == 0) | ((z + course * 4) % 8 == 0)
    rng = _rng(name)
    vol = rng.choice(2, size=(R, R, R)).astype(np.uint8)
    vol[mortar_mask] = 2
    return vol, [(material, brick_a), (material, brick_b), (material, mortar)]


def _grass_block(name):
    rng = _rng(name)
    vol = rng.choice(3, size=(R, R, R)).astype(np.uint8)  # dirt shades 0..2
    x, y, z = np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij")
    grass = rng.choice(3, size=(R, R, R)).astype(np.uint8) + 3
    fringe = y >= R - 3  # grass on top and a short fringe down the sides
    vol[fringe] = grass[fringe]
    return vol, [("dirt", c) for c in DIRT_SHADES] + [("dirt", c) for c in GRASS_SHADES]


def _glass(name, material, inner, frame):
    x, y, z = np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij")
    edge = (x == 0) | (x == R - 1) | (y == 0) | (y == R - 1) | (z == 0) | (z == R - 1)
    vol = np.where(edge, 1, 0).astype(np.uint8)
    return vol, [(material, inner), (material, frame)]


def _bookshelf(name):
    x, y, z = np.meshgrid(np.arange(R), np.arange(R), np.arange(R), indexing="ij")
    rng = _rng(name)
    vol = np.zeros((R, R, R), dtype=np.uint8)
    books = ((y >= 2) & (y <= 6)) | ((y >= 9) & (y <= 13))
    spine = rng.choice([1, 2, 3], size=(R, 1, R))
    vol[books] = np.broadcast_to(spine, (R, R, R))[books]
    return vol, [("wood", (150, 120, 70)), ("wood", (160, 60, 50)), ("wood", (60, 110, 70)), ("wood", (70, 80, 150))]


def _uniform(name, material, colour):
    return np.zeros((R, R, R), dtype=np.uint8), [(material, colour)]


DIRT_SHADES = [(134, 96, 67), (121, 85, 58), (146, 108, 76)]
GRASS_SHADES = [(110, 170, 60), (98, 158, 54), (122, 180, 70)]

# name -> builder. Built lazily and cached.
TEXTURES = {
    "cobblestone": lambda n: _voronoi(n, "concrete", [(128, 128, 128), (112, 112, 112), (142, 142, 142), (120, 124, 120)], (86, 86, 86)),
    "mossy_cobblestone": lambda n: _voronoi(n, "concrete", [(110, 118, 92), (96, 106, 80), (128, 132, 104)], (78, 84, 70)),
    "smooth_stone": lambda n: _speckle(n, "concrete", [(160, 160, 160), (150, 150, 150)], [0.8, 0.2]),
    "stone_dark": lambda n: _speckle(n, "concrete", [(92, 92, 92), (80, 80, 80), (104, 104, 104)]),
    "bricks": lambda n: _bricks(n, "brick", (150, 97, 83), (138, 88, 76), (160, 160, 150)),
    "terracotta": lambda n: _speckle(n, "brick", [(152, 94, 67), (140, 86, 60)], [0.7, 0.3]),
    "white_terracotta": lambda n: _speckle(n, "plaster", [(209, 178, 161), (198, 168, 152)], [0.7, 0.3]),
    "planks": lambda n: _planks(n, "wood", (162, 130, 78), (118, 92, 52), (176, 144, 90)),
    "log": lambda n: _log(n, "wood", (109, 85, 50), (88, 68, 40), (177, 144, 86), (152, 122, 70)),
    "stripped": lambda n: _log(n, "wood", (177, 144, 86), (160, 128, 74), (190, 158, 98), (170, 138, 80)),
    "hay": lambda n: _speckle(n, "wood", [(182, 150, 40), (166, 134, 34), (198, 166, 52)]),
    "dark_wood": lambda n: _speckle(n, "wood", [(62, 62, 62), (52, 52, 52)]),
    "bookshelf": _bookshelf,
    "grass_block": _grass_block,
    "dirt": lambda n: _speckle(n, "dirt", DIRT_SHADES),
    "dirt_path": lambda n: _speckle(n, "dirt", [(148, 121, 72), (136, 110, 64), (158, 130, 80)]),
    "farmland": lambda n: _speckle(n, "dirt", [(96, 64, 40), (84, 56, 34), (108, 72, 46)]),
    "clay": lambda n: _speckle(n, "dirt", [(160, 166, 179), (150, 156, 168)]),
    "leaves": lambda n: _speckle(n, "foliage", [(58, 118, 30), (48, 104, 24), (70, 132, 38)]),
    "stem": lambda n: _uniform(n, "foliage", (70, 140, 40)),
    "wheat": lambda n: _speckle(n, "foliage", [(190, 170, 70), (176, 156, 60)]),
    "dandelion": lambda n: _uniform(n, "foliage", (250, 230, 50)),
    "poppy": lambda n: _uniform(n, "foliage", (220, 40, 40)),
    "daisy": lambda n: _uniform(n, "foliage", (240, 240, 230)),
    "glass": lambda n: _glass(n, "glass", (205, 232, 240), (170, 200, 210)),
    "glass_y": lambda n: _glass(n, "glass", (229, 229, 51), (200, 200, 40)),
    "glass_w": lambda n: _glass(n, "glass", (240, 240, 240), (210, 210, 210)),
    "iron": lambda n: _uniform(n, "metal", (170, 170, 170)),
    "dark_metal": lambda n: _uniform(n, "metal", (62, 62, 62)),
    "bell": lambda n: _uniform(n, "metal", (240, 190, 60)),
    "wool_y": lambda n: _speckle(n, "plastic", [(248, 197, 39), (236, 186, 34)], [0.8, 0.2]),
    "wool_w": lambda n: _speckle(n, "plastic", [(233, 236, 236), (220, 222, 222)], [0.8, 0.2]),
    "wool_g": lambda n: _speckle(n, "plastic", [(84, 109, 27), (76, 98, 24)], [0.8, 0.2]),
    "torchwood": lambda n: _uniform(n, "wood", (120, 90, 50)),
    "flame": lambda n: _uniform(n, "unphysical", (255, 196, 80)),
    "pot": lambda n: _uniform(n, "plaster", (120, 70, 50)),
}


def texture(name):
    if name not in _tex_cache:
        _tex_cache[name] = TEXTURES[name](name)
    return _tex_cache[name]


# =============================================================================
# The block table: name -> (kind, texture). Kind picks the geometry.
# =============================================================================
TABLE = {
    "cobblestone": ("cube", "cobblestone"),
    "mossy_cobblestone": ("cube", "mossy_cobblestone"),
    "cobblestone_stairs": ("stairs", "cobblestone"),
    "cobblestone_slab": ("slab", "cobblestone"),
    "cobblestone_wall": ("wall", "cobblestone"),
    "smooth_stone": ("cube", "smooth_stone"),
    "smooth_stone_slab": ("slab", "smooth_stone"),
    "bricks": ("cube", "bricks"),
    "terracotta": ("cube", "terracotta"),
    "white_terracotta": ("cube", "white_terracotta"),
    "furnace": ("cube", "stone_dark"),
    "smoker": ("cube", "stone_dark"),
    "blast_furnace": ("cube", "stone_dark"),
    "stonecutter": ("slab", "smooth_stone"),
    "oak_planks": ("cube", "planks"),
    "oak_log": ("cube", "log"),
    "stripped_oak_log": ("cube", "stripped"),
    "stripped_oak_wood": ("cube", "stripped"),
    "oak_stairs": ("stairs", "planks"),
    "oak_slab": ("slab", "planks"),
    "oak_fence": ("fence", "planks"),
    "oak_fence_gate": ("gate", "planks"),
    "oak_door": ("door", "planks"),
    "oak_trapdoor": ("trapdoor", "planks"),
    "oak_pressure_plate": ("plate", "planks"),
    "ladder": ("ladder", "planks"),
    "bookshelf": ("cube", "bookshelf"),
    "chest": ("small", "planks"),
    "barrel": ("cube", "log"),
    "composter": ("cube", "log"),
    "lectern": ("small", "planks"),
    "loom": ("cube", "planks"),
    "cartography_table": ("cube", "planks"),
    "fletching_table": ("cube", "planks"),
    "smithing_table": ("cube", "dark_wood"),
    "crafting_table": ("cube", "planks"),
    "hay_block": ("cube", "hay"),
    "grass_block": ("cube", "grass_block"),
    "dirt": ("cube", "dirt"),
    "dirt_path": ("path", "dirt_path"),
    "farmland": ("path", "farmland"),
    "clay": ("cube", "clay"),
    "oak_leaves": ("cube", "leaves"),
    "short_grass": ("plant", "stem"),
    "tall_grass": ("plant", "stem"),
    "wheat": ("plant", "wheat"),
    "dandelion": ("plant", "dandelion"),
    "poppy": ("plant", "poppy"),
    "oxeye_daisy": ("plant", "daisy"),
    "potted_dandelion": ("potted", "dandelion"),
    "glass_pane": ("pane", "glass"),
    "yellow_stained_glass_pane": ("pane", "glass_y"),
    "white_stained_glass_pane": ("pane", "glass_w"),
    "iron_bars": ("pane", "iron"),
    "torch": ("torch", "torchwood"),
    "wall_torch": ("wall_torch", "torchwood"),
    "yellow_wool": ("cube", "wool_y"),
    "white_wool": ("cube", "wool_w"),
    "yellow_carpet": ("carpet", "wool_y"),
    "white_carpet": ("carpet", "wool_w"),
    "green_carpet": ("carpet", "wool_g"),
    "white_bed": ("bed", "wool_w"),
    "yellow_bed": ("bed", "wool_y"),
    "bell": ("small", "bell"),
    "water_cauldron": ("cube", "dark_metal"),
    "cauldron": ("cube", "dark_metal"),
    "brewing_stand": ("post", "iron"),
    "grindstone": ("small", "iron"),
    # Skipped on purpose (Teardown has its own water entity; lava later):
    "air": None, "water": None, "lava": None, "jigsaw": None, "structure_void": None,
    "cave_air": None,
}

# Representative colour per block for the low-res village preview.
PREVIEW_COLOUR = {name: texture(entry[1])[1][0][1] for name, entry in TABLE.items() if entry}


def parts(name, props, rng):
    """Yield (boxes, texture_name) for one block. name has no 'minecraft:'."""
    entry = TABLE.get(name, "MISSING")
    if entry == "MISSING":
        raise KeyError(f"no mapping for block {name}; add it to blocks.TABLE")
    if entry is None:
        return
    kind, tex = entry
    if kind == "cube":
        yield cube(), tex
    elif kind == "stairs":
        yield stairs(props), tex
    elif kind == "slab":
        yield slab(props), tex
    elif kind == "fence":
        yield fence(props), tex
    elif kind == "gate":
        yield fence_gate(props), tex
    elif kind == "wall":
        yield wall(props), tex
    elif kind == "door":
        yield door(props), tex
    elif kind == "trapdoor":
        yield trapdoor(props), tex
    elif kind == "plate":
        yield [(1, R - 1, 0, 1, 1, R - 1)], tex
    elif kind == "ladder":
        yield side_slab(props.get("facing", "north"), 2), tex
    elif kind == "carpet":
        yield [(0, R, 0, 1, 0, R)], tex
    elif kind == "bed":
        yield [(0, R, 3, 9, 0, R)], tex
        yield [(0, 2, 0, 3, 0, 2), (R - 2, R, 0, 3, 0, 2), (0, 2, 0, 3, R - 2, R), (R - 2, R, 0, 3, R - 2, R)], "planks"
    elif kind == "small":
        yield [(1, R - 1, 0, R - 2, 1, R - 1)], tex
    elif kind == "post":
        yield [(7, 9, 0, R - 2, 7, 9)], tex
    elif kind == "pane":
        yield pane(props), tex
    elif kind in ("torch", "wall_torch"):
        stick, flame = torch_parts(props, kind == "wall_torch")
        yield stick, tex
        yield flame, "flame"
    elif kind == "path":
        yield [(0, R, 0, R - 1, 0, R)], tex
    elif kind == "plant":
        n, h = {"short_grass": (6, 7), "tall_grass": (7, 13), "wheat": (9, 11)}.get(name, (1, 7))
        stems, tops = [], []
        for _ in range(n):
            x, z = rng.randrange(1, R - 1), rng.randrange(1, R - 1)
            hh = max(3, h + rng.randrange(-2, 3))
            stems.append((x, x + 1, 0, hh, z, z + 1))
            if name in ("dandelion", "poppy", "oxeye_daisy"):
                tops.append((max(0, x - 1), min(R, x + 2), hh, min(R, hh + 2), max(0, z - 1), min(R, z + 2)))
        yield stems, "stem" if name not in ("wheat",) else tex
        if tops:
            yield tops, tex
    elif kind == "potted":
        yield [(5, 11, 0, 6, 5, 11)], "pot"
        yield [(7, 9, 6, 11, 7, 9)], "stem"
        yield [(5, 11, 11, 14, 5, 11)], tex
    else:
        raise KeyError(f"unknown kind {kind} for {name}")
