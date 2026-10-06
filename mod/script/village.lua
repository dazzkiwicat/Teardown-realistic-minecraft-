--[[
village.lua  -  day/night cycle and zombies for the Minecraft village.

What it does
  * Runs a clock. A whole day is `daylength` seconds (default 240 = 4 min).
    0.0 is sunrise, 0.5 is sunset, night is the second half.
  * At night, zombies spawn at the <location tags="zombiespawn"> markers and
    walk toward the nearest player using Teardown's path planner.
  * A zombie that cannot make progress BITES: MakeHole with only the soft
    radius, so it eats wood, dirt, glass, plaster and plastic but NOT
    cobblestone (concrete), brick or metal. Build with stone to be safe.
  * Touching a zombie costs health and shoves you. Breaking a zombie (sledge,
    shotgun, car...) kills it: it is made of wood. At sunrise they crumble.
  * Zombies hover a little above the ground like the game's robots (two
    downward raycasts hold the height), so they glide up steps instead of
    tripping on them.
  * Doors (bodies tagged "door swing=+1/-1") are held shut by physics and
    open/close with the interact key. Zombies never open them: they chew
    through, doors are wood.
  * Two tools: a PICKAXE (removes one whole block, cobblestone included) and
    a BLOCK PLACER (cobblestone / planks / glass, cycled with the grab input).

Runs on Teardown 2.x (server/client tables) and on 1.x (global callbacks)
through the shim at the bottom.

Tuning lives in the <script> node of main.xml as param0="name=value".
]]

-- ========= compatibility shim (part 1) =========
local LEGACY = (server == nil and client == nil)
server = server or {}
client = client or {}
shared = shared or {}

-- ========= tuning =========
local DAY_LENGTH    = GetFloatParam("daylength", 240)   -- seconds per full day
local MAX_ZOMBIES   = GetIntParam("maxzombies", 4)
local ZOMBIE_SPEED  = GetFloatParam("zombiespeed", 2.2) -- metres per second
local START_TIME    = GetFloatParam("starttime", 0.3)   -- 0..1, 0.5 = sunset
local BURN_AT_DAWN  = GetBoolParam("burnatdawn", false) -- true = set them on fire (spreads!)
local FRONT_FLIP    = GetBoolParam("frontflip", false)  -- set true if zombies walk backwards
local HOVER         = GetFloatParam("hover", 0.2)       -- metres between feet and ground

-- The zombie's arms reach 0.45 m in front of its feet, so a wall it presses
-- against is about 0.45 m ahead. The bite sphere covers 0.45..1.55 m ahead:
-- it reaches the wall face without eating the zombie's own hands.
local BITE_RADIUS   = 0.55   -- metres. Soft materials only.
local BITE_INTERVAL = 0.6    -- seconds between bites
local BITE_REACH    = 1.0    -- sphere centre, metres in front of the feet
local STUCK_TIME    = 0.6    -- seconds without progress before biting starts
local HIT_RANGE     = 1.4    -- metres from zombie chest to player centre
local HIT_DAMAGE    = 0.15   -- player health is 0..1
local HIT_INTERVAL  = 0.8
local SPAWN_INTERVAL = 6.0
local REPATH_EVERY  = 1.5    -- seconds between path queries per zombie
local PATH_STEP     = 0.5    -- metres between stored path points
local ZOMBIE_HEIGHT = 1.7
local HIP_HEIGHT    = 0.9    -- hover raycasts start this far above the feet
local HOVER_AHEAD   = 0.35   -- second raycast this far ahead of the hips
local ZOMBIE_XML = "<body dynamic='true' tags='zombie'><vox file='MOD/vox/zombie.vox'/></body>"

-- Newer Teardown gives every zombie its own path planner. Older versions
-- have one shared planner, so zombies take turns (see updatePaths).
local HAS_PLANNERS = (CreatePathPlanner ~= nil)

-- ========= server state =========
local S = {
	t = START_TIME, day = 1, night = false,
	zombies = {}, spawnPoints = {}, spawnTimer = 0,
	pathOwner = nil,       -- the zombie whose QueryPath is running
	envDay = {}, envTimer = 0, kills = 0,
}

