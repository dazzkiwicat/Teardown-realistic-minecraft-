#!/usr/bin/env python3
"""Re-read every vox file the build wrote with the independent reader
(vox.read) and check it against what the build says it wrote.

    python3 -I tools/check_vox.py

Structures: each chunk's voxel count, size and bottom-centre pivot against
mod/vox/<stem>.json; every palette index used is one the JSON lists.
Ground: each tile against preview/layout.json. Door: size, pivot, count.
Also: every vox file main.xml references exists, and nothing in mod/vox is
unreferenced. Exits non-zero on any mismatch.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blocks  # noqa: E402
import mc2vox  # noqa: E402
import vox  # noqa: E402

R = blocks.R
VOXDIR = ROOT / "mod" / "vox"
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


n_files = n_vox = 0
for jpath in sorted(VOXDIR.glob("*.json")):
    info = json.loads(jpath.read_text())
    sx, sy, sz = info["size_blocks"]
    total = 0
    for c in info["chunks"]:
        r = vox.read(str(VOXDIR / c["file"]))
        n_files += 1
        n_vox += r["count"]
        total += r["count"]
        size = (c["sx"] * R, c["sz"] * R, sy * R)
        check(r["count"] == c["voxels"], f"{c['file']}: {r['count']} voxels, json says {c['voxels']}")
        check(tuple(r["size"]) == size, f"{c['file']}: size {r['size']}, expected {size}")
        check(r["translation"] == (0, 0, size[2] // 2), f"{c['file']}: pivot {r['translation']}")
        bad = set(map(str, r["hist"])) - set(info["materials"])
        check(not bad, f"{c['file']}: palette indices {sorted(bad)} not in json materials")
    check(total == info["voxels"], f"{jpath.name}: chunks hold {total}, json says {info['voxels']}")
    for idx, mat in info["materials"].items():
        lo, hi = blocks.PALETTE_RANGES[mat]
        check(lo <= int(idx) <= hi, f"{jpath.name}: index {idx} outside {mat} range")

layout = json.loads((ROOT / "preview" / "layout.json").read_text())
for t in layout["tiles"]:
    r = vox.read(str(VOXDIR / Path(t["file"]).name))
    check(r["count"] == t["voxels"], f"{t['file']}: {r['count']} voxels, layout says {t['voxels']}")
seen = set()
for t in layout["tiles"]:
    if t["file"] not in seen:
        seen.add(t["file"])
        n_files += 1
        n_vox += vox.read(str(VOXDIR / Path(t["file"]).name))["count"]

r = vox.read(str(mc2vox.DOOR_FILE))
x0, x1, z0, z1 = mc2vox.DOOR_WINDOW
door_expected = R * blocks.DOOR_T * 2 * R - (x1 - x0) * blocks.DOOR_T * (z1 - z0)
check(tuple(r["size"]) == (R, blocks.DOOR_T, 2 * R), f"door_oak.vox size {r['size']}")
check(r["translation"] == (R // 2, 0, R), f"door_oak.vox pivot {r['translation']}")
check(r["count"] == door_expected, f"door_oak.vox {r['count']} voxels, expected {door_expected}")
n_files += 1
n_vox += r["count"]

xml = (ROOT / "mod" / "main.xml").read_text()
refs = set(re.findall(r'file="MOD/vox/([^"]+)"', xml))
for name in refs:
    check((VOXDIR / name).exists(), f"main.xml references missing {name}")
spawned = set(re.findall(r"MOD/vox/([\w.]+\.vox)", (ROOT / "mod/script/village.lua").read_text()))
for p in VOXDIR.glob("*.vox"):
    check(p.name in refs | spawned, f"{p.name} is not referenced by main.xml or village.lua")

print(f"checked {n_files} vox files, {n_vox} voxels")
if errors:
    print("\n".join("FAIL " + e for e in errors))
    sys.exit(1)
print("all counts, sizes and pivots match")
