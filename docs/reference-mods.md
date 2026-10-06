# Teardown reference mods and code

Researched 2026-10-06 for the Minecraft-village zombie mod (zombies spawn at night, walk toward the player, break through soft materials).

This file has three parts: **(A)** open-source code that was actually fetched and read, with short verbatim excerpts; **(B)** Steam Workshop mods to subscribe to so the files can be sent to us; **(C)** a techniques summary and the pitfalls the repos and the official docs mention.

## Read this first

- **No open-source mod was found that makes zombies break walls.** The nearest pieces are separate: zombie body AI with no wall-breaking (A1), a chaser that calls `MakeHole` every tick (A4), and the robot script, which tags its own shapes `breakall` for 0.1 s whenever it is stuck (active logic in A3's `trooper.lua`; what the engine does with that tag is not documented in anything I could read, so it is a lead to test).
- **Best pathfinding references:** the robot-script copies (A2, A3) for a full walk-the-path loop, and `Police-Chase-System/nav.lua` (A5) for one path planner per agent, which is what a crowd of zombies needs.
- **Only one open-source day/night cycle exists** among the repos found (A7). It has no license and some quirks, so copy the idea, not the code.
- **Best Minecraft-theme code:** `NLferdiNL/Teardown-Minecraft-Tool` (A6, MIT) and `Zarbuz/FileToVox` (A14, MIT, reads `.schematic`).
- **Licenses matter.** Most of the repos below have no license file, which means all rights reserved by default: read them, do not paste them into our mod. The only repos found with permissive licenses are marked MIT / Unlicense / Apache-2.0 in the tables.
- **API generation matters.** Nearly all the repo code is from the Teardown 1.x era. In the 2.x API (docs 2.1.0, checked 2026-10-06) `MakeHole`, `Explosion`, `Shoot`, `Paint`, `SetEnvironmentProperty`, `SetEnvironmentDefault`, `SetPlayerHealth` and `ApplyPlayerDamage` are server-only, and scripts are split into `server.*` and `client.*` callbacks. See C.9.

## How this was gathered, and its limits

- `github.com` HTML pages return 403 to curl here. GitHub search, topic pages, repo pages and directory listings were read with the WebFetch tool; every source file excerpted below was downloaded with curl from `raw.githubusercontent.com`. `api.github.com` was not used. WebFetch was rate-limited (HTTP 429) repeatedly, so some queries were retried slowly.
- GitHub **code search needs a login**, so searching by function name (`QueryPath`, `SetBodyVelocity`, `SetShapeLocalTransform`) was not possible. Discovery was by repo name, description and topic, and by paging the repository search `teardown language:Lua` (173 results; pages 1 to 12 were read, about 120 repos). Repos with generic names and no description could have been missed.
- GitLab was searched through its public projects API. Codeberg's API returned 403 and its web search returned scraper-protection garbage, so **Codeberg is inconclusive**.
- Steam Workshop pages were read with curl and throttled by Steam (HTTP 429) at times. Two pages never loaded and are not used (`2831444760` "Zombies", `3340732218` "Spawnable pathfinding blocks").
- "License" below means: a `LICENSE`-type file probed at the repo root over raw (`LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `license`, `LICENCE`, `UNLICENSE`) plus what the GitHub page showed.
- Line numbers refer to the default-branch files as fetched on 2026-10-06. Commit hashes were not recorded, so numbers can drift if a repo changes.
- API signatures come from the official reference, https://teardowngame.com/modding/api.html and https://teardowngame.com/modding/api.xml (version 2.1.0 as served on the research date).
- "Last updated" values are copied from GitHub search listings; dates with no year are in the current year (2026).

---

# A. GitHub code

## A0. Summary table

| # | Repo | License | What it gives us | Relevance |
|---|---|---|---|---|
| A1 | [cheejins/Teardown-Mod---Basic-AI-Zombies](https://github.com/cheejins/Teardown-Mod---Basic-AI-Zombies) | none | Complete zombie body AI: velocity-driven walking, raycast obstacle handling, boids, spawn, prefab XML | Highest (zombies), but no pathfinding and no wall-breaking |
| A2 | [cheejins/Teardown__Robot-Vehicles](https://github.com/cheejins/Teardown__Robot-Vehicles) | none (contains a copy of Tuxedo Labs' robot script) | `QueryPath` walk loop, hover/walk via `ConstrainVelocity`, foot stepping, `breakall` tag | Highest (pathfinding) |
| A3 | [BovineOverlord/teardown-starwars-wavegen](https://github.com/BovineOverlord/teardown-starwars-wavegen) | none, explicitly | Wave spawner with FPS and population caps; robot-script units; `<script>` prefab; active stuck-to-`breakall` logic | High (waves, spawn throttling) |
| A4 | [SnazzahMods/TeardownStalkerMod](https://github.com/SnazzahMods/TeardownStalkerMod) | MIT | Straight chase plus `MakeHole` every tick | High (wall-breaking idea) |
| A5 | [Gabryel-lima/Police-Chase-System](https://github.com/Gabryel-lima/Police-Chase-System) | MIT | Per-agent path planners (`CreatePathPlanner`, `PathPlannerQuery`), async harvest, replan timer | High (crowd pathfinding) |
| A6 | [NLferdiNL/Teardown-Minecraft-Tool](https://github.com/NLferdiNL/Teardown-Minecraft-Tool) | MIT | Minecraft blocks spawned as inline `<voxbox>` XML on a 1.6 m grid; schematic and world-gen skeleton | High (theme) |
| A7 | [cheejins/Teardown__Day-and-Night-Cycle](https://github.com/cheejins/Teardown__Day-and-Night-Cycle) | none | Day/night via `SetEnvironmentProperty` | High (the only one found) |
| A8 | [Autumnagnificent/Teardown-Totally-Documented](https://github.com/Autumnagnificent/Teardown-Totally-Documented) (Shape Animation bundle) | none | Bone-style animation with `SetShapeLocalTransform` | Medium (animation) |
| A9 | [Barely-Dysfunctional/Animation-System](https://github.com/Barely-Dysfunctional/Animation-System) | none | Keyframe animation of bodies with `SetBodyTransform` | Medium (animation) |
| A10 | [zaap38/Teardown_RTS_mod](https://github.com/zaap38/Teardown_RTS_mod) | none | Main script commanding many unit scripts through the registry; serialised path-query queue | Medium (architecture) |
| A11 | [gnalvesteffer/teardown-sprite-weapons](https://github.com/gnalvesteffer/teardown-sprite-weapons) | AGPL-3.0 | Billboard-sprite NPCs (stationary) | Low |
| A12 | [superfroggman/Teardown-Companion](https://github.com/superfroggman/Teardown-Companion) | MIT | 59-line breadcrumb-following sprite | Low |
| A13 | [Thomasims/TeardownUMF](https://github.com/Thomasims/TeardownUMF) | Unlicense | Unofficial modding framework; several mods above include a file named `umf.lua`, presumably this | Low (not studied) |
| A14 | [Zarbuz/FileToVox](https://github.com/Zarbuz/FileToVox) | MIT | Converts `.schematic` and other formats to `.vox` | High (Minecraft to vox) |
| A15 | Other Minecraft-themed tools (table below) | mixed | MinecraftToVOX, Vox-Creator, teardown_patcher, others | Low to medium |

---

## A1. cheejins/Teardown-Mod---Basic-AI-Zombies

- URL: https://github.com/cheejins/Teardown-Mod---Basic-AI-Zombies (branch `main`, 22 commits, 2 stars, updated Feb 21, 2022)
- **License: none.** No LICENSE-type file at the root; the GitHub page shows none. It includes a `scripts/umf.lua`, presumably the Unlicense TeardownUMF framework (A13; I did not compare the files). The README is an empty placeholder.
- The author's Workshop page for this mod (id 2515136805, title "Basic Ai Zombies (OUTDATED)") says it "doesn't hold up to modern Teardown mods" and will not be updated. An older copy lives in `zombieMod/` of A2.
- Files read: `main.lua`, `scripts/zombie.lua`, `zombieConstructor.lua`, `spawning.lua`, `boids.lua` (partly), `utility.lua` (partly), `prefabs/zombie.xml`, `prefabs/zombie_arms.xml`, `spawn.txt`.

**What it does**

- **Body.** One dynamic body tagged `ai_zombie` holding five voxel shapes tagged `z_head`, `z_neck`, `z_body`, `z_legs`, `z_brain`. Limbs are found by tag at construction.
- **Moves (SetBodyVelocity, SetBodyTransform).** Every tick, while grounded and while its speed is below a limit, it sets a velocity built in the body's local space: forward speed plus a constant upward "hop" component, so zombies bunny-hop. It turns by slerping the rotation toward the player and writing it back with `SetBodyTransform`. It damps angular velocity every tick (`diminishBodyAngVel(zombie.body, 0.8)`). No joints, no `ConstrainVelocity`.
- **Path (no QueryPath).** None. Obstacle handling is two thick raycasts ahead (low at 0.5 m, high at 2.5 m): low hit with high clear means jump, both hit means sidestep or back up. Zombies avoid each other with a separation force from `QueryAabbBodies`.
- **States by distance:** still beyond 50 m, seeking inside 50 m (random speed), chasing inside 25 m, attacking inside 4 m.
- **Damage to the world: none.** Zombies sidestep walls; they never break them. Damage to the player is `SetPlayerHealth(GetPlayerHealth() - 0.18)` on a timer when the attack point is within 1 m.
- **Animation: none.** Rigid body only, apart from sounds and an outline.
- **Death.** Teardown has no health on bodies, so it infers death from damage: brain or neck shape broken, or body mass below 82 percent of the starting mass, or the body shape shrunk below a size threshold.
- **Spawn.** `Spawn('MOD/prefabs/<name>.xml', Transform(hitPos))`, then find the body in the returned entity table by tag. Pause-menu spawn entries come from `spawn.txt`.

Movement primitive (`scripts/zombie.lua` L203-L214):

```lua
function zombieMoveWalk(zombie, speed, hopAmt, sideAmt, velDir)
    if velDir == nil then
        local zTr = zombie.tr
        local zVel = GetBodyVelocity(zombie.body)
        local zFwdPos = TransformToParentPoint(zTr, Vec(sideAmt or 0, -hopAmt or -1, speed or 3))
        local zPos = zTr.pos
        local velSub = VecSub(zPos, zFwdPos)
        SetBodyVelocity(zombie.body, velSub)
    else
        SetBodyVelocity(zombie.body, velDir)
    end
end
```

Chase step (`scripts/zombie.lua` L275-L304):

```lua
function zombieChaseTarget(zombie, speed)

    if zombie.isVelLow() then

        -- Keep zombie stable
        zombieKeepUpright(zombie)
        zombieLookAt(zombie, zombie.ai.targetPos, 0.3)

        if isZombieOnGround(zombie) then
            local zVel = GetBodyVelocity(zombie.body)

            zombie.movement.speed = speed

            if not config.zombieMovementEnabled then
                zombie.raycastNavigate()
                zombie.boidsNavigate()
                zombieMoveWalk(zombie, 0, zombie.movement.hop)
            else
                zombie.raycastNavigate()
                zombie.boidsNavigate()
            end

            local zVelRaycast = GetBodyVelocity(zombie.body)
            local zVelLerp = VecLerp(zVel, zVelRaycast, 0.5)
            SetBodyVelocity(zombie.body, zVelLerp)
        end

    end

end
```

Obstacle decisions (`scripts/zombieConstructor.lua` L317-L350):

```lua
        local path = {
            walk = (not hitLower) and (not hitUpper) and isZombieOnGround(zombie),
            jump = (hitLower and not hitUpper) and (not zombieBodyCollision) and isZombieOnGround(zombie),
            blocked = ((hitLower and hitUpper) or hitUpper) and not zombieBodyCollision and hitShapeVelLow and GetShapeSize(hitShapeUpper) > 5,
        }

        -- Movement
        if path.jump then
            -- zombie.ai.pathing.status = "Jumping"

            if CalcDist(rc.lower.tr.pos, hitShapeLower) < JumpSpeed then
                zombieMoveWalk(zombie, -speed/2, jump) -- Back up
            else
                zombieMoveWalk(zombie, JumpSpeed, jump) -- Jump forward
            end

        elseif path.blocked then
            -- zombie.ai.pathing.status = "Blocked"

            -- Side movement based on center of shape.
            local sMin, sMax = GetShapeBounds(hitShapeUpper)
            local shapeCenter = VecLerp(sMin, sMax, 0.5)
            local sidePos = TransformToLocalPoint(zTr, shapeCenter)
            if sidePos[1] <= 0 then sidePos[1] = -1 else sidePos[1] = 1 end

            -- Smaller movement for zombies blocking zombies to prevent fast collisions.
            local isZombyBody = HasTag(GetShapeBody(hitShapeLower),'ai_zombie') or HasTag(GetShapeBody(hitShapeUpper),'ai_zombie')

            -- Move zombie.
            if isZombyBody then
                zombieMoveWalk(zombie, speed * 0.7, hop, sidePos[1])
            else
                zombieMoveWalk(zombie, -speed/5, hop/2, sidePos[1] * 2)
            end
```

Death detection (`scripts/zombieConstructor.lua` L201-L217):

```lua
    zombie.isAlive = function()
        if zombie.isBroken() then
            if IsShapeBroken(zombie.limbs.brain) or IsShapeBroken(zombie.limbs.neck) then
                return false
            elseif GetBodyMass(zombie.body) < zombie.mass.deathVal then
                return false
            else
                -- Check shape size of zombie body (sometimes small broken pieces become the zombie's shape)
                local x, y, z = GetShapeSize(zombie.limbs.body)
                local size = x+y+z
                if size < 20 then
                    return false
                end
            end
        end
        return true
    end
```

Player damage (`scripts/zombie.lua` L249-L254):

```lua
            -- Hit player
            if zombieToPlayerDist < zombie.ai.attacking.distance then
                SetPlayerHealth(GetPlayerHealth() - zombie.ai.attacking.damage) -- Decrease player health.
                -- DebugPrint('hit'..sfnTime())
                sounds.play.hit(zombie)
            end
```

Spawning (`scripts/spawning.lua` L78-L98):

```lua
            local hit, hitPos = raycastFromTransform(GetCameraTransform())
            if hit then

                local entities = Spawn('MOD/prefabs/' .. prefabFilename .. '.xml', Transform(hitPos))
                for key, entity in pairs(entities) do

                    if GetEntityType(entity) == "body" then

                        if HasTag(entity, 'ai_zombie') then

                            activateZombie(entity)
                            SetTag(entity, 'zombie_spawned')


                        end

                    end

                end

            end
```

Prefab XML (`prefabs/zombie.xml`, whole file):

```xml
<prefab version="0.6.0">
	<group id_="1239492480" open_="true" name="instance=MOD/prefabs/zombie.xml" pos="0 0 0" rot="0.0 0.0 0.0">
        <body strength="0.5" id_="1775675264" open_="true" name="ai_zombie" tags="ai_zombie nocull" pos="0 0 0" rot="0.0 180.0 0.0" dynamic="true">
			<vox texture="8" id_="1552249344" tags="z_head" pos="-0.05 1.8 0.3" rot="0 0 0" file="MOD/prefabs/zombie.vox" object="z_head">
				<joint id_="946332032" pos="0.05 0.0 0.05"/>
			</vox>
			<vox texture="8" id_="305875168" tags="z_neck" pos="0.0 1.7 0.35" rot="0 0 0" file="MOD/prefabs/zombie.vox" object="z_neck">
				<joint id_="1038415744" pos="0.0 0.0 0.0"/>
			</vox>
			<vox texture="8" id_="1224156160" open_="true" tags="z_body" pos="-0.05 1.0 0.0" rot="0 0 0" file="MOD/prefabs/zombie.vox" object="z_body">
				<joint id_="49089460" pos="0.05 0.0 0.4"/>
			</vox>
			<vox texture="8" id_="303319104" tags="z_legs" pos="-0.05 0.0 0.4" rot="0 0 0" file="MOD/prefabs/zombie.vox" object="z_legs"/>
			<vox texture="8" id_="1778427904" tags="z_brain" pos="-0.05 1.95 0.33" rot="0 0 0" file="MOD/prefabs/zombie.vox" object="brain_large">
				<joint id_="1481990528" pos="0.05 0.0 -0.05"/>
			</vox>
		</body>
	</group>
```

Spawn-menu registration (`spawn.txt` L1-L4):

```text
prefabs/zombie.xml : Civilian/ 1 zombie
prefabs/zombie_scientist.xml : Scientist/ 1 zombie
prefabs/zombie_soldier_swat.xml : SWAT/ 1 zombie
prefabs/zombie_soldier.xml : Soldier/ 1 zombie
```

**Notes**

- Movement is gated on `zombie.isVelLow()` (speed under 6): when an explosion or hit launches a zombie, the script stops overwriting its velocity.
- `zombieKeepUpright` scales the rotation's x and z components by 0.9999, which is nearly a no-op; what appears to keep zombies upright is the per-tick `SetBodyTransform` rotation toward a yaw-only look target plus the angular damping (my reading, not tested). Read before copying.
- Another Workshop zombie mod (SnakeyWakeys Terrific Zombies, id 2510386257) says in its description that its zombies "can be a little buggy and will start floating if u look into the sky".

---

## A2. cheejins/Teardown__Robot-Vehicles (modified copies of the game's robot script)

- URL: https://github.com/cheejins/Teardown__Robot-Vehicles (branch `master`, 14 commits, updated Oct 22, 2022)
- **License: none.** The robot script inside is Tuxedo Labs' game code, which the repo author could not license anyway. Read for study only.
- Relevant files: `custom_robot/scripts/robot_default.lua` (2206 lines) and `custom_robot/scripts/robot.lua` (2303 lines). Both are **modified copies of the built-in robot script**, not the pristine file: they share the original's `--= ROBOT OVERVIEW` header and the same function layout (`robotUpdate`, `navigationUpdate`, `hoverUpdate`), but set `robot.playerPos` from the player's crosshair (`getOuterCrosshairWorldPos()`) and add mod includes (the robot is player-controlled in this mod).
- **No pristine mirror of the game's `robot.lua` was found.** Two partial mirrors of the game's `data/script` folder exist (`ForCesCustom/Teardown-data`, `MrAdhit/Teardown-Default-Script`, both no license); both include `chopper.lua` and many other scripts but **return 404 for `robot.lua`**. The robot behaviour is documented below from the modified copies; I could not diff them against the shipped file, so details may differ from vanilla.

**How the robot walks toward a target**

1. **Target.** In the `hunt` state: if within 4 m of the player, stop and clear the path; otherwise `navigationSetTarget(lastSeenPos, timeout)` then `navigationUpdate(dt)`.
2. **Path request.** `QueryPath(startPos, target, 100, targetRadius, pathType)` with max length **100 m**, `targetRadius` 1.0 (4.0 if the player is in a vehicle), type `"low"` for wheeled robots and `"standard"` otherwise. Before the call it restricts the query with `QueryRequire("physical large")` and rejects its own bodies; start and target are snapped to the ground with a 5 m downward raycast.
3. **Poll and sample.** Each tick: if `GetPathState()` is `"busy"`, count think time and `AbortPath()` after a timeout; when `"done"` or `"fail"` copy points every 0.2 m with `GetPathPoint`, prune points already behind the robot, and keep a short piece of the old path while the next query runs.
4. **Follow.** Head for the first node; drop it within `PATH_NODE_TOLERANCE = 0.8` m (flat distance); slow down when the next segment climbs; if off the path or no progress for 5 s, discard everything and re-query.
5. **Drive.** Force-limited constraints on the robot body, relative to the ground body underneath it (`hover.hitBody`): forward velocity, zero sideways velocity, angular velocity for turning and staying upright, a hover constraint to hold ride height. Forces are scaled by body mass and by ground contact.
6. **Animate.** Feet are separate bodies steered with `ConstrainPosition` and `ConstrainOrientation` toward a target pose on a smoothstep arc plus a sine lift (animation by physics). `SetShapeLocalTransform` is not used.
7. **World damage.** `Shoot(pos, dir, type, strength)` for weapons. For getting through obstacles the script tags all its own shapes `breakall` for a moment when stuck. In these Robot-Vehicles copies the line that starts that timer is commented out (`robot_default.lua` L813), so the stuck logic is dormant here; the same block is **active in A3's `trooper.lua`**, where it is excerpted and explained. The engine's definition of `breakall` is **not documented** in any page I could read (the official modding page only says built-in tags are described in the editor's tag help), so treat "it breaks whatever it touches" as inferred from the name and usage.

Hunt state (`robot_default.lua` L281-L297):

```lua
			--Hunt player
			if state.id == "hunt" then
				if not state.init then
					navigationClear()
					state.init = true
					state.headAngle = 0
					state.headAngleTimer = 0
				end
				if robot.distToPlayer < 4.0 then
					robot.dir = VecCopy(robot.dirToPlayer)
					Eyes.dir = VecCopy(robot.dirToPlayer)
					robot.speed = 0
					navigationClear()
				else
					navigationSetTarget(Eyes.lastSeenPos, 1.0 + clamp(Eyes.timeSinceLastSeen, 0.0, 4.0))
					robot.speedScale = config.huntSpeedScale
					navigationUpdate(dt)
```

Poll the planner and collect the path (`robot_default.lua` L677-L700):

```lua
		function navigationUpdate(dt)
			if GetPathState() == "busy" then
				navigation.timeSinceProgress = 0
				navigation.thinkTime = navigation.thinkTime + dt
				if navigation.thinkTime > navigation.timeout then
					AbortPath()
				end
			end

			if GetPathState() ~= "busy" then
				if GetPathState() == "done" or GetPathState() == "fail" then
					if not navigation.resultRetrieved then
						if GetPathLength() > 0.5 then
							for l=0.2, GetPathLength(), 0.2 do
								navigation.path[#navigation.path+1] = GetPathPoint(l)
							end
						end
						navigation.lastQueryTime = navigation.thinkTime
						navigation.resultRetrieved = true
						navigation.state = "move"
						navigationPrunePath()
					end
				end
				navigation.thinkTime = 0
```

Issue the query (`robot_default.lua` L727-L741):

```lua
				local target = navigation.target
				-- if robot.limitTrigger ~= 0 then
				-- 	target = GetTriggerClosestPoint(robot.limitTrigger, target)
					target = truncateToGround(target)
				-- end

				QueryRequire("physical large")
				rejectAllBodies(robot.allBodies)
				QueryPath(startPos, target, 100, targetRadius, navigation.pathType)

				navigation.timeSinceProgress = 0
				navigation.hasNewTarget = false
				navigation.resultRetrieved = false
				navigation.state = "move"
			end
```

Follow the path (`robot_default.lua` L770-L806):

```lua
					local dv = VecSub(target, robot.navigationCenter)
					local distToFirstPathPoint = VecLength(dv)
					dv[2] = 0
					local d = VecLength(dv)
					if distToFirstPathPoint < 2.5 then
						if d < PATH_NODE_TOLERANCE then
							if #navigation.path > 1 then
								--Measure verticality which should decrease speed
								local diff = VecSub(navigation.path[2], navigation.path[1])
								navigation.vertical = diff[2] / (VecLength(diff)+0.001)
								--Remove the first one
								local newPath = {}
								for i=2, #navigation.path do
									newPath[#newPath+1] = navigation.path[i]
								end
								navigation.path = newPath
								navigation.timeSinceProgress = 0
							else
								--We're done
								navigation.path = {}
								robot.speed = 0
								return
							end
						else
							--Walk towards first point on path
							robot.dir = VecCopy(VecNormalize(VecSub(target, robot.transform.pos)))

							local dirDiff = VecDot(VecScale(robot.axes[3], -1), robot.dir)
							local speedScale = math.max(0.25, dirDiff)
							speedScale = speedScale * clamp(1.0 - navigation.vertical, 0.3, 1.0)
							robot.speed = config.speed * speedScale

						end
					else
						--Went off path, scrap everything and recompute
						navigation.hasNewTarget = true
						navigation.path = {}
```

Drive the body (`robot_default.lua` L1381-L1393):

```lua
		function hoverMove()
			local desiredSpeed = robot.speed * robot.speedScale
			local fwd = VecScale(robot.axes[3], -1)
			fwd[2] = 0
			fwd = VecNormalize(fwd)
			local side = VecCross(Vec(0,1,0), fwd)
			local currSpeed = VecDot(fwd, GetBodyVelocityAtPos(robot.body, robot.bodyCenter))
			local speed = currSpeed + clamp(desiredSpeed - currSpeed/2, -0.05*robot.speedScale, 0.05*robot.speedScale)
			local f = robot.mass*0.2 * hover.contact

			ConstrainVelocity(robot.body, hover.hitBody, robot.bodyCenter, fwd, speed, -f , f)
			ConstrainVelocity(robot.body, hover.hitBody, robot.bodyCenter, robot.axes[1], 0, -f , f)
		end
```

Foot stepping (`robot_default.lua` L1247-L1264):

```lua
				--Animate foot
				if hover.contact > 0 then
					if foot.stepAge < foot.stepLifeTime then
						foot.stepAge = math.min(foot.stepAge + dt, foot.stepLifeTime)
						local q = foot.stepAge / foot.stepLifeTime
						q = q * q * (3.0 - 2.0 * q) -- smoothstep
						local p = VecLerp(foot.lastTransform.pos, foot.targetTransform.pos, q)
						p[2] = p[2] + math.sin(math.pi * q)*stepHeight
						local r = QuatSlerp(foot.lastTransform.rot, foot.targetTransform.rot, q)
						foot.worldTransform = Transform(p, r)
						foot.localTransform = TransformToLocalTransform(robot.transform, foot.worldTransform)
						if foot.stepAge == foot.stepLifeTime then
							PlaySound(stepSound, p, 0.5)
						end
					end
					ConstrainPosition(foot.body, robot.body, GetBodyTransform(foot.body).pos, foot.worldTransform.pos, 8, foot.linForce)
					ConstrainOrientation(foot.body, robot.body, GetBodyTransform(foot.body).rot, foot.worldTransform.rot, 16, foot.angForce)
				end
```

Robot prefab XML, start of a body and its hinge joint (`custom_robot/robot/mech-basic.xml` L1-L7):

```xml
<prefab version="0.9.2">
	<group id_="1118833280" open_="true" name="instance=MOD/custom_robot/robot/mech-basic.xml" pos="0.0 0.0 0.0" rot="0.0 0.0 0.0">
		<body id_="1321614080" name="body" tags="body" pos="0.05 1.0 0.1" rot="0.0 0.0 0.0" dynamic="true">
			<vox id_="542671232" tags="unbreakable" pos="0.05 -0.2 0.1" rot="0.0 -180.0 0.0" texture="12 1" density="40" file="MOD/custom_robot/robot/mech-basic.vox" object="body"/>
		</body>
		<body id_="855690240" name="head" tags="head mech_basic" pos="0.0 1.1 0.1" rot="0.0 0.0 0.0" dynamic="true">
			<joint id_="6357380" name="head_joint" tags="head" pos="0.05 0.2 0.05" rot="-90.0 90.0 0.0" type="hinge" size="0.15" limits="-180 180"/>
```

---

## A3. BovineOverlord/teardown-starwars-wavegen

- URL: https://github.com/BovineOverlord/teardown-starwars-wavegen (branch `main`, 5 commits, updated Aug 24)
- **License: none, explicitly.** Its README states "no open-source license is granted over the mod as a whole" because it redistributes third-party assets (original "STAR WARS AI PACK" by tislericsm, Workshop id 2823645128, plus Tuxedo Labs' base robot AI and Star Wars IP). Study only.
- What it shows: a **wave generator** (`main.lua`, 466 lines) spawning prefab units on opposing sides and marching them to the centre, with FPS gating (`PERF_MAX_FRAME_DT = 0.0333`), a weighted alive cap (`MAX_ALIVE = 400`) and a hard body cap (`MAX_BODIES = 2000`). A "hunt the player" toggle makes every unit target the player. Units are `script/trooper.lua` and similar, each about 2300 lines, modified copies of the robot script (same `QueryPath`, `ConstrainVelocity`, `Shoot` and `GetPathState` calls as A2).
- Its tuning comment records a real pathfinding limit: "keep < 50 so the ~100m pathfinder can route them together".

Tuning constants (`main.lua` L17-L18):

```lua
SPAWN_DIST      = 40.0      -- how far each faction spawns from the battle centre
                            -- (keep < 50 so the ~100m pathfinder can route them together)
```

Throttle and spawn (`main.lua` L156-L188):

```lua
-- Hold the next wave until the battlefield thins out and the frame rate recovers.
function canSpawnNextWave()
	if wave.bodyCount >= MAX_BODIES then return false end           -- entity load (FPS)
	if (wave.eCount + wave.rCount) >= MAX_ALIVE then return false end -- weighted strength
	if wave.avgFrameDt > PERF_MAX_FRAME_DT then return false end     -- measured frame time
	return true
end

-- Spawn a prefab, snap it to the ground (or air height) and make ground units
-- advance aggressively across the map toward the nearest enemy.
function spawnUnit(prefab, x, z, air)
	local pos
	if air then
		-- Aircraft fly, so water underneath is fine; prefer dry land but don't require it.
		local g = findDryGround(x, z) or groundHit(x, z) or Vec(x, 6, z)
		pos = VecAdd(g, Vec(0, AIR_HEIGHT, 0))
	else
		-- Ground units must not spawn in water, or they die instantly.
		local g = findDryGround(x, z)
		if not g then return end   -- no dry land nearby; skip this unit
		pos = g
	end
	local t = Transform(pos, faceCenter(pos))
	local entities = Spawn(prefab, t)
	if entities then
		for i = 1, #entities do
			-- 'sw_aggro' makes the ground AI aggressive (read in factionInit) so
			-- units march toward the enemy even before they have line of sight.
			SetTag(entities[i], "sw_aggro")
		end
	end
	return entities
end
```

**How a stuck unit breaks through (active here, dormant in A2).** This is the closest thing found to "zombies break walls": each robot estimates whether it is making progress, and when it is not it briefly tags all its own shapes `breakall`; after about 2 s of being blocked it also reverses for 1 s.

1. Blocked estimate: when the robot is commanded to move (`robot.speed > 0`) but its forward speed is under about 0.5 m/s, `blocked` rises toward 1, low-pass filtered (95 percent old, 5 percent new). A detected drop ahead (`sensor.detectFall`) also forces `blocked = 1`.
2. If `robot.blocked > 0.2` for more than 0.2 s, set `robot.breakAllTimer = 0.1`.
3. Each tick the timer counts down; while it is above zero every shape of the robot carries the tag `breakall`; when it reaches zero the tag is removed.
4. If blocked persists for more than 2 s, `navigation.unblock = 1.0` makes the robot reverse (`robot.speed = -2`) for about a second.

Blocked estimate (`script/trooper.lua` L317-L323):

```lua
	local vel = GetBodyVelocity(robot.body)
	local fwdSpeed = VecDot(vel, robot.dir)
	local blocked = 0
	if robot.speed > 0 and fwdSpeed > -0.1 then
		blocked = 1.0 - clamp(fwdSpeed/0.5, 0.0, 1.0)
	end
	robot.blocked = robot.blocked * 0.95 + blocked * 0.05
```

Stuck check (`script/trooper.lua` L1510-L1525):

```lua
			--Check if stuck
			if robot.blocked > 0.2 then
				navigation.blocked = navigation.blocked + dt
				if navigation.blocked > 0.2 then
					robot.breakAllTimer = 0.1
					navigation.blocked = 0.0
				end
				navigation.unblockTimer = navigation.unblockTimer + dt
				if navigation.unblockTimer > 2.0 and navigation.unblock <= 0.0 then
					navigation.unblock = 1.0
					navigation.unblockTimer = 0
				end
			else
				navigation.blocked = 0
				navigation.unblockTimer = 0
			end
```

The `breakall` toggle (`script/trooper.lua` L341-L353):

```lua
	robot.breakAllTimer = math.max(0.0, robot.breakAllTimer - dt)
	if not robot.breakAll and robot.breakAllTimer > 0.0 then
		for i=1, #robot.allShapes do
			SetTag(robot.allShapes[i], "breakall")
		end
		robot.breakAll = true
	end
	if robot.breakAll and robot.breakAllTimer <= 0.0 then
		for i=1, #robot.allShapes do
			RemoveTag(robot.allShapes[i], "breakall")
		end
		robot.breakAll = false
	end
```

Prefab with a robot script as the parent of the bodies (`trooper.xml` L1-L4):

```xml
<prefab version="1.1.0">
	<group name="instance=MOD/trooper.xml" pos="10.7 1.2 1.29999" rot="0.0 0.0 0.0">
		<script pos="0.1 0.0 0.2" file="MOD/script/trooper.lua" param0="type=investigate chase">
			<body name="body" tags="body" pos="-0.05 1.2 0.0" rot="0.0 0.0 0.0" dynamic="true">
```

---

## A4. SnazzahMods/TeardownStalkerMod

- URL: https://github.com/SnazzahMods/TeardownStalkerMod (branch `master`, 12 commits, updated Jul 4, 2021)
- **License: MIT** (Copyright 2021 Snazzah). Sprites and sounds carry their own credits in the README.
- What it shows: the simplest possible chase. The entity is not a physics body; it is a Lua vector `figurePos` moved straight at the player each tick, drawn as a camera-facing sprite. With the "Destructive" modifier it calls `MakeHole(figurePos, 1.2, 1.2, 1.2, silent)` every tick, so it walks through anything, and it also calls `Explosion(figurePos, 1)` when it first appears. It kills with `SetPlayerHealth(0)` inside 1.5 m, and its walk speed is multiplied by 1 to 5 depending on distance (faster when far). **No pathfinding, no collision, no avoidance.**
- `MakeHole` per the 2.1.0 API: `MakeHole(position, r0, [r1], [r2], [silent])` with `r0` the radius for soft materials, `r1` for medium (not larger than `r0`), `r2` for hard (not larger than `r1`); `r1` and `r2` default to zero; it returns the number of voxels removed (zero if nothing changed). Here all three radii are equal, so it cuts every hardness. Passing `r1 = r2 = 0` would cut soft materials only.

Chase and carve (`main.lua` L134-L154):

```lua
	-- Figure Behavior
	if figureSpawned then
		if not figurePaused then
			--  Movement
			local dirVector = VecDirection(figurePos, playerPos)
			local newPos = VecCopy(figurePos)
			local movedDistance = VecScale(dirVector, walkSpeed * GetTimeStep())
			newPos = VecAdd(newPos, movedDistance)
			figurePos = newPos

			if figureDestructive then
				MakeHole(figurePos, 1.2, 1.2, 1.2, figureSilent)
			end

			if distance < 1.5 and not killed then
				killed = true
				SetPlayerHealth(0)
				SetString("level.state", "fail_stalker")
				PlaySound(deathSound)
			end
		end
```

Speed grows with distance (`main.lua` L86-L88):

```lua
	-- Speed up figure from long distances
	local distanceMult = (math.min(math.max(distance, 20), 100) / 20)
	walkSpeed = baseWalkSpeed * distanceMult
```

---

## A5. Gabryel-lima/Police-Chase-System

- URL: https://github.com/Gabryel-lima/Police-Chase-System (branch `main`, 4 commits)
- **License: MIT** (Copyright 2026 Gabryel Lima).
- The agents are police **cars**, not walkers, but `scripts/sim/nav.lua` is the cleanest example of the 2.x planner API and its comments (Portuguese) state the API facts that shape the design. Translated:
  - A query is **asynchronous**: fire it and poll `GetPathState` until it leaves `"busy"`; you cannot request and use a route in the same frame.
  - Each planner stores **only the last result**; a new query on the same planner discards the old one. So each unit gets its own planner and the polyline is copied out as soon as it is ready.
  - The navmesh is for a **character on foot**: it goes through doors, stairs and gaps a car cannot use. The route is a hint of direction, never a trajectory to follow literally; local sensors have final authority.
  - Even on `"fail"` the partial route is useful: it points to the nearest reachable point, which beats a straight line.
  - When there is no usable route, fall back to direct chase, never stop.
- Planners are pooled and reused (the code's comment says the docs recommend reuse over create/destroy). Re-query runs on a timer per agent, so a route to a moving target stays roughly right without a per-frame replan.

Planner pool (`scripts/sim/nav.lua` L29-L47):

```lua
-- Planners sao recursos de tempo de vida do script (a doc recomenda reusar em
-- vez de criar/destruir). Mantemos uma pool com lista de livres.
local pool = { free = {} }

function Nav.acquirePlanner()
	local n = #pool.free
	if n > 0 then
		local id = pool.free[n]
		pool.free[n] = nil
		return id
	end
	return CreatePathPlanner()
end

function Nav.releasePlanner(id)
	if id == nil then return end
	AbortPath(id)
	pool.free[#pool.free + 1] = id
end
```

Request (`scripts/sim/nav.lua` L75-L84):

```lua
-- Dispara uma consulta. Silenciosamente ignorada se ja houver uma em voo:
-- sobrescrever descartaria a rota anterior sem ganho nenhum.
function Nav.request(agent, from, to)
	if agent.pending then return false end
	local cfg = PCS.cfg.nav
	PathPlannerQuery(agent.planner, from, to, cfg.maxPathLength, cfg.targetRadius, "standart")
	agent.pending = true
	agent.goal = to
	return true
end
```

Harvest the result (`scripts/sim/nav.lua` L86-L120):

```lua
-- Le o resultado quando pronto. Chamar todo frame; e barato.
local function harvest(agent)
	if not agent.pending then return end

	local state = GetPathState(agent.planner)
	if state == "busy" then return end
	agent.pending = false

	if state ~= "done" and state ~= "fail" then
		-- "idle": nada a colher.
		return
	end

	-- Mesmo em "fail" a rota parcial e util: ela aponta para o ponto mais proximo
	-- que o planejador conseguiu alcancar, o que ainda e melhor que linha reta.
	local cfg = PCS.cfg.nav
	local length = GetPathLength(agent.planner)
	local pts, n = agent.points, 0
	local d = 0

	while d <= length and n < cfg.maxSamples do
		n = n + 1
		pts[n] = GetPathPoint(d, agent.planner)
		d = d + cfg.sampleStep
	end
	if length > 0 and n < cfg.maxSamples then
		n = n + 1
		pts[n] = GetPathPoint(length, agent.planner)
	end

	agent.count = n
	agent.cursor = 1
	agent.age = 0
	agent.ok = (state == "done") and n > 1
end
```

Official signatures (from api.xml): `CreatePathPlanner() -> id`; `PathPlannerQuery(id, start, end, [maxDist], [targetRadius], [type])`; `GetPathState([id])`, `GetPathLength([id])`, `GetPathPoint(dist, [id])`, `AbortPath([id])`, `DeletePathPlanner(id)`. Path type is one of `'low'`, `'standart'` (sic, the docs spell it so), `'water'`, `'flying'`; default `'standart'`; default `targetRadius` 2.0 m; default `maxDist` infinite. The legacy `QueryPath(start, end, [maxDist], [targetRadius], [type])` uses planner id 0.

---

## A6. NLferdiNL/Teardown-Minecraft-Tool

- URL: https://github.com/NLferdiNL/Teardown-Minecraft-Tool (branch `main`, 93 commits, updated Mar 10)
- **License: MIT** (Copyright 2021 Ferdi Alleman) for the code. The README credits the block vox models to The_Wolfian (most blocks) and The Mafia/Prop Guy (1.17+ blocks); the MIT file does not state terms for those models, so ask before reusing the art.
- The Workshop item "Minecraft Building Tool" (id 2755694436, author shown as FerdiBerdiii) lists the same features; I did not verify that it is this repo's published build.
- **Placement technique.** A block is a one-line `<voxbox size=... offset=... prop=... brush=...>` XML string passed straight to `Spawn(xml, transform, allowStatic, jointExisting)`; no prefab file is needed. A block is 16 voxels, which is **1.6 m** (`blockSize = 16`, `gridModulo = blockSize / 10`). Each block's properties live in `datascripts/blockData.lua` as a table row: display name, `MOD/vox/blocks/<name>.vox`, axis rotation, extra tags (TNT has `tags='explosive=2'`), size, offset, and a block-type code (full block, slab, stairs, door, redstone, ...).
- **World and schematics (in progress).** `scripts/schematics.lua` starts with `#version 2` and uses `server.PlaceBlock(name, pos)`; it has a 5x5x5 sample schematic as nested Lua tables indexed `[x][y][z]`, copy/paste state (`IDLE`, `COPYING`, `PASTING`), and a flat-grass generator. The terrain generator is a stub (`cave = 1`, `maxY = 20`, Perlin calls commented out; `scripts/perlin.lua` exists). `server.schematics_init()` currently only calls `generate_test()`.
- Mob or enemy AI: none seen in the folders listed (`scripts/items` lists `droppeditem`, `enderpearl`, `firecharge`, `flintandsteel`; the GitHub listing said more files may exist, so this is not exhaustive).

Block placement (`main.lua` L1080-L1086):

```lua
	local blockXML = "<voxbox " .. blockSizeXML .. " " .. blockOffsetXML .. " prop='" .. tostring(dynamicBlock or selectedBlockData[8]) .. "' " .. blockBrushXML .. "' " .. selectedBlockData[4] .. ">" .. extraBlockXML .. "</voxbox>"
	
	if string.find(selectedBlockData[2], "xml") ~= nil then
		blockXML = selectedBlockData[2]
	end
	
	local blockArray = Spawn(blockXML, blockTransform, not dynamicBlock, true)
```

Grid constants (`main.lua` L97-L98):

```lua
local blockSize = 16 --10
local gridModulo = blockSize / 10
```

Version 2 script header (`scripts/schematics.lua` L1-L2):

```lua
#version 2
#include "scripts/perlin.lua"
```

Flat-grass world generation (`scripts/schematics.lua` L53-L67):

```lua
local function generate_flatgrass()
	for x = -19, 20 do
		for y = 1, 4 do
			for z = -19, 20 do
				local blockPos = Vec(x * 1.6, y * 1.6, z * 1.6)
				if y == 1 then
					server.PlaceBlock("Bedrock", blockPos)
				elseif y >= 2 and y <= 3 then
					server.PlaceBlock("Dirt", blockPos)
				elseif y >= 4 then
					server.PlaceBlock("Grass", blockPos)
				end
			end
		end
	end
```

---

## A7. cheejins/Teardown__Day-and-Night-Cycle

- URL: https://github.com/cheejins/Teardown__Day-and-Night-Cycle (branch `main`, 3 commits, updated Jun 2, 2022)
- **License: none.**
- Description from the repo: "A timed day and night cycle similar to GTA V and Minecraft which smoothly transitions between map environments and weather."
- It is the **only open-source day/night cycle found** (GitHub name searches "teardown day night", "teardown night", "teardown weather", plus the Lua repo listing).
- **Technique.** A game clock advances in `tick`; five named environment templates (`sunrise`, `sunny`, `sunset`, `night`, `rainynight`) are Lua tables of every editor environment property; each tick it interpolates numbers between the current phase's template and the next phase's template, and writes **every property** with `SetEnvironmentProperty(name, v0, v1, v2, v3)`. The sun direction is computed from the hour with a cosine and set separately as `sunDir`.
- Property names used (from the template tables): `skybox`, `skyboxbrightness`, `skyboxtint`, `skyboxrot`, `sunDir`, `sunBrightness`, `sunFogScale`, `sunSpread`, `sunLength`, `sunColorTint`, `sunGlare`, `fogParams`, `fogColor`, `fogscale`, `nightlight`, `ambient`, `constant`, `brightness`, `exposure`, `ambientexponent`, `puddleamount`, `rain`, `wetness`, `puddlesize`, `slippery`, `wind`, `ambience`, `waterhurt`, `snowonground`, `snowamount`, `snowdir`. The official 2.1.0 docs say the available properties are "exactly the same as in the editor, except for 'snowonground' which is not currently supported", so drop that one.
- **Quirks as written (do not copy blindly).**
  - Default `TimeRate = 1` advances `Seconds` by `dt * 3600`, i.e. **one in-game hour per real second (24 s per day)**.
  - The blend fraction is `(GetTime() / 6 * TimeRate) % 1`: a 6-second sawtooth of wall-clock time, **not** progress through the current phase.
  - The "Morning" phase is wired to the `night` template, so the `sunrise` template is never used.
  - `daynight/API.lua`, which the README tells you to use, is an empty file (0 bytes).
  - It reads input keys directly (`r`, `t`, `o`, `p`, `l`, `c`) and draws a clock UI; strip those before reuse.
- In the 2.x API `SetEnvironmentProperty` is server-only, so the writes must happen in server code.

Phase table (`daynight/script/date.lua` L22-L27):

```lua
    DayPhasesTable = {
        { name = 'Morning', startH = 6,  env = ENV_TEMPLATES.night},
        { name = 'Noon',    startH = 12, env = ENV_TEMPLATES.sunny},
        { name = 'Evening', startH = 18, env = ENV_TEMPLATES.sunset},
        { name = 'Night',   startH = 24, env = ENV_TEMPLATES.night},
    }
```

Clock tick (`daynight/script/date.lua` L37-L40):

```lua
        Seconds = Seconds + GetTimeStep() * 60 * 60 * TimeRate
        Minutes = SecondsToMinutes(Seconds)
        Hours = SecondsToHours(Seconds)
        Days = SecondsToDays(Seconds)
```

Blend fraction and sun direction (`daynight/script/env.lua` L16-L31):

```lua
    local fraction = (GetTime() / 6 * TimeRate) % 1

    LerpENVs(DeepCopy(env1), DeepCopy(env2), fraction)

    -- SunDir = Vec(0, -1, 0)

    -- local dir2 = -2 * math.cos(math.pi * ((Hours)/12))


    SunDir[1] = -1 * math.cos((math.pi * ((Hours)/12)) + math.pi*0.5)
    SunDir[2] = -2 * math.cos(math.pi * ((Hours)/12))


    DebugWatch('SunDir', SunDir)

    SetEnvironmentProperty('sunDir', SunDir[1], SunDir[2], SunDir[3])
```

Interpolate and apply every property (`daynight/script/env.lua` L72-L108):

```lua
function LerpENVs(env_template1, env_template2, fraction)

    -- DebugWatch('fraction', fraction)

    for key, header in pairs(env_template1) do -- header = env categories.
        for name, env in pairs(header) do -- env = specific env table

            local p2env = env_template2[key][name]

            for i = 1, 4 do

                if type(env[i]) == 'number' then

                    env[i] = lerp(env[i], p2env[i], fraction)

                    if env[i] ~= 0 and env[i] ~= 1 then
                        -- DebugWatch(name, env[i])
                    end

                end

                if fraction > 0.5 then

                    if type(env[i]) == 'boolean' then
                        env[i] = p2env[i]
                    elseif type(env[i]) == 'string' then
                        env[i] = p2env[i]
                    end

                end

            end

            SetEnvironmentProperty(name, env[1], env[2], env[3], env[4])

        end
    end
```

The night template (`daynight/script/env_templates.lua` L123-L153):

```lua
ENV_TEMPLATES.night = {

    Skybox = {
        skybox = {"cloudy.dds"},
        skyboxbrightness = {0.050000000745058},
        skyboxtint = {1, 1, 1},
        skyboxrot = {0}
    },
    Sun = {
        sunDir = {0, 0, 0},
        sunBrightness = {0},
        sunFogScale = {1},
        sunSpread = {0},
        sunLength = {32},
        sunColorTint = {1, 1, 1},
        sunGlare = {1}
    },
    Fog = {
        fogParams = {20, 120, 0.89999997615814, 2},
        fogColor = {0.019999999552965, 0.019999999552965, 0.024000000208616},
        fogscale = {1}
    },
    Lighting = {
        nightlight = {true},
        ambient = {1},
        constant = {0.003000000026077, 0.003000000026077, 0.003000000026077},
        brightness = {1},
        exposure = {1, 5},
        ambientexponent = {1.2999999523163}
    },
    Rain = {puddleamount = {0}, rain = {0}, wetness = {0}, puddlesize = {0.5}},
```

---

## A8. Autumnagnificent/Teardown-Totally-Documented, Shape Animation bundle

- URL: https://github.com/Autumnagnificent/Teardown-Totally-Documented (branch `main`, 105 commits). Path: `Community Resource Bundles/Shape Animation - Autumnagnificent/shape_anim.lua` (254 lines).
- **License: none indicated** in the repo.
- It animates shapes **inside one body** like bones of an armature, set up from an XML file, using `SetShapeLocalTransform`. It needs the Automatic Framework to be present in the environment (its header says so). The bundle README says it is the same system the Lock N Load framework uses, made modular.
- The repo is otherwise a community wiki with API definitions as JSON; it has no robot or zombie code.

Apply the rig (`shape_anim.lua` L80-L91):

```lua
function animation_class:ApplyRig()
    for bone_id, bone_data in pairs(self.bones) do
        local bone_transform = self:GetBoneLocalTransform(bone_id)

        for i, shape_data in pairs(bone_data.shape_bones) do
            if IsHandleValid(shape_data.handle) then
                local shape_transform = TransformToParentTransform(bone_transform, shape_data.transform)
                SetShapeLocalTransform(shape_data.handle, shape_transform)
            end
        end
    end
end
```

## A9. Barely-Dysfunctional/Animation-System

- URL: https://github.com/Barely-Dysfunctional/Animation-System (branch `main`, 13 commits). **License: none.**
- Per its README: keyframes are bodies tagged `frame`, ordered by their position in the editor, with an optional time tag (default 1 second); transforms are uniquely tagged bodies numbered from 1. `animation_handler.lua` (marked work in progress in its README) interpolates between keyframes and moves **whole bodies** with `SetBodyTransform`, making them non-dynamic first.

Per-frame body placement (`animation_handler.lua` L126-L134):

```lua
                SetBodyDynamic(rig[id], false)

                startTrans = TransformToParentTransform(originTrans, currentTrans)
                endTrans = TransformToParentTransform(originTrans, nextTrans)  

                newPos = VecLerp(startTrans.pos, endTrans.pos, Interpolate(prog, posEase))
                newRot = QuatSlerp(startTrans.rot, endTrans.rot, Interpolate(prog, rotEase))

                SetBodyTransform(rig[id], Transform(newPos, newRot))
```

## A10. zaap38/Teardown_RTS_mod

- URL: https://github.com/zaap38/Teardown_RTS_mod (branch `main`, 20 commits, updated Jul 27, 2022). **License: none.**
- Architecture, not zombie code: `main.lua` (1564 lines) spawns unit prefabs (`script/infantry/spawn/combine.xml`, `heavy.xml`, ...), tags every returned entity with `identifier` and `team`, and **talks to the unit scripts through the registry** (`SetBool/SetFloat/SetInt/SetString("level.rts.*...." .. identifier, ...)`), because every script runs in its own Lua context. Units are `script/infantry/humanoid.lua` (2317 lines), a modified robot script whose own `QueryPath` call is commented out; instead `main.lua` runs **one path query at a time from a queue** and writes each finished path back to the asking units through the registry. The queue calls helper wrappers (`queryPath(md, ...)`, `getPathState(md)`) defined elsewhere in the repo (a vendored `Automatic.lua`); I did not read those wrappers.
- Lesson for many agents: either one planner per agent (A5) or one shared planner with a queue (this).

Path queue (`main.lua` L1474-L1500):

```lua
		if #queryQueue > 0 then
			queryQueue[1].status = getPathState(md)
			local status = queryQueue[1].status
			local askers = queryQueue[1].askers
			if queryQueue[1].status == "idle" then
				queryPath(md, queryQueue[1].start, queryQueue[1].target)
				countQuery = countQuery + 1
				queryQueue[1].status = getPathState(md)
			elseif queryQueue[1].status == "fail" or queryQueue[1].status == "done" then
				local newQueue = {}
				if queryQueue[1].status == "done" then
					local path = getSmoothPath(md)
					for i=1, #queryQueue[1].askers do
						personnalPath = deepcopy(path)
						table.insert(personnalPath, 1, getNavigationPosFromRegistry(queryQueue[1].askers[i]))
						setPathInRegistry(queryQueue[1].askers[i], personnalPath)
					end
					for i=1, #queryQueue[1].askers do
						setUpdatedStatusInRegistry(queryQueue[1].askers[i], true)
					end
				end
				abortPath(md)
				
				for i=2, #queryQueue do
					newQueue[#newQueue + 1] = queryQueue[i]
				end
				queryQueue = newQueue
```

## A11. gnalvesteffer/teardown-sprite-weapons ("Teardown Tactical")

- URL: https://github.com/gnalvesteffer/teardown-sprite-weapons (branch `main`, 65 commits, updated Feb 21, 2021). **License: AGPL-3.0** (strong copyleft: anything derived from it would have to be released under the AGPL).
- NPCs are billboard sprites drawn with `DrawSprite`, kept in a Lua table with a state machine (`idle`, `aim`, `fire`, `dead`) and line-of-sight via `QueryRaycast`. In the files read (`npcs/init.lua`, `npc.lua`, `npc_registry.lua`, `content/ai/test/definition.lua`) the NPC does not move toward the player and has no pathfinding; it shoots with `SetPlayerHealth`. Not useful for a walking body.

## A12. superfroggman/Teardown-Companion

- URL: https://github.com/superfroggman/Teardown-Companion (branch `main`, 9 commits). **License: MIT** (Copyright 2021 superfroggman).
- A dog sprite that replays the player's last 300 positions with smoothing and snaps to the ground using a raycast. `main.lua` is 59 lines. Only useful as a minimal "follow" without pathfinding.

## A13. Thomasims/TeardownUMF

- URL: https://github.com/Thomasims/TeardownUMF (branch `master`, 268 commits, 38 stars). **License: Unlicense (public domain).**
- "Unofficial extension of the modding system", distributed as packages. Several repos above (A1, A2, A3 and others) contain a file named `umf.lua`, presumably this framework; I did not compare them. Only the repo root and README were read; its APIs were not studied.

## A14. Minecraft to vox: Zarbuz/FileToVox

- URL: https://github.com/Zarbuz/FileToVox (branch `master`). **License: MIT** (Copyright 2019 Nicolas Perrier).
- Not Teardown-specific. README: "FileToVox is a console program which allow you to convert a file into a vox file (Magicavoxel)". Input list includes `.schematic` (Minecraft schematic), `.obj`, `.fbx`, `.ply`, `.png`, `.qb`, `.binvox`, `.asc`, `.tif`, `.csv`, `.json`, `.xyz`, and a folder of PNG layers. "It support world region, so you can convert a terrain bigger than 126^3 voxels." Only the README was read; I did not verify which Minecraft versions' `.schematic` it reads, nor whether "world region" means Minecraft `.mca` files. Teardown reads MagicaVoxel `.vox` files.
- `NLferdiNL/Teardown-Minecraft-Vox-Creator` (A15) builds on `FileToVoxCore`.

## A15. Other Minecraft-themed tools and repos (read at root level only)

| Repo | License | What it is |
|---|---|---|
| [MWstudios/MinecraftToVOX](https://github.com/MWstudios/MinecraftToVOX) | none | C# (.NET 10) command-line tool that batch-converts Minecraft **atlas textures** (16x16 tile grid) into Teardown/MagicaVoxel `.vox` blocks, using a user-painted metadata texture for block faces, shape and material. 5 commits. |
| [NLferdiNL/Teardown-Minecraft-Vox-Creator](https://github.com/NLferdiNL/Teardown-Minecraft-Vox-Creator) | none | WinForms app "that uses FileToVoxCore to generate Minecraft blocks for use in Teardown". 4 commits. |
| [Tresquel/teardown_patcher](https://github.com/Tresquel/teardown_patcher) | Apache-2.0 | Rust CLI, "minecraft resource packs but for teardown": applies zip patches over the game folder with a `manifest.toml`, keeps the originals restorable. Not a gameplay mod. |
| [justinthebergejr/TeardownMinecraft](https://github.com/justinthebergejr/TeardownMinecraft) | none | Archived Aug 2023; contains only `blowtorch.vox` turned into a torch and a to-do list. |
| [TTFH/Teardown-Converter](https://github.com/TTFH/Teardown-Converter) | file header reads "GNU JUSTIFIED PUBLIC LICENSE Version 3" (not a standard license; check before use) | C++ tool converting Teardown maps (`.tdbin`) into editable `.xml` and `.vox`. Useful for inspecting vanilla maps, not for Minecraft. |

**Nothing found:** no repo that converts Minecraft worlds (`.mca`/Anvil or Bedrock) directly into Teardown maps or prefabs, and no Teardown-specific schematic importer other than the unfinished one inside A6.

---

## A16. Looked at and set aside

| Repo | Why set aside |
|---|---|
| [NLferdiNL/Teardown-Weather-Machine](https://github.com/NLferdiNL/Teardown-Weather-Machine) (MIT) | Registers a tool; no `SetEnvironmentProperty` call in `main.lua` or in `scripts/` (menu, savedata, ui, utils, textbox were grepped). |
| [andrewpratt64/TeardownCustomWeather](https://github.com/andrewpratt64/TeardownCustomWeather) | Snow is drawn with sprites (`DrawSprite`), not environment properties. Custom license: free to use and modify, credit required if reuploaded. |
| [nathangur/TeardownAI](https://github.com/nathangur/TeardownAI) | Traffic AI, README says "W.I.P. not working yet" (5/18/22). No license. |
| [cheejins/Teardown__Glowing-Sea](https://github.com/cheejins/Teardown__Glowing-Sea) | Procedural open world survival; root listing only, not read in depth. No license. |
| [2crabs/Teardown-Survival](https://github.com/2crabs/Teardown-Survival) | Wood and tree material scripts; no enemies. Listing only. |
| [ForCesCustom/Teardown-data](https://github.com/ForCesCustom/Teardown-data), [MrAdhit/Teardown-Default-Script](https://github.com/MrAdhit/Teardown-Default-Script) | Partial mirrors of the game's `data/script`; neither contains `robot.lua` (404 on raw). No license; Tuxedo Labs code. |
| alan8325/kinda-realistic-humans (GitLab) | "Ragdoll mod for Teardown"; the only Teardown project GitLab's search returned. Listing only. |
| andrewpratt64/TearDown_Npc_Test | Shown in GitHub search ("wip", Jan 2021, Lua) but the repo page returns 404 now (deleted, renamed or private), so nothing could be read. |

## A17. Searches that found nothing (stated plainly)

- GitHub repository search returned **0 results** for: `teardown enemy`, `teardown monster`, `teardown gamemode`, `teardown creeper`, `teardown destroy lua`, `nextbot teardown`, and the topic page `teardown-mods` ("hasn't been used on any public repositories"). `teardown robot lua` returned 0 results; `teardown robot` returned only unrelated "robot framework" and vacuum-cleaner repos plus A2. `teardown horde` returned only an unrelated Natural Selection 2 repo.
- The `teardown-mod` topic and the `teardown` + Lua topic page showed no zombie or enemy-AI repo other than those listed above.
- **No open-source zombie mod that breaks walls.** **No pristine mirror of the game's `robot.lua`.** **No second open-source day/night cycle.** **No Minecraft-world-to-Teardown converter.**
- Several generic web searches ("teardown mod zombie lua github", "teardown mod enemy ai github QueryPath lua", "teardown robot.lua github", day/night with `SetEnvironmentProperty`, `breakall` tag) returned nothing beyond the repos found by GitHub search, and nothing documenting `breakall`.
- The author of the Workshop AI base used by many mods (tislericsm: Star Wars AI Pack, TeaREX) has a GitHub account with **0 public repositories**; the author of "Better NextBot" (What42Pizza) has no repo matching "teardown". Their mods are closed source as far as I could find.
- **Codeberg: inconclusive** (API 403; search page served scraper-protection noise). **GitLab:** one unrelated ragdoll mod.
- Real repos seen in search listings but **not opened**, in case you want to follow up: `Thomasims/TeardownUMF-Examples`, `Autumnagnificent/Automatic-Framework`, `lpenguin/Teardown-VangersMod`, `NLferdiNL/Teardown-Chaos-Mod`, `elboydo/Teardown_Touring_Cars`, `CodeFrit/teardown-touring-cars-ai-racing-spawn-fix`.

---

# B. Steam Workshop mods to subscribe to (Teardown, app id 1167630)

Workshop files cannot be downloaded from here, so these are the ones worth subscribing to and sending us the files. Titles are exact as shown on each page; dates and sizes are as shown by Steam (no year means 2026). Descriptions were read (long ones only up to about 1400 characters); **none of them says that zombies break walls**, so wall-breaking would have to be verified by reading the files or playing them.

| # | Exact title | URL | Author | Size, last updated | Why it matters |
|---|---|---|---|---|---|
| 1 | Zombies [AUTUMNAGNIFICENT] | https://steamcommunity.com/sharedfiles/filedetails/?id=3011292197 | Autumn | 25.962 MB, Aug 3, 2024 | The reference zombie mod that most others build on. Description says the zombies' inner workings, tags and how to extend them without editing base code are in a markdown file inside the mod ("Z CREDIT AND INFO.md"). Read that file first. |
| 2 | Zombiedown - Multiplayer Survival Improved and Updated | https://steamcommunity.com/sharedfiles/filedetails/?id=3802385928 | GooMan | 6.636 MB, posted Sep 15 | Description: "Cooperative zombie survival gamemode. Improved zombie pathfinding, spawn systems, Stuck Checks, Blood FX/ Splatter, Performance, etc. Credit To nazucos, the original creator." The best match for pathfinding plus spawning plus stuck handling (the original, id 3625899189 below, describes wave-based base defence). |
| 3 | WIP Driving system! [NPC Weapons, Zombies, Potions, Teams!] Steve's Advanced NPCs | https://steamcommunity.com/sharedfiles/filedetails/?id=3619320878 | Steve | 228.359 MB, Sep 27 | Description: "more advanced pathfinding, smarter and better pathfinding than the Vanilla robots", zombie hordes, "Zombify - Run Towards Player and infect NPCs". Large; probably worth reading the Lua rather than the assets. |
| 4 | Cold_Days-  (Dynamic Weather) (MP) | https://steamcommunity.com/sharedfiles/filedetails/?id=3654339913 | o_O-r. | 57.265 MB, Jul 5 | "A dynamic weather mod with day/night cycle and especial effects (fog/rain/lightning)". Requires Teardown 2.0. The exact title has two spaces after "Cold_Days-". |
| 5 | Dynamic Time Mod | https://steamcommunity.com/sharedfiles/filedetails/?id=3734448106 | QuadView | 420.908 KB, posted May 28 | "Adds dynamic day and night system and works in multiplayer servers". Tiny, so likely easy to read. |
| 6 | A.I Mutant Minecraft Mobs | https://steamcommunity.com/sharedfiles/filedetails/?id=3002996975 | TDC | 21.687 MB, posted Jul 11, 2023 | Mutant Steve, Mutant Zombie, Mutant Villager with AI; credits "Tislericsm's Tearex mod for the A.I". A Minecraft-themed zombie with a walking AI. |
| 7 | Minecraft Village | https://steamcommunity.com/sharedfiles/filedetails/?id=2429708963 | The_Wolfian | 5.088 MB, May 31, 2023 | "A sandbox level of a small minecraft village, containing several buildings and structures for your destructive pleasure." Same author as most of the block art in A6. |
| 8 | Procedural Minecraft World [1.7.0 Edition] | https://steamcommunity.com/sharedfiles/filedetails/?id=3631447761 | Steve | 53.503 MB, Jan 1 | "procedural Minecraft map: flowers, terrain, trees, ores, stone, deepslate, water ... made by using perlin noise"; "[Resume/Stop Generation key: F9]". A working Minecraft-style world generator. |

### Also worth a look (not in the top eight)

| Exact title | URL | Note |
|---|---|---|
| Zombiedown - Multiplayer Survival | https://steamcommunity.com/sharedfiles/filedetails/?id=3625899189 | Original of #2: "Defend the base from waves of zombies, earn cash, and upgrade". Setting for zombie speed; three wave events. |
| Improved Nazucos Zombie Gamemode TEST fix | https://steamcommunity.com/sharedfiles/filedetails/?id=3798562654 | "improved pathfinding, smarter AI, blood splatters". A second fork of the same game mode. |
| SnakeyWakey's ZOMBIE APOCALYPSE | https://steamcommunity.com/sharedfiles/filedetails/?id=2755668756 | Zombie waves toggled with H; credits Cheejins (A1) and Tesseractahedron. 568 KB. |
| Basic Ai Zombies (OUTDATED) | https://steamcommunity.com/sharedfiles/filedetails/?id=2515136805 | Published build of A1 (source is already on GitHub). |
| Zombies from PvZ AI ! | https://steamcommunity.com/sharedfiles/filedetails/?id=3030477793 | Says it is based on the mod above and that mod "must be downloaded in order for the zombies to have AI". |
| Minecraft Mobs | https://steamcommunity.com/sharedfiles/filedetails/?id=3277559482 | "shows some minecraft entities and there's 2 versions: Ai or Ragdoll" (Steve); the no-gore version of "Minecraft Gore Mobs" (id 3261427252, not opened). |
| Ai Minecraft Warden | https://steamcommunity.com/sharedfiles/filedetails/?id=3214751724 | Warden with AI that "follow sounds because he is blind" (Steve). 565 KB. |
| Minecraft Village [MP] | https://steamcommunity.com/sharedfiles/filedetails/?id=3622385264 | Multiplayer port of #7 by another author; says the map is not theirs. |
| Endless village generation | https://steamcommunity.com/sharedfiles/filedetails/?id=3373098236 | "endless aleatory village generation map", assets by The_Wolfian; built from #7 and "Minecraft Superflat World". |
| Minecraft Building Tool | https://steamcommunity.com/sharedfiles/filedetails/?id=2755694436 | Probably the published build of A6. 100+ blocks, doors, redstone. |
| Block World v0.1 | https://steamcommunity.com/sharedfiles/filedetails/?id=2759938135 | "places large blocks as you walk throughout the world"; early prototype (2022). |
| ekzesh's Dynamic Weather and Time [BETA] | https://steamcommunity.com/sharedfiles/filedetails/?id=3706414759 | "Global cinematic day and night cycle plus synchronized dynamic weather". Says it was made with AI help. |
| [Dynamic Weather + Dynamic Time] | https://steamcommunity.com/sharedfiles/filedetails/?id=3736552149 | "A realistic weather and time system that works in multiplayer." F9 skips time. |
| [RSL] Weather and Time | https://steamcommunity.com/sharedfiles/filedetails/?id=3639387869 | "every 2 minutes the time of day progress automatically". |
| Dark Night | https://steamcommunity.com/sharedfiles/filedetails/?id=3595390976 | Applies a very dark night from the pause menu; 37 KB. Does not override weather. |
| AlwaysNight + RTplus | https://steamcommunity.com/sharedfiles/filedetails/?id=2421590903 | Forces night on every mod map (2021). |
| Better NextBot (v1.4.5) | https://steamcommunity.com/sharedfiles/filedetails/?id=2873518320 | Chaser AI; description says `EntityAI.lua` holds the pathfinding and movement code and `nextbot.lua` the abilities (jump, explode, kill). Includes "Max path compute time" option. |
| TeaREX | https://steamcommunity.com/sharedfiles/filedetails/?id=2851033645 | By tislericsm, who also made the Star Wars AI Pack (A3's base) and whose "Tearex mod" AI is credited by "A.I Mutant Minecraft Mobs" (#6). Closed source as far as I found. |

---

# C. Techniques summary

## C.1 The common pattern for moving a body toward the player

This is what the code above converges on:

1. **Target.** Read the player position each tick (zombie mod leads the target using the player's velocity when far; robot stops within 4 m).
2. **Mode by distance.** Idle when far; navigate with a path at mid range; chase directly when close; attack at melee range. All repos use distance bands and timers rather than per-frame work.
3. **Path (optional).** Snap start and target to the ground, request a path (A2: max 100 m, radius 1 m), poll until done, sample points every 0.2 m (A2) or a configurable step (A5), follow nodes with about 0.8 m tolerance, and re-query on a timer, when off the path, or after about 5 s without progress.
4. **Steer.** Direction = normalised (next node minus position), flattened to the horizontal plane; rotate toward it.
5. **Drive the body**, in one of three ways seen:
   - **(a) `SetBodyVelocity` each tick** on a dynamic body (A1): simplest; ignores mass; add a small upward "hop" so it clears ground friction and small steps; gate it on the body being grounded and slow so explosions and hits still work.
   - **(b) Force-limited constraints** (A2): `ConstrainVelocity(body, groundBody, point, dir, speed, -f, f)` for forward and zero sideways motion; `ConstrainAngularVelocity` for turn and upright; forces scaled by mass. Physically believable, can be pushed, more tuning.
   - **(c) No physics body** (A4, A9, A12): advance a position vector (optionally `SetBodyTransform`), draw a sprite or place bodies. Walks through everything unless you add checks.
6. **Local avoidance.** Raycasts ahead at two heights to choose jump vs sidestep (A1); separation from neighbours with `QueryAabbBodies` (A1); keep the path as a hint, not a rail (A5).
7. **Attack and damage.** `SetPlayerHealth(GetPlayerHealth() - x)` on a timer in range (A1), `Shoot` (A2), `Explosion` (A4, A10).

## C.2 Breaking through soft materials: what the repos show

- `MakeHole(pos, r0, r1, r2, silent)` at the entity's front each tick (A4). Soft-only is `MakeHole(pos, r, 0, 0)` (API: `r1`, `r2` default to zero). The return value is the number of voxels removed, so a zero return in front of a blocked zombie suggests the material is too hard for those radii (inference).
- Engine tag `breakall` on the entity's own shapes for 0.1 s whenever it has been blocked (A3: commanded speed but forward speed under about 0.5 m/s, `blocked > 0.2` for 0.2 s), with a 1 s back-up after 2 s of being blocked. The engine's meaning of `breakall` is undocumented in what I could read; the usage implies it makes the tagged shape break what it touches. Test in game, and note the robot shapes are also tagged `unbreakable` so they survive the contact.
- `Explosion(pos, size)` with size 0.5 to 4.0 per the docs (A4 on spawn, A10 mines). Too blunt for walls.
- Nothing found combines pathfinding with wall-breaking. Our zombie would have to join the two: path toward the player with the navmesh, and when the path fails or stalls (A2's 5 s no-progress rule, A1's blocked branch), carve with `MakeHole` in the direction of travel.

## C.3 Pathfinding facts

- `QueryPath` is **asynchronous** (A5, A2, official API). Poll `GetPathState` for `"busy"`, `"done"`, `"fail"`, `"idle"`.
- **One result per planner.** Legacy `QueryPath` uses planner id 0 (the API's default id; A5 notes planners are script-lifetime resources), so a crowd needs either a planner per agent (`CreatePathPlanner`, A5) or a queue (A10).
- **Length cap.** A2 passes 100 m; A3 comments that sides must start under 50 m apart so the "~100m pathfinder" can route them. The API describes `maxDist` as the "maximum path length before giving up", so a farther target should be expected to fail.
- **Navmesh is for a person on foot** (A5): paths use doors and stairs. Water and flying types exist (`'water'`, `'flying'`), `'low'` is used by wheeled robots (A2).
- **Partial results on `"fail"`** can still be followed (A5).
- **Query setup in A2:** `QueryRequire("physical large")` and reject the agent's own bodies before the call, ground-snap both ends.
- **Cost control:** one query in flight per planner, timers (A5), think-time timeout with `AbortPath` (A2), reuse part of the old path (A2).

## C.4 Spawning and prefab XML

- `Spawn(xml, transform, [allowStatic], [jointExisting])` returns a table of **every** spawned entity (bodies, shapes, joints, lights); filter by `GetEntityType` and tag (A1). `xml` may be a file name or an XML string (A6). `allowStatic` defaults to false and `jointExisting` to false (API), and A6 passes both as needed.
- Prefab files seen: single dynamic body with several `<vox>` shapes and `tags=` for lookup (A1); robot prefab with a `<script file=... param0="type=investigate chase">` as parent of bodies, hinge/ball joints with limits, shapes tagged `unbreakable` (A2, A3). Inline XML strings for blocks (A6).
- Register spawn-menu entries in `spawn.txt` as `path/to/prefab.xml : Category/Name` (A1).
- Wave spawning (A3): spawn in a line away from the player, face the target, snap to dry ground (ground units spawned in water "die instantly" per A3's comment), tag spawned entities, cap by FPS, weighted alive count and body count.
- Scripts have separate Lua contexts: coordinate through tags or registry keys keyed by a unit id (A10).

## C.5 Animation options seen

- Rigid body, no animation (A1).
- Physics-driven limbs: feet and legs as bodies on joints, steered with constraints (A2).
- Bone-style animation of shapes in one body with `SetShapeLocalTransform` (A8).
- Keyframes moving whole bodies with `SetBodyTransform` (A9).
- Sprites (A4, A11, A12): no model animation at all.

## C.6 Day/night

- Mechanism in A7: write environment properties with `SetEnvironmentProperty(name, ...)` every tick, interpolating between templates; set `sunDir` from the hour; phases = morning, noon, evening, night. Properties are the same as the editor's environment panel. `SetEnvironmentDefault()` resets them. Read current values with `GetEnvironmentProperty(name)`, which is how A7 prints a template.
- Workshop cycles exist (B #4, #5) and describe multiplayer support and Teardown 2.0, so their source is probably the best reference for the 2.x server-side approach once the files are in hand.
- Use a clock tied to `GetTimeStep()` and a **per-phase** blend fraction; A7's 6-second wall-clock sawtooth and 24-second day are artifacts.
- "Night" in A7 is: `skyboxbrightness` 0.05, `sunBrightness` 0, `fogColor` about 0.02, `nightlight` true, ambience `outdoor/night.ogg`.

## C.7 Pitfalls the repos and docs mention

| Pitfall | Source |
|---|---|
| Path queries are async; do not expect a result the same frame. | A5, A2, official API |
| A planner keeps only its last result; a new query on it discards the old route. | A5; API says planner id defaults to 0 |
| Pathfinder range is about 100 m; keep spawn groups under half that from their target. | A3, A2 (`maxDist` 100) |
| The navmesh is built for a person on foot; do not follow it blindly with a wide or tall body. | A5 |
| Reject the agent's own bodies from the path query, restrict to `"physical large"`, ground-snap start and target. | A2 |
| Re-plan on a timer, on no progress (5 s in A2), or when off the path; do not re-plan every frame. | A2, A5 |
| Detect stuck by comparing commanded speed with actual forward velocity (low-pass filtered), not by position alone. | A3 (`trooper.lua`) |
| Stop driving velocity while the body is moving fast (hit, explosion), or you cancel the physics. | A1 (`isVelLow`) |
| Bodies tip and float: damp angular velocity and reapply rotation every tick; another zombie mod reports floating zombies. | A1, Workshop id 2510386257 |
| Ground units spawned in water die; snap to dry ground; cap population by FPS, alive weight and body count. | A3 |
| Death has to be inferred (brain or neck shape broken, mass loss, shape shrunk): there is no health on bodies. | A1 |
| `Spawn` returns all entities; static shapes and bodies are not spawned unless `allowStatic` is true (API: "Allow spawning static shapes and bodies (default false)"). | A1, API |
| Scripts cannot see each other's variables; use registry keys or tags. | A10 |
| `SetEnvironmentProperty` does not support `snowonground`. | Official API |
| `MakeHole`, `Explosion`, `Shoot`, `SetEnvironmentProperty`, `SetPlayerHealth`, `ApplyPlayerDamage` are server-only in 2.x; call them from `server.*` code. | Official API (`serveronly` in api.xml) |
| Day/night code in A7: blend fraction and phase wiring bugs, unused sunrise template, empty `API.lua`. | A7 (observed by reading) |
| `MakeHole` radii must satisfy `r0 >= r1 >= r2`; `silent` suppresses break sounds. | Official API |

## C.8 Licensing summary

- **Safe to copy with attribution:** A4 (MIT), A5 (MIT), A6 (MIT, code only), A12 (MIT), A13 (Unlicense), A14 (MIT), Tresquel/teardown_patcher (Apache-2.0).
- **Copyleft:** A11 (AGPL-3.0), do not mix into a non-AGPL mod.
- **No license, all rights reserved by default:** A1, A2, A3, A7, A8, A9, A10 and the other no-license repos. Treat them as documentation of techniques and re-implement from the official API.
- **Not the repo author's to license:** the robot-script copies in A2 and A3 are Tuxedo Labs' game code; the Star Wars AI Pack assets in A3 belong to their authors and rights holders.
- The excerpts in this file are short (under 40 lines each) and given for study of the technique.

## C.9 API generation: 1.x versus 2.x

- The 2.1.0 reference states: "Starting with version 2.0, the Teardown API supports networked multiplayer using a client/server architecture. The same script runs both on the server and on each client". It has `server` and `client` tables with their own `init`, `tick`, `update`; the host is both server and a client (I assume a single-player session is a host-only session; not verified).
- Marked `serveronly` in `api.xml` (relevant subset): `MakeHole`, `Explosion`, `Shoot`, `Paint`, `PaintRGBA`, `SpawnFire`, `AddHeat`, `SetEnvironmentProperty`, `SetEnvironmentDefault`, `SetPlayerHealth`, `ApplyPlayerDamage(targetPlayerId, damage, [cause], [instigatingPlayerId])`, `SetPlayerTransform`, `SetPlayerVelocity`, `SetGravity`, `SetTimeScale`, `DriveVehicle`. Not flagged: `Spawn`, `SetBodyVelocity`, `SetBodyTransform`, `ConstrainVelocity`, `QueryPath`, `PathPlannerQuery`, raycasts. What an unflagged call does in a networked session was not checked. Player functions take a `playerId` (0 is the local player on a client and the host on the server).
- Of the repos above, A6 is written in the new style (`#version 2` header, `server.PlaceBlock`, `client.schematics_init`). A5 ships a copy of the **2.0.4** API reference and uses the planner API, but still defines global `init()` and `tick()` while calling the server-only `DriveVehicle`; that suggests global-style scripts still run with server rights in a single-player 2.0.x session (inference, multiplayer not tested). The remaining repos (2021 to 2024) use the old global `init/tick/draw` style.
- For wall-breaking, damage and the environment the safe assumption is: call them from server code (`server.tick`), and keep drawing and sound on the client.
- `#version 2` appears as the first line of A6's files; I did not find it described in the API text I searched, so confirm its exact role.

## C.10 Suggested direction (my inference, not from any repo)

- Zombie body: A1's prefab and velocity approach for the first version, or A2's constraint driving if zombies should be pushable.
- Navigation: one planner per zombie (A5) with a staggered re-query timer, falling back to direct chase when no route, plus A1's low/high raycasts for local steering.
- Wall-breaking: carve with `MakeHole(pos, r, 0, 0)` ahead of a zombie that has made no progress for a few seconds, from server code; test the `breakall` tag (A3's stuck logic) as an alternative.
- Night: server-side clock plus an A7-style template blend with a per-phase fraction; spawn waves at dusk using A3's throttles.
- Village and blocks: A6's `<voxbox>` inline XML on a 1.6 m grid, or `.vox` models converted with FileToVox (A14).