-- ========= small helpers =========
local function flat(v) return Vec(v[1], 0, v[3]) end
local function dist2d(a, b) return VecLength(flat(VecSub(a, b))) end
local function clamp(x, lo, hi) if x < lo then return lo elseif x > hi then return hi else return x end end

-- Daylight 1 = full day, 0 = full night, with ramps at sunset and sunrise.
local function daylight(t)
	if t < 0.45 then return 1 end
	if t < 0.55 then return 1 - (t - 0.45) / 0.10 end
	if t < 0.95 then return 0 end
	return (t - 0.95) / 0.05
end

local function players()
	if not LEGACY and GetAllPlayers then
		local ids = GetAllPlayers()
		if ids and #ids > 0 then return ids end
	end
	return { 0 }
end

local function playerFeet(id)
	if LEGACY then return GetPlayerTransform().pos end
	return GetPlayerTransform(id).pos
end

local function nearestPlayer(pos)
	local best, bestD = 0, 1e9
	for _, id in ipairs(players()) do
		local d = dist2d(pos, playerFeet(id))
		if d < bestD then best, bestD = id, d end
	end
	return best, bestD
end

-- ========= environment (day/night look) =========
-- These property names are the Teardown editor's environment properties.
-- Any that cannot be read is reported once with DebugPrint and skipped.
local ENV_SCALED = { "sunBrightness", "skyboxbrightness", "ambient" }

local function captureEnv()
	for _, k in ipairs(ENV_SCALED) do
		local ok, v = pcall(GetEnvironmentProperty, k)
		if ok and type(v) == "number" then
			S.envDay[k] = v
		else
			DebugPrint("village.lua: environment key not readable: " .. k)
		end
	end
end

local function applyEnv(light)
	local f = 0.04 + 0.96 * light   -- never pitch black
	for k, v in pairs(S.envDay) do
		SetEnvironmentProperty(k, v * f)
	end
	SetEnvironmentProperty("nightlight", light < 0.5)
end

