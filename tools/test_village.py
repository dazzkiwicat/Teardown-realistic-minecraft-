#!/usr/bin/env python3
"""Run mod/script/village.lua against a fake Teardown API.

    python3 -I tools/test_village.py

This is not Teardown. It is a stand-in that answers the API calls the script
makes, so we can catch syntax errors, nil indexes and broken state machines
before Darren loads the mod. It runs the script in Lua 5.1 (Teardown's
version) when lupa provides it. The fake world is one straight line: a
zombie spawns at x = -10, the player stands at x = +10, and there is a wall
at x = 6..7. The ground is the plane y = 0.

Scenario A: the wall is wood. The zombie must walk, get stuck, bite three
times, get through and hurt the player. It must hover about 0.2 m above the
ground the whole way.
Scenario B: the wall is cobblestone (MakeHole returns 0). The zombie must give
up biting after four tries and ask for a new path, never hurting the player.
Scenario C (daytime, no zombies): a door opens and closes with "interact"
only when looked at; the pickaxe removes one snapped block; the placer spawns
a static block at an integer corner, cycles material, and refuses to place
inside the player.
All scenarios run in 2.x mode (server/client tables, ServerCall) and 1.x mode
(globals). In 2.x mode the mock also flags server-only functions called from
client code and client-only functions called from server code.
"""
import sys
from pathlib import Path

try:  # Teardown runs Lua 5.1; use it when this lupa build has it
    from lupa.lua51 import LuaRuntime
except ImportError:  # pragma: no cover
    from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "mod/script/village.lua").read_text()

