# Minecraft Village Nights (a Teardown mod)

A small Minecraft plains village, built from Minecraft's own village
templates, inside Teardown. Zombies come out at night and chew through
wood, dirt and glass. Cobblestone holds. Survive until morning.

By Darren and Jasper.

## Install (Windows)

1. On this page click the green **Code** button, then **Download ZIP**.
2. Unzip it. Inside is a folder called `mod`.
3. Copy that `mod` folder to `Documents\Teardown\mods\` and rename it
   `MinecraftVillageNights` (any name with only letters and numbers works).
4. Start Teardown, open **Mods**, select **Minecraft Village Nights**, press **Play**.

You should see: a grassy field with a fountain in the middle, three small
wooden houses, a bigger house, a farm and an animal pen. A line of text at
the top says `Day 1   DAY` with a sunset countdown.

## Controls

- **Interact key (E by default)** while looking at a door: opens or closes
  it. Zombies cannot open doors; they chew through them.
- **Pickaxe** (select it from the tool bar): use it on any block to mine a
  whole metre cube, cobblestone included. Hit a zombie with it too.
- **Block placer**: use it to place a one metre block on the surface you
  aim at. The grab key (right mouse by default) cycles cobblestone, planks,
  glass. Cobblestone is the zombie-proof one.

## What to try

- Wait for the countdown. The light drops, the text says `NIGHT`, and
  zombies walk in from the edge of the field.
- Stand inside a wooden house. The zombie bites through the planks.
- Stand behind the cobblestone fountain or a cobblestone wall. It bites,
  gives up, and walks round.
- Hit a zombie with the sledgehammer until it breaks apart. That kills it.
- At sunrise the remaining zombies crumble.

Settings are in `mod/main.xml` on the `<script>` line:
`daylength` (seconds per full day, 240), `maxzombies` (4),
`starttime` (0.3 is mid morning, 0.5 is sunset).

## How it is built

Everything in `mod/vox/` and `mod/main.xml` is generated. Do not edit those
by hand; edit the tools and rebuild:

```
python3 -I tools/build_level.py
python3 -I tools/test_village.py
```

- `source/minecraft/village/plains/` are Minecraft's real plains village
  structure templates (`.nbt`), fetched from the mcmeta mirror of the game
  data. They are Mojang's assets, used here for a fan project.
- `tools/nbt.py` reads them. `tools/blocks.py` says what each Minecraft
  block becomes: its shape (stairs, slabs, fences, doors, panes, torches)
  and its Teardown material. `tools/mc2vox.py` writes MagicaVoxel files.
- One Minecraft block is 1 metre, which is 10 x 10 x 10 Teardown voxels.
- Teardown decides a voxel's material from its palette index. The table in
  `blocks.py` came from the official palette file in the modding docs.
  Soft (zombies eat it): glass, grass, dirt, wood, plaster, plastic.
  Medium (holds): concrete, brick, weak metal. Rock is unbreakable and
  forms the bottom of the ground.
- `mod/script/village.lua` is the game logic: clock, lighting, spawning,
  pathfinding, biting with `MakeHole` using only the soft radius.
- `tools/render.py` draws a preview PNG of any vox file, because this was
  written on a machine that cannot run Teardown. See `preview/`.
- `tools/test_village.py` runs the Lua against a fake Teardown API.

Reference notes pulled from the official docs are in `docs/`.
