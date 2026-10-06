"""Minecraft block -> Teardown voxel geometry and material.

One Minecraft block is 1 metre. One Teardown voxel is 0.1 metre, so every
block becomes a 10 x 10 x 10 voxel cell (B = 10 below). Partial blocks
(stairs, slabs, fences, doors, panes, torches...) are built from small boxes
inside that cell so the village keeps its Minecraft shapes.

Coordinates inside this file are MINECRAFT axes: x east, y up, z south.
mc2vox.py converts to MagicaVoxel's z-up when it places the voxels.

MATERIAL is what the zombies care about. Teardown reads it from the palette
index of the voxel (PALETTE_RANGES). Zombies will use MakeHole with only the
"soft" radius, which eats glass, foliage, dirt, wood, plaster and plastic but
not masonry or metal, so a cobblestone wall holds and a plank wall does not.
"""

B = 10  # voxels per block edge

# Teardown material by MagicaVoxel palette index (1-based, inclusive).
# Read off the official teardown_palette.vox / .png from the modding docs
# (8 colours per row; row labels: glass, grass x2, dirt x2, rock x2, wood x2,
# concrete x2, brick x2, plaster x2, weak metal x2, heavy metal x2, plastic x2,
# hard metal, hard masonry, reserved..., unphysical x2).
#
# Hardness per the docs: SOFT = glass, grass(foliage), dirt, plastic, wood,
# plaster. MEDIUM = concrete, brick, weak metal. HARD = hard masonry, hard
# metal. Rock and heavy metal cannot be broken at all.
# Zombies call MakeHole with only the soft radius, so plank walls fall and
# cobblestone (concrete) walls hold.
PALETTE_RANGES = {
    "glass":       (1, 8),
    "foliage":     (9, 24),     # labelled "grass" on the palette
    "dirt":        (25, 40),
    "rock":        (41, 56),    # unbreakable: used for the ground base layer
    "wood":        (57, 72),
    "concrete":    (73, 88),    # medium: cobblestone, stone
    "brick":       (89, 104),   # medium: bricks, terracotta
    "plaster":     (105, 120),
    "metal":       (121, 136),  # "weak metal", medium
    "heavymetal":  (137, 152),  # unbreakable
    "plastic":     (153, 168),
    "hardmetal":   (169, 176),
    "hardmasonry": (177, 184),
    "unphysical":  (225, 240),  # torch flames (emissive, no collision)
}

# ---- colours (approximate Minecraft textures) -------------------------------
C = {
    "cobble": (125, 125, 125), "mossy": (108, 118, 92), "smooth": (158, 158, 158),
    "planks": (162, 130, 78), "bark": (109, 85, 50), "stripped": (177, 144, 86),
    "grass": (116, 178, 62), "dirt": (134, 96, 67), "path": (148, 121, 72),
    "farm": (96, 64, 40), "terracotta_w": (209, 178, 161), "terracotta": (152, 94, 67),
    "glass": (205, 232, 240), "glass_y": (229, 229, 51), "glass_w": (240, 240, 240),
    "leaves": (58, 118, 30), "torchwood": (120, 90, 50), "flame": (255, 196, 80),
    "wool_y": (248, 197, 39), "wool_w": (233, 236, 236), "wool_g": (84, 109, 27),
    "hay": (182, 150, 40), "book": (140, 112, 66), "iron": (170, 170, 170),
    "bell": (240, 190, 60), "clay": (160, 166, 179), "dark": (62, 62, 62),
    "brick": (150, 97, 83), "furnace": (92, 92, 92), "stem": (70, 140, 40),
    "dandelion": (250, 230, 50), "poppy": (220, 40, 40), "daisy": (240, 240, 230),
    "wheat": (190, 170, 70), "pot": (120, 70, 50), "water": (60, 110, 220),
}


def box(x0, x1, y0, y1, z0, z1):
    """Voxel coords for the half-open box [x0,x1) x [y0,y1) x [z0,z1)."""
    return {(x, y, z) for x in range(x0, x1) for y in range(y0, y1) for z in range(z0, z1)}


def cube():
    return box(0, B, 0, B, 0, B)


# Direction helpers: offsets in (dx, dz) for Minecraft facing names.
DIR = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def side_slab(direction, thickness, y0=0, y1=B):
    """A vertical slab `thickness` voxels thick pressed against one side."""
    dx, dz = DIR[direction]
    if dx == 1:
        return box(B - thickness, B, y0, y1, 0, B)
    if dx == -1:
        return box(0, thickness, y0, y1, 0, B)
    if dz == 1:
        return box(0, B, y0, y1, B - thickness, B)
    return box(0, B, y0, y1, 0, thickness)