MOCK = r"""
function Vec(x, y, z) return {x or 0, y or 0, z or 0} end
function VecAdd(a, b) return {a[1]+b[1], a[2]+b[2], a[3]+b[3]} end
function VecSub(a, b) return {a[1]-b[1], a[2]-b[2], a[3]-b[3]} end
function VecScale(a, s) return {a[1]*s, a[2]*s, a[3]*s} end
function VecLength(a) return math.sqrt(a[1]*a[1] + a[2]*a[2] + a[3]*a[3]) end
function Transform(p, r) return {pos = p or {0,0,0}, rot = r or {0,0,0,1}} end
function TransformToParentPoint(tr, p) return VecAdd(tr.pos, p) end
-- Fake quaternions hold euler degrees {x, y, z, 1}. Rotation order follows
-- the docs: yaw (Y), then pitch (Z), then roll (X), i.e. v' = Ry Rz Rx v.
function QuatEuler(x, y, z) return {x, y, z, 1} end
function GetQuatEuler(q) return q[1], q[2], q[3] end
function QuatLookAt(a, b) return {0, 0, 0, 1} end
local function rotX(v, a) local c, s = math.cos(a), math.sin(a) return {v[1], v[2]*c - v[3]*s, v[2]*s + v[3]*c} end
local function rotY(v, a) local c, s = math.cos(a), math.sin(a) return {v[1]*c + v[3]*s, v[2], -v[1]*s + v[3]*c} end
local function rotZ(v, a) local c, s = math.cos(a), math.sin(a) return {v[1]*c - v[2]*s, v[1]*s + v[2]*c, v[3]} end
function TransformToParentVec(t, v)
  local r, d = t.rot, math.pi / 180
  return rotY(rotZ(rotX(v, r[1]*d), r[3]*d), r[2]*d)
end

PARAMS = {}
function GetFloatParam(n, d) if PARAMS[n] ~= nil then return PARAMS[n] end return d end
GetIntParam, GetBoolParam = GetFloatParam, GetFloatParam

GROUND_SHAPE, WALL_SHAPE, WORLD_BODY = 1, 2, 3
WORLD = {
  time = 0, bodies = {}, nextHandle = 10, holes = {}, debug = {},
  wallX = 6, wallHP = 3, wallSoft = true,
  player = {pos = {10, 0, 0}, health = 1, vel = {0, 0, 0}},
  env = {sunBrightness = 3, skyboxbrightness = 1, ambient = 1},
  envLog = {}, pathState = "idle", pathQueries = 0,
  spawnLocs = {{-10, 0.5, 0}, {-10, 0.5, 0}, {-10, 0.5, 0}},
  tags = {}, reject = {}, pressed = {}, reg = {}, tools = {}, toolEnabled = {},
  spawns = {}, violations = {}, texts = {}, toolTransforms = {}, serverCalls = {},
  camera = {pos = {10, 1.7, 0}, rot = {0, 90, 0, 1}}, tool = "",
  angConstraints = 0, vertConstraints = 0, hoverSamples = {},
}
-- side checks (2.x only; WORLD.side is nil in legacy mode)
local function serverOnly(name)
  if WORLD.side == "client" then WORLD.violations[#WORLD.violations+1] = name .. " called on client" end
end
local function clientOnly(name)
  if WORLD.side == "server" then WORLD.violations[#WORLD.violations+1] = name .. " called on server" end
end

function GetTime() return WORLD.time end
function DebugPrint(s) WORLD.debug[#WORLD.debug+1] = tostring(s) end
function FindLocations(tag, global) return {1, 2, 3} end
function FindBodies(tag, global)
  local out = {}
  for h, t in pairs(WORLD.tags) do if t[tag] ~= nil and WORLD.bodies[h] then out[#out+1] = h end end
  table.sort(out)
  return out
end
function HasTag(h, tag) return WORLD.tags[h] ~= nil and WORLD.tags[h][tag] ~= nil end
function GetTagValue(h, tag) return (WORLD.tags[h] and WORLD.tags[h][tag]) or "" end
function IsBodyBroken(h) return WORLD.bodies[h] ~= nil and WORLD.bodies[h].broken == true end
function ConstrainPosition(a, b, pa, pb, v, imp)
  local body = WORLD.bodies[a]; if body then body.targetPos = pb end
end
function GetLocationTransform(h) return {pos = WORLD.spawnLocs[h]} end
function GetEnvironmentProperty(k)
  if WORLD.env[k] == nil then error("unknown environment property " .. k) end
  return WORLD.env[k]
end
function SetEnvironmentProperty(k, v) serverOnly("SetEnvironmentProperty"); WORLD.envLog[k] = v end
function Spawn(xml, tr, allowStatic)
  serverOnly("Spawn")
  local h = WORLD.nextHandle; WORLD.nextHandle = h + 2
  local zombie = string.find(xml, "zombie", 1, true) ~= nil
  WORLD.bodies[h] = {pos = tr.pos, vel = {0,0,0}, shape = h + 1, voxels = 345, valid = true,
                     kind = zombie and "zombie" or "block", born = WORLD.time,
                     box = zombie and {min = {-0.3, 0, -0.3}, max = {0.3, 1.7, 0.3}} or nil}
  WORLD.spawnXml = xml
  WORLD.spawns[#WORLD.spawns+1] = {xml = xml, pos = tr.pos, allowStatic = allowStatic == true}
  return {h, h + 1}
end
function GetEntityType(h) if WORLD.bodies[h] then return "body" end return "shape" end
function GetBodyShapes(h) return {WORLD.bodies[h].shape} end
local function bodyOfShape(s) for h, b in pairs(WORLD.bodies) do if b.shape == s then return b, h end end end
function GetShapeBody(s) local _, h = bodyOfShape(s); return h or WORLD_BODY end
function GetShapeVoxelCount(s) local b = bodyOfShape(s); return b and b.voxels or 0 end
function IsHandleValid(h)
  if WORLD.bodies[h] then return WORLD.bodies[h].valid end
  local b = bodyOfShape(h); return b ~= nil and b.valid
end
function Delete(h) WORLD.bodies[h].valid = false end
function GetBodyTransform(h) local b = WORLD.bodies[h]; return {pos = b.pos, rot = b.rot or {0,0,0,1}} end
function GetBodyMass(h) return 120 end
function GetBodyCenterOfMass(h) return {0, 0.8, 0} end
function GetBodyVelocity(h) return WORLD.bodies[h].vel end
function ConstrainVelocity(a, b, point, dir, relVel, mn, mx)
  local body = WORLD.bodies[a]
  body.want = VecAdd(body.want or {0,0,0}, VecScale(dir, relVel))
  if dir[2] ~= 0 then body.vset = true; WORLD.vertConstraints = WORLD.vertConstraints + 1 end
end
function ConstrainOrientation(a, b, qa, qb)
  local body = WORLD.bodies[a]; if body then body.targetRot = qb end
end
function ConstrainAngularVelocity(a, b, dir, v, mn, mx)
  WORLD.angConstraints = WORLD.angConstraints + 1
end

-- Scene queries. Filters last for one query, as the docs say.
function QueryRequire() end
function QueryRejectBody(h) WORLD.reject[h] = true end
function QueryRejectPlayer() end
local function rayBox(o, d, mn, mx)
  local tmin, tmax, nrm = -1e9, 1e9, nil
  for i = 1, 3 do
    if math.abs(d[i]) < 1e-9 then
      if o[i] < mn[i] or o[i] > mx[i] then return nil end
    else
      local t1, t2 = (mn[i] - o[i]) / d[i], (mx[i] - o[i]) / d[i]
      local n = {0, 0, 0}
      if t1 <= t2 then n[i] = -1 else t1, t2 = t2, t1; n[i] = 1 end
      if t1 > tmin then tmin, nrm = t1, n end
      if t2 < tmax then tmax = t2 end
      if tmin > tmax then return nil end
    end
  end
  if tmin < 0 then return nil end
  return tmin, nrm
end
function QueryRaycast(o, d, maxDist)
  local reject = WORLD.reject; WORLD.reject = {}
  local best, bn, bs = maxDist + 1e-6, nil, nil
  if d[2] < 0 then  -- ground plane y = 0
    local t = o[2] / -d[2]
    if t >= 0 and t < best then best, bn, bs = t, {0, 1, 0}, GROUND_SHAPE end
  end
  if WORLD.wallHP > 0 then
    local t, n = rayBox(o, d, {WORLD.wallX, 0, -50}, {WORLD.wallX + 1, 3, 50})
    if t and t < best then best, bn, bs = t, n, WALL_SHAPE end
  end
  for h, b in pairs(WORLD.bodies) do
    if b.valid and b.box and not reject[h] then
      local t, n = rayBox(o, d, VecAdd(b.pos, b.box.min), VecAdd(b.pos, b.box.max))
      if t and t < best then best, bn, bs = t, n, b.shape end
    end
  end
  if bs then return true, best, bn, bs end
  return false, 0, {0, 0, 0}, 0
end

-- Path planners keyed by id; id 0 is the shared default one.
WORLD.planners = {}
local function planner(id) id = id or 0; WORLD.planners[id] = WORLD.planners[id] or {state = "idle"}; return WORLD.planners[id] end
function GetPathState(id) return planner(id).state end
local function startQuery(id, s, e)
  WORLD.reject = {}
  local p = planner(id); p.state = "busy"; p.start = s; p["end"] = e; p.age = 0
  WORLD.pathQueries = WORLD.pathQueries + 1
  WORLD.queryTimes = WORLD.queryTimes or {}
  WORLD.queryTimes[#WORLD.queryTimes+1] = WORLD.time
end
function QueryPath(s, e, maxDist, radius) startQuery(0, s, e) end
function GetPathLength(id) local p = planner(id); return VecLength(VecSub(p["end"], p.start)) end
function GetPathPoint(d, id)
  local p = planner(id); local l = GetPathLength(id); if l == 0 then return p.start end
  return VecAdd(p.start, VecScale(VecSub(p["end"], p.start), d / l))
end

-- Players, camera, input, registry, tools
function GetAllPlayers() return {0} end
function GetPlayerTransform(id) return {pos = WORLD.player.pos} end
function GetPlayerHealth(id) return WORLD.player.health end
function SetPlayerHealth(h, id) serverOnly("SetPlayerHealth"); WORLD.player.health = h end
function GetPlayerVelocity(id) return WORLD.player.vel end
function SetPlayerVelocity(v, id) serverOnly("SetPlayerVelocity"); WORLD.player.vel = v end
function GetPlayerCameraTransform(id) return {pos = WORLD.camera.pos, rot = WORLD.camera.rot} end
function InputPressed(name, id) return WORLD.pressed[name] == true end
function SetBool(k, v) WORLD.reg[k] = v end
function GetBool(k) return WORLD.reg[k] == true end
function SetString(k, v) WORLD.reg[k] = v end
function GetString(k) local v = WORLD.reg[k]; if v == nil then return "" end return tostring(v) end
function RegisterTool(id, name, file, group) serverOnly("RegisterTool"); WORLD.tools[id] = file end
function SetToolTransform(t, sway, id)
  clientOnly("SetToolTransform")
  WORLD.toolTransforms[#WORLD.toolTransforms+1] = t.rot[1]
end
function SETTOOL(id) WORLD.tool = id; WORLD.reg["game.player.tool"] = id end

-- The wall is a one-block slab from wallX to wallX+1. A bite counts if the
-- sphere overlaps the slab.
function MakeHole(pos, r0, r1, r2)
  serverOnly("MakeHole")
  WORLD.holes[#WORLD.holes+1] = {pos = pos, r0 = r0, r1 = r1 or 0, r2 = r2 or 0, t = WORLD.time}
  if pos[1] + r0 > WORLD.wallX and pos[1] - r0 < WORLD.wallX + 1 and WORLD.wallHP > 0 then
    if WORLD.wallSoft then WORLD.wallHP = WORLD.wallHP - 1; return 50 end
    return 0
  end
  return 0
end
function SpawnFire() serverOnly("SpawnFire") end
function UiPush() end  function UiPop() end  function UiAlign() end
function UiTranslate() end  function UiFont() end  function UiColor() end
function UiTextOutline() end  function UiCenter() return 640 end  function UiMiddle() return 360 end
function UiText(t) WORLD.lastText = t; WORLD.texts[#WORLD.texts+1] = t; return 0, 0, 0, 0 end

-- 2.x-only API (see run()): per-agent planners, per-player tools, ServerCall.
function MOCK_2X()
  WORLD.nextPlanner = 1
  function CreatePathPlanner() local id = WORLD.nextPlanner; WORLD.nextPlanner = id + 1; planner(id); return id end
  function DeletePathPlanner(id) WORLD.planners[id] = nil end
  function PathPlannerQuery(id, s, e, maxDist, radius) startQuery(id, s, e) end
  function GetPlayerTool(id) return WORLD.tool end
  function GetPlayerCanUseTool(id) return true end
  function SetToolEnabled(tool, on, id)
    serverOnly("SetToolEnabled")
    WORLD.toolEnabled[tool .. "@" .. tostring(id)] = on
  end
  -- Synchronous stand-in: run the named function as the server would.
  function ServerCall(name, ...)
    if WORLD.side ~= "client" then WORLD.violations[#WORLD.violations+1] = "ServerCall from server" end
    local f = _G
    for part in string.gmatch(name, "[^%.]+") do f = f and f[part] end
    if type(f) ~= "function" then error("ServerCall: no function " .. name) end
    WORLD.serverCalls[#WORLD.serverCalls+1] = name
    local prev = WORLD.side; WORLD.side = "server"
    f(...)
    WORLD.side = prev
  end
end

-- Fake physics: a zombie moves at the velocity the constraints asked for,
-- except it cannot cross the wall while the wall stands. Vertically it
-- follows the hover constraint when there is one, else gravity drops it to
-- the ground plane. Doors and placed blocks do not move.
function STEP(dt)
  WORLD.time = WORLD.time + dt
  WORLD.pressed = {}
  for _, p in pairs(WORLD.planners) do
    if p.state == "busy" then
      p.age = p.age + dt
      if p.age > 0.1 then p.state = "done" end
    end
  end
  for h, b in pairs(WORLD.bodies) do
    if b.valid and b.kind == "zombie" then
      local w = b.want or {0,0,0}
      local nx = b.pos[1] + w[1] * dt
      -- arms reach 0.45 m in front of the feet, so the body stops there
      local stopX = WORLD.wallX - 0.45
      if WORLD.wallHP > 0 and b.pos[1] <= stopX and nx > stopX then
        nx = stopX; w = {0, w[2], 0}
      end
      local ny
      if b.vset then
        b.fall = 0; ny = b.pos[2] + w[2] * dt
      else
        b.fall = (b.fall or 0) - 9.8 * dt; ny = math.max(0, b.pos[2] + b.fall * dt)
      end
      b.pos = {nx, ny, b.pos[3] + w[3] * dt}
      b.vel = w
      b.want = nil; b.vset = nil
      if WORLD.time - b.born > 1.0 then
        WORLD.hoverSamples[#WORLD.hoverSamples+1] = ny
      end
    end
  end
end
"""


