#!/usr/bin/env python3
"""Run mod/script/village.lua against a fake Teardown API.

    python3 -I tools/test_village.py

This is not Teardown. It is a stand-in that answers the API calls the script
makes, so we can catch syntax errors, nil indexes and broken state machines
before Darren loads the mod. The fake world is one straight line: a zombie
spawns at x = -10, the player stands at x = +10, and there is a wall at x = 6.

Scenario A: the wall is wood. The zombie must walk, get stuck, bite three
times, get through and hurt the player.
Scenario B: the wall is cobblestone (MakeHole returns 0). The zombie must give
up biting after four tries and ask for a new path, never hurting the player.
Both scenarios run in 2.x mode (server/client tables) and 1.x mode (globals).
"""
import sys
from pathlib import Path

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "mod/script/village.lua").read_text()

MOCK = r"""
function Vec(x, y, z) return {x or 0, y or 0, z or 0} end
function VecAdd(a, b) return {a[1]+b[1], a[2]+b[2], a[3]+b[3]} end
function VecSub(a, b) return {a[1]-b[1], a[2]-b[2], a[3]-b[3]} end
function VecScale(a, s) return {a[1]*s, a[2]*s, a[3]*s} end
function VecLength(a) return math.sqrt(a[1]*a[1] + a[2]*a[2] + a[3]*a[3]) end
function Transform(p, r) return {pos = p, rot = r or {0,0,0,1}} end
function TransformToParentPoint(tr, p) return VecAdd(tr.pos, p) end
function QuatEuler(x, y, z) return {x, y, z, 1} end
function QuatLookAt(a, b) return {0, 0, 0, 1} end

PARAMS = {}
function GetFloatParam(n, d) if PARAMS[n] ~= nil then return PARAMS[n] end return d end
GetIntParam, GetBoolParam = GetFloatParam, GetFloatParam

WORLD = {
  time = 0, bodies = {}, nextHandle = 10, holes = {}, debug = {},
  wallX = 6, wallHP = 3, wallSoft = true,
  player = {pos = {10, 0, 0}, health = 1, vel = {0, 0, 0}},
  env = {sunBrightness = 3, skyboxbrightness = 1, ambient = 1},
  envLog = {}, pathState = "idle", pathQueries = 0,
  spawnLocs = {{-10, 0.5, 0}, {-10, 0.5, 0}, {-10, 0.5, 0}},
}
function GetTime() return WORLD.time end
function DebugPrint(s) WORLD.debug[#WORLD.debug+1] = tostring(s) end
function FindLocations(tag, global) return {1, 2, 3} end
function GetLocationTransform(h) return {pos = WORLD.spawnLocs[h]} end
function GetEnvironmentProperty(k)
  if WORLD.env[k] == nil then error("unknown environment property " .. k) end
  return WORLD.env[k]
end
function SetEnvironmentProperty(k, v) WORLD.envLog[k] = v end
function Spawn(xml, tr)
  local h = WORLD.nextHandle; WORLD.nextHandle = h + 2
  WORLD.bodies[h] = {pos = tr.pos, vel = {0,0,0}, shape = h + 1, voxels = 345, valid = true}
  WORLD.spawnXml = xml
  return {h, h + 1}
end
function GetEntityType(h) if WORLD.bodies[h] then return "body" end return "shape" end
function GetBodyShapes(h) return {WORLD.bodies[h].shape} end
local function bodyOfShape(s) for _, b in pairs(WORLD.bodies) do if b.shape == s then return b end end end
function GetShapeVoxelCount(s) local b = bodyOfShape(s); return b and b.voxels or 0 end
function IsHandleValid(h)
  if WORLD.bodies[h] then return WORLD.bodies[h].valid end
  local b = bodyOfShape(h); return b ~= nil and b.valid
end
function Delete(h) WORLD.bodies[h].valid = false end
function GetBodyTransform(h) return {pos = WORLD.bodies[h].pos, rot = {0,0,0,1}} end
function GetBodyMass(h) return 120 end
function GetBodyCenterOfMass(h) return {0, 0.8, 0} end
function GetBodyVelocity(h) return WORLD.bodies[h].vel end
function ConstrainVelocity(a, b, point, dir, relVel, mn, mx)
  local body = WORLD.bodies[a]
  body.want = VecAdd(body.want or {0,0,0}, VecScale(dir, relVel))
end
function ConstrainOrientation() end
function GetPathState() return WORLD.pathState end
function QueryPath(s, e, maxDist, radius)
  WORLD.pathState = "busy"; WORLD.pathStart = s; WORLD.pathEnd = e; WORLD.pathAge = 0
  WORLD.pathQueries = WORLD.pathQueries + 1
  WORLD.queryTimes = WORLD.queryTimes or {}
  WORLD.queryTimes[#WORLD.queryTimes+1] = WORLD.time
end
function GetPathLength() return VecLength(VecSub(WORLD.pathEnd, WORLD.pathStart)) end
function GetPathPoint(d)
  local l = GetPathLength(); if l == 0 then return WORLD.pathStart end
  return VecAdd(WORLD.pathStart, VecScale(VecSub(WORLD.pathEnd, WORLD.pathStart), d / l))
end
function GetAllPlayers() return {0} end
function GetPlayerTransform(id) return {pos = WORLD.player.pos} end
function GetPlayerHealth(id) return WORLD.player.health end
function SetPlayerHealth(h, id) WORLD.player.health = h end
function GetPlayerVelocity(id) return WORLD.player.vel end
function SetPlayerVelocity(v, id) WORLD.player.vel = v end
-- The wall is a one-block slab from wallX to wallX+1. A bite counts if the
-- sphere overlaps the slab.
function MakeHole(pos, r0, r1, r2)
  WORLD.holes[#WORLD.holes+1] = {pos = pos, r0 = r0, r1 = r1, r2 = r2, t = WORLD.time}
  if pos[1] + r0 > WORLD.wallX and pos[1] - r0 < WORLD.wallX + 1 and WORLD.wallHP > 0 then
    if WORLD.wallSoft then WORLD.wallHP = WORLD.wallHP - 1; return 50 end
    return 0
  end
  return 0
end
function SpawnFire() end
function UiPush() end  function UiPop() end  function UiAlign() end
function UiTranslate() end  function UiFont() end  function UiColor() end
function UiTextOutline() end  function UiCenter() return 640 end
function UiText(t) WORLD.lastText = t; return 0, 0, 0, 0 end

-- Fake physics: a body moves at the velocity the constraints asked for,
-- except it cannot cross the wall while the wall stands.
function STEP(dt)
  WORLD.time = WORLD.time + dt
  if WORLD.pathState == "busy" then
    WORLD.pathAge = WORLD.pathAge + dt
    if WORLD.pathAge > 0.1 then WORLD.pathState = "done" end
  end
  for h, b in pairs(WORLD.bodies) do
    if b.valid then
      local w = b.want or {0,0,0}
      local nx = b.pos[1] + w[1] * dt
      -- arms reach 0.45 m in front of the feet, so the body stops there
      local stopX = WORLD.wallX - 0.45
      if WORLD.wallHP > 0 and b.pos[1] <= stopX and nx > stopX then
        nx = stopX; w = {0,0,0}
      end
      b.pos = {nx, b.pos[2], b.pos[3] + w[3] * dt}
      b.vel = w
      b.want = nil
    end
  end
end
"""