def half_towards(direction, y0, y1):
    """The half of the cell on the `direction` side, between heights y0..y1."""
    dx, dz = DIR[direction]
    if dx == 1:
        return box(B // 2, B, y0, y1, 0, B)
    if dx == -1:
        return box(0, B // 2, y0, y1, 0, B)
    if dz == 1:
        return box(0, B, y0, y1, B // 2, B)
    return box(0, B, y0, y1, 0, B // 2)


def stairs(props):
    """Bottom half full, top half on the `facing` side (the high step).
    half=top flips it upside down (ceiling stairs under roof eaves)."""
    facing = props.get("facing", "north")
    if props.get("half") == "top":
        return box(0, B, B // 2, B, 0, B) | half_towards(facing, 0, B // 2)
    return box(0, B, 0, B // 2, 0, B) | half_towards(facing, B // 2, B)


def slab(props):
    t = props.get("type", "bottom")
    if t == "double":
        return cube()
    if t == "top":
        return box(0, B, B // 2, B, 0, B)
    return box(0, B, 0, B // 2, 0, B)


def _arm(direction, x0, x1, y0, y1):
    """A rail from the centre post out to one side of the cell."""
    dx, dz = DIR[direction]
    c0, c1 = B // 2 - 1, B // 2 + 1  # 2 voxels wide, centred
    if dx == 1:
        return box(B // 2, B, y0, y1, c0, c1)
    if dx == -1:
        return box(0, B // 2, y0, y1, c0, c1)
    if dz == 1:
        return box(c0, c1, y0, y1, B // 2, B)
    return box(c0, c1, y0, y1, 0, B // 2)


def fence(props):
    out = box(3, 7, 0, B, 3, 7)  # 4x4 post
    for d in DIR:
        if props.get(d) == "true":
            out |= _arm(d, 0, 0, 3, 5) | _arm(d, 0, 0, 7, 9)
    return out


def fence_gate(props):
    facing = props.get("facing", "north")
    across = ("east", "west") if facing in ("north", "south") else ("north", "south")
    out = set()
    for d in across:
        out |= _arm(d, 0, 0, 3, 5) | _arm(d, 0, 0, 7, 9)
        # posts at the two ends
        dx, dz = DIR[d]
        px = 0 if dx == -1 else B - 2 if dx == 1 else B // 2 - 1
        pz = 0 if dz == -1 else B - 2 if dz == 1 else B // 2 - 1
        out |= box(px, px + 2, 0, B, pz, pz + 2)
    return out


def wall(props):
    out = box(2, 8, 0, B, 2, 8)  # 6x6 post
    for d in DIR:
        v = props.get(d, "none")
        if v in ("low", "tall", "true"):
            h = B if v == "tall" else B - 2
            dx, dz = DIR[d]
            if dx:
                out |= box(B // 2 if dx == 1 else 0, B if dx == 1 else B // 2, 0, h, 3, 7)
            else:
                out |= box(3, 7, 0, h, B // 2 if dz == 1 else 0, B if dz == 1 else B // 2)
    return out


def door(props):
    """Closed door: 2-voxel panel on the side opposite `facing`. Open: swung to
    the hinge side. Each half (lower/upper) is its own block, so just a panel."""
    facing = props.get("facing", "north")
    opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
    if props.get("open") == "true":
        # swing 90 degrees: panel along the hinge side
        hinge_left = props.get("hinge", "left") == "left"
        order = ["north", "east", "south", "west"]
        i = order.index(facing)
        side = order[(i - 1) % 4] if hinge_left else order[(i + 1) % 4]
        return side_slab(side, 2)
    return side_slab(opposite[facing], 2)


def trapdoor(props):
    if props.get("open") == "true":
        return side_slab(props.get("facing", "north"), 2)
    if props.get("half") == "top":
        return box(0, B, B - 2, B, 0, B)
    return box(0, B, 0, 2, 0, B)


def pane(props):
    out = box(4, 6, 0, B, 4, 6)
    connected = [d for d in DIR if props.get(d) == "true"]
    if not connected:
        connected = list(DIR)
    for d in connected:
        dx, dz = DIR[d]
        if dx:
            out |= box(B // 2 if dx == 1 else 0, B if dx == 1 else B // 2, 0, B, 4, 6)
        else:
            out |= box(4, 6, 0, B, B // 2 if dz == 1 else 0, B if dz == 1 else B // 2)
    return out


def torch_parts(props, on_wall):
    """Returns [(stick coords), (flame coords)]."""
    if on_wall:
        # wall_torch `facing` is the direction the torch points AWAY from the wall
        dx, dz = DIR[props.get("facing", "north")]
        cx = B // 2 - 1 - dx * 3
        cz = B // 2 - 1 - dz * 3
        stick = box(cx, cx + 2, 3, 8, cz, cz + 2)
        flame = box(cx, cx + 2, 8, B, cz, cz + 2)
    else:
        stick = box(4, 6, 0, 6, 4, 6)
        flame = box(4, 6, 6, 8, 4, 6)
    return stick, flame


def ladder(props):
    return side_slab(props.get("facing", "north"), 1)


def plant(kind, rng):
    """Small foliage sprigs. kind: grass | tall | flower | wheat."""
    out, tops = set(), set()
    n, h = {"grass": (4, 5), "tall": (5, 9), "flower": (1, 5), "wheat": (6, 7)}[kind]
    for _ in range(n):
        x, z = rng.randrange(1, B - 1), rng.randrange(1, B - 1)
        hh = max(2, h + rng.randrange(-1, 2))
        out |= box(x, x + 1, 0, hh, z, z + 1)
        if kind == "flower":
            tops |= box(x - 1, x + 2, hh, hh + 2, z - 1, z + 2)
    return out, tops


# ---- the block table ---------------------------------------------------------
# name -> (kind, material, colour key). Kind picks the geometry function.
TABLE = {
    "cobblestone": ("cube", "concrete", "cobble"),
    "mossy_cobblestone": ("cube", "concrete", "mossy"),
    "cobblestone_stairs": ("stairs", "concrete", "cobble"),
    "cobblestone_slab": ("slab", "concrete", "cobble"),
    "cobblestone_wall": ("wall", "concrete", "cobble"),
    "smooth_stone": ("cube", "concrete", "smooth"),
    "smooth_stone_slab": ("slab", "concrete", "smooth"),
    "bricks": ("cube", "brick", "brick"),
    "terracotta": ("cube", "brick", "terracotta"),
    "white_terracotta": ("cube", "plaster", "terracotta_w"),
    "furnace": ("cube", "concrete", "furnace"),
    "smoker": ("cube", "concrete", "furnace"),
    "blast_furnace": ("cube", "concrete", "furnace"),
    "stonecutter": ("slab", "concrete", "smooth"),
    "oak_planks": ("cube", "wood", "planks"),
    "oak_log": ("cube", "wood", "bark"),
    "stripped_oak_log": ("cube", "wood", "stripped"),
    "stripped_oak_wood": ("cube", "wood", "stripped"),
    "oak_stairs": ("stairs", "wood", "planks"),
    "oak_slab": ("slab", "wood", "planks"),
    "oak_fence": ("fence", "wood", "planks"),
    "oak_fence_gate": ("gate", "wood", "planks"),
    "oak_door": ("door", "wood", "planks"),
    "oak_trapdoor": ("trapdoor", "wood", "planks"),
    "oak_pressure_plate": ("plate", "wood", "planks"),
    "ladder": ("ladder", "wood", "planks"),
    "bookshelf": ("cube", "wood", "book"),
    "chest": ("small", "wood", "planks"),
    "barrel": ("cube", "wood", "bark"),
    "composter": ("cube", "wood", "bark"),
    "lectern": ("small", "wood", "planks"),
    "loom": ("cube", "wood", "planks"),
    "cartography_table": ("cube", "wood", "planks"),
    "fletching_table": ("cube", "wood", "planks"),
    "smithing_table": ("cube", "wood", "dark"),
    "crafting_table": ("cube", "wood", "planks"),
    "hay_block": ("cube", "wood", "hay"),
    "grass_block": ("grass_block", "dirt", "dirt"),
    "dirt": ("cube", "dirt", "dirt"),
    "dirt_path": ("path", "dirt", "path"),
    "farmland": ("path", "dirt", "farm"),
    "clay": ("cube", "dirt", "clay"),
    "oak_leaves": ("cube", "foliage", "leaves"),
    "short_grass": ("plant", "foliage", "stem"),
    "tall_grass": ("plant", "foliage", "stem"),
    "wheat": ("plant", "foliage", "wheat"),
    "dandelion": ("plant", "foliage", "dandelion"),
    "poppy": ("plant", "foliage", "poppy"),
    "oxeye_daisy": ("plant", "foliage", "daisy"),
    "potted_dandelion": ("potted", "foliage", "dandelion"),
    "glass_pane": ("pane", "glass", "glass"),
    "yellow_stained_glass_pane": ("pane", "glass", "glass_y"),
    "white_stained_glass_pane": ("pane", "glass", "glass_w"),
    "iron_bars": ("pane", "metal", "iron"),
    "torch": ("torch", "wood", "torchwood"),
    "wall_torch": ("wall_torch", "wood", "torchwood"),
    "yellow_wool": ("cube", "plastic", "wool_y"),
    "white_wool": ("cube", "plastic", "wool_w"),
    "yellow_carpet": ("carpet", "plastic", "wool_y"),
    "white_carpet": ("carpet", "plastic", "wool_w"),
    "green_carpet": ("carpet", "plastic", "wool_g"),
    "white_bed": ("bed", "plastic", "wool_w"),
    "yellow_bed": ("bed", "plastic", "wool_y"),
    "bell": ("small", "metal", "bell"),
    "water_cauldron": ("cube", "metal", "dark"),
    "cauldron": ("cube", "metal", "dark"),
    "brewing_stand": ("post", "metal", "iron"),
    "grindstone": ("small", "metal", "iron"),
    # Skipped on purpose (Teardown has its own water entity; lava later):
    "air": None, "water": None, "lava": None, "jigsaw": None, "structure_void": None,
    "cave_air": None,
}


def parts(name: str, props: dict, rng):
    """Yield (coords, material, rgb) for one block. name has no 'minecraft:'."""
    entry = TABLE.get(name, "MISSING")
    if entry == "MISSING":
        raise KeyError(f"no mapping for block {name}; add it to blocks.TABLE")
    if entry is None:
        return
    kind, material, colour = entry
    rgb = C[colour]
    if kind == "cube":
        yield cube(), material, rgb
    elif kind == "stairs":
        yield stairs(props), material, rgb
    elif kind == "slab":
        yield slab(props), material, rgb
    elif kind == "fence":
        yield fence(props), material, rgb
    elif kind == "gate":
        yield fence_gate(props), material, rgb
    elif kind == "wall":
        yield wall(props), material, rgb
    elif kind == "door":
        yield door(props), material, rgb
    elif kind == "trapdoor":
        yield trapdoor(props), material, rgb
    elif kind == "plate":
        yield box(1, B - 1, 0, 1, 1, B - 1), material, rgb
    elif kind == "ladder":
        yield ladder(props), material, rgb
    elif kind == "carpet":
        yield box(0, B, 0, 1, 0, B), material, rgb
    elif kind == "bed":
        yield box(0, B, 3, 6, 0, B), material, rgb
        yield box(0, B, 0, 3, 0, B), "wood", C["planks"]
    elif kind == "small":
        yield box(1, B - 1, 0, B - 1, 1, B - 1), material, rgb
    elif kind == "post":
        yield box(4, 6, 0, B - 2, 4, 6), material, rgb
    elif kind == "pane":
        yield pane(props), material, rgb
    elif kind == "torch":
        stick, flame = torch_parts(props, False)
        yield stick, material, rgb
        yield flame, "unphysical", C["flame"]  # emissive, see mc2vox
    elif kind == "wall_torch":
        stick, flame = torch_parts(props, True)
        yield stick, material, rgb
        yield flame, "unphysical", C["flame"]
    elif kind == "grass_block":
        yield box(0, B, 0, B - 1, 0, B), "dirt", C["dirt"]
        yield box(0, B, B - 1, B, 0, B), "dirt", C["grass"]
    elif kind == "path":
        yield box(0, B, 0, B - 1, 0, B), material, rgb
    elif kind == "plant":
        pk = {"short_grass": "grass", "tall_grass": "tall", "wheat": "wheat"}.get(name, "flower")
        stems, tops = plant(pk, rng)
        yield stems, "foliage", C["stem"] if pk != "wheat" else rgb
        if tops:
            yield tops, "foliage", rgb
    elif kind == "potted":
        yield box(3, 7, 0, 4, 3, 7), "plaster", C["pot"]
        yield box(4, 6, 4, 7, 4, 6), "foliage", C["stem"]
        yield box(3, 7, 7, 9, 3, 7), "foliage", rgb
    else:
        raise KeyError(f"unknown kind {kind} for {name}")