class Sim:
    """One Lua state with the mock and the script loaded, in 2.x or 1.x mode."""

    def __init__(self, mode: str, setup: str = ""):
        self.mode = mode
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCK)
        if setup:
            self.lua.execute(setup)
        if mode == "2x":
            self.lua.execute("server = {}; client = {}; shared = {}; MOCK_2X()")
        self.lua.execute(SCRIPT)
        self.g = self.lua.globals()
        self.W = self.g.WORLD
        self.side("server")
        if mode == "2x":
            self.g.server.init()
        else:
            self.g.init()
        self.side(None)

    def side(self, s):
        self.W.side = s if self.mode == "2x" else None

    def frame(self, dt=1 / 60, press=()):
        for name in press:
            self.W.pressed[name] = True
        g = self.g
        if self.mode == "2x":
            self.side("server"); g.server.tick(dt)
            self.side("client"); g.client.tick(dt)
            self.side("server"); g.server.update(dt)
            self.side(None)
        else:
            g.tick(dt)
            g.update(dt)
        g.STEP(dt)

    def run(self, seconds, dt=1 / 60):
        for _ in range(int(round(seconds / dt))):
            self.frame(dt)

    def draw(self):
        self.lua.execute("WORLD.texts = {}")
        self.side("client")
        (self.g.client.draw if self.mode == "2x" else self.g.draw)()
        self.side(None)
        return list(self.W.texts.values())

    def look(self, pos, rot):
        self.lua.execute(f"WORLD.camera = {{pos = {{{pos[0]}, {pos[1]}, {pos[2]}}}, "
                         f"rot = {{{rot[0]}, {rot[1]}, {rot[2]}, 1}}}}")

    def lst(self, name):
        t = self.W[name]
        return list(t.values()) if t else []