def run(mode: str, soft_wall: bool, seconds: float = 40.0):
    """40 s with a 100 s day starting at 0.48: night falls at 2 s and lasts
    until 52 s, so every check below is made while it is still night."""
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(f"WORLD.wallSoft = {'true' if soft_wall else 'false'}")
    # start just before sunset so the night begins within a few seconds
    lua.execute("PARAMS.daylength = 100; PARAMS.starttime = 0.48; PARAMS.maxzombies = 1")
    if mode == "2x":
        lua.execute("server = {}; client = {}; shared = {}")
    lua.execute(SCRIPT)
    g = lua.globals()
    if mode == "2x":
        init, tick, update, draw = g.server.init, g.server.tick, g.server.update, g.client.draw
    else:
        init, tick, update, draw = g.init, g.tick, g.update, g.draw
    init()
    dt = 1 / 60
    steps = int(seconds / dt)
    for _ in range(steps):
        tick(dt)
        update(dt)
        g.STEP(dt)
    draw()
    W = g.WORLD
    bodies = [b for _, b in W.bodies.items()]
    hole_times = [h.t for _, h in W.holes.items()]
    query_times = list(W.queryTimes.values()) if W.queryTimes else []
    # time from the 4th bite to the next path query (None if no such query)
    repath_delay = None
    if len(hole_times) >= 4:
        after = [q for q in query_times if q >= hole_times[3]]
        repath_delay = (after[0] - hole_times[3]) if after else None
    return {
        "debug": list(W.debug.values()),
        "zombies_spawned": len(bodies),
        "zombie_x": bodies[0].pos[1] if bodies else None,
        "holes": len(W.holes),
        "repath_delay": repath_delay,
        "wall_hp": W.wallHP,
        "player_health": W.player.health,
        "path_queries": W.pathQueries,
        "env_sun": W.envLog.sunBrightness,
        "nightlight": W.envLog.nightlight,
        "hud": W.lastText,
        "spawn_xml": W.spawnXml,
        "shared_title": g.shared.title,
    }


def check(cond, msg, failures):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


if __name__ == "__main__":
    failures = []
    for mode in ("2x", "legacy"):
        print(f"[{mode}] scenario A: wooden wall")
        r = run(mode, soft_wall=True)
        check(r["zombies_spawned"] == 1, f"one zombie spawned ({r['zombies_spawned']})", failures)
        check(r["wall_hp"] == 0, f"wooden wall eaten (hp left {r['wall_hp']}, holes {r['holes']})", failures)
        check(r["zombie_x"] is not None and r["zombie_x"] > 8.5, f"zombie reached the player (x={r['zombie_x']})", failures)
        check(r["player_health"] < 1, f"player was hurt (health {r['player_health']:.2f})", failures)
        check(r["path_queries"] >= 2, f"path re-queried ({r['path_queries']} queries)", failures)
        check(r["env_sun"] is not None and r["env_sun"] < 1, f"sun dimmed at night ({r['env_sun']})", failures)
        check(r["nightlight"] is True, "nightlight on at night", failures)
        check("NIGHT" in (r["shared_title"] or ""), f"HUD says night: {r['shared_title']!r}", failures)
        check(not any("not readable" in d for d in r["debug"]), "all env keys read", failures)

        print(f"[{mode}] scenario B: cobblestone wall")
        r = run(mode, soft_wall=False)
        check(r["wall_hp"] == 3, "stone wall untouched", failures)
        check(r["holes"] >= 4, f"zombie tried biting ({r['holes']} bites)", failures)
        check(r["zombie_x"] is not None and r["zombie_x"] < 6, f"zombie still outside the wall (x={r['zombie_x']})", failures)
        check(r["player_health"] == 1, "player never hurt", failures)
        check(r["repath_delay"] is not None and r["repath_delay"] < 0.3,
              f"new path asked for right after the 4th futile bite (delay {r['repath_delay']})", failures)
        for d in r["debug"]:
            print("  debug:", d)
    print()
    if failures:
        print(f"{len(failures)} FAILED")
        sys.exit(1)
    print("all checks passed")
