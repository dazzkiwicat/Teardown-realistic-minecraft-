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
	ConstrainOrientation(z.body, 0, tr.rot, QuatLookAt(feet, lookTarget), 8, mass * 0.15)

	-- climb a step when the path goes up right in front of us
	if goal[2] > feet[2] + 0.3 and dGoal < 1.2 then
		ConstrainVelocity(z.body, 0, com, Vec(0, 1, 0), 4.5, 0, maxImp * 3)
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

-- ========= doors =========
-- Each door is its own dynamic body whose origin is the hinge line (see
-- tools/build_level.py). Closed = the transform it was built with. The
-- physics holds it there; a zombie that bites it to pieces simply removes
-- it from this list. Opening with the interact key comes in brief 02.
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
			local rx, ry, rz = GetQuatEuler(d.closed.rot)
			ConstrainPosition(d.body, 0, tr.pos, d.closed.pos, 6, mass * 2)
			ConstrainOrientation(d.body, 0, tr.rot, QuatEuler(rx, ry + yaw, rz), 8, mass * 2)
		end
	end
end

-- ========= server callbacks =========
function server.init()
	initDoors()
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

-- ========= client callbacks (HUD) =========
function client.init() end
function client.tick(dt) end

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
	UiPop()
end

-- ========= compatibility shim (part 2) =========
-- On Teardown 1.x there are no server/client tables; the engine calls these.
if LEGACY then
	function init() server.init(); client.init() end
	function tick(dt) server.tick(dt); client.tick(dt) end
	function update(dt) server.update(dt) end
	function draw(dt) client.draw(dt) end
end