def run(mode: str, soft_wall: bool, seconds: float = 40.0):
    """40 s with a 100 s day starting at 0.48: night falls at 2 s and lasts
    until 52 s, so every check below is made while it is still night."""
    setup = (f"WORLD.wallSoft = {'true' if soft_wall else 'false'}\n"
             # start just before sunset so the night begins within a few seconds
             "PARAMS.daylength = 100; PARAMS.starttime = 0.48; PARAMS.maxzombies = 1")
    sim = Sim(mode, setup)
    sim.run(seconds)
    sim.draw()
    W, g = sim.W, sim.g
    zombies = [b for _, b in W.bodies.items() if b.kind == "zombie"]
    hole_times = [h.t for h in sim.lst("holes")]
    query_times = sim.lst("queryTimes")
    # time from the 4th bite to the next path query (None if no such query)
    repath_delay = None
    if len(hole_times) >= 4:
        after = [q for q in query_times if q >= hole_times[3]]
        repath_delay = (after[0] - hole_times[3]) if after else None
    hover = sim.lst("hoverSamples")
    return {
        "debug": sim.lst("debug"),
        "zombies_spawned": len(zombies),
        "zombie_x": zombies[0].pos[1] if zombies else None,
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
        "planners_live": len([1 for _ in W.planners.items()]),
        "hover_n": len(hover),
        "hover_dev": max((abs(y - 0.2) for y in hover), default=None),
        "vert": W.vertConstraints,
        "ang": W.angConstraints,
        "violations": sim.lst("violations"),
    }


