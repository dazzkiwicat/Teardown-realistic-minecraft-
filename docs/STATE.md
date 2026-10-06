# State file

Last updated: 6 October 2026, first build.

## Where we are

The first checkable piece is built and pushed: a village of 8 structures
from the real Minecraft templates, a 60 x 60 m ground, a day/night clock,
and zombies that path to the player and bite through soft materials.

Nothing has been seen in Teardown yet. Everything below under "unverified"
is a guess that one screenshot from Darren settles.

## Verified here (without the game)

- All 46 plains templates parse; 70 block types all have a mapping.
- Every vox file re-reads with an independent reader: sizes and voxel
  counts match, chunks are well formed.
- Previews: `preview/plains_small_house_1.png`, `preview/zombie.png`,
  `preview/village.png` look right (roof, windows, door, zombie pose,
  layout with no overlaps).
- `tools/test_village.py`: 28 checks pass in both the 2.x (server/client)
  and 1.x (global callbacks) API styles.
- Material palette ranges match the official `teardown_palette.png`.

## Unverified (needs the game)

1. **API version.** The public docs describe Teardown 2.1 with
   `server.`/`client.` callbacks. The script has a shim for the old
   global style too. Which one Darren's game runs decides nothing yet,
   but if the HUD text never appears, this is the first suspect.
2. **Vox placement.** Each vox has a scene graph that puts its bottom
   centre at the origin, and `main.xml` places structures by footprint
   centre with the foundation 1 m below ground. If every house floats or
   sinks by the same amount, change the `-1` in `write_xml` in
   `tools/build_level.py`. If houses are shifted sideways by half their
   width, the pivot assumption is wrong: change the `_t` translation in
   `tools/vox.py`.
3. **Environment keys.** `sunBrightness`, `skyboxbrightness`, `ambient`
   are the editor's names from memory; the docs do not list them. The
   script prints `environment key not readable: X` for any that fail.
   The documented `nightlight` toggle is used regardless.
4. **Zombie facing.** If zombies walk backwards, set `frontflip=true`
   as a script param in `main.xml`.
5. **Mirroring.** Teardown may mirror the z axis when importing vox.
   The village would then be a mirror image, which is harmless.
6. **Spawn string.** Zombies are spawned from an inline `<body>` XML
   string. If `Spawn returned no body` prints, move it to a prefab file.

## Asks for Darren (any one of these moves things)

- The game version shown in the main menu (bottom corner).
- A screenshot after pressing Play, whatever it shows.
- The folder `Steam\steamapps\common\Teardown\mods\` zipped: the example
  mods that ship with the game show the exact XML the current version
  writes. Also `Steam\steamapps\common\Teardown\data\script\` zipped
  (small Lua files; the game's own robot enemy lives there).
- In the editor (Mods menu, select this mod, Edit), click the
  Environment node and screenshot its property list: that is the
  authoritative list of lighting keys.

## From the mod research (docs/reference-mods.md)

- No open-source mod makes zombies break walls. Ours does it with
  MakeHole; the game's own robots do a different thing when stuck: they
  tag their shapes `breakall` for a tenth of a second. Untested lead if
  MakeHole feels wrong.
- Each zombie now has its own path planner (`CreatePathPlanner`), as the
  Police-Chase-System mod does. Falls back to the shared planner on old
  versions. Path queries use the robots' filter: `QueryRequire("physical
  large")` and reject the zombie's own body.
- Workshop mods worth subscribing to and sending me the files of, best
  first: **Zombies [AUTUMNAGNIFICENT]** (the reference zombie mod, has a
  markdown file explaining its insides), **Zombiedown - Multiplayer
  Survival Improved and Updated** (pathfinding, spawning, stuck checks),
  **Dynamic Time Mod** (tiny day/night, easy to read), **Minecraft
  Village** by The_Wolfian (a hand-built one to compare with). Links in
  reference-mods.md part B. Subscribed files land in
  `Steam\steamapps\workshop\content\1167630\<id>\`.

## Round 2 (6 Oct, evening): what changed and what to look for

Darren loaded round 1: it worked, zombies walked and bit. Complaints: low
res, zombies trip, no doors, no pickaxe, no building. Darren is on
Teardown 2.x (the Castdown game-mode menu proves it; Castdown is the
game's own fishing mode, not ours).

Built since: 16-voxel textured blocks, 16 buildings with roads, doors as
hinged bodies, hovering zombies, pickaxe, block placer. 87 mock checks
pass. None of it seen in the game yet. Watch for:

1. **Doors**: if they hang in the wrong place or swing the wrong way, the
   one constant `YAW_SIGN` in `tools/build_level.py` flips both. The
   butcher's north door is the clearest test.
2. **Placed blocks**: colour is written as 0..1 values on the voxbox
   string; if placed blocks come out white or black, change to 0..255 in
   `placeBlock` in village.lua. Material names `concrete`, `glass` are
   undocumented guesses; `wood` is documented.
3. **Tools**: registered server-side and enabled two ways (registry key
   and `SetToolEnabled`). If they do not appear in the tool bar, one of
   those is wrong. The pickaxe may look oversized in hand.
4. **Hover**: zombies float 0.2 m. If they bob or sink, tune `hover`
   param and the gain 8 in `moveZombie`.
5. **Temple door** starts 1 m below floor level (template quirk).
6. Castdown menu: a 2.x game-mode selector shown for content mods; no
   known way to hide it from the mod yet.

## Next move

Load it. Then, in order of what the screenshot shows: fix placement, fix
lighting keys, tune zombie speed and bite rate so Jasper can outrun one
but not ignore it.

After that works: more houses from the template set (all 46 are already
downloaded), dirt paths between houses, water in the fountain (Teardown
has a `<water>` node), zombie sounds, a sun/moon in the sky.
