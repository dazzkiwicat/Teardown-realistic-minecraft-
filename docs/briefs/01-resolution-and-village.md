# Brief 01: 16-voxel blocks with textures, bigger village, doors as bodies

One job: rebuild the converter and level builder so the village is high
resolution and textured, has many more structures with streets, and has
every door as its own body ready for a script to swing. Python only. Do not
touch `mod/script/village.lua`. Do not commit.

## Already done (read these first)

- `tools/blocks.py` is REWRITTEN: `R = 16` voxels per block, `SCALE = 0.625`
  (the `<vox scale>` that makes a 16-voxel block one metre). Geometry
  functions now return lists of boxes `(x0,x1,y0,y1,z0,z1)` in Minecraft
  axes (x east, y up, z south), and `blocks.parts(name, props, rng)` yields
  `(boxes, texture_name)`. `blocks.texture(name)` returns
  `(volume[R,R,R] of shade ids, shades=[(material, rgb), ...])`.
  `blocks.PALETTE_RANGES` maps material -> palette index range.
  `blocks.PREVIEW_COLOUR[name]` is one rgb per block for low-res previews.
- `tools/vox.py` writes/reads MagicaVoxel files. `write(path, size, voxels,
  palette, emissive, name)` accepts a numpy uint8 grid in VOX axes (x, y,
  z-up) and writes a scene graph that puts the model's bottom centre at the
  origin. `read(path)` is an independent checker.
- `tools/nbt.py` loads the Minecraft templates in `source/minecraft/village/plains/`.
- `tools/mc2vox.py`, `tools/build_level.py`, `tools/render.py` are the OLD
  10-voxel pipeline; they no longer match blocks.py and must be updated.
- `docs/teardown-api-notes.md` has the verbatim Teardown API/XML facts.
  Section 3c: the `[vox]` node has `pos`, `rot` (degrees), `scale`, `file`,
  `object`. Section 5: a MagicaVoxel model is at most 256 voxels per axis.

## Tasks

### 1. `tools/vox.py`: optional pivot
Add a `pivot` parameter to `write()`: default `"bottom-center"` (current
behaviour, translation `(0, 0, sz//2)`), or an explicit `(tx, ty, tz)`
translation tuple written into the nTRN `_t`. MagicaVoxel places a model's
centre at `_t`, so a model of size `(sx, sy, sz)` spans
`[t - size/2, t + size/2)` on each axis. Keep `read()` working.

### 2. `tools/mc2vox.py`: numpy, textures, chunks, doors
Rewrite `convert(nbt_path, out_stem)`:
- Build one uint8 grid in Minecraft axes `(sx*R, sy*R, sz*R)` of palette
  indices. For each block, for each `(boxes, tex)` from `blocks.parts`: get
  `vol, shades = blocks.texture(tex)`; map each shade to a palette index
  with a per-file `Palette` (same `(material, rgb)` -> same index, allocate
  inside `PALETTE_RANGES[material]`, reuse nearest colour of that material
  when the range is full); build a lookup table `lut` so `lut[vol]` is an
  index grid; for each box write `grid[slice] = lut[vol[slice]]` offset by
  the block position. Shades whose material is `"unphysical"` are emissive
  (flux 6) as before.
- Jigsaw blocks: use `nbt.final_state` as before (`parse_state`).
- DOORS: blocks named `oak_door` are NOT written to the grid. Collect them:
  the `half=lower` block gives `facing`, `hinge`, `open`; record
  `{"bx","by","bz","facing","hinge","open"}` per door (by = the lower
  block). Write ONE shared door model `mod/vox/door_oak.vox` (only once,
  if missing): size in vox axes `(R, 3, 2*R)` = 16 wide, 3 thick, 32 tall,
  textured with `blocks.texture("planks")`, pivot translation `(R//2, 0, R)`
  so the model spans x 0..16, y -1.5..1.5, z 0..32: the HINGE EDGE is at
  x = 0 and the panel extends along +x. Also carve a small window: leave
  voxels empty for x in 4..12, z in 20..28 on the panel.
- CHUNKS: a MagicaVoxel model is capped at 256 voxels = 16 blocks per axis.
  Split the block grid into chunks of at most 16 blocks in x and in z
  (y is always <= 12 blocks in these templates). Write each chunk as its own
  vox file: `<stem>.vox` if there is exactly one chunk, else
  `<stem>__<i>_<j>.vox`. Convert to vox axes with
  `np.transpose(chunk, (0, 2, 1))` (Minecraft (x, y, z) -> vox (x, z, y)).
  Skip writing a chunk that has no voxels.
- Write `<stem>.json`: `size_blocks`, `blocks_placed`, `voxels` (total),
  `chunks: [{file, bx0, bz0, sx, sz}]` (block offsets and block sizes of
  each chunk), `doors: [...]`, `materials` (index -> material),
  `emissive_indices`.
- Keep a CLI: `python3 -I tools/mc2vox.py <nbt> <out_stem>`.
- Raise with a clear message on an unmapped block name.

### 3. `tools/build_level.py`: bigger village, streets, doors, layered ground
- Plot grid with pitch 18 m: plot centres at `(i*18, j*18)` for i, j in
  -2..2. Centre plot (0,0): `town_centers/plains_fountain_01`. Road plots
  (0, ±18), (0, ±36), (±18, 0), (±36, 0): street tiles `streets/straight_01`
  (16 x 16 blocks). Look inside `straight_01.nbt` to see which axis the
  `dirt_path` strip runs along, and give the tiles on the other road the
  attribute `rot="0 90 0"` so both roads have the path running along them.
  Put `streets/crossroad_01` on... no: the fountain is the crossing; leave it.