-- ========= zombies =========
local function spawnZombie()
	local pos
	if #S.spawnPoints > 0 then
		-- prefer a spawn point at least 12 m from every player
		for _ = 1, 8 do
			pos = S.spawnPoints[math.random(#S.spawnPoints)]
			local _, d = nearestPlayer(pos)
			if d > 12 then break end
		end
	else
		local p = playerFeet(players()[1])
		local a = math.random() * 6.2832
		pos = VecAdd(p, Vec(math.cos(a) * 15, 0, math.sin(a) * 15))
	end
	local ents = Spawn(ZOMBIE_XML, Transform(VecAdd(pos, Vec(0, 0.2, 0)), QuatEuler(0, math.random(0, 359), 0)))
	local body
	for _, e in ipairs(ents) do
		if GetEntityType(e) == "body" then body = e end
	end
	if not body then
		DebugPrint("village.lua: Spawn returned no body")
		return
	end
	local shape = GetBodyShapes(body)[1]
	S.zombies[#S.zombies + 1] = {
		body = body, shape = shape,
		vox0 = GetShapeVoxelCount(shape),
		planner = HAS_PLANNERS and CreatePathPlanner() or nil, querying = false,
		path = nil, pathIndex = 1, pathTime = -1e9,
		stuck = 0, biteTimer = 0, biteHigh = false, failedBites = 0,
		hitTimer = 0, dying = nil, bites = 0,
	}
end

local function killZombie(i)
	local z = S.zombies[i]
	if IsHandleValid(z.body) then Delete(z.body) end
	if z.planner then DeletePathPlanner(z.planner) end
	table.remove(S.zombies, i)
	if S.pathOwner == z then S.pathOwner = nil end
end

-- Copy the finished path out of planner `id` (0 = the shared one).
local function readPath(z, id)
	local len = GetPathLength(id)
	z.path = {}
	local d = PATH_STEP
	while d < len do
		z.path[#z.path + 1] = GetPathPoint(d, id)
		d = d + PATH_STEP
	end
	z.path[#z.path + 1] = GetPathPoint(len, id)
	z.pathIndex = 1
end

-- Same filter the game's own robots use: only large physical shapes count
-- as obstacles, and never the zombie itself.
local function queryFilter(z)
	QueryRequire("physical large")
	QueryRejectBody(z.body)
end

local function updatePaths()
	local now = GetTime()
	if HAS_PLANNERS then
		for _, z in ipairs(S.zombies) do
			if IsHandleValid(z.body) and not z.dying then
				if z.querying then
					local st = GetPathState(z.planner)
					if st == "done" or st == "fail" then
						-- on "fail" the path still leads to the closest reachable point
						readPath(z, z.planner)
						z.querying = false
					elseif st == "idle" then
						z.querying = false
					end
				elseif now - z.pathTime > REPATH_EVERY then
					local feet = GetBodyTransform(z.body).pos
					local id = nearestPlayer(feet)
					queryFilter(z)
					PathPlannerQuery(z.planner, feet, playerFeet(id), 150, 1.0)
					z.pathTime = now
					z.querying = true
				end
			end
		end
		return
	end

	-- Old API: one shared planner, zombies take turns.
	if S.pathOwner then
		local st = GetPathState()
		if st == "done" or st == "fail" then
			readPath(S.pathOwner, 0)
			S.pathOwner = nil
		elseif st == "idle" then
			S.pathOwner = nil
		end
	end
	if S.pathOwner then return end
	local best, bestAge = nil, REPATH_EVERY
	for _, z in ipairs(S.zombies) do
		if IsHandleValid(z.body) and not z.dying then
			local age = now - z.pathTime
			if age > bestAge then best, bestAge = z, age end
		end
	end
	if best then
		local feet = GetBodyTransform(best.body).pos
		local id = nearestPlayer(feet)
		queryFilter(best)
		QueryPath(feet, playerFeet(id), 150, 1.0)
		best.pathTime = now
		S.pathOwner = best
	end
end

local function goalFor(z, feet, target)
	if not z.path or #z.path == 0 then return target end
	while z.pathIndex < #z.path and dist2d(feet, z.path[z.pathIndex]) < 0.7 do
		z.pathIndex = z.pathIndex + 1
	end
	return z.path[z.pathIndex]
end

-- Distance from the hips down to the ground: the shorter of a raycast
-- straight down from the hips and one from HOVER_AHEAD in front of them.
-- nil if both miss (standing over a hole).
local function groundDistance(z, feet, dir)
	local hips = VecAdd(feet, Vec(0, HIP_HEIGHT, 0))
	local best
	for _, origin in ipairs({ hips, VecAdd(hips, VecScale(dir, HOVER_AHEAD)) }) do
		QueryRejectBody(z.body)   -- filters only last for one query
		local hit, d = QueryRaycast(origin, Vec(0, -1, 0), HIP_HEIGHT + HOVER + 2)
		if hit and (best == nil or d < best) then best = d end
	end
	return best
end

local function moveZombie(z, dt)
	local tr = GetBodyTransform(z.body)
	local feet = tr.pos
	local chest = VecAdd(feet, Vec(0, ZOMBIE_HEIGHT * 0.6, 0))
	local mass = GetBodyMass(z.body)
	if mass <= 0 then mass = 100 end
	local maxImp = mass * 0.25           -- per update: up to 0.25 m/s change

	local id = nearestPlayer(feet)
	local target = playerFeet(id)
	local goal = goalFor(z, feet, target)
	local toGoal = flat(VecSub(goal, feet))
	local dGoal = VecLength(toGoal)
	local dir = dGoal > 0.05 and VecScale(toGoal, 1 / dGoal) or Vec(0, 0, 1)
	local side = Vec(-dir[3], 0, dir[1])

	-- stop walking into the player; hit range handles the rest
	local want = (dist2d(feet, target) > 0.9) and ZOMBIE_SPEED or 0

	-- walk: push along dir, kill sideways slide, stay upright facing dir
	local com = TransformToParentPoint(tr, GetBodyCenterOfMass(z.body))
	ConstrainVelocity(z.body, 0, com, dir, want, -maxImp, maxImp)
	ConstrainVelocity(z.body, 0, com, side, 0, -maxImp, maxImp)
	local lookTarget = FRONT_FLIP and VecSub(feet, dir) or VecAdd(feet, dir)
	ConstrainOrientation(z.body, 0, tr.rot, QuatLookAt(feet, lookTarget), 10, mass * 0.6)
	-- kill roll and pitch spin, leave yaw free
	ConstrainAngularVelocity(z.body, 0, dir, 0, -mass * 0.3, mass * 0.3)
	ConstrainAngularVelocity(z.body, 0, side, 0, -mass * 0.3, mass * 0.3)

	-- hover like the game's robots: hold the hips HIP_HEIGHT + HOVER above
	-- the ground. The raycast ahead sees a step early, so the body rises
	-- onto it instead of tripping. Over a hole (no hit) gravity takes over.
	local measured = groundDistance(z, feet, dir)
	if measured then
		local desired = HIP_HEIGHT + HOVER
		local vy = clamp((desired - measured) * 8, -3, 4)
		ConstrainVelocity(z.body, 0, com, Vec(0, 1, 0), vy, -maxImp * 0.5, maxImp * 3)
	end

	-- stuck?  (wanting to move, barely moving)
	local vel = GetBodyVelocity(z.body)
	local speed = VecLength(flat(vel))
	if want > 0 and speed < 0.35 then z.stuck = z.stuck + dt else z.stuck = 0 end

	-- bite through whatever is in the way (soft materials only)
	z.biteTimer = z.biteTimer - dt
	if z.stuck > STUCK_TIME and z.biteTimer <= 0 then
		z.biteTimer = BITE_INTERVAL
		local h = z.biteHigh and 1.4 or 0.5
		z.biteHigh = not z.biteHigh
		local centre = VecAdd(VecAdd(feet, VecScale(dir, BITE_REACH)), Vec(0, h, 0))
		local n = MakeHole(centre, BITE_RADIUS, 0, 0)
		z.bites = z.bites + 1
		if n > 0 then
			z.failedBites = 0
		else
			z.failedBites = z.failedBites + 1
			if z.failedBites >= 4 then
				-- hard wall (cobblestone). Ask for a new path.
				z.failedBites = 0
				z.pathTime = -1e9
				z.path = nil
			end
		end
	end

	-- hurt the player
	z.hitTimer = z.hitTimer - dt
	local pc = VecAdd(target, Vec(0, 0.9, 0))
	if z.hitTimer <= 0 and VecLength(VecSub(pc, chest)) < HIT_RANGE then
		z.hitTimer = HIT_INTERVAL
		local hp = LEGACY and GetPlayerHealth() or GetPlayerHealth(id)
		local shove = VecAdd(VecScale(dir, 5), Vec(0, 2, 0))
		if LEGACY then
			SetPlayerHealth(math.max(0, hp - HIT_DAMAGE))
			SetPlayerVelocity(VecAdd(GetPlayerVelocity(), shove))
		else
			SetPlayerHealth(math.max(0, hp - HIT_DAMAGE), id)
			SetPlayerVelocity(VecAdd(GetPlayerVelocity(id), shove), id)
		end
	end
end

local function updateZombies(dt)
	local now = GetTime()
	for i = #S.zombies, 1, -1 do
		local z = S.zombies[i]
		if not IsHandleValid(z.body) or not IsHandleValid(z.shape) then
			killZombie(i)
		elseif z.dying then
			if now - z.dying > 2.5 then killZombie(i) end
		elseif GetShapeVoxelCount(z.shape) < z.vox0 * 0.55 then
			S.kills = S.kills + 1
			killZombie(i)
		else
			moveZombie(z, dt)
		end
	end
end

local function dawn()
	for _, z in ipairs(S.zombies) do
		if not z.dying and IsHandleValid(z.body) then
			z.dying = GetTime()
			if BURN_AT_DAWN then
				SpawnFire(VecAdd(GetBodyTransform(z.body).pos, Vec(0, 1.0, 0)))
			end
		end
	end
end

-- ========= server calls from client code =========
-- Client code (input, aiming) asks the server to do server-only work
-- (MakeHole, Spawn, door state). On 2.x this goes through ServerCall with the
-- function's full name, as in the docs' example ServerCall("server.setPlayerReady", ...).
-- On 1.x there is only one side, so the function is simply called.
local function callServer(name, ...)
	if LEGACY then
		return server[name](...)
	end
	ServerCall("server." .. name, ...)
end

-- ========= doors =========
-- Each door is its own dynamic body whose origin is the hinge line (see
-- tools/build_level.py). Closed = the transform it was built with; open =
-- that turned 90 degrees in the door's swing direction. The physics holds
-- the hinge in place and the leaf at the target angle; a zombie that bites
-- the door to pieces simply removes it from this list. Zombies never open
-- doors: only server.toggleDoor (the interact key) changes `open`.
local function initDoors()
	S.doors = {}
	for _, body in ipairs(FindBodies("door", true)) do
		S.doors[#S.doors + 1] = {
			body = body, closed = GetBodyTransform(body),
			swing = tonumber(GetTagValue(body, "swing")) or 1, open = false,
		}
	end
end

local function holdDoors()
	for i = #S.doors, 1, -1 do
		local d = S.doors[i]
		if not IsHandleValid(d.body) or IsBodyBroken(d.body) then
			table.remove(S.doors, i)
		else
			local tr = GetBodyTransform(d.body)
			local mass = GetBodyMass(d.body)
			if mass <= 0 then mass = 20 end
			local yaw = d.open and d.swing * 90 or 0
			-- QuatRotateQuat is not in the docs, so build the target from
			-- the closed pose's euler angles.
			local rx, ry, rz = GetQuatEuler(d.closed.rot)
			ConstrainPosition(d.body, 0, tr.pos, d.closed.pos, 6, mass * 2)
			ConstrainOrientation(d.body, 0, tr.rot, QuatEuler(rx, ry + yaw, rz), 8, mass * 2)
		end
	end
end

function server.toggleDoor(body)
	for _, d in ipairs(S.doors or {}) do
		if d.body == body then
			d.open = not d.open
			return
		end
	end
end

-- ========= tools: pickaxe and block placer =========
local TOOLS = {
	{ id = "pickaxe", name = "Pickaxe",      file = "MOD/vox/pickaxe.vox" },
	{ id = "placer",  name = "Block Placer", file = "MOD/vox/placer.vox" },
}
-- Placer materials. The voxbox `material` names and the `color` attribute are
-- not documented; these are Teardown's palette group names, colour 0..1.
local BLOCKS = {
	{ label = "COBBLESTONE", material = "concrete", rgb = { 125, 125, 125 } },
	{ label = "PLANKS",      material = "wood",     rgb = { 162, 130, 78 } },
	{ label = "GLASS",       material = "glass",    rgb = { 205, 232, 240 } },
}
local PICK_RANGE, PICK_COOLDOWN = 4, 0.35
local PLACE_RANGE, PLACE_COOLDOWN = 5, 0.25
local SWING_TIME = 0.2      -- pickaxe swing animation, seconds
local DOOR_RANGE = 3
local CYCLE_INPUT = "grab"  -- logical input "Grab" (right mouse by default)

-- Server: register both tools (RegisterTool is SERVER ONLY) and enable them.
-- index.html enables a custom tool with the registry key
-- game.tool.<id>.enabled; api.html 2.1 says tools start disabled and must be
-- enabled per player with SetToolEnabled. Do both.
local function registerTools()
	if not RegisterTool then
		DebugPrint("village.lua: RegisterTool missing, no pickaxe or placer")
		return
	end
	for _, t in ipairs(TOOLS) do
		RegisterTool(t.id, t.name, t.file)
		SetBool("game.tool." .. t.id .. ".enabled", true)
	end
	S.toolsEnabledFor = {}
end

local function enableToolsForPlayers()
	if LEGACY or not SetToolEnabled or not S.toolsEnabledFor then return end
	for _, id in ipairs(players()) do
		if not S.toolsEnabledFor[id] then
			S.toolsEnabledFor[id] = true
			for _, t in ipairs(TOOLS) do SetToolEnabled(t.id, true, id) end
		end
	end
end

local function snapCentre(v)
	return Vec(math.floor(v[1]) + 0.5, math.floor(v[2]) + 0.5, math.floor(v[3]) + 0.5)
end

-- Pickaxe on a block: remove the whole one-metre block the hit is in.
-- Medium radius too, so cobblestone (concrete) breaks as in Minecraft.
function server.mineBlock(centre)
	MakeHole(centre, 0.5, 0.5, 0)
end

-- Pickaxe on a zombie: a small soft-only bite out of it.
function server.hitZombie(pos)
	MakeHole(pos, 0.35, 0, 0)
end

-- Is the one-metre cell with min corner c inside any player?
-- (feet .. feet + 1.8 tall, 0.4 m around the feet horizontally)
local function cellHitsPlayer(c)
	for _, id in ipairs(players()) do
		local p = playerFeet(id)
		if c[2] < p[2] + 1.8 and c[2] + 1 > p[2] then
			local dx = math.max(c[1] - p[1], 0, p[1] - (c[1] + 1))
			local dz = math.max(c[3] - p[3], 0, p[3] - (c[3] + 1))
			if dx * dx + dz * dz < 0.4 * 0.4 then return true end
		end
	end
	return false
end

function server.placeBlock(corner, kind)
	local b = BLOCKS[kind] or BLOCKS[1]
	if cellHitsPlayer(corner) then return end
	-- The position goes ONLY in the transform; the XML string has none.
	local xml = string.format("<voxbox size='10 10 10' material='%s' color='%.3f %.3f %.3f'/>",
		b.material, b.rgb[1] / 255, b.rgb[2] / 255, b.rgb[3] / 255)
	Spawn(xml, Transform(Vec(corner[1], corner[2], corner[3])), true)
end

-- ========= server callbacks =========
function server.init()
	initDoors()
	registerTools()
	for _, loc in ipairs(FindLocations("zombiespawn", true)) do
		S.spawnPoints[#S.spawnPoints + 1] = GetLocationTransform(loc).pos
	end
	if #S.spawnPoints == 0 then
		DebugPrint("village.lua: no zombiespawn locations; zombies will spawn 15 m from the player")
	end
	captureEnv()
	S.t = clamp(START_TIME, 0, 0.999)
	S.night = S.t >= 0.5
	applyEnv(daylight(S.t))
	DebugPrint("village.lua loaded: day length " .. DAY_LENGTH .. " s, max zombies " .. MAX_ZOMBIES)
end

function server.tick(dt)
	enableToolsForPlayers()

	-- clock
	S.t = S.t + dt / DAY_LENGTH
	if S.t >= 1 then
		S.t = S.t - 1
		S.day = S.day + 1
	end
	local night = S.t >= 0.5
	if night ~= S.night then
		S.night = night
		if not night then dawn() end
	end

	-- lighting, 10 times a second is plenty
	S.envTimer = S.envTimer - dt
	if S.envTimer <= 0 then
		S.envTimer = 0.1
		applyEnv(daylight(S.t))
	end

	-- spawning
	if night then
		S.spawnTimer = S.spawnTimer - dt
		if S.spawnTimer <= 0 and #S.zombies < MAX_ZOMBIES then
			S.spawnTimer = SPAWN_INTERVAL
			spawnZombie()
		end
	else
		S.spawnTimer = 0
	end

	updatePaths()

	-- HUD text for the client part
	local secsLeft
	if night then secsLeft = (1 - S.t) * DAY_LENGTH else secsLeft = (0.5 - S.t) * DAY_LENGTH end
	shared.title = string.format("Day %d   %s", S.day, night and "NIGHT" or "DAY")
	shared.sub = string.format("%s in %d s     zombies %d     killed %d",
		night and "Sunrise" or "Sunset", math.floor(secsLeft), #S.zombies, S.kills)
	shared.hint = night and "Zombies eat WOOD, DIRT and GLASS. Cobblestone holds." or ""
end

function server.update(dt)
	holdDoors()
	updateZombies(dt)
end

-- ========= client: aiming, doors, tools, HUD =========
local C = { cooldown = 0, swing = 0, block = 1, doorHint = false, toolLine = "" }

-- Raycast from the player camera along its forward (-z) axis.
-- Returns hit, point, normal, shape.
local function aim(maxDist)
	local cam = GetPlayerCameraTransform()
	local dir = TransformToParentVec(cam, Vec(0, 0, -1))
	if QueryRejectPlayer then QueryRejectPlayer() end
	local toolBody = GetToolBody and GetToolBody() or 0
	if toolBody ~= 0 then QueryRejectBody(toolBody) end
	local hit, d, normal, shape = QueryRaycast(cam.pos, dir, maxDist)
	if not hit then return false end
	return true, VecAdd(cam.pos, VecScale(dir, d)), normal, shape
end

local function bodyTagged(shape, tag)
	if not shape or shape == 0 then return nil end
	local body = GetShapeBody(shape)
	if body and body ~= 0 and HasTag(body, tag) then return body end
	return nil
end

-- Id of the tool the local player holds. GetPlayerTool is the 2.x call;
-- on 1.x fall back to the registry key the old game used (not in the docs).
local function heldTool()
	if GetPlayerTool then return GetPlayerTool() or "" end
	return GetString("game.player.tool")
end

local function clientDoors()
	local hit, _, _, shape = aim(DOOR_RANGE)
	local door = hit and bodyTagged(shape, "door") or nil
	C.doorHint = door ~= nil
	if door and InputPressed("interact") then
		callServer("toggleDoor", door)
	end
end

local function usePickaxe()
	local hit, pos, normal, shape = aim(PICK_RANGE)
	if not hit then return end
	if bodyTagged(shape, "zombie") then
		callServer("hitZombie", pos)
	else
		-- step 5 cm INTO the surface so the hit lands inside the block
		callServer("mineBlock", snapCentre(VecSub(pos, VecScale(normal, 0.05))))
	end
end

local function usePlacer()
	local hit, pos, normal = aim(PLACE_RANGE)
	if not hit then return end
	-- step 5 cm OUT of the surface: the empty cell in front of the face
	local p = VecAdd(pos, VecScale(normal, 0.05))
	callServer("placeBlock", Vec(math.floor(p[1]), math.floor(p[2]), math.floor(p[3])), C.block)
end

local function clientTools(dt)
	C.cooldown = math.max(0, C.cooldown - dt)
	C.swing = math.max(0, C.swing - dt)
	local tool = heldTool()
	local canUse = (GetPlayerCanUseTool == nil) or GetPlayerCanUseTool()

	if tool == "pickaxe" then
		C.toolLine = "Pickaxe"
		if canUse and InputPressed("usetool") and C.cooldown <= 0 then
			C.cooldown = PICK_COOLDOWN
			C.swing = SWING_TIME
			usePickaxe()
		end
		-- swing: tip the head forward, decaying to rest over SWING_TIME.
		-- SetToolTransform must be set every frame from tick.
		if SetToolTransform then
			SetToolTransform(Transform(Vec(0, 0, 0), QuatEuler(-50 * C.swing / SWING_TIME, 0, 0)))
		end
	elseif tool == "placer" then
		if canUse and InputPressed(CYCLE_INPUT) then
			C.block = C.block % #BLOCKS + 1
		end
		if canUse and InputPressed("usetool") and C.cooldown <= 0 then
			C.cooldown = PLACE_COOLDOWN
			usePlacer()
		end
		C.toolLine = "Placer: " .. BLOCKS[C.block].label
	elseif tool ~= "" then
		C.toolLine = "Tool: " .. tool
	else
		C.toolLine = ""
	end
end

function client.init() end

function client.tick(dt)
	clientDoors()
	clientTools(dt)
end

function client.draw()
	UiPush()
	UiAlign("center top")
	UiTranslate(UiCenter(), 24)
	UiFont("bold.ttf", 34)
	UiColor(1, 1, 1)
	UiTextOutline(0, 0, 0, 1, 0.1)
	UiText(shared.title or "")
	UiTranslate(0, 40)
	UiFont("regular.ttf", 22)
	UiText(shared.sub or "")
	UiTranslate(0, 28)
	UiColor(1, 0.85, 0.4)
	UiText(shared.hint or "")
	UiTranslate(0, 28)
	UiColor(0.8, 0.9, 1)
	UiText(C.toolLine)
	UiPop()

	if C.doorHint then
		UiPush()
		UiAlign("center middle")
		UiTranslate(UiCenter(), UiMiddle() + 60)
		UiFont("regular.ttf", 22)
		UiColor(1, 1, 1)
		UiTextOutline(0, 0, 0, 1, 0.1)
		-- the input docs name the key only as the logical input "interact"
		UiText("Interact: open/close door")
		UiPop()
	end
end

-- ========= compatibility shim (part 2) =========
-- On Teardown 1.x there are no server/client tables; the engine calls these.
if LEGACY then
	function init() server.init(); client.init() end
	function tick(dt) server.tick(dt); client.tick(dt) end
	function update(dt) server.update(dt) end
	function draw(dt) client.draw(dt) end
end