# Scenario C world: a door whose hinge is at (8, 0, 4.5), leaf along +z,
# closed yaw 30, swing "+1" (the exact tag text main.xml writes); a dummy
# zombie-tagged body at (8, 0, -3); the stone wall at x = 6..7.
TOOLS_SETUP = """
WORLD.wallSoft = false
PARAMS.daylength = 100; PARAMS.starttime = 0.1
WORLD.bodies[50] = {pos = {8, 0, 4.5}, rot = {0, 30, 0, 1}, vel = {0,0,0}, shape = 51, voxels = 400,
                    valid = true, kind = "door", box = {min = {-0.05, 0, 0}, max = {0.05, 2, 1}}}
WORLD.tags[50] = {door = "", swing = "+1"}
WORLD.bodies[60] = {pos = {8, 0, -3}, vel = {0,0,0}, shape = 61, voxels = 345,
                    valid = true, kind = "dummy", box = {min = {-0.3, 0, -0.3}, max = {0.3, 1.7, 0.3}}}
WORLD.tags[60] = {zombie = ""}
"""
LOOK_WEST = (0, 90, 0)    # camera -z turned to world -x
LOOK_EAST = (0, -90, 0)


def run_tools(mode: str, check, failures):
    sim = Sim(mode, TOOLS_SETUP)
    W, g = sim.W, sim.g
    tag = f"[{mode}]"

    # --- registration
    sim.frame()
    check(W.tools.pickaxe == "MOD/vox/pickaxe.vox" and W.tools.placer == "MOD/vox/placer.vox",
          f"{tag} both tools registered with RegisterTool", failures)
    check(all((ROOT / "mod/vox" / f).exists() for f in ("pickaxe.vox", "placer.vox")),
          f"{tag} tool vox files exist (tools/make_tools.py)", failures)
    check(W.reg["game.tool.pickaxe.enabled"] is True and W.reg["game.tool.placer.enabled"] is True,
          f"{tag} tools enabled via game.tool.<id>.enabled", failures)
    if mode == "2x":
        check(W.toolEnabled["pickaxe@0"] is True and W.toolEnabled["placer@0"] is True,
              f"{tag} tools enabled per player with SetToolEnabled", failures)

    def door_yaw():
        sim.run(0.2)
        return W.bodies[50].targetRot[2]

    # --- door
    sim.look((10, 1.7, 5), LOOK_WEST)
    yaw0 = door_yaw()
    check(yaw0 == 30, f"{tag} door held closed (target yaw {yaw0})", failures)
    texts = sim.draw()
    check(any("open/close door" in t for t in texts), f"{tag} door hint shown when looking at it", failures)
    sim.look((10, 1.7, 5), LOOK_EAST)
    sim.frame(press=["interact"])
    yaw1 = door_yaw()
    check(yaw1 == 30, f"{tag} interact looking away leaves the door shut (yaw {yaw1})", failures)
    texts = sim.draw()
    check(not any("open/close door" in t for t in texts), f"{tag} no door hint when looking away", failures)
    sim.look((10, 1.7, 5), LOOK_WEST)
    sim.frame(press=["interact"])
    yaw2 = door_yaw()
    check(yaw2 == 120, f"{tag} interact on the door opens it (yaw {yaw2}, closed 30, swing +1)", failures)
    sim.frame(press=["interact"])
    yaw3 = door_yaw()
    check(yaw3 == 30, f"{tag} interact again closes it (yaw {yaw3})", failures)
    check(tuple(W.bodies[50].targetPos.values()) == (8, 0, 4.5), f"{tag} door hinge pinned", failures)
    if mode == "2x":
        check("server.toggleDoor" in sim.lst("serverCalls"), f"{tag} door toggled through ServerCall", failures)

    # --- pickaxe on a block
    g.SETTOOL("pickaxe")
    sim.look((10, 1.7, 0.3), LOOK_WEST)   # mid-cell: z = 0 is a block edge
    n0 = len(W.holes)
    sim.frame(press=["usetool"])
    sim.frame(press=["usetool"])   # inside the 0.35 s cooldown: ignored
    holes = sim.lst("holes")[n0:]
    check(len(holes) == 1, f"{tag} pickaxe rate-limited ({len(holes)} holes from two quick clicks)", failures)
    if holes:
        h = holes[0]
        c = tuple(h.pos.values())
        snapped = all(abs((v - 0.5) - round(v - 0.5)) < 1e-9 for v in c)
        check(h.r0 == 0.5 and h.r1 == 0.5 and h.r2 == 0 and snapped and c == (6.5, 1.5, 0.5),
              f"{tag} pickaxe MakeHole r=({h.r0},{h.r1},{h.r2}) at {c}", failures)
    swings = [a for a in sim.lst("toolTransforms") if a < -1]
    check(len(swings) > 0, f"{tag} pickaxe swings with SetToolTransform", failures)
    texts = sim.draw()
    check("Pickaxe" in texts, f"{tag} HUD tool line: Pickaxe", failures)
    sim.run(0.4)
    check(sim.lst("toolTransforms")[-1] == 0, f"{tag} swing decays back to rest", failures)
    # --- pickaxe on a zombie
    sim.look((10, 1.2, -3), LOOK_WEST)
    n0 = len(W.holes)
    sim.frame(press=["usetool"])
    holes = sim.lst("holes")[n0:]
    check(len(holes) == 1 and holes[0].r0 == 0.35 and holes[0].r1 == 0,
          f"{tag} pickaxe on a zombie: soft-only MakeHole 0.35", failures)
    sim.run(0.4)

    # --- placer
    g.SETTOOL("placer")
    sim.look((10, 1.7, 0.3), (-45, 90, 0))   # 45 degrees down, facing -x
    s0 = len(W.spawns)
    sim.frame(press=["usetool"])
    spawns = sim.lst("spawns")[s0:]
    check(len(spawns) == 1, f"{tag} placer spawned one block", failures)
    if spawns:
        s = spawns[0]
        p = tuple(s.pos.values())
        check(s.allowStatic and p == (8, 0, 0) and all(float(v).is_integer() for v in p),
              f"{tag} placer Spawn allowStatic={s.allowStatic} at corner {p}", failures)
        check("pos=" not in s.xml and "material='concrete'" in s.xml,
              f"{tag} voxbox string has no pos and is cobblestone: {s.xml}", failures)
    texts = sim.draw()
    check("Placer: COBBLESTONE" in texts, f"{tag} HUD tool line: Placer: COBBLESTONE", failures)
    sim.run(0.3)
    sim.frame(press=["grab"])
    texts = sim.draw()
    check("Placer: PLANKS" in texts, f"{tag} grab cycles material to PLANKS", failures)
    sim.run(0.3)
    sim.frame(press=["usetool"])
    last = sim.lst("spawns")[-1]
    check("material='wood'" in last.xml, f"{tag} planks block is wood", failures)
    sim.run(0.3)
    s0 = len(W.spawns)
    sim.look((10, 1.7, 0.3), (-90, 90, 0))   # straight down at own feet
    sim.frame(press=["usetool"])
    check(len(W.spawns) == s0, f"{tag} placer refuses to place inside the player", failures)

    check(not sim.lst("violations"), f"{tag} no server/client side violations {sim.lst('violations')}", failures)


