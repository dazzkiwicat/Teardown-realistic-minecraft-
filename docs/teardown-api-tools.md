# Teardown API: tools, input, aiming, shapes, sound, particles (verbatim extract)

Sources: `api.html` ("Teardown scripting API (2.1.0)", https://teardowngame.com/modding/api.html) and `index.html` (https://teardowngame.com/modding/), both saved in the session scratchpad.
Every function block below is machine-extracted from `api.html`: the first line of each fence is the doc's own signature, followed by its Arguments, Return value and description text exactly as written (typos included, e.g. "SetToolTranform"). The doc's own example follows each block. Bracketed names in a signature are optional arguments. The `[SERVER ONLY]` / `[CLIENT ONLY]` labels are the doc's own function tags; `[no SERVER/CLIENT tag in docs]` means the docs attach no tag to that function.
Text from `index.html` is quoted with `>`. "NOT FOUND IN DOCS" means a grep of both files found nothing.

## 0. Every function in api.html whose name contains "Tool"

Total: 23 (case-insensitive match on "tool"; no function name contains lowercase "tool" only). The api.html table of contents has NO section named "Tools": these functions are listed under the sections shown in the last column.

| # | Function | Tag | Signature | api.html TOC section |
|---|---|---|---|---|
| 1 | `SetPlayerSpawnTool` | SERVER ONLY | `SetPlayerSpawnTool(id, [playerId])` | Player |
| 2 | `GetPlayerCanUseTool` | - | `canusetool = GetPlayerCanUseTool([playerId])` | Player |
| 3 | `SetPlayerTool` | SERVER ONLY | `SetPlayerTool(toolId, [playerId])` | Player |
| 4 | `GetPlayerTool` | - | `toolId = GetPlayerTool([playerId])` | Player |
| 5 | `RegisterTool` | SERVER ONLY | `RegisterTool(id, name, file, [group])` | Player |
| 6 | `SetToolAmmoPickupAmount` | SERVER ONLY | `SetToolAmmoPickupAmount(toolId, ammo)` | Player |
| 7 | `GetToolAmmoPickupAmount` | - | `ammo = GetToolAmmoPickupAmount(toolId)` | Player |
| 8 | `GetToolBody` | - | `handle = GetToolBody([playerId])` | Player |
| 9 | `GetToolHandPoseLocalTransform` | - | `right, left = GetToolHandPoseLocalTransform([playerId])` | Player |
| 10 | `GetToolHandPoseWorldTransform` | - | `right, left = GetToolHandPoseWorldTransform([playerId])` | Player |
| 11 | `SetToolHandPoseLocalTransform` | CLIENT ONLY | `SetToolHandPoseLocalTransform(right, left, [playerId])` | Player |
| 12 | `GetToolLocationLocalTransform` | - | `location = GetToolLocationLocalTransform(name, [playerId])` | Player |
| 13 | `GetToolLocationWorldTransform` | - | `location = GetToolLocationWorldTransform(name, [playerId])` | Player |
| 14 | `SetToolTransform` | CLIENT ONLY | `SetToolTransform(transform, [sway], [playerId])` | Player |
| 15 | `SetToolAllowedZoom` | CLIENT ONLY | `SetToolAllowedZoom(zoom, [zoom sensitivity])` | Player |
| 16 | `SetToolTransformOverride` | CLIENT ONLY | `SetToolTransformOverride(transform, [playerId])` | Player |
| 17 | `SetToolOffset` | CLIENT ONLY | `SetToolOffset(offset, [playerId])` | Player |
| 18 | `SetToolAmmo` | SERVER ONLY | `SetToolAmmo(toolId, ammo, [playerId])` | Player |
| 19 | `GetToolAmmo` | - | `ammo = GetToolAmmo(toolId, [playerId])` | Player |
| 20 | `SetToolEnabled` | SERVER ONLY | `SetToolEnabled(toolId, enabled, [playerId])` | Player |
| 21 | `IsToolEnabled` | - | `enabled = IsToolEnabled(toolId, [playerId])` | Player |
| 22 | `SpawnTool` | - | `entities = SpawnTool(id, transform, [allowStatic], [voxScale])` | Spawn |
| 23 | `SetToolHaptic` | CLIENT ONLY | `SetToolHaptic(id, handle, [amplitude])` | Miscellaneous |

Requested names that do NOT exist in api.html (checked against all 609 function names):

| Requested | Result |
|---|---|
| `SetToolHandPoseWorldTransform` | NOT FOUND IN DOCS (only `GetToolHandPoseWorldTransform` exists; the setter exists only as `SetToolHandPoseLocalTransform`) |
| `SetShapeVoxel` | NOT FOUND IN DOCS |
| `GetShapeVoxel` | NOT FOUND IN DOCS (nearest: `GetShapeMaterialAtIndex`, `GetShapeVoxelCount`) |
| `ExtendShape` | NOT FOUND IN DOCS (nearest: `ExtrudeShape`) |
| `SetShapeStrength` | NOT FOUND IN DOCS |

## 1. Registering and handling custom tools

### 1.1 "Tools" section intro

NOT FOUND IN DOCS. api.html has no "Tools" section and no tools-specific intro paragraph. The tool functions sit in the "Player" section (RegisterTool ... IsToolEnabled), `SpawnTool` in "Spawn" and `SetToolHaptic` in "Miscellaneous". The whole intro text of the "Player" section is:

```text
The player functions expose certain information about the player.
```

The only prose about custom tools anywhere is in index.html, section "Custom Tools" (verbatim, including the code block):


> ## Custom Tools
>
> It is possible to add custom Tools to the player inventory. 
> This is done using the [`RegisterTool()`](api.html#RegisterTool) Lua function. 
>
> ```lua
> --Register tool and enable it
> RegisterTool("lasergun", "Laser Gun", "MOD/vox/lasergun.vox")
> SetBool("game.tool.lasergun.enabled", true)
> ```
> Take a look at the script for the "Laser Gun" built-in mod for more details how to include you own custom tools (or weapons) in Teardown. 

index.html, `info.txt` (the Laser Gun example mod's tag):


> The tags key is an optional comma separated list of tags used to categorize the mod in the Steam Workshop. 
> Valid tags are: **Map, Gameplay, Asset, Vehicle, Tool**.
> ```markdown
> name = Laser Gun
> author = Tuxedo Labs
> description = Custom tool example mod. Laser gun that cuts through most materials
> tags = Tool
> ```

index.html, `main.lua (from base game)`:

> ####	main.lua (from base game)  
> To equip the player with the same tools they have unlocked and upgraded in the main game, include the main.lua script from the main game.

### 1.2 What the docs say about client vs server for tool code

The docs never state a rule of the form "tool logic runs in callback X". What exists is the following, all verbatim.

api.html intro (multiplayer architecture):

```text
Starting with version 2.0, the Teardown API supports networked multiplayer using a client/server architecture.
The same script runs both on the server and on each client, but different parts of the script are used. This is implemented
through the server and client tables. Teardown does not use dedicated servers, so the player hosting a session will be
the server for that session while also acting as one of the clients. Hence, the host is both the server and one of the clients,
while everyone else is just a client.
```

api.html, before the server callbacks table: `Each script has the following server callback functions that will be called by the game engine. Note that all of them are optional. In many cases, you will only need the init and tick. Most of the game logic should be implemented on the server.`

api.html, before the client callbacks table: `The following optional callback functions are available on the client. The client part of a script is typically used for overlay graphics and user interfaces, but it can also be used for optimization purposes to spawn local particle effects, sounds or animations.`

What the doc's own `RegisterTool` example shows (see 1.3): `RegisterTool`, `SetToolEnabled`, `SetToolAmmo` and the `GetPlayerTool(p) == "lasergun"` + `InputPressed("usetool", p)` firing logic are in `server.init` / `server.tick`; the comment in `client.tick` says `-- Spawn client side particles, play sound, etc.`

Tool-related function tags (the doc's own tags):

| Tag | Functions |
|---|---|

| SERVER ONLY | `SetPlayerSpawnTool`, `SetPlayerTool`, `RegisterTool`, `SetToolAmmoPickupAmount`, `SetToolAmmo`, `SetToolEnabled` |
| CLIENT ONLY | `SetToolHandPoseLocalTransform`, `SetToolTransform`, `SetToolAllowedZoom`, `SetToolTransformOverride`, `SetToolOffset`, `SetToolHaptic` |
| no tag | `GetPlayerCanUseTool`, `GetPlayerTool`, `GetToolAmmoPickupAmount`, `GetToolBody`, `GetToolHandPoseLocalTransform`, `GetToolHandPoseWorldTransform`, `GetToolLocationLocalTransform`, `GetToolLocationWorldTransform`, `GetToolAmmo`, `IsToolEnabled`, `SpawnTool` |

Notes taken from the argument text of those functions:

- `SetToolTransform`, `SetToolTransformOverride`, `SetToolOffset`, `SetToolHandPoseLocalTransform`: "You need to set this every frame from the tick function." / "call the function every frame from the tick function." / "This function must be called every frame from the tick function." Their `playerId` text: "On client, zero means client player." All four are tagged CLIENT ONLY and their doc examples are in `function client.tick()`.
- `SetToolAllowedZoom` is CLIENT ONLY (example in `function client.tick()`) and has no `playerId` argument.
- `GetToolBody`, `GetToolHandPose*`, `GetToolLocation*`, `GetToolAmmo`, `IsToolEnabled`, `GetPlayerTool`, `GetPlayerCanUseTool` have no tag; their `playerId` text reads "On client, zero means client player. On server, zero means server (host) player."
- `RegisterTool`, `SetToolEnabled`, `SetToolAmmo`, `SetToolAmmoPickupAmount`, `SetPlayerSpawnTool`, `SpawnTool`: see tags in the table in section 0.

### 1.3 Registry keys that matter for tools

The registry intro text and key table (verbatim cells):

```text
The Teardown engine uses a global key/value-pair registry that scripts
can read and write. The engine exposes a lot of internal information through
the registry, but it can also be used as way for scripts to communicate with
each other.

The registry is a hierarchical node structure and can store a value in each node (parent nodes can also have a value).
The values can be of type floating point number, integer, boolean or string, but all types are automatically converted if another type is requested.
Some registry nodes are reserved and used for special purposes.

Registry node names may only contain the characters a-z, numbers 0-9, dot, dash and underscore.
```

| Key | Description |
|---|---|
| `options` | reserved for game settings (write protected from mods) |
| `game` | reserved for the game engine internals (see documentation) |
| `savegame` | used for persistent game data (write protected for mods) |
| `savegame.mod` | used for persistent mod data. Use only alphanumeric character for key name. |
| `level` | not reserved, but recommended for level specific entries and script communication |

Result of grepping both files for the keys you asked about:

| Key | Result |
|---|---|
| `game.player.tool` | NOT FOUND IN DOCS. API equivalents: `GetPlayerTool`, `SetPlayerTool` (section 1.4) |
| `game.tool.<id>.enabled` | Appears once, in index.html "Custom Tools": `SetBool("game.tool.lasergun.enabled", true)` (quoted in 1.1). API equivalent: `SetToolEnabled` / `IsToolEnabled`. Note the conflict: index.html (older doc) enables the tool through this registry key right after `RegisterTool`; api.html 2.1.0 says `RegisterTool`: "Tools are disabled by default after RegisterTool and must be enabled per player using SetToolEnabled before they can be selected or used." and its example calls `SetToolEnabled("lasergun", true, p)` |
| `game.tool.<id>.ammo` | NOT FOUND IN DOCS. API equivalents: `SetToolAmmo`, `GetToolAmmo` |
| `game.player.canusetool` | NOT FOUND IN DOCS. API equivalent: `GetPlayerCanUseTool` (no setter exists in the docs) |
| `game.player.disabletools` | NOT FOUND IN DOCS (no similar key found). Closest functions that exist: `DisablePlayerInput`, `DisablePlayer`, `IsPlayerDisabled`, `DisablePlayerDamage` (section 3, related) |
| any other `game.*` key | Only these occur, all in doc examples: `ListKeys("game.tool")` (comment shows child keys `steroid`, `rifle`, `...`), `HasKey("game.tool.rifle")`, `SetColor("game.tool.wire.color", 1.0, 0.5, 0.3)`, and `GetBool("game.thirdperson")` (inside the `SetToolHandPoseLocalTransform` and `SetToolTransformOverride` examples) |

The `ListKeys` example, verbatim:

```lua
--If the registry looks like this:
--	game
--		tool
--			steroid
--			rifle
--			...

function init()
	local list = ListKeys("game.tool")
	for i=1, #list do
		DebugPrint(list[i])
	end
end

--This will output:
--steroid
--rifle
-- ...
```

### 1.4 Tool function entries (all of them, in api.html order)

#### RegisterTool  [SERVER ONLY]

```text
RegisterTool(id, name, file, [group])

Arguments

id (string) – Tool unique identifier

name (string) – Tool name to show in hud

file (string) – Path to vox file or prefab xml

group (number, optional) – Tool group for this tool (1-6) Default is 6.

Return value

none

Register a custom tool that will show up in the player inventory and
can be selected with scroll wheel. Do this only once per tool.
Tools are disabled by default after RegisterTool and must be enabled per
player using SetToolEnabled before they can be selected or used.
```

Doc example (verbatim):

```lua
#include "script/include/player.lua"

function server.init()
	RegisterTool("lasergun", "Laser Gun", "MOD/vox/lasergun.vox", 6)
end

function server.tick()

	for p in PlayersAdded() do
		SetToolEnabled("lasergun", true, p)
		SetToolAmmo("lasergun", 60, p)
	end

	for p in Players() do
		if GetPlayerTool(p) == "lasergun" then
			--Tool is selected. Tool logic goes here.
			if InputPressed("usetool", p) then
				-- Fire the tool
			end
		end
	end
end

function client.tick()
	for p in Players() do
		if GetPlayerTool(p) == "lasergun" then
			if InputPressed("usetool", p) then
				-- Spawn client side particles, play sound, etc.
			end
		end
	end
end
```

#### SetToolTransform  [CLIENT ONLY]

```text
SetToolTransform(transform, [sway], [playerId])

Arguments

transform (TTransform) – Tool body transform

sway (number, optional) – Tool sway amount. Default is 1.0

playerId (number, optional) – Player ID. On client, zero means client player.

Return value

none

Apply an additional transform on the visible tool body. This can be used to
create tool animations. You need to set this every frame from the tick function.
The optional sway parameter control the amount of tool swaying when walking.
Set to zero to disable completely.
```

Doc example (verbatim):

```lua
function client.tick()
	--Offset the tool half a meter to the right for the local player
	local offset = Transform(Vec(0.5, 0, 0))
	SetToolTransform(offset)
end
```

#### SetToolTransformOverride  [CLIENT ONLY]

```text
SetToolTransformOverride(transform, [playerId])

Arguments

transform (TTransform) – Tool body transform

playerId (number, optional) – Player ID. On client, zero means client player.

Return value

none

This function serves as an alternative to SetToolTransform, providing full control over tool animation by disabling all internal tool animations.
When using this function, you must manually include pitch, sway, and crouch movements in the transform. To maintain this control, call the function every frame from the tick function.
```

Doc example (verbatim):

```lua
function client.tick()

	if GetBool("game.thirdperson") then
		local toolTransform = Transform(Vec(0.3, -0.3, -0.2), Quat(0.0, 0.0, 15.0))

		-- Rotate around point
		local pivotPoint = Vec(-0.01, -0.2, 0.04)
		toolTransform.pos = VecSub(toolTransform.pos, pivotPoint)
		local rotation = Transform(Vec(), QuatAxisAngle(Vec(0,0,1), GetPlayerPitch()))
		toolTransform = TransformToParentTransform(rotation, toolTransform)
		toolTransform.pos = VecAdd(toolTransform.pos, pivotPoint)

		SetToolTransformOverride(toolTransform)
	else
		local toolTransform = Transform(Vec(0.3, -0.3, -0.2), Quat(0.0, 0.0, 15.0))
		SetToolTransform(toolTransform)
	end
end
```

#### GetToolBody  [no SERVER/CLIENT tag in docs]

```text
handle = GetToolBody([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

handle (number) – Handle to currently visible tool body or zero if none

Return body handle of the visible tool. You can use this to retrieve tool shapes
and animate them, change emissiveness, etc. Do not attempt to set the tool body
transform, since it is controlled by the engine. Use SetToolTranform for that.
```

Doc example (verbatim):

```lua
function client.tick()
	local toolBody = GetToolBody()
	if toolBody~=0 then
		DebugPrint("Tool body: " .. toolBody)
	end
end
```

#### GetToolHandPoseLocalTransform  [no SERVER/CLIENT tag in docs]

```text
right, left = GetToolHandPoseLocalTransform([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

right (TTransform) – Transform of right hand relative to the tool body origin, or nil if the right hand is not used

left (TTransform) – Transform of left hand, or nil if left hand is not used
```

Doc example (verbatim):

```lua
local right, left = GetToolHandPoseLocalTransform()
```

#### SetToolHandPoseLocalTransform  [CLIENT ONLY]

```text
SetToolHandPoseLocalTransform(right, left, [playerId])

Arguments

right (TTransform) – Transform of right hand relative to the tool body origin, or nil if right hand is not used

left (TTransform) – Transform of left hand, or nil if left hand is not used

playerId (number, optional) – Player ID. On client, zero means client player.

Return value

none

Use this function to position the character's hands on the currently equipped tool. This function must be called every frame from the tick function.
In third-person view, failing to call this function can lead to different outcomes depending on how the tool is animated:

- If the tool's transform is not explicitly set or is set using SetToolTransform, not calling this function will trigger a fallback solution where the right hand is automatically positioned.

- If the tool is animated using the SetToolTransformOverride function, not calling this function will result in the character's animation taking control of the hand movement
```

Doc example (verbatim):

```lua
if GetBool("game.thirdperson") then
	if aiming then
		SetToolHandPoseLocalTransform(Transform(Vec(0.2,0.0,0.0), QuatAxisAngle(Vec(0,1,0), 90.0)), Transform(Vec(-0.1, 0.0, -0.4)))
	else
		SetToolHandPoseLocalTransform(Transform(Vec(0.2,0.0,0.0), QuatAxisAngle(Vec(0,1,0), 90.0)), nil)
	end
end
```

#### GetToolHandPoseWorldTransform  [no SERVER/CLIENT tag in docs]

```text
right, left = GetToolHandPoseWorldTransform([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

right (TTransform) – Transform of right hand in world space, or nil if the right hand is not used

left (TTransform) – Transform of left hand, or nil if left hand is not used
```

Doc example (verbatim):

```lua
local right, left = GetToolHandPoseWorldTransform()
```

#### SetToolAllowedZoom  [CLIENT ONLY]

```text
SetToolAllowedZoom(zoom, [zoom sensitivity])

Arguments

zoom (number) – Zoom factor

zoom sensitivity (number, optional) – Input sensitivity when zoomed in. Default is 1.0.

Return value

none

Set the allowed zoom for a registered tool. The zoom sensitivity will be factored
with the user options for sensitivity.
```

Doc example (verbatim):

```lua
function client.tick()
	-- allow our scoped tool to zoom by factor 4.
	SetToolAllowedZoom(4.0, 0.5)
end
```

#### SetToolOffset  [CLIENT ONLY]

```text
SetToolOffset(offset, [playerId])

Arguments

offset (TVec) – Tool body offset

playerId (number, optional) – Player ID. On client, zero means client player.

Return value

none

Apply an additional offset on the visible tool body. This can be used to
tweak tool placement for different characters. You need to set this every frame from the tick function.
```

Doc example (verbatim):

```lua
function client.tick()
	--Offset the tool depending on character height
	local defaultEyeY = 1.7
	local offsetY = characterHeight - defaultEyeY
	local offset = Vec(0, offsetY, 0)
	SetToolOffset(offset)
end
```

#### SetToolHandPoseWorldTransform

NOT FOUND IN DOCS

Other tool functions in api.html (needed to enable / equip / feed a registered tool):

#### SetToolEnabled  [SERVER ONLY]

```text
SetToolEnabled(toolId, enabled, [playerId])

Arguments

toolId (string) – Tool ID

enabled (bool) – Tool enabled

playerId (number, optional) – Player ID

Return value

none
```

Doc example (verbatim):

```lua
SetToolEnabled("gun", false, playerId)
```

#### IsToolEnabled  [no SERVER/CLIENT tag in docs]

```text
enabled = IsToolEnabled(toolId, [playerId])

Arguments

toolId (string) – Tool ID

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

enabled (bool) – Tool enabled for player
```

Doc example (verbatim):

```lua
if IsToolEnabled("gun", 1) then
	...
end
```

#### SetToolAmmo  [SERVER ONLY]

```text
SetToolAmmo(toolId, ammo, [playerId])

Arguments

toolId (string) – Tool ID

ammo (number) – Total ammo

playerId (number, optional) – Player ID. On server, zero means server (host) player.

Return value

none
```

Doc example (verbatim):

```lua
SetToolAmmo("gun", 10, 1)
```

#### GetToolAmmo  [no SERVER/CLIENT tag in docs]

```text
ammo = GetToolAmmo(toolId, [playerId])

Arguments

toolId (string) – Tool ID

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

ammo (number) – Total ammo for tool
```

Doc example (verbatim):

```lua
local ammo = GetToolAmmo("gun", 1)
```

#### SetToolAmmoPickupAmount  [SERVER ONLY]

```text
SetToolAmmoPickupAmount(toolId, ammo)

Arguments

toolId (string) – Tool ID

ammo (number) – The default ammo pickup amount

Return value

none

Sets the default amount of ammo granted when picking up an ammo crate
associated with a specific tool. This is useful if your mod provides
custom crates or ammo pickups for tools.
```

Doc example (verbatim):

```lua
function server.init()
	RegisterTool("lasergun", "Laser Gun", "MOD/vox/lasergun.vox", 6)
	SetToolAmmoPickupAmount("lasergun", 30)
end
```

#### GetToolAmmoPickupAmount  [no SERVER/CLIENT tag in docs]

```text
ammo = GetToolAmmoPickupAmount(toolId)

Arguments

toolId (string) – Tool ID

Return value

ammo (number) – The default ammo pickup amount
```

Doc example (verbatim):

```lua
local ammo = GetToolAmmoPickupAmount("gun")
```

#### GetToolLocationLocalTransform  [no SERVER/CLIENT tag in docs]

```text
location = GetToolLocationLocalTransform(name, [playerId])

Arguments

name (string) – Name of location

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

location (TTransform) – Transform of a tool location in tool space or nil if location is not found.

Return transform of a tool location in tool space. Locations can be defined using the tool prefab editor.
```

Doc example (verbatim):

```lua
local right  = GetToolLocationLocalTransform("righthand")
SetToolHandPoseLocalTransform(right, nil)
```

#### GetToolLocationWorldTransform  [no SERVER/CLIENT tag in docs]

```text
location = GetToolLocationWorldTransform(name, [playerId])

Arguments

name (string) – Name of location

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

location (TTransform) – Transform of a tool location in world space or nil if the location is not found or if there is no visible tool body.

Return transform of a tool location in world space. Locations can be defined using the tool prefab editor. A tool location is defined in tool space and to get the world space transform a tool body is required.
If a tool body does not exist this function will return nil.
```

Doc example (verbatim):

```lua
local muzzle = GetToolLocationWorldTransform("muzzle")
Shoot(muzzle, direction)
```

#### SetPlayerTool  [SERVER ONLY]

```text
SetPlayerTool(toolId, [playerId])

Arguments

toolId (string) – Set Tool ID

playerId (number, optional) – Player ID. On server, zero means server (host) player.

Return value

none
```

Doc example (verbatim):

```lua
function playerJoined(playerId)
	-- Server sets player tool to "gun"
	SetPlayerTool("gun", playerId)
end
```

#### GetPlayerTool  [no SERVER/CLIENT tag in docs]

```text
toolId = GetPlayerTool([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

toolId (string) – Get Tool ID
```

Doc example (verbatim):

```lua
local tool = GetPlayerTool()
```

#### GetPlayerCanUseTool  [no SERVER/CLIENT tag in docs]

```text
canusetool = GetPlayerCanUseTool([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

canusetool (bool) – If the player currenty can use tool.

Will be false if player is in vehicle, interacting with a screen, has pause menu open, is dead or uses interactive UI.
```

Doc example (verbatim):

```lua
function server.tick()
	for p in Players() do
		if GetPlayerCanUseTool(p) and InputPressed("usetool", p) then
			-- fire laser
		end
	end
end
```

#### SpawnTool  [no SERVER/CLIENT tag in docs]

```text
entities = SpawnTool(id, transform, [allowStatic], [voxScale])

Arguments

id (string) – Tool ID

transform (TTransform) – Spawn transform

allowStatic (boolean, optional) – Allow spawning static shapes and bodies (default false)

voxScale (number, optional) – Applies a scale to voxels (default 1.0)

Return value

entities (table) – Indexed table with handles to all spawned entities
```

Doc example (verbatim):

```lua
function server.init()
	SpawnTool("sledge", Transform(Vec(0, 5, 0)))
end
```

#### SetToolHaptic  [CLIENT ONLY]

```text
SetToolHaptic(id, handle, [amplitude])

Arguments

id (string) – Tool unique identifier

handle (string) – Handle of haptic effect

amplitude (number, optional) – Amplitude multiplier. Default (1.0)

Return value

none

Register haptic as a "Tool haptic" for custom tools.
"Tool haptic" will be played on repeat while this tool is active.
Also it can be used for Active Triggers of DualSense controller
```

Doc example (verbatim):

```lua
function client.init()
	RegisterTool("minigun", "loc@MINIGUN", "MOD/vox/minigun.vox")
	toolHaptic = LoadHaptic("MOD/haptic/tool.xml")
	SetToolHaptic("minigun", toolHaptic)
end
```

(`SetPlayerSpawnTool` is in section 9.)

## 2. Input

### InputPressed  [no SERVER/CLIENT tag in docs]

```text
pressed = InputPressed(input, [playerId])

Arguments

input (string) – The input identifier

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

pressed (boolean) – True if input was pressed during last frame
```

Doc example (verbatim):

```lua
function client.tick()
	if InputPressed("interact") then
		DebugPrint("interact")
	end
end
```

### InputDown  [no SERVER/CLIENT tag in docs]

```text
pressed = InputDown(input, [playerId])

Arguments

input (string) – The input identifier

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

pressed (boolean) – True if input is currently held down
```

Doc example (verbatim):

```lua
function client.tick()
	if InputDown("interact") then
		DebugPrint("interact")
	end
end
```

### InputReleased  [no SERVER/CLIENT tag in docs]

```text
pressed = InputReleased(input, [playerId])

Arguments

input (string) – The input identifier

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

pressed (boolean) – True if input was released during last frame
```

Doc example (verbatim):

```lua
function client.tick()
	if InputReleased("interact") then
		DebugPrint("interact")
	end
end
```

### InputValue  [no SERVER/CLIENT tag in docs]

```text
value = InputValue(input, [playerId])

Arguments

input (string) – The input identifier

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

value (number) – Depends on input type
```

Doc example (verbatim):

```lua
local scrollPos = 0
function client.tick()
	scrollPos = scrollPos + InputValue("mousewheel")
	DebugPrint(scrollPos)
end
```

### InputLastPressedKey  [no SERVER/CLIENT tag in docs]

```text
name = InputLastPressedKey([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

name (string) – Name of last pressed key, empty if no key is pressed
```

Doc example (verbatim):

```lua
function client.tick()
	local name = InputLastPressedKey()
	if string.len(name) > 0 then
		DebugPrint(name)
	end
end
```

Related input functions that exist in api.html: `InputClear()`, `InputResetOnTransition()` (full text below).

### InputClear  [CLIENT ONLY]

```text
InputClear()

Arguments

none

Return value

none

All player input is "forgotten" by the game after calling this function
```

Doc example (verbatim):

```lua
function client.update()
    -- Prints '2' because InputClear() allows the game to "forget" the player's input
	if InputDown("interact") then
        InputClear()
		if InputDown("interact") then
			DebugPrint(1)
		else
			DebugPrint(2)
		end
	end
end
```

### InputResetOnTransition  [CLIENT ONLY]

```text
InputResetOnTransition()

Arguments

none

Return value

none

This function will reset everything we need to reset during state transition
```

Doc example (verbatim):

```lua
function update()
	if InputDown("interact") then
        -- In this form, you won't be able to notice the result of the function; you need a specific context
		InputResetOnTransition()
	end
end
```

### 2.1 Full list of input names (verbatim from the "Script control" section of api.html)

The docs state the names in two tables, "Physical input" and "Logical input". There is no other text about them in api.html beyond the per-function argument descriptions above. The intro sentence of the section is only: `General functions that control the operation and flow of the script.`

**Physical input**


| Physical input | Description |
|---|---|
| `esc` | Escape key |
| `tab` | Tab key |
| `lmb` | Left mouse button |
| `rmb` | Right mouse button |
| `mmb` | Middle mouse button |
| `uparrow` | Up arrow key |
| `downarrow` | Down arrow key |
| `leftarrow` | Left arrow key |
| `rightarrow` | Right arrow key |
| `f1-f12` | Function keys |
| `backspace` | Backspace key |
| `alt` | Alt key |
| `delete` | Delete key |
| `home` | Home key |
| `end` | End key |
| `pgup` | Pgup key |
| `pgdown` | Pgdown key |
| `insert` | Insert key |
| `space` | Space bar |
| `shift` | Shift key |
| `ctrl` | Ctrl key |
| `return` | Return key |
| `any` | Any key or button |
| `a,b,c,...` | Latin, alphabetical keys a through z |
| `0-9` | Digits, zero to nine |
| `mousedx` | Mouse horizontal diff. Only valid in InputValue. |
| `mousedy` | Mouse vertical diff. Only valid in InputValue. |
| `mousewheel` | Mouse wheel. Only valid in InputValue. |

**Logical input**

| Logical input | Description |
|---|---|
| `up` | Move forward / Accelerate |
| `down` | Move backward / Brake |
| `left` | Move left |
| `right` | Move right |
| `interact` | Interact |
| `flashlight` | Flashlight |
| `jump` | Jump |
| `crouch` | Crouch |
| `usetool` | Use tool |
| `grab` | Grab |
| `handbrake` | Handbrake |
| `map` | Map |
| `pause` | Pause game (escape) |
| `vehicleraise` | Raise vehicle parts |
| `vehiclelower` | Lower vehicle parts |
| `vehicleaction` | Vehicle action |
| `camerax` | Camera x movement, scaled by sensitivity. Only valid in InputValue. |
| `cameray` | Camera y movement, scaled by sensitivity. Only valid in InputValue. |
| `tool_group_prev` | Switch to previous tool group |
| `tool_group_next` | Switch to next tool group |
| `extra0` | Extra action 0 |
| `extra1` | Extra action 1 |
| `extra2` | Extra action 2 |
| `extra3` | Extra action 3 |
| `extra4` | Extra action 4 |
| `extra5` | Extra action 5 |
| `extra6` | Extra action 6 |
| `photomode` | Photomode |
| `zoom` | Zoom |
| `menu_left` | Menu left |
| `menu_right` | Menu right |
| `menu_up` | Menu up |
| `menu_down` | Menu down |
| `menu_next` | Menu next |
| `menu_prev` | Menu prev |
| `menu_accept` | Menu accept |
| `menu_cancel` | Menu cancel |

Notes on usage found in the docs: index.html says `User input should be handled in tick() and never in update().` (older global-callback text); the `SetVehicleHealth` and `GetPlayerCanUseTool` examples use `InputPressed("usetool", playerId)` / `InputPressed("usetool", p)`. There is no name for "pickaxe" or "place": use `lmb`/`rmb`/`usetool`/`grab`/`interact` etc. from the tables above. `usetool` is the only tool-specific logical name; `tool_group_prev` / `tool_group_next` switch tool groups; `extra0` ... `extra6` are "Extra action" inputs.

## 3. Player camera and aiming

### GetPlayerCameraTransform  [no SERVER/CLIENT tag in docs]

```text
transform = GetPlayerCameraTransform([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

transform (TTransform) – Current player camera transform

The player camera transform is usually the same as what you get from GetCameraTransform,
but if you have set a camera transform manually with SetCameraTransform, you can retrieve
the standard player camera transform with this function.
```

Doc example (verbatim):

```lua
function client.init()
	local t = GetPlayerCameraTransform()
	DebugPrint(TransformStr(t))
end
```

### GetPlayerEyeTransform  [no SERVER/CLIENT tag in docs]

```text
transform = GetPlayerEyeTransform([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

transform (TTransform) – Current player eye transform

The player eye transform is the same as what you get from GetCameraTransform when playing in first-person,
but if you have set a camera transform manually with SetCameraTransform or playing in third-person, you can retrieve
the player eye transform with this function.
```

Doc example (verbatim):

```lua
function client.init()
	local t = GetPlayerEyeTransform()
	DebugPrint(TransformStr(t))
end
```

### GetCameraTransform  [CLIENT ONLY]

```text
transform = GetCameraTransform()

Arguments

none

Return value

transform (TTransform) – Current camera transform
```

Doc example (verbatim):

```lua
function client.tick()
	local t = GetCameraTransform()
	DebugPrint(TransformStr(t))
end
```

### Scene queries

Section intro (api.html "Scene queries"): `Query the level in various ways.`

### QueryRaycast  [no SERVER/CLIENT tag in docs]

```text
hit, dist, normal, shape = QueryRaycast(origin, direction, maxDist, [radius], [rejectTransparent])

Arguments

origin (TVec) – Raycast origin as world space vector

direction (TVec) – Unit length raycast direction as world space vector

maxDist (number) – Raycast maximum distance. Keep this as low as possible for good performance.

radius (number, optional) – Raycast thickness. Default zero.

rejectTransparent (boolean, optional) – Raycast through transparent materials. Default false.

Return value

hit (boolean) – True if raycast hit something

dist (number) – Hit distance from origin

normal (TVec) – World space normal at hit point

shape (number) – Handle to hit shape

This will perform a raycast or spherecast (if radius is more than zero) query.
If you want to set up a filter for the query you need to do so before every call
to this function.
```

Doc example (verbatim):

```lua
function client.init()
	local vehicle = FindVehicle("vehicle")
	QueryRejectVehicle(vehicle)
	--Raycast from a high point straight downwards, excluding a specific vehicle
	local hit, d = QueryRaycast(Vec(0, 100, 0), Vec(0, -1, 0), 100)
	if hit then
		DebugPrint(d)
	end
end
```

### QueryRejectBody  [no SERVER/CLIENT tag in docs]

```text
QueryRejectBody(body)

Arguments

body (number) – Body handle

Return value

none

Exclude body from the next query
```

Doc example (verbatim):

```lua
function client.tick()
	local body = FindBody("body")
	QueryRequire("physical dynamic large")
	--Do not include body in next raycast
	QueryRejectBody(body)
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```

### QueryRejectShape  [no SERVER/CLIENT tag in docs]

```text
QueryRejectShape(shape)

Arguments

shape (number) – Shape handle

Return value

none

Exclude shape from the next query
```

Doc example (verbatim):

```lua
function client.tick()
	local shape = FindShape("shape")
	QueryRequire("physical dynamic large")
	--Do not include shape in next raycast
	QueryRejectShape(shape)
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```

### QueryRequire  [no SERVER/CLIENT tag in docs]

```text
QueryRequire(layers)

Arguments

layers (string) – Space separate list of layers

Return value

none

Set required layers for next query. Available layers are:
 Layer  |  Description

physical	 |  have a physical representation
dynamic		 |  part of a dynamic body
static		 |  part of a static body
large		 |  above debris threshold
small		 |  below debris threshold
visible		 |  only hit visible shapes
animator	 |  part of an animator hierarchy
player       |  part of an player animator hierarchy
tool         |  part of a tool
```

Doc example (verbatim):

```lua
--Raycast dynamic, physical objects above debris threshold, but not specific vehicle
function client.tick()
	local vehicle = FindVehicle("vehicle")
	QueryRequire("physical dynamic large")
	QueryRejectVehicle(vehicle)
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```

### Shape accessors

### GetShapeMaterialAtPosition  [no SERVER/CLIENT tag in docs]

```text
type, r, g, b, a, entry = GetShapeMaterialAtPosition(handle, pos, [includeUnphysical])

Arguments

handle (number) – Shape handle

pos (TVec) – Position in world space

includeUnphysical (boolean, optional) – Include unphysical voxels in the search. Default false.

Return value

type (string) – Material type

r (number) – Red

g (number) – Green

b (number) – Blue

a (number) – Alpha

entry (number) – Palette entry for voxel (zero if empty)

Return material properties for a particular voxel
```

Doc example (verbatim):

```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
end

function client.tick()
	local pos = GetCameraTransform().pos
	local dir = Vec(0, 0, 1)
	local hit, dist, normal, shape = QueryRaycast(pos, dir, 10)
	if hit then
		local hitPoint = VecAdd(pos, VecScale(dir, dist))
		local mat = GetShapeMaterialAtPosition(shape, hitPoint)
		DebugPrint("Raycast hit voxel made out of " .. mat)
	end
	DebugLine(pos, VecAdd(pos, VecScale(dir, 10)))
end
```

### GetShapeMaterialAtIndex  [no SERVER/CLIENT tag in docs]

```text
type, r, g, b, a, entry = GetShapeMaterialAtIndex(handle, x, y, z)

Arguments

handle (number) – Shape handle

x (number) – X integer coordinate

y (number) – Y integer coordinate

z (number) – Z integer coordinate

Return value

type (string) – Material type

r (number) – Red

g (number) – Green

b (number) – Blue

a (number) – Alpha

entry (number) – Palette entry for voxel (zero if empty)

Return material properties for a particular voxel in the voxel grid indexed by integer values.
The first index is zero (not one, as opposed to a lot of lua related things)
```

Doc example (verbatim):

```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
	local mat = GetShapeMaterialAtIndex(shape, 0, 0, 0)
	DebugPrint("The voxel is of material: " .. mat)
end
```

### GetShapeBody  [no SERVER/CLIENT tag in docs]

```text
handle = GetShapeBody(handle)

Arguments

handle (number) – Shape handle

Return value

handle (number) – Body handle

Get handle to the body this shape is owned by. A shape is always owned by a body,
but can be transfered to a new body during destruction.
```

Doc example (verbatim):

```lua
local body = 0
function client.init()
	body = GetShapeBody(FindShape("shape", true))
end

function client.tick()
	DebugCross(GetBodyCenterOfMass(body))
end
```

### GetShapeWorldTransform  [no SERVER/CLIENT tag in docs]

```text
transform = GetShapeWorldTransform(handle)

Arguments

handle (number) – Shape handle

Return value

transform (TTransform) – Return shape transform in world space

This is a convenience function, transforming the shape out of body space
```

Doc example (verbatim):

```lua
--GetShapeWorldTransform is equivalent to
--local shapeTransform = GetShapeLocalTransform(shape)
--local bodyTransform = GetBodyTransform(GetShapeBody(shape))
--worldTranform = TransformToParentTransform(bodyTransform, shapeTransform)

local shape = 0
function client.init()
	shape = FindShape("shape", true)
end

function client.tick()
	DebugCross(GetShapeWorldTransform(shape).pos)
end
```

### GetShapeLocalTransform  [no SERVER/CLIENT tag in docs]

```text
transform = GetShapeLocalTransform(handle)

Arguments

handle (number) – Shape handle

Return value

transform (TTransform) – Return shape transform in body space
```

Doc example (verbatim):

```lua
local shape = 0
function client.init()
	shape = FindShape("shape")
end

function client.tick()
	--Shape transform in body local space
	local shapeTransform = GetShapeLocalTransform(shape)

	--Body transform in world space
	local bodyTransform = GetBodyTransform(GetShapeBody(shape))

	--Shape transform in world space
	local worldTranform = TransformToParentTransform(bodyTransform, shapeTransform)

	DebugCross(worldTranform)
end
```

### GetShapeSize  [no SERVER/CLIENT tag in docs]

```text
xsize, ysize, zsize, scale = GetShapeSize(handle)

Arguments

handle (number) – Shape handle

Return value

xsize (number) – Size in voxels along x axis

ysize (number) – Size in voxels along y axis

zsize (number) – Size in voxels along z axis

scale (number) – The size of one voxel in meters (with default scale it is 0.1)

Return the size of a shape in voxels
```

Doc example (verbatim):

```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
	local x, y, z = GetShapeSize(shape)
	DebugPrint("Shape size: " .. x .. ";" .. y .. ";" .. z)
end
```

### GetShapeBounds  [no SERVER/CLIENT tag in docs]

```text
min, max = GetShapeBounds(handle)

Arguments

handle (number) – Shape handle

Return value

min (TVec) – Vector representing the AABB lower bound

max (TVec) – Vector representing the AABB upper bound

Return the world space, axis-aligned bounding box for a shape.
```

Doc example (verbatim):

```lua
function printShapeBounds()
	local shape = FindShape("shape", true)

	local min, max = GetShapeBounds(shape)
	local boundsSize = VecSub(max, min)
	local center = VecLerp(min, max, 0.5)

	DebugPrint(VecStr(boundsSize) .. " " .. VecStr(center))
end
```

Section intro (api.html "Shape"):

```text
A shape is a voxel object and always owned by a body. A single body may contain multiple shapes. The transform
of shape is expressed in the parent body coordinate system.
```

### Related functions present in the docs (not requested, but relevant to aiming / ray hits)

### GetPlayerAimInfo  [no SERVER/CLIENT tag in docs]

```text
hit, startpos, endpos, direction, hitnormal, hitdist, hitentity, hitmaterial = GetPlayerAimInfo(position, [maxdist], [playerId])

Arguments

position (TVec) – Start position of the search

maxdist (number, optional) – Max search distance

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

hit (boolean) – TRUE if hit, FALSE otherwise.

startpos (TVec) – Player can modify start position when close to walls etc

endpos (TVec) – Hit position

direction (TVec) – Direction from start position to end position

hitnormal (TVec) – Normal of the hitpoint

hitdist (number) – Distance of the hit

hitentity (handle) – Handle of the entitiy being hit

hitmaterial (handle) – Name of the material being hit
```

Doc example (verbatim):

```lua
local muzzle = GetToolLocationWorldTransform("muzzle")
local _, pos, _, dir = GetPlayerAimInfo(muzzle.pos)
Shoot(pos, dir)
```

### QueryRejectPlayer  [no SERVER/CLIENT tag in docs]

```text
QueryRejectPlayer([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

none

Exclude player from the next query
```

Doc example (verbatim):

```lua
--Do not include shape in next raycast
QueryRejectPlayer(1)
QueryRaycast(...)
```

### QueryRejectBodies  [no SERVER/CLIENT tag in docs]

```text
QueryRejectBodies(bodies)

Arguments

bodies (table) – Array with bodies handles

Return value

none

Exclude bodies from the next query
```

Doc example (verbatim):

```lua
function client.tick()
	local body = FindBody("body")
	QueryRequire("physical dynamic large")
	local bodies = {body}
	--Do not include body in next raycast
	QueryRejectBodies(bodies)
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```

### QueryRejectShapes  [no SERVER/CLIENT tag in docs]

```text
QueryRejectShapes(shapes)

Arguments

shapes (table) – Array with shapes handles

Return value

none

Exclude shapes from the next query
```

Doc example (verbatim):

```lua
function client.tick()
	local shape = FindShape("shape")
	QueryRequire("physical dynamic large")
	local shapes = {shape}
	--Do not include shape in next raycast
	QueryRejectShapes(shapes)
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```

### QueryInclude  [no SERVER/CLIENT tag in docs]

```text
QueryInclude(layers)

Arguments

layers (string) – Space separate list of layers

Return value

none

Set included layers for next query. Queries include all layers except tool and player per default. Available layers are:
 Layer  |  Description

physical	 |  have a physical representation
dynamic		 |  part of a dynamic body
static		 |  part of a static body
large		 |  above debris threshold
small		 |  below debris threshold
visible		 |  only hit visible shapes
animator     |  part of an animator hierarchy
player       |  part of an player
tool         |  part of a tool
```

Doc example (verbatim):

```lua
--Raycast all the default layers and include the player layer.
function client.tick()
	QueryInclude("player")
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```

### QueryCollisionMask  [no SERVER/CLIENT tag in docs]

```text
QueryCollisionMask(mask)

Arguments

mask (number) – Mask bits (0-255)

Return value

none

Set collision mask filter for the next query. Queries have a mask of 255 by default
```

Doc example (verbatim):

```lua
--Find the closest point on any shape (within 2 meters) to the player eye that the player can collide with.
function client.tick()
	QueryRequire("physical")
	QueryCollisionMask(GetPlayerParam("CollisionMask"))
	local hit, hitpos = QueryClosestPoint(GetPlayerEyeTransform().pos, 2)
	if hit then
		DebugCross(hitpos)
	end
end
```

### GetShapeMaterial  [no SERVER/CLIENT tag in docs]

```text
type, red, green, blue, alpha, reflectivity, shininess, metallic, emissive = GetShapeMaterial(shape, entry)

Arguments

shape (number) – Shape handle

entry (number) – Material entry

Return value

type (string) – Type

red (number) – Red value

green (number) – Green value

blue (number) – Blue value

alpha (number) – Alpha value

reflectivity (number) – Range 0 to 1

shininess (number) – Range 0 to 1

metallic (number) – Range 0 to 1

emissive (number) – Range 0 to 32

Return material properties for specific matirial entry.
```

Doc example (verbatim):

```lua
function client.init()
	local type, r, g, b, a, reflectivity, shininess, metallic, emissive = GetShapeMaterial(FindShape("shape2", true), 1)
	DebugPrint(type)
end
```

### GetShapeVoxelCount  [no SERVER/CLIENT tag in docs]

```text
count = GetShapeVoxelCount(handle)

Arguments

handle (number) – Shape handle

Return value

count (number) – Number of voxels in shape

Return the number of voxels in a shape, not including empty space
```

Doc example (verbatim):

```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
	local voxelCount = GetShapeVoxelCount(shape)
	DebugPrint(voxelCount)
end
```

### GetPlayerPitch  [no SERVER/CLIENT tag in docs]

```text
pitch = GetPlayerPitch([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

pitch (number) – Current player pitch angle

The player pitch angle is applied to the player camera transform. This value can be used to animate tool pitch movement when using SetToolTransformOverride.
```

Doc example (verbatim):

```lua
function client.init()
	local pitchRotation = Quat(Vec(1,0,0), GetPlayerPitch())
end
```

### DisablePlayerInput  [SERVER ONLY]

```text
DisablePlayerInput(player)

Arguments

player (playerIndex) – Player to disable input for

Return value

none

Disable input for a player. Should be called from tick.
```

Doc example (verbatim):

```lua
-- Disable player 2 input as she/he is interacting with something.
DisablePlayerInput(2)
```

### DisablePlayer  [SERVER ONLY]

```text
DisablePlayer(playerId)

Arguments

playerId (number) – Player to disable

Return value

none

Disables the player from any interaction, physics and rendering.
```

Doc example (verbatim):

```lua
function updateFinalScoreboard()
	for i=1,#hiddenPlayers do
		DisablePlayer(hiddenPlayers[i])
	end
end
```

### IsPlayerDisabled  [no SERVER/CLIENT tag in docs]

```text
IsPlayerDisabled(playerId)

Arguments

playerId (number) – Check if player is disabled

Return value

none

Check if player is actively disabled
```

Doc example (verbatim):

```lua
--check if disabled
playerDisabled = IsPlayerDisabled(playerId)
```

## 4. Server / client bridging

### ServerCall  [no SERVER/CLIENT tag in docs]

```text
ServerCall(function, [param1, param2, .., paramN])

Arguments

function (string) – Name of the function to be invoked. This function must exist within issuing script.

param1, param2, .., paramN (any, optional) – Optional parameters to send to the server. Arguments should match the signature of the specified function.

Return value

none
```

Doc example (verbatim):

```lua
function client.tick()
	if UiTextButton("I am Ready") then
		ServerCall("server.setPlayerReady", GetLocalPlayer())
	end
end

function server.setPlayerReady(playerId)
	shared.playersReady[playerId] = true
end
```

### ClientCall  [no SERVER/CLIENT tag in docs]

```text
ClientCall(playerId, function, [param1, param2, .., paramN])

Arguments

playerId (number) – Player ID of the recipient. Use 0 to broadcast to every player.

function (string) – Name of the function to be invoked. This function must exist within issuing script.

param1, param2, .., paramN (any, optional) – Optional parameters to send to the recipent(s). Arguments should match the signature of the specified function.

Return value

none
```

Doc example (verbatim):

```lua
function server.tick()
	for p in Players() do
		if GetPlayerHealth(p) == 0) then
			ClientCall(p, "client.showRespawnBtn")
		end
	end

	if matchEnded then
		ClientCall(0, "client.displayParticles", "confetti", 200, 0.3, Vec(0, 30, 0))
	end
end

function client.showRespawnBtn()
	-- show respawn ui..
end

function client.displayParticles(particleName, amount, life, pos)
	-- spawn particles..
end
```

### 4.1 The `shared` table (verbatim, api.html intro)


| Built in table | Description |
|---|---|
| `server` | Only exists on the server. You can put your own global variables in here, but they will only be available on the server. |
| `client` | This is similar to the server table, but only exists on clients. |
| `shared` | Automatically synchronized data from server to client parts of the same script. Read-only from the client part of the script. The server can put any data type in the shared table, including tables, but having a lot of data that changes often can consume a lot of bandwith. |

grep for the word `shared` finds only that table row and one line in the `ServerCall` example, `shared.playersReady[playerId] = true` (inside `function server.setPlayerReady(playerId)`). Nothing in the docs shows how to initialise a `shared` table or mentions `shared` in `ClientCall`.

### 4.2 Tags of the functions you asked about (the doc's own tags)

| Function | Doc tag |
|---|---|
| `MakeHole` | SERVER ONLY |
| `Spawn` | none (no tag; docs do not say server-only or client-only) |
| `Delete` | none (no tag; docs do not say server-only or client-only) |
| `SetShapeEmissiveScale` | none (no tag; docs do not say server-only or client-only) |
| `Paint` | SERVER ONLY |
| `Shoot` | SERVER ONLY |
| `Explosion` | SERVER ONLY |
| `SpawnParticle` | none (no tag; docs do not say server-only or client-only) |
| `PlaySound` | none (no tag; docs do not say server-only or client-only) |

The docs contain no further statement (outside the tags and the intro text quoted in 1.2) about which of these run where. Full entries follow.

### MakeHole  [SERVER ONLY]

```text
count = MakeHole(position, r0, [r1], [r2], [silent])

Arguments

position (TVec) – Hole center point

r0 (number) – Hole radius for soft materials

r1 (number, optional) – Hole radius for medium materials. May not be bigger than r0. Default zero.

r2 (number, optional) – Hole radius for hard materials. May not be bigger than r1. Default zero.

silent (boolean, optional) – Make hole without playing any break sounds.

Return value

count (number) – Number of voxels that was cut out. This will be zero if there were no changes to any shape.

Make a hole in the environment. Radius is given in meters.
Soft materials: glass, foliage, dirt, wood, plaster and plastic.
Medium materials: concrete, brick and weak metal.
Hard materials: hard metal and hard masonry.
```

Doc example (verbatim):

```lua
function server.init()
	MakeHole(Vec(0, 0, 0), 5.0, 1.0)
end
```

### Delete  [no SERVER/CLIENT tag in docs]

```text
Delete(handle)

Arguments

handle (number) – Entity handle

Return value

none

Remove an entity from the scene. All entities owned by this entity
will also be removed.
```

Doc example (verbatim):

```lua
function init()
	local body = FindBody("body", true)
	--All shapes associated with body will also be removed
	Delete(body)
end
```

### SetShapeEmissiveScale  [no SERVER/CLIENT tag in docs]

```text
SetShapeEmissiveScale(handle, scale)

Arguments

handle (number) – Shape handle

scale (number) – Scale factor for emissiveness

Return value

none

Scale emissiveness for shape. If the shape has light sources attached,
their intensity will be scaled by the same amount.
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	shape = FindShape("shape", true)

	--Pulsate emissiveness and light intensity for shape
	local scale = math.sin(GetTime())*0.5 + 0.5
	SetShapeEmissiveScale(shape, scale)
end
```

### Paint  [SERVER ONLY]

```text
Paint(origin, radius, [type], [probability])

Arguments

origin (TVec) – Origin in world space as vector

radius (number) – Affected radius, in range 0.0 to 5.0

type (string, optional) – Paint type. Can be "explosion" or "spraycan". Default is spraycan.

probability (number, optional) – Dithering probability between zero and one, default is 1.0

Return value

none

Tint the color of objects within radius to either black or yellow.
```

Doc example (verbatim):

```lua
function server.tick()
	Paint(Vec(0, 2, 0), 5.0, "spraycan")
end
```

### Shoot  [SERVER ONLY]

```text
Shoot(origin, direction, [type], [strength], [maxDist], [playerId])

Arguments

origin (TVec) – Origin in world space as vector

direction (TVec) – Unit length direction as world space vector

type (string, optional) – Shot type, see description, default is "bullet"

strength (number, optional) – Strength scaling, default is 1.0

maxDist (number, optional) – Maximum distance, default is 100.0

playerId (number, optional) – Instigating player. Can be skipped for non-player shots (helicopters etc.)

Return value

none

Fire projectile. Type can be one of "bullet", "rocket", "gun" or "shotgun".
For backwards compatilbility, type also accept a number, where 1 is same as "rocket" and anything else "bullet"
Note that this function will only spawn the projectile, not make any sound.
```

Doc example (verbatim):

```lua
function server.tick()
	Shoot(Vec(0, 10, 0), Vec(0, -1, 0), "shotgun")
end
```

### Explosion  [SERVER ONLY]

```text
Explosion(pos, size, [instigatingPlayerId])

Arguments

pos (TVec) – Position in world space as vector

size (number) – Explosion size from 0.5 to 4.0

instigatingPlayerId (number, optional) – Instigating player ID.

Return value

none
```

Doc example (verbatim):

```lua
function server.init()
	Explosion(Vec(0, 5, 0), 1)
end
```

(`Spawn` is in section 5, `SpawnParticle` in section 8, `PlaySound` in section 7.)

### 4.3 Complete list of every function the docs tag SERVER ONLY (42)

`SetVehicleParam`, `DriveVehicle`, `SetVehicleHealth`, `SetPlayerTransform`, `SetPlayerTransformWithPitch`, `SetPlayerGroundVelocity`, `SetPlayerSpawnTransform`, `SetPlayerSpawnHealth`, `SetPlayerSpawnTool`, `SetPlayerVehicle`, `SetPlayerVelocity`, `ReleasePlayerGrab`, `SetPlayerScreen`, `SetPlayerHealth`, `SetPlayerRegenerationState`, `SetPlayerTool`, `RespawnPlayer`, `RespawnPlayerAtTransform`, `SetPlayerWalkingSpeed`, `SetPlayerCrouchSpeedScale`, `SetPlayerHurtSpeedScale`, `SetPlayerParam`, `RegisterTool`, `SetToolAmmoPickupAmount`, `SetToolAmmo`, `SetToolEnabled`, `ApplyPlayerDamage`, `DisablePlayerInput`, `DisablePlayer`, `DisablePlayerDamage`, `Shoot`, `Paint`, `PaintRGBA`, `MakeHole`, `Explosion`, `SpawnFire`, `RemoveAabbFires`, `SetTimeScale`, `SetEnvironmentDefault`, `SetEnvironmentProperty`, `AddHeat`, `SetGravity`

### 4.4 Complete list of every function the docs tag CLIENT ONLY (33)

`InputClear`, `InputResetOnTransition`, `SetPlayerCharacter`, `SetPlayerCameraOffsetTransform`, `SetToolHandPoseLocalTransform`, `SetToolTransform`, `SetToolAllowedZoom`, `SetToolTransformOverride`, `SetToolOffset`, `SetPlayerRigTags`, `SetSoundLoopUser`, `PlaySoundForUser`, `AddMapMarker`, `SelectedMapMarker`, `GetCameraTransform`, `SetCameraTransform`, `RequestFirstPerson`, `RequestThirdPerson`, `SetCameraOffsetTransform`, `AttachCameraTo`, `SetPivotClipBody`, `ShakeCamera`, `SetCameraFov`, `SetCameraDof`, `DisableMotionBlur`, `SetLowHealthBlurThreshold`, `LoadHaptic`, `CreateHaptic`, `PlayHaptic`, `PlayHapticDirectional`, `HapticIsPlaying`, `SetToolHaptic`, `StopHaptic`

## 5. Spawning blocks

Section intro (api.html "Spawn"): `Functions to spawn entities in the scene. The Spawn function can spawn prefabs from file or xml.`

### Spawn  [no SERVER/CLIENT tag in docs]

```text
entities = Spawn(xml, transform, [allowStatic], [jointExisting])

Arguments

xml (string) – File name or xml string

transform (TTransform) – Spawn transform

allowStatic (boolean, optional) – Allow spawning static shapes and bodies (default false)

jointExisting (boolean, optional) – Allow joints to connect to existing scene geometry (default false)

Return value

entities (table) – Indexed table with handles to all spawned entities

The first argument can be either a prefab XML file in your mod folder or a string with XML content. It is also
possible to spawn prefabs from other mods, by using the mod id followed by colon, followed by the prefab path.
Spawning prefabs from other mods should be used with causion since the referenced mod might not be installed.
```

Doc example (verbatim):

```lua
function server.init()
	Spawn("MOD/prefab/mycar.xml", Transform(Vec(0, 5, 0)))
	Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", Transform(Vec(0, 10, 0)))
end
```

### SpawnLayer  [no SERVER/CLIENT tag in docs]

```text
entities = SpawnLayer(xml, layer, transform, [allowStatic], [jointExisting])

Arguments

xml (string) – File name or xml string

layer (string) – Vox layer name

transform (TTransform) – Spawn transform

allowStatic (boolean, optional) – Allow spawning static shapes and bodies (default false)

jointExisting (boolean, optional) – Allow joints to connect to existing scene geometry (default false)

Return value

entities (table) – Indexed table with handles to all spawned entities

Same functionality as Spawn(), except using a specific layer in the vox-file
```

Doc example (verbatim):

```lua
function server.init()
	Spawn("MOD/prefab/mycar.xml", "some_vox_layer", Transform(Vec(0, 5, 0)))
	Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", "some_vox_layer", Transform(Vec(0, 10, 0)))
end
```

### 5.1 `<voxbox>` element: every mention in both files

grep for `voxbox` (case-insensitive) in api.html and index.html finds exactly three lines.

**There is no attribute reference for `<voxbox>`.** The only attributes that appear anywhere are `size`, `prop` and `material`, in the two `Spawn` doc examples (shown in full in section 5 above):

```lua
Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", Transform(Vec(0, 10, 0)))
Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", "some_vox_layer", Transform(Vec(0, 10, 0)))
```

The only other mention is in index.html (Hierarchy & Inheritance, verbatim): `The scene above shows two voxbox shapes, "box1" and "box2", both having the `foo` tag. The API has a function `FindShapes()` that allows the script to find shapes using a tag as search criteria.`

| Attribute | Result |
|---|---|
| `size` | Only seen as `size='10 10 10'` (three space-separated numbers). No description. |
| `material` | Only seen as `material='wood'`. No list of valid values. |
| `prop` | Only seen as `prop='true'`. No description. |
| `color` | NOT FOUND IN DOCS |
| `texture` | NOT FOUND IN DOCS as a voxbox attribute (index.html line 237 mentions "the texture property for the *small_junk1* object in the Editor" in a screenshot caption, nothing about attribute names) |
| `pbr` | NOT FOUND IN DOCS |
| `<voxbox>` element definition / XML schema | NOT FOUND IN DOCS (index.html says the editor's built-in help is the reference, see below) |

greps for `material=` and `material='`: only the two api.html `Spawn` example lines above.

### 5.2 Valid material name strings

NOT FOUND IN DOCS as an authoritative list of strings for `<voxbox material=...>`, `CreateShape`, `SetBrush` or any other function. `SetBrush` takes a numeric material index (section 6). The docs mention material names only in the following places.

api.html, `MakeHole` description (soft/medium/hard names, lower case, verbatim):

```text
Soft materials: glass, foliage, dirt, wood, plaster and plastic.
Medium materials: concrete, brick and weak metal.
Hard materials: hard metal and hard masonry.
```

index.html, "Materials" table (verbatim; display names, not identifier strings):


> ## Materials 
>
> The following is a list of all materials, their respective hardness from softest to hardest, and whether the sledgehammer, blowtorch, explosives and guns (handgun and shotgun) affects them.
>
> | Material     | Hardness    | Sledge | Blowtorch | Guns  | Explosives |
> | :----------- | :---------- | :----- | :-------- | :---- | :--------- |
> | Glass        | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
> | Grass        | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
> | Dirt         | Soft        | **✓**  | ✗         | **✓** | **✓**      |
> | Plastic      | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
> | Wood         | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
> | Plaster      | Soft        | **✓**  | ✗         | **✓** | **✓**      |
> | Concrete     | Medium      | ✗      | ✗         | **✓** | **✓**      |
> | Brick        | Medium      | ✗      | ✗         | **✓** | **✓**      |
> | Weak Metal   | Medium      | ✗      | **✓**     | **✓** | **✓**      |
> | Hard Masonry | Hard        | ✗      | ✗         | ✗     | **✓**      |
> | Hard Metal   | Hard        | ✗      | ✗         | ✗     | **✓**      |
> | Heavy Metal  | Unbreakable | ✗      | ✗         | ✗     | ✗          |
> | Rock         | Unbreakable | ✗      | ✗         | ✗     | ✗          |

index.html, Palette Indices (verbatim; this is how a voxel's material is decided in a .vox file):


> ## Palette Indices 
>
> In MagicaVoxel the palette is made up of 255 indexed colors. This means each color slot has a index number according to its position in the palette. These indices are used in Teardown to decide what material any individual voxel is made of. 
>
> ![Teardown MagicaVoxel Palette](images/teardown_palette.png)
>
> Observe that the actual color (whether its green, blue, white, or any other color) doesn't matter. Only the position in the palette is important from a material perspective. For example, the color at index 9 is always grass, no matter what actual color it is. You can see what index a particular color position has by hovering over it. The index will be shown in the console at the bottom of the screen.  
>
> ![](images/magicavoxel_console.png)
>
> To assist with materials, we are providing a MagicaVoxel file which has the palette annotated with the material names next to the colors. The palette can be downloaded [here](downloadable/teardown_palette.vox). If you can't see the material names when you open the file, click the little arrow button at the top of the palette (marked with a red outline in the image above). 

index.html, material appearance (verbatim, one sentence about the wood palette group):

> Observe that the material appearance doesn't affect what material Teardown assigns to a voxel. An object made of colors in the  wood group (indices 57 - 72) will still be wood in the game, even if you make it look like metal.

Result of grepping both files for each quoted-string form (`"wood"`, `'wood'`, etc.):

| String | Quoted-string occurrences |
|---|---|
| `wood` | `material='wood'` in the two `Spawn` examples only |
| `concrete`, `masonry`, `brick`, `dirt`, `grass`, `plaster`, `metal`, `heavymetal`, `hardmetal`, `hardmasonry`, `plastic`, `glass`, `rock`, `foliage` | NOT FOUND IN DOCS as quoted strings. Unquoted lower-case in api.html only inside the `MakeHole` sentences above: glass, foliage, dirt, wood, plaster, plastic, concrete, brick, "weak metal", "hard metal", "hard masonry". In index.html only as display names (Glass, Grass, Dirt, Plastic, Wood, Plaster, Concrete, Brick, Weak Metal, Hard Masonry, Hard Metal, Heavy Metal, Rock) plus ordinary prose. The tokens `heavymetal`, `hardmetal`, `hardmasonry` (one word) never appear in either file. |
| `unphysical` | Appears only in api.html as the argument text `includeUnphysical (boolean, optional) - Include unphysical voxels in the search. Default false.` of `GetShapeMaterialAtPosition`. It is not given as a material string. |

`GetShapeMaterialAtPosition` and `GetShapeMaterialAtIndex` return `type (string) - Material type` and their example does `DebugPrint("Raycast hit voxel made out of " .. mat)`, so a material name string exists at run time, but the docs never list the possible values. Full entries are in section 3 (`GetShapeMaterial` is in the related list there).

### 5.3 XML / prefab format

NOT FOUND IN DOCS. index.html (verbatim) on where the XML reference lives:


> ## Built In Help System
> The Editor has a built-in Help system that describes both the Editor itself and how to work with the functionality that the editor offers. This page is not a comprehensive reference to the Editor. The Editor is continuously updated with new functionality and the best place to find current and correct information is from the built-in Help system. The built in help-system can be opened by choosing "Help" in the menu. 
>
> ![Editor Help Window](images/editor_help.png)
>
> The Help window can be moved as any other window in the editor and can remain open while working on a level. In addition to the Help window the Teardown Editor gives you context specific information when you hover the mouse pointer over a property. This feature is extremely useful and sometimes the only place where you can find information about a particular property. 
>
> ![Context Specific Help](images/editor_help_tooltip.png)
>
> The image above shows the context specific info on the texture property for the *small_junk1* object in the Editor.  

## 6. Runtime shapes (CreateShape, brushes)

Requested names that are NOT in api.html: `SetShapeVoxel`, `GetShapeVoxel`, `ExtendShape`, `SetShapeStrength` (all NOT FOUND IN DOCS). Voxels are written with `SetBrush` + `DrawShapeBox` / `DrawShapeLine` / `ExtrudeShape` and read with `GetShapeMaterialAtIndex` / `GetShapeMaterialAtPosition` (section 3).

### CreateShape  [no SERVER/CLIENT tag in docs]

```text
newShape = CreateShape(body, transform, refShape)

Arguments

body (number) – Body handle

transform (TTransform) – Shape transform in body space

refShape (number or string) – Handle to reference shape or path to vox file

Return value

newShape (number) – Handle of new shape

Create new, empty shape on existing body using the palette of a reference shape.
The reference shape can be any existing shape in the scene or an external vox file.
The size of the new shape will be 1x1x1.
```

Doc example (verbatim):

```lua
server.tick()
	local players = GetAllPlayers()
	for i=1, #players do
		tickPlayer(players[i])
	end
end

function tickPlayer(playerId)
	if InputPressed("interact", playerId) then
		local t = Transform(Vec(0, 5, 0), QuatEuler(0, 0, 0))
		local handle = CreateShape(FindBody("shape", true), t, FindShape("shape", true))
		DebugPrint(handle)
	end
end
```

### ResizeShape  [no SERVER/CLIENT tag in docs]

```text
resized, offset = ResizeShape(shape, xmi, ymi, zmi, xma, yma, zma)

Arguments

shape (number) – Shape handle

xmi (number) – Lower X coordinate

ymi (number) – Lower Y coordinate

zmi (number) – Lower Z coordinate

xma (number) – Upper X coordinate

yma (number) – Upper Y coordinate

zma (number) – Upper Z coordinate

Return value

resized (boolean) – Resized successfully

offset (TVec) – Offset vector in shape local space

Resize an existing shape. The new coordinates are expressed in the existing shape coordinate frame,
so you can provide negative values. The existing content is preserved, but may be cropped if needed.
The local shape transform will be moved automatically with an offset vector to preserve the original content in body space.
This offset vector is returned in shape local space.
```

Doc example (verbatim):

```lua
function server.init()
	ResizeShape(FindShape("shape", true), -5, 0, -5, 5, 5, 5)
end
```

### SetBrush  [no SERVER/CLIENT tag in docs]

```text
SetBrush(type, size, index or path, [object])

Arguments

type (string) – One of "sphere", "cube" or "noise"

size (number) – Size of brush in voxels (must be in range 1 to 16)

index or path (number or string) – Material index or path to brush vox file

object (string, optional) – Optional object in brush vox file if brush vox file is used

Return value

none

Set material index to be used for following calls to DrawShapeLine and DrawShapeBox and ExtrudeShape.
An optional brush vox file and subobject can be used and provided instead of material index,
in which case the content of the brush will be used and repeated. Use material index zero
to remove of voxels.
```

Doc example (verbatim):

```lua
function server.init()
	SetBrush("sphere", 3, 3)
end
```

### DrawShapeBox  [no SERVER/CLIENT tag in docs]

```text
DrawShapeBox(shape, x0, y0, z0, x1, y1, z1)

Arguments

shape (number) – Handle to shape

x0 (number) – Start X coordinate

y0 (number) – Start Y coordinate

z0 (number) – Start Z coordinate

x1 (number) – End X coordinate

y1 (number) – End Y coordinate

z1 (number) – End Z coordinate

Return value

none

Draw box between (x0,y0,z0) and (x1,y1,z1) into shape using the material
set up with SetBrush.
```

Doc example (verbatim):

```lua
function server.init()
	SetBrush("sphere", 3, 4)
	DrawShapeBox(FindShape("shape", true), 0, 0, 0, 10, 50, 5)
end
```

### DrawShapeLine  [no SERVER/CLIENT tag in docs]

```text
DrawShapeLine(shape, x0, y0, z0, x1, y1, z1, [paint], [noOverwrite])

Arguments

shape (number) – Handle to shape

x0 (number) – Start X coordinate

y0 (number) – Start Y coordinate

z0 (number) – Start Z coordinate

x1 (number) – End X coordinate

y1 (number) – End Y coordinate

z1 (number) – End Z coordinate

paint (boolean, optional) – Paint mode. Default is false.

noOverwrite (boolean, optional) – Only fill in voxels if space isn't already occupied. Default is false.

Return value

none

Draw voxelized line between (x0,y0,z0) and (x1,y1,z1) into shape using the material
set up with SetBrush. Paint mode will only change material of existing voxels (where
the current material index is non-zero). noOverwrite mode will only fill in voxels if the
space isn't already occupied by another shape in the scene.
```

Doc example (verbatim):

```lua
function server.init()
	SetBrush("sphere", 3, 1)
	DrawShapeLine(FindShape("shape"), 0, 0, 0, 10, 50, 5, false, true)
end
```

### TrimShape  [no SERVER/CLIENT tag in docs]

```text
offset = TrimShape(shape)

Arguments

shape (number) – Source handle

Return value

offset (TVec) – Offset vector in shape local space

Trim away empty regions of shape, thus potentially making it smaller.
If the size of the shape changes, the shape will be automatically moved
to preserve the shape content in body space. The offset vector for this
translation is returned in shape local space.
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	shape = FindShape("shape", true)
	TrimShape(shape)
end
```

### MergeShape  [no SERVER/CLIENT tag in docs]

```text
shape = MergeShape(shape)

Arguments

shape (number) – Input shape

Return value

shape (number) – Shape handle after merge

Try to merge shape with a nearby, matching shape. For a merge to happen, the
shapes need to be aligned to the same rotation and touching. If the
provided shape was merged into another shape, that shape may be resized to
fit the merged content. If shape was merged, the handle to the other shape is
returned, otherwise the input handle is returned.
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	shape = FindShape("shape", true)
	DebugPrint(shape)
	shape = MergeShape(shape)
	DebugPrint(shape)
end
```

### SetShapeBody  [no SERVER/CLIENT tag in docs]

```text
SetShapeBody(shape, body, [transform])

Arguments

shape (number) – Shape handle

body (number) – Body handle

transform (TTransform, optional) – New local shape transform. Default is existing local transform.

Return value

none

Move existing shape to a new body, optionally providing a new local transform.
```

Doc example (verbatim):

```lua
function server.init()
	SetShapeBody(FindShape("shape", true), FindBody("custombody", true), true)
end
```

### IsShapeDisconnected  [no SERVER/CLIENT tag in docs]

```text
disconnected = IsShapeDisconnected(shape)

Arguments

shape (number) – Input shape

Return value

disconnected (boolean) – True if shape disconnected (has detached parts)
```

Doc example (verbatim):

```lua
function client.tick()
	DebugWatch("IsShapeDisconnected", IsShapeDisconnected(FindShape("shape", true)))
end
```

### SetShapeDensity  [no SERVER/CLIENT tag in docs]

```text
SetShapeDensity(handle, density)

Arguments

handle (number) – Shape handle

density (number) – New density for the shape

Return value

none

Change the material density of the shape.
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	shape = FindShape("shape", true)

	local density = 10.0
	SetShapeDensity(shape, density)
end
```

### 6.1 Closest functions that do exist for the missing names

### ExtrudeShape  [no SERVER/CLIENT tag in docs]

```text
ExtrudeShape(shape, x, y, z, dx, dy, dz, steps, mode)

Arguments

shape (number) – Handle to shape

x (number) – X coordinate to extrude

y (number) – Y coordinate to extrude

z (number) – Z coordinate to extrude

dx (number) – X component of extrude direction, should be -1, 0 or 1

dy (number) – Y component of extrude direction, should be -1, 0 or 1

dz (number) – Z component of extrude direction, should be -1, 0 or 1

steps (number) – Length of extrusion in voxels

mode (string) – Extrusion mode, one of "exact", "material", "geometry". Default is "exact"

Return value

none

Extrude region of shape. The extruded region will be filled in with the material set up with SetBrush.
The mode parameter sepcifies how the region is determined.
Exact mode selects region of voxels that exactly match the input voxel at input coordinate.
Material mode selects region that has the same material type as the input voxel.
Geometry mode selects any connected voxel in the same plane as the input voxel.
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	SetBrush("sphere", 3, 4)
	shape = FindShape("shape")
	ExtrudeShape(shape, 0, 5, 0, -1, 0, 0, 50, "exact")
end
```

### ClearShape  [no SERVER/CLIENT tag in docs]

```text
ClearShape(shape)

Arguments

shape (number) – Shape handle

Return value

none

Fill a voxel shape with zeroes, thus removing all voxels.
```

Doc example (verbatim):

```lua
function server.init()
	ClearShape(FindShape("shape", true))
end
```

### SplitShape  [no SERVER/CLIENT tag in docs]

```text
newShapes = SplitShape(shape, removeResidual)

Arguments

shape (number) – Source handle

removeResidual (boolean) – Remove residual shapes (default false)

Return value

newShapes (table) – List of shape handles created

Split up a shape into multiple shapes based on connectivity. If the removeResidual flag
is used, small disconnected chunks will be removed during this process to reduce the number
of newly created shapes.
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	shape = FindShape("shape", true)
	SplitShape(shape, true)
end
```

### CopyShapeContent  [no SERVER/CLIENT tag in docs]

```text
CopyShapeContent(src, dst)

Arguments

src (number) – Source shape handle

dst (number) – Destination shape handle

Return value

none

Copy voxel content from source shape to destination shape. If destination
shape has a different size, it will be resized to match the source shape.
```

Doc example (verbatim):

```lua
function server.init()
	CopyShapeContent(FindShape("shape", true), FindShape("shape2", true))
end
```

### CopyShapePalette  [no SERVER/CLIENT tag in docs]

```text
CopyShapePalette(src, dst)

Arguments

src (number) – Source shape handle

dst (number) – Destination shape handle

Return value

none

Copy the palette from source shape to destination shape.
```

Doc example (verbatim):

```lua
function server.init()
	CopyShapePalette(FindShape("shape", true), FindShape("shape2", true))
end
```

### GetShapePalette  [no SERVER/CLIENT tag in docs]

```text
entries = GetShapePalette(shape)

Arguments

shape (number) – Shape handle

Return value

entries (table) – Palette material entries

Return list of material entries, each entry is a material index that
can be provided to GetShapeMaterial or used as brush for populating a
shape.
```

Doc example (verbatim):

```lua
function server.init()
	local palette = GetShapePalette(FindShape("shape2", true))
	for i = 1, #palette do
		DebugPrint(palette[i])
	end
end
```

### SetShapeLocalTransform  [no SERVER/CLIENT tag in docs]

```text
SetShapeLocalTransform(handle, transform)

Arguments

handle (number) – Shape handle

transform (TTransform) – Shape transform in body space

Return value

none
```

Doc example (verbatim):

```lua
local shape = 0
function server.init()
	shape = FindShape("shape")
	local transform = Transform(Vec(0, 1, 0), QuatEuler(0, 90, 0))
	SetShapeLocalTransform(shape, transform)
end

function client.init()
	shape = FindShape("shape")
end

function client.tick()
	--Shape transform in body local space
	local shapeTransform = GetShapeLocalTransform(shape)

	--Body transform in world space
	local bodyTransform = GetBodyTransform(GetShapeBody(shape))

	--Shape transform in world space
	local worldTranform = TransformToParentTransform(bodyTransform, shapeTransform)

	DebugCross(worldTranform)
end
```

### SetShapeCollisionFilter  [no SERVER/CLIENT tag in docs]

```text
SetShapeCollisionFilter(handle, layer, mask)

Arguments

handle (number) – Shape handle

layer (number) – Layer bits (0-255)

mask (number) – Mask bits (0-255)

Return value

none

This is used to filter out collisions with other shapes. Each shape can be given a layer
bitmask (8 bits, 0-255) along with a mask (also 8 bits). The layer of one object must be in
the mask of the other object and vice versa for the collision to be valid. The default layer
for all objects is 1 and the default mask is 255 (collide with all layers).
```

Doc example (verbatim):

```lua
local shapeA = 0
local shapeB = 0
local shapeC = 0
local shapeD = 0
function server.init()
	shapeA = FindShape("shapeA")
	shapeB = FindShape("shapeB")
	shapeC = FindShape("shapeC")
	shapeD = FindShape("shapeD")
	--This will put shapes a and b in layer 2 and disable collisions with
	--object shapes in layers 2, preventing any collisions between the two.
	SetShapeCollisionFilter(shapeA, 2, 255-2)
	SetShapeCollisionFilter(shapeB, 2, 255-2)

	--This will put shapes c and d in layer 4 and allow collisions with other
	--shapes in layer 4, but ignore all other collisions with the rest of the world.
	SetShapeCollisionFilter(shapeC, 4, 4)
	SetShapeCollisionFilter(shapeD, 4, 4)
end
```

### IsShapeBroken  [no SERVER/CLIENT tag in docs]

```text
broken = IsShapeBroken(handle)

Arguments

handle (number) – Shape handle

Return value

broken (boolean) – Return true if shape is broken

Determine if shape has been broken. Note that a shape can be transfered
to another body during destruction, but might still not be considered
broken if all voxels are intact.
```

Doc example (verbatim):

```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
end

function client.tick()
	DebugPrint("Is shape broken: " .. tostring(IsShapeBroken(shape)))
end
```

## 7. Sound

Section intro (api.html "Sound"), verbatim:

```text
Sound functions are used for playing sounds or loops in the world. There sound functions are
always positioned and will be affected by acoustics simulation. If you want to play dry sounds
without acoustics you should use UiSound and UiSoundLoop in the User Interface section.
```

### LoadSound  [no SERVER/CLIENT tag in docs]

```text
handle = LoadSound(path, [nominalDistance])

Arguments

path (string) – Path to ogg sound file

nominalDistance (number, optional) – The distance in meters this sound is recorded at. Affects attenuation, default is 10.0

Return value

handle (number) – Sound handle
```

Doc example (verbatim):

```lua
function client.init()
	local snd = LoadSound("warning-beep.ogg")
end
```

### PlaySound  [no SERVER/CLIENT tag in docs]

```text
handle = PlaySound(handle, [pos], [volume], [registerVolume], [pitch])

Arguments

handle (number) – Sound handle

pos (TVec, optional) – World position as vector. Default is player position.

volume (number, optional) – Playback volume. Default is 1.0

registerVolume (boolean, optional) – Register position and volume of this sound for GetLastSound. Default is true

pitch (number, optional) – Playback pitch. Default 1.0

Return value

handle (number) – Sound play handle
```

Doc example (verbatim):

```lua
local snd
function client.init()
	snd = LoadSound("warning-beep.ogg")
end

function client.tick()
	if InputPressed("interact") then
		local pos = Vec(0, 0, 0)
		PlaySound(snd, pos, 0.5)
	end
end

-- If you have a list of sound files and you add a sequence number, starting from zero, at the end of each filename like below,
-- then each time you call PlaySound it will pick a random sound from that list and play that sound.

-- "example-sound0.ogg"
-- "example-sound1.ogg"
-- "example-sound2.ogg"
-- "example-sound3.ogg"
-- ...
--[[
	local snd
	function client.init()
		snd = LoadSound("example-sound0.ogg")
	end

	-- Plays a random sound from the loaded sound series
	function client.tick()
		if trigSound then
			local pos = Vec(100, 0, 0)
			PlaySound(snd, pos, 0.5)
		end
	end
]]
```

### UiSound  [no SERVER/CLIENT tag in docs]

```text
UiSound(path, [volume], [pitch], [panAzimuth], [panDepth])

Arguments

path (string) – Path to sound file (OGG format)

volume (number, optional) – Playback volume. Default 1.0

pitch (number, optional) – Playback pitch. Default 1.0

panAzimuth (number, optional) – Playback stereo panning azimuth (-PI to PI). Default 0.0.

panDepth (number, optional) – Playback stereo panning depth (0.0 to 1.0). Default 1.0.

Return value

none

UI sounds are not affected by acoustics simulation. Use LoadSound / PlaySound for that.
```

Doc example (verbatim):

```lua
UiSound("click.ogg")
```

### 7.1 Sound paths and the .tde files

index.html, verbatim (the only text about the encrypted game sounds):

> Sound effects and music in Teardown is using the .ogg audio format. Each song and sound effect is available as an individual file in the game file structure. Due to licensing reasons all .ogg audio files that comes with Teardown have been encrypted into .tde files that can only be read by the game. It is possible to override an encrypted .tde files by adding a new .ogg file with the same filename (excluding the .tde extension) to the same directory. The game will automatically load the file with the expected name and the .ogg extension prior to loading a file with the .tde extension.  

What the docs say and do not say about referencing game sounds by path:

- NOT FOUND IN DOCS: any list of built-in game sound file names, or any statement that a path such as `tools/sledge-hit0.ogg` can be passed to `LoadSound` / `PlaySound` / `UiSound`. grep for `sledge`, `tools/`, `snd/`, `.tde` in api.html finds only `SpawnTool("sledge", ...)` (a tool id, not a sound).
- The index.html text above implies (does not state) that the shipped .ogg files exist in the game file structure as .tde files under the same name and that the game resolves `name.ogg` before `name.tde`. It does not say what the directory layout is or whether mod scripts can load a base-game sound by that path.
- Path examples that appear in api.html doc examples (all relative, no prefix): `LoadSound("warning-beep.ogg")`, `LoadSound("radio/jazz.ogg")`, `LoadSound("example-sound0.ogg")`; `LoadLoop("radio/jazz.ogg")`; `PlayMusic("about.ogg")`; `UiSound("click.ogg")`; `UiSoundLoop("screech.ogg")`. Mod-file path examples use the `MOD/` prefix: `RegisterTool(..., "MOD/vox/lasergun.vox", 6)`, `Spawn("MOD/prefab/mycar.xml", ...)`, `LoadHaptic("MOD/haptic/tool.xml")`, `AddMapMarker(..., "MOD/gfx/bonus_info.png", ...)`; sprites/images use plain relative paths like `"gfx/laser.png"`.
- index.html on the `MOD` keyword (verbatim): `In the main.xml file (and all xml-files for levels) the keyword **MOD** is used as a reference to the mods folder.` That sentence is about XML files; Lua examples in api.html use it in strings too.

Related sound functions present in the docs:

### LoadLoop  [no SERVER/CLIENT tag in docs]

```text
handle = LoadLoop(path, [nominalDistance])

Arguments

path (string) – Path to ogg sound file

nominalDistance (number, optional) – The distance in meters this sound is recorded at. Affects attenuation, default is 10.0

Return value

handle (number) – Loop handle
```

### PlaySoundForUser  [CLIENT ONLY]

```text
handle = PlaySoundForUser(handle, user, [pos], [volume], [registerVolume], [pitch])

Arguments

handle (number) – Sound handle

user (number) – Index of user to play.

pos (TVec, optional) – World position as vector. Default is player position.

volume (number, optional) – Playback volume. Default is 1.0

registerVolume (boolean, optional) – Register position and volume of this sound for GetLastSound. Default is true

pitch (number, optional) – Playback pitch. Default 1.0

Return value

handle (number) – Sound play handle
```

### StopSound  [no SERVER/CLIENT tag in docs]

```text
StopSound(handle)

Arguments

handle (number) – Sound play handle

Return value

none
```

### UnloadSound  [no SERVER/CLIENT tag in docs]

```text
UnloadSound(handle)

Arguments

handle (number) – Sound handle

Return value

none
```

### PlayLoop  [no SERVER/CLIENT tag in docs]

```text
PlayLoop(handle, [pos], [volume], [registerVolume], [pitch])

Arguments

handle (number) – Loop handle

pos (TVec, optional) – World position as vector. Default is player position.

volume (number, optional) – Playback volume. Default is 1.0

registerVolume (boolean, optional) – Register position and volume of this sound for GetLastSound. Default is true

pitch (number, optional) – Playback pitch. Default 1.0

Return value

none

Call this function continuously to play loop
```

### UiSoundLoop  [no SERVER/CLIENT tag in docs]

```text
UiSoundLoop(path, [volume], [pitch])

Arguments

path (string) – Path to looping sound file (OGG format)

volume (number, optional) – Playback volume. Default 1.0

pitch (number, optional) – Playback pitch. Default 1.0

Return value

none

Call this continuously to keep playing loop.
UI sounds are not affected by acoustics simulation. Use LoadLoop / PlayLoop for that.
```

### GetLastSound  [no SERVER/CLIENT tag in docs]

```text
volume, position = GetLastSound()

Arguments

none

Return value

volume (number) – Volume of loudest sound played last frame

position (TVec) – World position of loudest sound played last frame
```

## 8. Particles

Section intro (api.html "Particles"), verbatim:

```text
Functions to configure and emit particles, used for fire, smoke and other visual effects. There are
two types of particles in Teardown - plain particles and smoke particles. Plain particles are simple
billboard particles simulated with gravity and velocity that can be used for fire, debris, rain, snow and such.
Smoke particles are only intended for smoke and they are simulated with fluid dynamics internally and rendered
with some special tricks to get a more smoke-like appearance.

All functions in the particle API, except for SpawnParticle modify properties in the particle state, which is
then used when emitting particles, so the idea is to set up a state, and then emit one or several particles
using that state.

Most properties in the particle state can be either constant or animated over time. Supply a single argument
for constant, two argument for linear interpolation, and optionally a third argument for other types of
interpolation. There are also fade in and fade out parameters that fade from and to zero.
```

### ParticleReset  [no SERVER/CLIENT tag in docs]

```text
ParticleReset()

Arguments

none

Return value

none

Reset to default particle state, which is a plain, white particle of radius 0.5.
Collision is enabled and it alpha animates from 1 to 0.
```

Doc example (verbatim):

```lua
function client.init()
	ParticleReset()
end
```

### ParticleType  [no SERVER/CLIENT tag in docs]

```text
ParticleType(type)

Arguments

type (string) – Type of particle. Can be "smoke" or "plain".

Return value

none

Set type of particle
```

Doc example (verbatim):

```lua
function client.init()
	ParticleType("smoke")
end
```

### ParticleColor  [no SERVER/CLIENT tag in docs]

```text
ParticleColor(r0, g0, b0, [r1], [g1], [b1])

Arguments

r0 (number) – Red value

g0 (number) – Green value

b0 (number) – Blue value

r1 (number, optional) – Red value at end

g1 (number, optional) – Green value at end

b1 (number, optional) – Blue value at end

Return value

none

Set particle color to either constant (three arguments) or linear interpolation (six arguments)
```

Doc example (verbatim):

```lua
function client.init()
	--Constant red
	ParticleColor(1,0,0)

	--Animating from yellow to red
	ParticleColor(1,1,0, 1,0,0)
end
```

### ParticleRadius  [no SERVER/CLIENT tag in docs]

```text
ParticleRadius(r0, [r1], [interpolation], [fadein], [fadeout])

Arguments

r0 (number) – Radius

r1 (number, optional) – End radius

interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.

fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.

fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

Return value

none

Set the particle radius. Max radius for smoke particles is 1.0.
```

Doc example (verbatim):

```lua
function client.init()
	--Constant radius 0.4 meters
	ParticleRadius(0.4)

	--Interpolate from small to large
	ParticleRadius(0.1, 0.7)
end
```

### ParticleGravity  [no SERVER/CLIENT tag in docs]

```text
ParticleGravity(g0, [g1], [interpolation], [fadein], [fadeout])

Arguments

g0 (number) – Gravity

g1 (number, optional) – End gravity

interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.

fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.

fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

Return value

none

Set particle gravity. It will be applied along the world Y axis. A negative value will move the particle downwards.
```

Doc example (verbatim):

```lua
function client.init()
	--Move particles slowly upwards
	ParticleGravity(2)
end
```

### ParticleAlpha  [no SERVER/CLIENT tag in docs]

```text
ParticleAlpha(a0, [a1], [interpolation], [fadein], [fadeout])

Arguments

a0 (number) – Alpha (0.0 - 1.0)

a1 (number, optional) – End alpha (0.0 - 1.0)

interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.

fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.

fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

Return value

none

Set the particle alpha (opacity).
```

Doc example (verbatim):

```lua
function client.init()
	--Interpolate from opaque to transparent
	ParticleAlpha(1.0, 0.0)
end
```

### SpawnParticle  [no SERVER/CLIENT tag in docs]

```text
SpawnParticle(pos, velocity, lifetime)

Arguments

pos (TVec) – World space point as vector

velocity (TVec) – World space velocity as vector

lifetime (number) – Particle lifetime in seconds

Return value

none

Spawn particle using the previously set up particle state. You can call this multiple times
using the same particle state, but with different position, velocity and lifetime. You can
also modify individual properties in the particle state in between calls to to this function.
```

Doc example (verbatim):

```lua
function client.tick()
	ParticleReset()
	ParticleType("smoke")
	ParticleColor(0.7, 0.6, 0.5)
	--Spawn particle at world origo with upwards velocity and a lifetime of ten seconds
	SpawnParticle(Vec(0, 5, 0), Vec(0, 1, 0), 10.0)
end
```

Other particle-state functions in api.html (signatures only; full text via the doc):

- `ParticleTile(type)`  [no tag]
- `ParticleDrag(d0, [d1], [interpolation], [fadein], [fadeout])`  [no tag]
- `ParticleEmissive(d0, [d1], [interpolation], [fadein], [fadeout])`  [no tag]
- `ParticleRotation(r0, [r1], [interpolation], [fadein], [fadeout])`  [no tag]
- `ParticleStretch(s0, [s1], [interpolation], [fadein], [fadeout])`  [no tag]
- `ParticleSticky(s0, [s1], [interpolation], [fadein], [fadeout])`  [no tag]
- `ParticleCollide(c0, [c1], [interpolation], [fadein], [fadeout])`  [no tag]
- `ParticleFlags(bitmask)`  [no tag]

## 9. Player

### GetPlayerTransform  [no SERVER/CLIENT tag in docs]

```text
transform = GetPlayerTransform([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

transform (TTransform) – Current player transform

The player transform is located at the bottom of the player. The player transform
considers heading (looking left and right). Forward is along negative Z axis.
Player pitch (looking up and down) does not affect player transform.
If you want the transform of the eye, use GetPlayerCameraTransform() instead.
```

Doc example (verbatim):

```lua
function client.init()
	local t = GetPlayerTransform()
	DebugPrint(TransformStr(t))
end
```

### SetPlayerTransform  [SERVER ONLY]

```text
SetPlayerTransform(transform, [playerId])

Arguments

transform (TTransform) – Desired player transform

playerId (number, optional) – Player ID. On server, zero means server (host) player.

Return value

none

Instantly teleport the player to desired transform, excluding pitch.
If you want to include pitch, use SetPlayerTransformWithPitch instead.
Player velocity will be reset to zero.
```

Doc example (verbatim):

```lua
function server.tick()
	if InputPressed("jump", playerId) then
		local t = Transform(Vec(50, 0, 0), QuatEuler(0, 90, 0))
		SetPlayerTransform(t, playerId)
	end
end
```

### IsPlayerGrounded  [no SERVER/CLIENT tag in docs]

```text
isGrounded = IsPlayerGrounded([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

isGrounded (boolean) – Whether the player is grounded
```

Doc example (verbatim):

```lua
local isGrounded = IsPlayerGrounded()
```

### GetPlayerGrabShape  [no SERVER/CLIENT tag in docs]

```text
handle = GetPlayerGrabShape([playerId])

Arguments

playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.

Return value

handle (number) – Handle to grabbed shape or zero if not grabbing.
```

Doc example (verbatim):

```lua
function client.tick()
	local shape = GetPlayerGrabShape()
	if shape ~= 0 then
		DebugPrint("Player is grabbing a shape")
	end
end
```

### SetPlayerWalkingSpeed  [SERVER ONLY]

```text
SetPlayerWalkingSpeed(speed, [playerId])

Arguments

speed (number) – Set player walking speed

playerId (number, optional) – Player ID. On server, zero means server (host) player.

Return value

none

This function sets base speed, but real player speed depends on many
factors such as health, crouch, water, grabbing objects.
```

Doc example (verbatim):

```lua
function server.tick()

	for p in Players() do
		-- Set player walking speed based on whether shift is pressed
		if InputDown("shift", p) then
			SetPlayerWalkingSpeed(15.0, p)
		else
			SetPlayerWalkingSpeed(7.0, p)
		end
	end
end
```

### SetPlayerSpawnTool  [SERVER ONLY]

```text
SetPlayerSpawnTool(id, [playerId])

Arguments

id (string) – Tool unique identifier

playerId (number, optional) – Player ID. On server, zero means server (host) player.

Return value

none

Call this function during init to alter the player spawn active tool.
```

Doc example (verbatim):

```lua
function playerJoined(playerId)
	SetPlayerSpawnTool("pistol", playerId)
end
```

### SetPlayerSpawnHealth  [SERVER ONLY]

```text
SetPlayerSpawnHealth(health, [playerId])

Arguments

health (number) – Desired player spawn health (between zero and one)

playerId (number, optional) – Player ID. On server, zero means server (host) player.

Return value

none

Call this function during init to alter the player spawn health amount.
```

Doc example (verbatim):

```lua
function playerJoined(playerId)
	SetPlayerSpawnHealth(0.5, playerId)
end
```

