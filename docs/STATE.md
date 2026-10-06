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

## Next move

Load it. Then, in order of what the screenshot shows: fix placement, fix
lighting keys, tune zombie speed and bite rate so Jasper can outrun one
but not ignore it.

After that works: more houses from the template set (all 46 are already
downloaded), dirt paths between houses, water in the fountain (Teardown
has a `<water>` node), zombie sounds, a sun/moon in the sky.