CHECKS = [0]


def check(cond, msg, failures):
    CHECKS[0] += 1
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
        if mode == "2x":
            check(r["planners_live"] == 1, f"zombie got its own path planner ({r['planners_live']} live, shared slot unused)", failures)
        check(r["env_sun"] is not None and r["env_sun"] < 1, f"sun dimmed at night ({r['env_sun']})", failures)
        check(r["nightlight"] is True, "nightlight on at night", failures)
        check("NIGHT" in (r["shared_title"] or ""), f"HUD says night: {r['shared_title']!r}", failures)
        check(not any("not readable" in d for d in r["debug"]), "all env keys read", failures)
        check(r["hover_n"] > 100 and r["hover_dev"] is not None and r["hover_dev"] < 0.03,
              f"zombie hovers 0.2 m above ground (max deviation {r['hover_dev']}, {r['hover_n']} samples)", failures)
        check(r["vert"] > 0 and r["ang"] > 0, f"hover and anti-spin constraints applied ({r['vert']}, {r['ang']})", failures)
        check(not r["violations"], f"no server/client side violations {r['violations']}", failures)

        print(f"[{mode}] scenario B: cobblestone wall")
        r = run(mode, soft_wall=False)
        check(r["wall_hp"] == 3, "stone wall untouched", failures)
        check(r["holes"] >= 4, f"zombie tried biting ({r['holes']} bites)", failures)
        check(r["zombie_x"] is not None and r["zombie_x"] < 6, f"zombie still outside the wall (x={r['zombie_x']})", failures)
        check(r["player_health"] == 1, "player never hurt", failures)
        check(r["repath_delay"] is not None and r["repath_delay"] < 0.3,
              f"new path asked for right after the 4th futile bite (delay {r['repath_delay']})", failures)
        check(r["hover_dev"] is not None and r["hover_dev"] < 0.03,
              f"zombie hovers while pressed against the wall (max deviation {r['hover_dev']})", failures)
        for d in r["debug"]:
            print("  debug:", d)

        print(f"[{mode}] scenario C: doors and tools")
        run_tools(mode, check, failures)
    print()
    if failures:
        print(f"{len(failures)} of {CHECKS[0]} checks FAILED")
        sys.exit(1)
    print(f"all {CHECKS[0]} checks passed")