- The 16 remaining plots get, one each: `houses/plains_small_house_1..4`,
  `houses/plains_medium_house_1`, `houses/plains_medium_house_2`,
  `houses/plains_big_house_1`, `houses/plains_library_1`,
  `houses/plains_temple_4`, `houses/plains_butcher_shop_1`,
  `houses/plains_armorer_house_1`, `houses/plains_tool_smith_1`,
  `houses/plains_small_farm_1`, `houses/plains_large_farm_1`,
  `houses/plains_animal_pen_1`, `houses/plains_stable_1`. Also place
  `plains_lamp_1` at the four corners around the fountain (±6, ±6).
  Check every chosen template's footprint fits inside 16 x 16 blocks; if
  one does not, swap it for another from the list in `source/`.
- Each structure is placed with its foundation layer (Minecraft y = 0)
  from world y = -1 to 0, so the `<vox pos>` y is -1 for every chunk.
  Chunk centre x = structure x0 + bx0 + sx/2 (same for z). Every `<vox>`
  gets `scale="0.625"` (blocks.SCALE). All chunks of one structure go in
  one `<body>`.
- Rotated street tiles: pos is the tile centre, so `rot="0 90 0"` about
  the bottom-centre pivot keeps it in place.
- GROUND in three layers, every layer in tiles of 20 m, covering the layout
  bounding box plus a 12 m margin, rounded out to whole tiles:
  1. Top layer, `scale="1"` (0.1 m voxels), 0.5 m thick, from y -0.5 to 0:
     top voxel row grass speckle (3 greens, random per voxel, material
     dirt), below it dirt speckle. 200 x 200 x 5 voxels per tile.
  2. Middle layer, `scale="2"` (0.2 m voxels), from y -1.1 to -0.5, dirt,
     100 x 100 x 3 voxels per tile.
  3. Bottom layer, `scale="4"` (0.4 m voxels), from y -2.3 to -1.1,
     material ROCK (unbreakable), colour (90, 90, 95), 50 x 50 x 3 per tile.
  Carve the structure footprints (whole rectangles) out of layers 1 and 2
  only (the template's own ground blocks fill the hole). Layer y positions
  in the XML are the layer BOTTOM (pivot is bottom centre).
- DOORS: for every door reported in a structure's JSON, emit
  `<body dynamic="true" tags="door swing=<+1|-1>"><vox file="MOD/vox/door_oak.vox" pos="<hx> <hy> <hz>" rot="0 <yaw> 0" scale="0.625"/></body>`.
  Geometry (Minecraft axes, metres, block cell `[cx, cx+1) x [cz, cz+1)` in
  world after adding the structure's x0/z0 and y = -1 + by):
  the closed panel lies against the cell side OPPOSITE to `facing`
  (facing north -> panel along the south edge, z = cz + 1 - 0.09375).
  `hinge=left` means the hinge is on the LEFT when looking in the facing
  direction (facing north: left is west -> hinge at x = cx; facing south:
  left is east -> hinge at x = cx + 1; facing east: left is north -> hinge
  at z = cz; facing west: left is south -> hinge at z = cz + 1).
  `hinge=right` is the other end of the same panel. The door model's +x
  axis must point from the hinge to the far edge of the panel, so compute
  the yaw (degrees about world y) that rotates the model's +x onto that
  direction, treating world z as the Minecraft z. Put the math in one
  well-commented function `door_pose(x0, z0, by, door) -> (pos, yaw, swing)`
  with `swing = +1` when opening means yaw increases (door swings into the
  facing direction), else -1. Write the mapping out in a comment so the
  sign can be flipped in one place if the game shows it mirrored.
- Script line stays: `<script file="MOD/script/village.lua" param0="daylength=240" param1="maxzombies=4" param2="starttime=0.3"/>`.
- Spawn ring: 12 `<location tags="zombiespawn">` at radius 52 m, y 0.5.
  Boundary ±62. Spawnpoint `pos="0 0.2 8" rot="0 180 0"`.
- Write `preview/layout.json` and the block-resolution village preview
  `preview/village.png` using `blocks.PREVIEW_COLOUR` (one voxel per block,
  `render.render`, scale 7).
- Print a summary: structures, chunks, doors, ground tiles, total size of
  `mod/vox/` in MB. Keep total under 90 MB; if over, reduce the top ground
  layer to 0.4 m thick and say so.

### 4. `tools/render.py`
Keep it working for the new files (it reads any vox). Render
`mod/vox/plains_small_house_1.vox` at scale 3, `mod/vox/plains_library_1*.vox`
(first chunk) at scale 2, and `mod/vox/door_oak.vox` at scale 8 into
`preview/`. Look at the PNGs (Read tool) and fix anything that is clearly
wrong (missing roof, inverted stairs, door window missing).

### 5. Verify
- `python3 -I tools/build_level.py` runs clean.
- For every vox written, `vox.read` must agree with the JSON voxel counts
  (write a short check loop in `tools/check_vox.py` and run it).
- Delete stale old files in `mod/vox/` that the new build does not produce
  (old 10-voxel ground tiles etc.), so the mod folder has only current files.

## Report back (short)
Sizes, counts, which templates were swapped and why, anything you were
unsure of, and the paths of the PNGs you looked at.
