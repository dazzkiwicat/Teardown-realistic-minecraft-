# Teardown modding docs: verbatim notes

Sources (all fetched 2026-10-06 and saved under the scratchpad dir):

- https://teardowngame.com/modding/api.html  -> saved as `api.html` (title: **"Teardown scripting API (2.1.0)"**)
- https://teardowngame.com/modding/  -> saved as `index.html` (Markdeep source; this is the only prose page: mod folder, editor, MagicaVoxel, callbacks)
- https://www.teardowngame.com/modding/api.xml (machine-readable API listing, linked from the index)
- https://www.teardowngame.com/modding/images/teardown_palette.png and https://www.teardowngame.com/modding/downloadable/teardown_palette.vox (the palette image/file the Materials docs point to)
- Screenshots referenced by the index page and read by eye: `images/mod_path.jpg`, `editor_help.png`, `editor_help_tooltip.png`, `editor_properties.png`, `editor_scene_explorer_1.png`, `minus_layer.png`, `editor_tags_2.png`, `search_window.jpg` (transcribed in section 3c)
- Probed and not existing (HTTP 404): `modding/editor.html`, `xml.html`, `environment.html`, `materials.html`, `level.html`. The index links to no other documentation pages than api.html / api.xml.

Function blocks below are machine-extracted from `api.html` and reproduced verbatim (signature line, Arguments, Return value, description, doc example). The "(SERVER ONLY)" etc. labels are the doc's own function tags. Text from the index page is quoted with `>`.

## Read this first: gaps and caveats found in the docs

1. **The docs describe the 2.x client/server API.** `api.html` is version 2.1.0. Its callbacks are `server.init/tick/update/postUpdate/destroy` and `client.init/tick/update/postUpdate/draw/render/destroy`. The index page still documents the older global `init()/tick(dt)/update(dt)/draw(dt)`, and one example in api.html (`HasVersion`) still uses a global `function init()`. The docs never say explicitly which style a script must use or whether the global style is still run. See "Level script lifecycle".
2. **Many functions take a `playerId`.** In the 2.x docs most player functions have an optional `playerId` argument (see the Player section). On the client, `0` means the local player; on the server `0` means the server (host) player.
3. **Some functions are SERVER ONLY** (e.g. `MakeHole`, `Explosion`, `SetEnvironmentProperty`, `SetPlayerSpawnTransform`...). The doc tag is printed next to each name below. Rendering/UI functions (`Ui*`) can only be called from `client.draw()` (or global `draw()` in the old style).
4. **NOT in the public docs as written text:** the XML element/attribute reference (`<scene>`, `<environment>`, `<spawnpoint>`, `<body>`, `<vox>`, `<voxbox>`, `<boundary>`, `<script>`, `<prefab>`, `<location>`, `<trigger>`, `<light>`), the list of environment property keys, the built-in tag list, and a textual palette-index-to-material table. The index page explicitly says the editor's built-in Help and property tooltips are the authority for those (quoted under "XML / level format"). Those headings below say NOT FOUND IN DOCS and list only the fragments that do appear. Section 3c transcribes what the docs' own screenshots show (the `[vox]` node's property names and defaults, node type names).
5. **`VecDist` does not exist in the docs.** Use `VecLength(VecSub(a, b))`.
6. The doc itself contains typos that matter when copying strings: `QueryPath` type is spelled `"standart"` (not "standard").

# 1. Level script lifecycle: init, tick, update, draw

## 1a. api.html 2.1.0 (client/server)

Verbatim intro text from api.html:

```
Teardown uses Lua version 5.1 as scripting language. The Lua 5.1 reference manual can be found here.
Each Teardown script runs in its own Lua context and can only interact with the engine and other scripts
through API functions and the registry. The registry is a database of hierarchical global variables that is used both internally
in the engine, for communication between scripts and as a way to save persistent data.

The Teardown API uses only native lua types. Handles to objects are plain Lua numbers. Vector types are represented
as plain Lua tables, and so on. 

Starting with version 2.0, the Teardown API supports networked multiplayer using a client/server architecture.
The same script runs both on the server and on each client, but different parts of the script are used. This is implemented 
through the server and client tables. Teardown does not use dedicated servers, so the player hosting a session will be 
the server for that session while also acting as one of the clients. Hence, the host is both the server and one of the clients,
while everyone else is just a client.

[table: reproduced below]

Each script has the following server callback functions that will be called by the game engine. Note that all of them
are optional. In many cases, you will only need the init and tick. Most of the game logic should be implemented on the server.

[table: reproduced below]

The following optional callback functions are available on the client. The client part of a script is typically used for overlay graphics
and user interfaces, but it can also be used for optimization purposes to spawn local particle effects, sounds or animations.

[table: reproduced below]
```

Server callbacks table (verbatim cells):

| Function | Description |
|---|---|
| `function server.init()` | Called once at load time |
| `function server.tick(dt)` | Called exactly once per frame. The time step is variable but always between 0.0 and 0.0333333 |
| `function server.update(dt)` | Called at a fixed update rate, but at the most two times per frame. Time step is always 0.0166667 (60 updates per second). Depending on frame rate it might not be called at all for a particular frame. |
| `function server.postUpdate()` | Called like update, but after physics. Because update can trigger physics updates, it can be necessary to do some additional calculations afterwards. |
| `function server.destroy()` | For game mode scripts, this is called when the game mode is stopped |

Client callbacks table (verbatim cells):

| Function | Description |
|---|---|
| `function client.init()` | Called once at load time |
| `function client.tick(dt)` | Called exactly once per frame. The time step is variable but always between 0.0 and 0.0333333 |
| `function client.update(dt)` | Called at a fixed update rate, but at the most two times per frame. Time step is always 0.0166667 (60 updates per second). Depending on frame rate it might not be called at all for a particular frame. |
| `function client.postUpdate()` | Called like update, but after physics. Because update can trigger physics updates, it can be necessary to do some additional calculations afterwards. This is usually used by animators. |
| `function client.draw()` | Called when the 2D overlay is being draw, after the scene but before the standard HUD. Ui functions can only be used from this callback. |
| `function client.render(dt)` | Called exactly once per frame, right before things are actually drawn to the screen. |
| `function client.destroy()` | For game mode scripts, this is called when the game mode is stopped |

Built-in tables (verbatim cells):

| Function | Description |
|---|---|
| `server` | Only exists on the server. You can put your own global variables in here, but they will only be available on the server. |
| `client` | This is similar to the server table, but only exists on clients. |
| `shared` | Automatically synchronized data from server to client parts of the same script. Read-only from the client part of the script. The server can put any data type in the shared table, including tables, but having a lot of data that changes often can consume a lot of bandwith. |

## 1b. modding index page: Game Callback Functions (older global-function style)

> ## Game Callback Functions
> The Teardown mod scripts are called by the game using callback functions that are invoked from the main game and the game loop. A script can choose to implement one or more of the functions described below depending on purpose of the script.
>
> During a game frame the `tick()` callback is called first. It is followed by zero, one or two calls to `update()` depending on frame rate. The `draw()` function is called once at the end of the frame. User input should be handled in `tick()` and never in `update()`. This is to avoid missing out or getting double input during a frame due to changes in the frame rate. The delta-time (`dt`) variable passed to `tick(dt)`, `update(dt)`, and `draw(dt)` contains the amount of time passed in the last rendered frame. This is usually used to scale effects in the game. Such as a body which should move 1 meter per frame should have its movement set to 1 * `dt`.
>
> #### init()
> The init function is called once and only once at load time. This is a good place to configure initial states and values. 
>
> #### tick(dt)
> The tick function is called once per frame. The time step is variable but always between 0.0 and 0.0333333 seconds.
>
> #### update(dt)
> The update function is called at a fixed update rate, but at the most two times per frame. Time step is always 0.0166667 (60 updates per second). Depending on frame rate it might not be called at all for a particular frame.
>
> #### draw(dt)
> The draw callback function is called when the 2D overlay is being draw, after the scene but before the standard HUD. The API User Interface functions can only be used from this callback.

### The difference between tick and update (as stated by the docs)

- `tick(dt)`: "called once per frame. The time step is variable but always between 0.0 and 0.0333333 seconds." (api.html: "Called exactly once per frame.")
- `update(dt)`: "called at a fixed update rate, but at the most two times per frame. Time step is always 0.0166667 (60 updates per second). Depending on frame rate it might not be called at all for a particular frame."
- Order within a frame: "During a game frame the `tick()` callback is called first. It is followed by zero, one or two calls to `update()` depending on frame rate. The `draw()` function is called once at the end of the frame."
- Input: "User input should be handled in `tick()` and never in `update()`."
- `postUpdate()` (api.html): "Called like update, but after physics. Because update can trigger physics updates, it can be necessary to do some additional calculations afterwards."
- `draw`: "Called when the 2D overlay is being draw, after the scene but before the standard HUD. Ui functions can only be called from this callback."

### Parameters (script parameters from level XML), verbatim

```
Scripts can have parameters defined in the level XML file. These serve as
input to a specific instance of the script and can be used to configure
various options and parameters of the script. While these parameters can
be read at any time in the script, it's recommended to copy them to a global
variable in or outside the init function.
```

### GetIntParam

```
value = GetIntParam(name, default)
```

Arguments
name (string) – Parameter name
default (number) – Default parameter value
Return value
value (number) – Parameter value

Doc example:
```lua
--Retrieve blinkcount parameter, or set to 5 if omitted
parameterBlinkCount = GetIntParam("blinkcount", 5)

function init()
	DebugPrint(parameterBlinkCount)
end
```

### GetFloatParam

```
value = GetFloatParam(name, default)
```

Arguments
name (string) – Parameter name
default (number) – Default parameter value
Return value
value (number) – Parameter value

Doc example:
```lua
--Retrieve speed parameter, or set to 10.0 if omitted
parameterSpeed = GetFloatParam("speed", 10.0)

function init()
	DebugPrint(parameterSpeed)
end
```

### GetBoolParam

```
value = GetBoolParam(name, default)
```

Arguments
name (string) – Parameter name
default (boolean) – Default parameter value
Return value
value (boolean) – Parameter value

Doc example:
```lua
--Retrieve playsound parameter, or false if omitted
parameterPlaySound = GetBoolParam("playsound", false)


function init()
	DebugPrint(parameterPlaySound)
end
```

### GetStringParam

```
value = GetStringParam(name, default)
```

Arguments
name (string) – Parameter name
default (string) – Default parameter value
Return value
value (string) – Parameter value

Doc example:
```lua
--Retrieve mode parameter, or "idle" if omitted
parameterMode = GetStringParam("mode", "idle")

function init()
	DebugPrint(parameterMode)
end
```


# 2. Lua API functions

## MakeHole (and which materials are soft / medium / hard)

### MakeHole (SERVER ONLY)

```
count = MakeHole(position, r0, [r1], [r2], [silent])
```

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

Doc example:
```lua
function server.init()
	MakeHole(Vec(0, 0, 0), 5.0, 1.0)
end
```

Related index-page hardness table (see section 4b): Soft = Glass, Grass, Dirt, Plastic, Wood, Plaster; Medium = Concrete, Brick, Weak Metal; Hard = Hard Masonry, Hard Metal; Unbreakable = Heavy Metal, Rock. The MakeHole doc lists only soft, medium and hard; it says nothing about rock/heavy metal (they are not listed under any radius).

### Explosion (SERVER ONLY)

```
Explosion(pos, size, [instigatingPlayerId])
```

Arguments
pos (TVec) – Position in world space as vector
size (number) – Explosion size from 0.5 to 4.0
instigatingPlayerId (number, optional) – Instigating player ID.
Return value
none

Doc example:
```lua
function server.init()
	Explosion(Vec(0, 5, 0), 1)
end
```

### SpawnFire (SERVER ONLY)

```
SpawnFire(pos)
```

Arguments
pos (TVec) – Position in world space as vector
Return value
none

Doc example:
```lua
function server.tick()
	SpawnFire(Vec(0, 2, 0))
end
```


## Spawn (and the XML root element a spawnable file needs)

Functions to spawn entities in the scene. The Spawn function can spawn prefabs from file or xml.

### Spawn

```
entities = Spawn(xml, transform, [allowStatic], [jointExisting])
```

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

Doc example:
```lua
function server.init()
	Spawn("MOD/prefab/mycar.xml", Transform(Vec(0, 5, 0)))
	Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", Transform(Vec(0, 10, 0)))
end
```

### SpawnLayer

```
entities = SpawnLayer(xml, layer, transform, [allowStatic], [jointExisting])
```

Arguments
xml (string) – File name or xml string
layer (string) – Vox layer name
transform (TTransform) – Spawn transform
allowStatic (boolean, optional) – Allow spawning static shapes and bodies (default false)
jointExisting (boolean, optional) – Allow joints to connect to existing scene geometry (default false)
Return value
entities (table) – Indexed table with handles to all spawned entities
Same functionality as Spawn(), except using a specific layer in the vox-file

Doc example:
```lua
function server.init()
	Spawn("MOD/prefab/mycar.xml", "some_vox_layer", Transform(Vec(0, 5, 0)))
	Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", "some_vox_layer", Transform(Vec(0, 10, 0)))
end
```

**Root element of a spawnable file: NOT FOUND IN DOCS.** The only statements in the docs are:

- Spawn: "The first argument can be either a prefab XML file in your mod folder or a string with XML content."
- Index page, Prefabs: "If you right-click a group in the scene explorer, you can convert it to a prefab. This will save out the group as a separate XML file, and you can then place multiple copies of the same prefab in the level using instances."
- Index page, Spawnable assets: "In order to export an asset, you must first convert it to a prefab, so the asset has a separate XML file."
- The Spawn doc example passes a bare `<voxbox .../>` string (no `<prefab>` wrapper): `Spawn("<voxbox size='10 10 10' prop='true' material='wood'/>", Transform(Vec(0, 10, 0)))`.

The docs never write the literal string `<prefab>` as a root element.


## Pathfinding: QueryPath, GetPathState, GetPathLength, GetPathPoint, AbortPath

### QueryPath

```
QueryPath(start, end, [maxDist], [targetRadius], [type])
```

Arguments
start (TVec) – World space start point
end (TVec) – World space target point
maxDist (number, optional) – Maximum path length before giving up. Default is infinite.
targetRadius (number, optional) – Maximum allowed distance to target in meters. Default is 2.0
type (string, optional) – Type of path. Can be "low", "standart", "water", "flying". Default is "standart"
Return value
none
Initiate path planning query. The result will run asynchronously as long as GetPathState
returns "busy". An ongoing path query can be aborted with AbortPath. The path planning query
will use the currently set up query filter, just like the other query functions.
Using the 'water' type allows you to build a path within the water.
The 'flying' type builds a path in the entire three-dimensional space.

Doc example:
```lua
function client.init()
	QueryPath(Vec(-10, 0, 0), Vec(10, 0, 0))
end
```

### GetPathState

```
state = GetPathState([id])
```

Arguments
id (number, optional) – Path planner id. Default value is 0.
Return value
state (string) – Current path planning state
Return the current state of the last path planning query.
 State  |  Description
idle	 |  No recent query
busy	 |  Busy computing. No path found yet.
fail	 |  Failed to find path. You can still get the resulting path (even though it won't reach the target).
done	 |  Path planning completed and a path was found. Get it with GetPathLength and GetPathPoint)

Doc example:
```lua
function server.init()
	QueryPath(Vec(-10, 0, 0), Vec(10, 0, 0))
end

function server.tick()
	local s = GetPathState()
	if s == "done" then
		DebugPrint("done")
	end
end
```

### GetPathLength

```
length = GetPathLength([id])
```

Arguments
id (number, optional) – Path planner id. Default value is 0.
Return value
length (number) – Length of last path planning result (in meters)
Return the path length of the most recently computed path query. Note that the result can often be retrieved even
if the path query failed. If the target point couldn't be reached, the path endpoint will be the point closest
to the target.

Doc example:
```lua
function server.init()
	QueryPath(Vec(-10, 0, 0), Vec(10, 0, 0))
end

function server.tick()
	local s = GetPathState()
	if s == "done" then
		DebugPrint("done " .. GetPathLength())
	end
end
```

### GetPathPoint

```
point = GetPathPoint(dist, [id])
```

Arguments
dist (number) – The distance along path. Should be between zero and result from GetPathLength()
id (number, optional) – Path planner id. Default value is 0.
Return value
point (TVec) – The path point dist meters along the path
Return a point along the path for the most recently computed path query. Note that the result can often be retrieved even
if the path query failed. If the target point couldn't be reached, the path endpoint will be the point closest
to the target.

Doc example:
```lua
function client.init()
	QueryPath(Vec(-10, 0, 0), Vec(10, 0, 0))
end

function client.tick()
	local d = 0
	local l = GetPathLength()
	while d < l do
		DebugCross(GetPathPoint(d))
		d = d + 0.5
	end
end
```

### AbortPath

```
AbortPath([id])
```

Arguments
id (number, optional) – Path planner id. Default value is 0.
Return value
none
Abort current path query, regardless of what state it is currently in. This is a way to
save computing resources if the result of the current query is no longer of interest.

Doc example:
```lua
function server.init()
	QueryPath(Vec(-10, 0, 0), Vec(10, 0, 0))
	AbortPath()
end
```


## SetEnvironmentProperty / GetEnvironmentProperty: supported property keys

### SetEnvironmentDefault (SERVER ONLY)

```
SetEnvironmentDefault()
```

Arguments
none
Return value
none
Reset the environment properties to default. This is often useful before
setting up a custom environment.

Doc example:
```lua
function server.init()
	SetEnvironmentDefault()
end
```

### SetEnvironmentProperty (SERVER ONLY)

```
SetEnvironmentProperty(name, value0, [value1], [value2], [value3])
```

Arguments
name (string) – Property name
value0 (any) – Property value (type depends on property)
value1 (any, optional) – Extra property value (only some properties)
value2 (any, optional) – Extra property value (only some properties)
value3 (any, optional) – Extra property value (only some properties)
Return value
none
This function is used for manipulating the environment properties. The available properties are
exactly the same as in the editor, except for "snowonground" which is not currently supported.

Doc example:
```lua
function server.init()
	SetEnvironmentDefault()
	SetEnvironmentProperty("skybox", "cloudy.dds")
	SetEnvironmentProperty("rain", 0.7)
	SetEnvironmentProperty("fogcolor", 0.5, 0.5, 0.8)
	SetEnvironmentProperty("nightlight", false)
end
```

### GetEnvironmentProperty

```
value0, value1, value2, value3, value4 = GetEnvironmentProperty(name)
```

Arguments
name (string) – Property name
Return value
value0 (any) – Property value (type depends on property)
value1 (any) – Property value (only some properties)
value2 (any) – Property value (only some properties)
value3 (any) – Property value (only some properties)
value4 (any) – Property value (only some properties)
This function is used for querying the current environment properties. The available properties are
exactly the same as in the editor.

Doc example:
```lua
function client.init()
	local skyboxPath = GetEnvironmentProperty("skybox")
	local rainValue = GetEnvironmentProperty("rain")
	local r,g,b = GetEnvironmentProperty("fogcolor")
	local enabled = GetEnvironmentProperty("nightlight")
	DebugPrint(skyboxPath)
	DebugPrint(rainValue)
	DebugPrint(r .. " " .. g .. " " .. b)
	DebugPrint(enabled)
end
```

### Full list of environment property keys

**NOT FOUND IN DOCS.** Both functions say only: "The available properties are exactly the same as in the editor" (SetEnvironmentProperty adds: "...except for "snowonground" which is not currently supported."). There is no key table in api.html, api.xml or the index page. A text search of all three for `sunBrightness`, `skyboxbrightness`, `fogParams`, `ambient`, `exposure`, `sunColorTint`, `snowdir`, `wetness`, `puddleamount` returns zero hits.

The only key names that appear anywhere in the docs (all from the examples above), with the value types the examples use:

| Key | Value(s) used in doc example | Where |
|---|---|---|
| `"skybox"` | string, e.g. `"cloudy.dds"` | Set and Get examples |
| `"rain"` | number, e.g. `0.7` | Set and Get examples |
| `"fogcolor"` | three numbers `0.5, 0.5, 0.8` (Get returns `r,g,b`) | Set and Get examples |
| `"nightlight"` | boolean, e.g. `false` | Set and Get examples |
| `"snowonground"` | mentioned only as NOT supported by SetEnvironmentProperty | SetEnvironmentProperty description |

`nightlight` IS documented (boolean). `sunBrightness`, `skyboxbrightness`, `ambient`, `fogParams`: NOT FOUND IN DOCS. Index page pointer for where property info lives: "In addition to the Help window the Teardown Editor gives you context specific information when you hover the mouse pointer over a property. This feature is extremely useful and sometimes the only place where you can find information about a particular property." So the authoritative key list is the editor's `<environment>` property tooltips, which can be read by selecting the environment node in the Teardown editor.

Post-processing counterpart (same "exactly the same as in the editor" wording; only keys shown are `"saturation"` (1 number) and `"colorbalance"` (3 numbers)):

### SetPostProcessingProperty

```
SetPostProcessingProperty(name, value0, [value1], [value2])
```

Arguments
name (string) – Property name
value0 (number) – Property value
value1 (number, optional) – Extra property value (only some properties)
value2 (number, optional) – Extra property value (only some properties)
Return value
none
This function is used for manipulating the post processing properties. The available properties are
exactly the same as in the editor.

Doc example:
```lua
--Sepia post processing
function client.tick()
	SetPostProcessingProperty("saturation", 0.4)
	SetPostProcessingProperty("colorbalance", 1.3, 1.0, 0.7)
end
```

### GetPostProcessingProperty

```
value0, value1, value2 = GetPostProcessingProperty(name)
```

Arguments
name (string) – Property name
Return value
value0 (number) – Property value
value1 (number) – Property value (only some properties)
value2 (number) – Property value (only some properties)
This function is used for querying the current post processing properties.
The available properties are exactly the same as in the editor.

Doc example:
```lua
function client.tick()
	SetPostProcessingProperty("saturation", 0.4)
	SetPostProcessingProperty("colorbalance", 1.3, 1.0, 0.7)
	local saturation = GetPostProcessingProperty("saturation")
	local r,g,b = GetPostProcessingProperty("colorbalance")
	DebugPrint("saturation " .. saturation)
	DebugPrint("colorbalance " .. r .. " " .. g .. " " .. b)
end
```

### SetPostProcessingDefault

```
SetPostProcessingDefault()
```

Arguments
none
Return value
none
Reset the post processing properties to default.

Doc example:
```lua
function client.tick()
	SetPostProcessingProperty("saturation", 0.4)
	SetPostProcessingProperty("colorbalance", 1.3, 1.0, 0.7)
	SetPostProcessingDefault()
end
```


## Player functions

The player functions expose certain information about the player.

### GetPlayerTransform

```
transform = GetPlayerTransform([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
transform (TTransform) – Current player transform
The player transform is located at the bottom of the player. The player transform
considers heading (looking left and right). Forward is along negative Z axis.
Player pitch (looking up and down) does not affect player transform.
If you want the transform of the eye, use GetPlayerCameraTransform() instead.

Doc example:
```lua
function client.init()
	local t = GetPlayerTransform()
	DebugPrint(TransformStr(t))
end
```

### GetPlayerPos

```
position = GetPlayerPos([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
position (TVec) – Player center position
Return center point of player. This function is deprecated.
Use GetPlayerTransform instead.

Doc example:
```lua
function client.init()
	local p = GetPlayerPos()
	DebugPrint(p)

	--This is equivalent to
	p = VecAdd(GetPlayerTransform().pos, Vec(0,1,0))
	DebugPrint(p)
end
```

### GetPlayerVelocity

```
velocity = GetPlayerVelocity([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
velocity (TVec) – Player velocity in world space as vector

Doc example:
```lua
function client.tick()
	local vel = GetPlayerVelocity()
	DebugPrint(VecStr(vel))
end
```

### GetPlayerCameraTransform

```
transform = GetPlayerCameraTransform([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
transform (TTransform) – Current player camera transform
The player camera transform is usually the same as what you get from GetCameraTransform,
but if you have set a camera transform manually with SetCameraTransform, you can retrieve
the standard player camera transform with this function.

Doc example:
```lua
function client.init()
	local t = GetPlayerCameraTransform()
	DebugPrint(TransformStr(t))
end
```

### SetPlayerHealth (SERVER ONLY)

```
SetPlayerHealth(health, [playerId])
```

Arguments
health (number) – Set player health (between zero and one)
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none

Doc example:
```lua
function server.tick()
	if InputPressed("interact", playerId) then
		if GetPlayerHealth() < 0.75 then
			SetPlayerHealth(1.0, playerId)
		else
			SetPlayerHealth(0.5, playerId)
		end
	end
end
```

### GetPlayerHealth

```
health = GetPlayerHealth([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
health (number) – Current player health

Doc example:
```lua
function server.tick()
	if InputPressed("interact", playerId) then
		if GetPlayerHealth() < 0.75 then
			SetPlayerHealth(1.0, playerId)
		else
			SetPlayerHealth(0.5, playerId)
		end
	end
end
```

### RespawnPlayer (SERVER ONLY)

```
RespawnPlayer([playerId])
```

Arguments
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
Respawn player at spawn position without modifying the scene

Doc example:
```lua
function server.tick()
	for p in Players() do
		if InputPressed("interact", p) then
			RespawnPlayer(p)
		end
	end
end
```

Note: many doc examples iterate players with `for p in Players() do ... end`, but there is **no function entry for `Players`** in api.html (it is not in the function list; `GetAllPlayers`, `GetPlayerCount`, `GetLocalPlayer` are).


### Where the player starts / related player control (SetPlayerSpawnTransform and friends)

### SetPlayerSpawnTransform (SERVER ONLY)

```
SetPlayerSpawnTransform(transform, [playerId])
```

Arguments
transform (TTransform) – Desired player spawn transform
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
Call this function during init to alter the player spawn transform.

Doc example:
```lua
function setPlayerSpawnTransform(playerId)
	local t = Transform(Vec(10, 0, 0), QuatEuler(0, 90, 0))
	SetPlayerSpawnTransform(t, playerId)
end
```

### SetPlayerSpawnHealth (SERVER ONLY)

```
SetPlayerSpawnHealth(health, [playerId])
```

Arguments
health (number) – Desired player spawn health (between zero and one)
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
Call this function during init to alter the player spawn health amount.

Doc example:
```lua
function playerJoined(playerId)
	SetPlayerSpawnHealth(0.5, playerId)
end
```

### SetPlayerSpawnTool (SERVER ONLY)

```
SetPlayerSpawnTool(id, [playerId])
```

Arguments
id (string) – Tool unique identifier
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
Call this function during init to alter the player spawn active tool.

Doc example:
```lua
function playerJoined(playerId)
	SetPlayerSpawnTool("pistol", playerId)
end
```

### RespawnPlayerAtTransform (SERVER ONLY)

```
RespawnPlayerAtTransform(transform, [playerId])
```

Arguments
transform (transform) – Transform
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
Respawn player at spawn position without modifying the scene

Doc example:
```lua
function server.tick()
	for p in Players() do
		if InputPressed("interact", p) then
			RespawnPlayerAtTransform(Transform(Vec(1,2,3)), p)
		end
	end
end
```

### SetPlayerTransform (SERVER ONLY)

```
SetPlayerTransform(transform, [playerId])
```

Arguments
transform (TTransform) – Desired player transform
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
Instantly teleport the player to desired transform, excluding pitch.
If you want to include pitch, use SetPlayerTransformWithPitch instead.
Player velocity will be reset to zero.

Doc example:
```lua
function server.tick()
	if InputPressed("jump", playerId) then
		local t = Transform(Vec(50, 0, 0), QuatEuler(0, 90, 0))
		SetPlayerTransform(t, playerId)
	end
end
```

### SetPlayerVelocity (SERVER ONLY)

```
SetPlayerVelocity(velocity, [playerId])
```

Arguments
velocity (TVec) – Player velocity in world space as vector
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none

Doc example:
```lua
function server.tick()
	if InputPressed("jump", playerId) then
		SetPlayerVelocity(Vec(0, 5, 0), playerId)
	end
end
```

### ApplyPlayerDamage (SERVER ONLY)

```
ApplyPlayerDamage(targetPlayerId, damage, [cause], [instigatingPlayerId])
```

Arguments
targetPlayerId (number) – Target player ID
damage (number) – Damage to apply to target player
cause (string, optional) – The cause of damage
instigatingPlayerId (number, optional) – Instigating player ID.
Return value
none
Apply damage to a player. Instigating player ID could be used to correctly
attribute the "score" to a player.

Doc example:
```lua
function server.tick(dt)
	
	for player in Players() do
		if isOnFire(player) then
			-- Apply 20% of dt as damage to the player
			ApplyPlayerDamage(player, 0.2 * dt, "fire")
		end
	end
	
	-- or

	for player in Players() do
		if InputIsPressed("usetool", player) then
			for target in Players() do
				if target ~= player and isInRange(player, target) then
					-- Apply 50% damage to the target player
					ApplyPlayerDamage(target, 0.5, "tool", player)
				end
			end
		end
	end
end
```

### GetLocalPlayer

```
GetLocalPlayer = GetLocalPlayer()
```

Arguments
none
Return value
GetLocalPlayer (number) – Local player ID.

Doc example:
```lua
local p = GetLocalPlayer()
```

### GetAllPlayers

```
name = GetAllPlayers()
```

Arguments
none
Return value
name (list) – List of all player Ids

Doc example:
```lua
local playerIds = GetAllPlayers()
```

### GetPlayerEyeTransform

```
transform = GetPlayerEyeTransform([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
transform (TTransform) – Current player eye transform
The player eye transform is the same as what you get from GetCameraTransform when playing in first-person,
but if you have set a camera transform manually with SetCameraTransform or playing in third-person, you can retrieve
the player eye transform with this function.

Doc example:
```lua
function client.init()
	local t = GetPlayerEyeTransform()
	DebugPrint(TransformStr(t))
end
```

### SetPlayerWalkingSpeed (SERVER ONLY)

```
SetPlayerWalkingSpeed(speed, [playerId])
```

Arguments
speed (number) – Set player walking speed
playerId (number, optional) – Player ID. On server, zero means server (host) player.
Return value
none
This function sets base speed, but real player speed depends on many
factors such as health, crouch, water, grabbing objects.

Doc example:
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

### DisablePlayerDamage (SERVER ONLY)

```
DisablePlayerDamage(playerId)
```

Arguments
playerId (number) – Player for which damage should be disabled
Return value
none
Disables the player from any incoming damage, such as explosions, gun shots, or drowning.

Doc example:
```lua
function server.tick()
	for i=1,#invulnerablePlayers do
		DisablePlayerDamage(invulnerablePlayers[i])
	end
end
```

**`<spawnpoint>` XML element: NOT FOUND IN DOCS** (no mention of the string "spawnpoint" in any fetched page; confirm with `grep -c spawnpoint`).


## Body functions

A body represents a rigid body in the scene. It can be either static or dynamic. Only dynamic bodies are
affected by physics.

### GetBodyTransform

```
transform = GetBodyTransform(handle)
```

Arguments
handle (number) – Body handle
Return value
transform (TTransform) – Transform of the body

Doc example:
```lua
function init()
	local handle = FindBody("target", true)
	local t = GetBodyTransform(handle)
	DebugPrint(TransformStr(t))
end
```

### SetBodyTransform

```
SetBodyTransform(handle, transform)
```

Arguments
handle (number) – Body handle
transform (TTransform) – Desired transform
Return value
none

Doc example:
```lua
function init()
	local handle = FindBody("body", true)

	--Move a body 1 meter upwards
	local t = GetBodyTransform(handle)
	t.pos = VecAdd(t.pos, Vec(0, 3, 0))
	SetBodyTransform(handle, t)
end
```

### GetBodyVelocity

```
velocity = GetBodyVelocity(handle)
```

Arguments
handle (number) – Body handle (should be a dynamic body)
Return value
velocity (TVec) – Linear velocity as vector

Doc example:
```lua
handle = 0
function server.init()
	handle = FindBody("body", true)
	local vel = Vec(0,10,0)
	SetBodyVelocity(handle, vel)
end

function client.init()
	handle = FindBody("body", true)
end

function client.tick()
	DebugPrint(VecStr(GetBodyVelocity(handle)))
end
```

### SetBodyVelocity

```
SetBodyVelocity(handle, velocity)
```

Arguments
handle (number) – Body handle (should be a dynamic body)
velocity (TVec) – Vector with linear velocity
Return value
none
This can be used for animating bodies with preserved physical interaction,
but in most cases you are better off with a motorized joint instead.

Doc example:
```lua
function init()
	local handle = FindBody("body", true)
	local vel = Vec(0,10,0)
	SetBodyVelocity(handle, vel)
end
```

### SetBodyDynamic

```
SetBodyDynamic(handle, dynamic)
```

Arguments
handle (number) – Body handle
dynamic (boolean) – True for dynamic. False for static.
Return value
none
Change the dynamic state of a body. There is very limited use for this
function. In most situations you should leave it up to the engine to decide.
Use with caution.

Doc example:
```lua
function init()
	local handle = FindBody("body", true)
	SetBodyDynamic(handle, false)
	DebugPrint(IsBodyDynamic(handle))
end
```

### IsBodyActive

```
active = IsBodyActive(handle)
```

Arguments
handle (number) – Body handle
Return value
active (boolean) – Return true if body is active
Check if body is body is currently simulated. For performance reasons,
bodies that don't move are taken out of the simulation. This function
can be used to query the active state of a specific body. Only dynamic
bodies can be active.

Doc example:
```lua
-- try to break the body to see the logs
function client.tick()
	handle = FindBody("body", true)
	if IsBodyActive(handle) then
		DebugPrint("Body is active")
	end
end
```

### SetBodyActive

```
SetBodyActive(handle, active)
```

Arguments
handle (number) – Body handle
active (boolean) – Set to tru if body should be active (simulated)
Return value
none
This function makes it possible to manually activate and deactivate bodies to include or
exclude in simulation. The engine normally handles this automatically, so use with care.

Doc example:
```lua
handle = 0
function server.tick()
	handle = FindBody("body", true)

	-- Forces body to "sleep"
	SetBodyActive(handle, false)
end

function client.init()
	handle = FindBody("body", true)
end

function client.tick()
	handle = FindBody("body", true)

	if IsBodyActive(handle) then
		DebugPrint("Body is active")
	end
end
```

### GetBodyCenterOfMass

```
point = GetBodyCenterOfMass(handle)
```

Arguments
handle (number) – Body handle
Return value
point (TVec) – Vector representing local center of mass in body space

Doc example:
```lua
function client.init()
	handle = FindBody("body", true)
end

function client.tick()
	--Visualize center of mass on for body
	local com = GetBodyCenterOfMass(handle)
	local worldPoint = TransformToParentPoint(GetBodyTransform(handle), com)
	DebugCross(worldPoint)
end
```

### GetBodyBounds

```
min, max = GetBodyBounds(handle)
```

Arguments
handle (number) – Body handle
Return value
min (TVec) – Vector representing the AABB lower bound
max (TVec) – Vector representing the AABB upper bound
Return the world space, axis-aligned bounding box for a body.

Doc example:
```lua
function client.init()
	handle = FindBody("body", true)

	local min, max = GetBodyBounds(handle)
	local boundsSize = VecSub(max, min)
	local center = VecLerp(min, max, 0.5)
	DebugPrint(VecStr(boundsSize) .. " " .. VecStr(center))
end
```

### GetBodyShapes

```
list = GetBodyShapes(handle)
```

Arguments
handle (number) – Body handle
Return value
list (table) – Indexed table of shape handles
Return handles to all shapes owned by a body

Doc example:
```lua
function client.init()
	handle = FindBody("body", true)

	local shapes = GetBodyShapes(handle)
	for i=1,#shapes do
		local shape = shapes[i]
		DebugPrint(shape)
	end
end
```

### IsBodyBroken

```
broken = IsBodyBroken(handle)
```

Arguments
handle (number) – Body handle
Return value
broken (boolean) – Return true if body is broken
Determine if any shape of a body has been broken.

Doc example:
```lua
local handle = 0
function client.init()
	handle = FindBody("body", true)
end

function client.tick()
	DebugPrint(IsBodyBroken(handle))
end
```


### Related body functions (angular velocity, dynamic state, mass, forces)

### IsBodyDynamic

```
dynamic = IsBodyDynamic(handle)
```

Arguments
handle (number) – Body handle
Return value
dynamic (boolean) – Return true if body is dynamic
Check if body is dynamic. Note that something that was created static
may become dynamic due to destruction.

Doc example:
```lua
function init()
	local handle = FindBody("body", true)
	DebugPrint(IsBodyDynamic(handle))
end
```

### GetBodyAngularVelocity

```
angVel = GetBodyAngularVelocity(handle)
```

Arguments
handle (number) – Body handle (should be a dynamic body)
Return value
angVel (TVec) – Angular velocity as vector

Doc example:
```lua
handle = 0
function server.init()
	handle = FindBody("body", true)
	local angVel = Vec(0,100,0)
	SetBodyAngularVelocity(handle, angVel)
end

function client.init()
	handle = FindBody("body", true)
end

function client.tick()
	DebugPrint(VecStr(GetBodyAngularVelocity(handle)))
end
```

### SetBodyAngularVelocity

```
SetBodyAngularVelocity(handle, angVel)
```

Arguments
handle (number) – Body handle (should be a dynamic body)
angVel (TVec) – Vector with angular velocity
Return value
none
This can be used for animating bodies with preserved physical interaction,
but in most cases you are better off with a motorized joint instead.

Doc example:
```lua
function server.init()
	handle = FindBody("body", true)
	local angVel = Vec(0,100,0)
	SetBodyAngularVelocity(handle, angVel)
end
```

### GetBodyMass

```
mass = GetBodyMass(handle)
```

Arguments
handle (number) – Body handle
Return value
mass (number) – Body mass. Static bodies always return zero mass.

Doc example:
```lua
function init()
	local handle = FindBody("body", true)

	--Move a body 1 meter upwards
	local mass = GetBodyMass(handle)
	DebugPrint(mass)
end
```

### ApplyBodyImpulse

```
ApplyBodyImpulse(handle, position, impulse)
```

Arguments
handle (number) – Body handle (should be a dynamic body)
position (TVec) – World space position as vector
impulse (TVec) – World space impulse as vector
Return value
none
Apply impulse to dynamic body at position (give body a push).

Doc example:
```lua
function applyImpulse()
	handle = FindBody("body", true)

	local pos = Vec(0,1,0)
	local imp = Vec(0,0,10)
	ApplyBodyImpulse(handle, pos, imp)
end
```

### GetBodyVelocityAtPos

```
velocity = GetBodyVelocityAtPos(handle, pos)
```

Arguments
handle (number) – Body handle (should be a dynamic body)
pos (TVec) – World space point as vector
Return value
velocity (TVec) – Linear velocity on body at pos as vector
Return the velocity on a body taking both linear and angular velocity into account.

Doc example:
```lua
handle = 0
function server.init()
	handle = FindBody("body", true)
	local vel = Vec(0,10,0)
	SetBodyVelocity(handle, vel)
end

function client.init()
	handle = FindBody("body", true)
end

function client.tick()
	DebugPrint(VecStr(GetBodyVelocityAtPos(handle, Vec(0, 0, 0))))
end
```


## Constrain* (moving bodies smoothly)

### ConstrainPosition

```
ConstrainPosition(bodyA, bodyB, pointA, pointB, [maxVel], [maxImpulse])
```

Arguments
bodyA (number) – First body handle (zero for static)
bodyB (number) – Second body handle (zero for static)
pointA (TVec) – World space point for first body
pointB (TVec) – World space point for second body
maxVel (number, optional) – Maximum relative velocity (default: infinite)
maxImpulse (number, optional) – Maximum impulse (default: infinite)
Return value
none
This is a helper function that uses ConstrainVelocity to constrain a point on one
body to a point on another body while not affecting the bodies more than the provided
maximum relative velocity and maximum impulse. In other words: physically push on
the bodies so that pointA and pointB are aligned in world space. This is useful for
physically animating objects. This function should only be used from the update callback.

Doc example:
```lua
local handleA = 0
local handleB = 0
function server.init()
	handleA = FindBody("body", true)
	handleB = FindBody("target", true)
end

function server.update()
	--Constrain the origo of body a to an animated point in the world
	local worldPos = Vec(0, 3+math.sin(GetTime()), 0)
	ConstrainPosition(handleA, 0, GetBodyTransform(handleA).pos, worldPos)

	--Constrain the origo of body a to the origo of body b (like a ball joint)
	ConstrainPosition(handleA, handleA, GetBodyTransform(handleA).pos, GetBodyTransform(handleB).pos)
end
```

### ConstrainVelocity

```
ConstrainVelocity(bodyA, bodyB, point, dir, relVel, [min], [max])
```

Arguments
bodyA (number) – First body handle (zero for static)
bodyB (number) – Second body handle (zero for static)
point (TVec) – World space point
dir (TVec) – World space direction
relVel (number) – Desired relative velocity along the provided direction
min (number, optional) – Minimum impulse (default: -infinity)
max (number, optional) – Maximum impulse (default: infinity)
Return value
none
This will tell the physics solver to constrain the velocity between two bodies. The physics solver
will try to reach the desired goal, while not applying an impulse bigger than the min and max values.
This function should only be used from the update callback.

Doc example:
```lua
local handleA = 0
local handleB = 0
function server.init()
	handleA = FindBody("body", true)
	handleB = FindBody("target", true)
end

function server.update()
	--Constrain the velocity between bodies A and B so that the relative velocity
	--along the X axis at point (0, 5, 0) is always 3 m/s
	ConstrainVelocity(handleA, handleB, Vec(0, 5, 0), Vec(1, 0, 0), 3)
end
```

### ConstrainOrientation

```
ConstrainOrientation(bodyA, bodyB, quatA, quatB, [maxAngVel], [maxAngImpulse])
```

Arguments
bodyA (number) – First body handle (zero for static)
bodyB (number) – Second body handle (zero for static)
quatA (TQuat) – World space orientation for first body
quatB (TQuat) – World space orientation for second body
maxAngVel (number, optional) – Maximum relative angular velocity (default: infinite)
maxAngImpulse (number, optional) – Maximum angular impulse (default: infinite)
Return value
none
This is the angular counterpart to ConstrainPosition, a helper function that uses
ConstrainAngularVelocity to constrain the orientation of one body to the orientation
on another body while not affecting the bodies more than the provided maximum relative
angular velocity and maximum angular impulse. In other words: physically rotate the
bodies so that quatA and quatB are aligned in world space. This is useful for
physically animating objects. This function should only be used from the update callback.

Doc example:
```lua
local handleA = 0
local handleB = 0
function server.init()
	handleA = FindBody("body", true)
	handleB = FindBody("target", true)
end

function server.update()
	--Constrain the orietation of body a to an upright orientation in the world
	ConstrainOrientation(handleA, 0, GetBodyTransform(handleA).rot, Quat())

	--Constrain the orientation of body a to the orientation of body b
	ConstrainOrientation(handleA, handleB, GetBodyTransform(handleA).rot, GetBodyTransform(handleB).rot)
end
```

### ConstrainAngularVelocity

```
ConstrainAngularVelocity(bodyA, bodyB, dir, relAngVel, [min], [max])
```

Arguments
bodyA (number) – First body handle (zero for static)
bodyB (number) – Second body handle (zero for static)
dir (TVec) – World space direction
relAngVel (number) – Desired relative angular velocity along the provided direction
min (number, optional) – Minimum angular impulse (default: -infinity)
max (number, optional) – Maximum angular impulse (default: infinity)
Return value
none
This will tell the physics solver to constrain the angular velocity between two bodies. The physics solver
will try to reach the desired goal, while not applying an angular impulse bigger than the min and max values.
This function should only be used from the update callback.

Doc example:
```lua
local handleA = 0
local handleB = 0
function server.init()
	handleA = FindBody("body", true)
	handleB = FindBody("target", true)
end

function server.update()
	--Constrain the angular velocity between bodies A and B so that the relative angular velocity
	--along the Y axis is always 3 rad/s
	ConstrainAngularVelocity(handleA, handleB, Vec(1, 0, 0), 3)
end
```


## Shape functions

A shape is a voxel object and always owned by a body. A single body may contain multiple shapes. The transform
of shape is expressed in the parent body coordinate system.

### GetShapeLocalTransform

```
transform = GetShapeLocalTransform(handle)
```

Arguments
handle (number) – Shape handle
Return value
transform (TTransform) – Return shape transform in body space

Doc example:
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

### SetShapeLocalTransform

```
SetShapeLocalTransform(handle, transform)
```

Arguments
handle (number) – Shape handle
transform (TTransform) – Shape transform in body space
Return value
none

Doc example:
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

### GetShapeMaterialAtPosition

```
type, r, g, b, a, entry = GetShapeMaterialAtPosition(handle, pos, [includeUnphysical])
```

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

Doc example:
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

### GetShapeSize

```
xsize, ysize, zsize, scale = GetShapeSize(handle)
```

Arguments
handle (number) – Shape handle
Return value
xsize (number) – Size in voxels along x axis
ysize (number) – Size in voxels along y axis
zsize (number) – Size in voxels along z axis
scale (number) – The size of one voxel in meters (with default scale it is 0.1)
Return the size of a shape in voxels

Doc example:
```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
	local x, y, z = GetShapeSize(shape)
	DebugPrint("Shape size: " .. x .. ";" .. y .. ";" .. z)
end
```

### GetShapeVoxelCount

```
count = GetShapeVoxelCount(handle)
```

Arguments
handle (number) – Shape handle
Return value
count (number) – Number of voxels in shape
Return the number of voxels in a shape, not including empty space

Doc example:
```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
	local voxelCount = GetShapeVoxelCount(shape)
	DebugPrint(voxelCount)
end
```

### IsShapeBroken

```
broken = IsShapeBroken(handle)
```

Arguments
handle (number) – Shape handle
Return value
broken (boolean) – Return true if shape is broken
Determine if shape has been broken. Note that a shape can be transfered
to another body during destruction, but might still not be considered
broken if all voxels are intact.

Doc example:
```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
end

function client.tick()
	DebugPrint("Is shape broken: " .. tostring(IsShapeBroken(shape)))
end
```


### Related shape functions (world transform, parent body, voxel material lookup)

### GetShapeWorldTransform

```
transform = GetShapeWorldTransform(handle)
```

Arguments
handle (number) – Shape handle
Return value
transform (TTransform) – Return shape transform in world space
This is a convenience function, transforming the shape out of body space

Doc example:
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

### GetShapeBody

```
handle = GetShapeBody(handle)
```

Arguments
handle (number) – Shape handle
Return value
handle (number) – Body handle
Get handle to the body this shape is owned by. A shape is always owned by a body,
but can be transfered to a new body during destruction.

Doc example:
```lua
local body = 0
function client.init()
	body = GetShapeBody(FindShape("shape", true))
end

function client.tick()
	DebugCross(GetBodyCenterOfMass(body))
end
```

### GetShapeMaterialAtIndex

```
type, r, g, b, a, entry = GetShapeMaterialAtIndex(handle, x, y, z)
```

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

Doc example:
```lua
local shape = 0
function client.init()
	shape = FindShape("shape", true)
	local mat = GetShapeMaterialAtIndex(shape, 0, 0, 0)
	DebugPrint("The voxel is of material: " .. mat)
end
```

### GetShapeBounds

```
min, max = GetShapeBounds(handle)
```

Arguments
handle (number) – Shape handle
Return value
min (TVec) – Vector representing the AABB lower bound
max (TVec) – Vector representing the AABB upper bound
Return the world space, axis-aligned bounding box for a shape.

Doc example:
```lua
function printShapeBounds()
	local shape = FindShape("shape", true)

	local min, max = GetShapeBounds(shape)
	local boundsSize = VecSub(max, min)
	local center = VecLerp(min, max, 0.5)

	DebugPrint(VecStr(boundsSize) .. " " .. VecStr(center))
end
```


## Find* and triggers

### FindBody

```
handle = FindBody([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
handle (number) – Handle to first body with specified tag or zero if not found

Doc example:
```lua
function init()
	--Search for a body tagged "target" in script scope
	local target = FindBody("body")
	DebugPrint(target)

	--Search for a body tagged "escape" in entire scene
	local escape = FindBody("body", true)
	DebugPrint(escape)
end
```

### FindBodies

```
list = FindBodies([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
list (table) – Indexed table with handles to all bodies with specified tag

Doc example:
```lua
function init()
	--Search for bodies tagged "target" in script scope
	local targets = FindBodies("target", true)
	for i=1, #targets do
		local target = targets[i]
		DebugPrint(target)
	end
end
```

### FindShape

```
handle = FindShape([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
handle (number) – Handle to first shape with specified tag or zero if not found

Doc example:
```lua
local target = 0
local escape = 0
function client.init()
	--Search for a shape tagged "mybox" in script scope
	target = FindShape("mybox")

	--Search for a shape tagged "laserturret" in entire scene
	escape = FindShape("laserturret", true)
end

function client.tick()
	DebugCross(GetShapeWorldTransform(target).pos)
	DebugCross(GetShapeWorldTransform(escape).pos)
end
```

### FindShapes

```
list = FindShapes([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
list (table) – Indexed table with handles to all shapes with specified tag

Doc example:
```lua
local shapes = {}
function client.init()
	--Search for shapes tagged "body"
	shapes = FindShapes("body", true)
end

function client.tick()
	for i=1, #shapes do
		local shape = shapes[i]
		DebugCross(GetShapeWorldTransform(shape).pos)
	end
end
```

### FindLocation

```
handle = FindLocation([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
handle (number) – Handle to first location with specified tag or zero if not found

Doc example:
```lua
local loc = 0
function client.init()
	loc = FindLocation("loc1")
end

function client.tick()
	DebugCross(GetLocationTransform(loc).pos)
end
```

### FindLocations

```
list = FindLocations([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
list (table) – Indexed table with handles to all locations with specified tag

Doc example:
```lua
local locations
function client.init()
	locations = FindLocations("loc1")

	for i=1, #locations do
		local loc = locations[i]
		DebugPrint(DebugPrint(loc))
	end
end
```

### FindTrigger

```
handle = FindTrigger([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
handle (number) – Handle to first trigger with specified tag or zero if not found

Doc example:
```lua
function server.init()
	local goal = FindTrigger("goal")
end
```

### IsPointInTrigger

```
inside = IsPointInTrigger(trigger, point)
```

Arguments
trigger (number) – Trigger handle
point (TVec) – Word space point as vector
Return value
inside (boolean) – True if point is in trigger volume

Doc example:
```lua
local trigger = 0
local point = {}
function client.init()
	trigger = FindTrigger("toxic", true)
	point = Vec(0, 0, 0)
end

function client.tick()
	if IsPointInTrigger(trigger, point) then
		DebugPrint("In trigger!")
	end
end
```


### Related location / trigger functions

Locations are transforms placed in the editor as markers. Location transforms are always expressed in
world space coordinates.

Triggers can be placed in the scene and queried by scripts to see if something is within a certain part
of the scene.

### GetLocationTransform

```
transform = GetLocationTransform(handle)
```

Arguments
handle (number) – Location handle
Return value
transform (TTransform) – Transform of the location

Doc example:
```lua
local location = 0
function client.init()
	location = FindLocation("loc1")
	DebugPrint(VecStr(GetLocationTransform(location).pos))
end
```

### GetTriggerTransform

```
transform = GetTriggerTransform(handle)
```

Arguments
handle (number) – Trigger handle
Return value
transform (TTransform) – Current trigger transform in world space

Doc example:
```lua
function client.init()
	local trigger = FindTrigger("toxic")
	local t = GetTriggerTransform(trigger)
	DebugPrint(t.pos)
end
```

### FindTriggers

```
list = FindTriggers([tag], [global])
```

Arguments
tag (string, optional) – Tag name
global (boolean, optional) – Search in entire scene
Return value
list (table) – Indexed table with handles to all triggers with specified tag

Doc example:
```lua
function client.init()
	--Find triggers tagged "toxic" in script scope
	local triggers = FindTriggers("toxic")
	for i=1, #triggers do
		local trigger = triggers[i]
		DebugPrint(trigger)
	end
end
```

### IsBodyInTrigger

```
inside = IsBodyInTrigger(trigger, body)
```

Arguments
trigger (number) – Trigger handle
body (number) – Body handle
Return value
inside (boolean) – True if body is in trigger volume
This function will only check the center point of the body

Doc example:
```lua
local trigger = 0
local body = 0
function client.init()
	trigger = FindTrigger("toxic")
	body = FindBody("body")
end

function client.tick()
	if IsBodyInTrigger(trigger, body) then
		DebugPrint("In trigger!")
	end
end
```

### IsShapeInTrigger

```
inside = IsShapeInTrigger(trigger, shape)
```

Arguments
trigger (number) – Trigger handle
shape (number) – Shape handle
Return value
inside (boolean) – True if shape is in trigger volume
This function will only check the center point of the shape

Doc example:
```lua
local trigger = 0
local shape = 0
function client.init()
	trigger = FindTrigger("toxic")
	shape = FindShape("shape")
end

function client.tick()
	if IsShapeInTrigger(trigger, shape) then
		DebugPrint("In trigger!")
	end
end
```

### IsTriggerEmpty

```
empty, maxpoint = IsTriggerEmpty(handle, [demolision])
```

Arguments
handle (number) – Trigger handle
demolision (boolean, optional) – If true, small debris and vehicles are ignored
Return value
empty (boolean) – True if trigger is empty
maxpoint (TVec) – World space point of highest point (largest Y coordinate) if not empty
This function will check if trigger is empty. If trigger contains any part of a body
it will return false and the highest point as second return value.

Doc example:
```lua
local trigger = 0
function client.init()
	trigger = FindTrigger("toxic")
end

function client.tick()
	local empty, highPoint = IsTriggerEmpty(trigger)
	if not empty then
		--highPoint[2] is the tallest point in trigger
		DebugPrint("Is not empty")
	end
end
```

### GetTriggerBounds

```
min, max = GetTriggerBounds(handle)
```

Arguments
handle (number) – Trigger handle
Return value
min (TVec) – Lower point of trigger bounds in world space
max (TVec) – Upper point of trigger bounds in world space
Return the lower and upper points in world space of the trigger axis aligned bounding box

Doc example:
```lua
function client.init()
	local trigger = FindTrigger("toxic")
	local mi, ma = GetTriggerBounds(trigger)

	local list = QueryAabbShapes(mi, ma)
	for i = 1, #list do
		DebugPrint(list[i])
	end
end
```


## Entity: tags, delete, handles, type

An Entity is the basis of most objects in the Teardown engine (bodies, shapes, lights, locations, etc).
All entities can have tags, which is a way to store custom properties on entities for scripting purposes.
Some tags are also reserved for engine use. See documentation for details.

### SetTag

```
SetTag(handle, tag, [value])
```

Arguments
handle (number) – Entity handle
tag (string) – Tag name
value (string, optional) – Tag value
Return value
none

Doc example:
```lua
function init()
	local handle = FindBody("body", true)
	--Add "special" tag to an entity
	SetTag(handle, "special")
	DebugPrint(HasTag(handle, "special"))

	--Add "team" tag to an entity and give it value "red"
	SetTag(handle, "team", "red")
	DebugPrint(HasTag(handle, "team"))
end
```

### HasTag

```
exists = HasTag(handle, tag)
```

Arguments
handle (number) – Entity handle
tag (string) – Tag name
Return value
exists (boolean) – Returns true if entity has tag

Doc example:
```lua
function init()
	local handle = FindBody("body", true)
	--Add "special" tag to an entity
	SetTag(handle, "special")
	DebugPrint(HasTag(handle, "special"))

	--Add "team" tag to an entity and give it value "red"
	SetTag(handle, "team", "red")
	DebugPrint(HasTag(handle, "team"))
end
```

### GetTagValue

```
value = GetTagValue(handle, tag)
```

Arguments
handle (number) – Entity handle
tag (string) – Tag name
Return value
value (string) – Returns the tag value, if any. Empty string otherwise.

Doc example:
```lua
function init()
	local handle = FindBody("body", true)

	--Add "team" tag to an entity and give it value "red"
	SetTag(handle, "team", "red")
	DebugPrint(GetTagValue(handle, "team"))
end
```

### RemoveTag

```
RemoveTag(handle, tag)
```

Arguments
handle (number) – Entity handle
tag (string) – Tag name
Return value
none
Remove tag from an entity. If the tag had a value it is removed too.

Doc example:
```lua
function init()
	local handle = FindBody("body", true)
	--Add "special" tag to an entity
	SetTag(handle, "special")
	RemoveTag(handle, "special")
	DebugPrint(HasTag(handle, "special"))

	--Add "team" tag to an entity and give it value "red"
	SetTag(handle, "team", "red")
	DebugPrint(HasTag(handle, "team"))
end
```

### Delete

```
Delete(handle)
```

Arguments
handle (number) – Entity handle
Return value
none
Remove an entity from the scene. All entities owned by this entity
will also be removed.

Doc example:
```lua
function init()
	local body = FindBody("body", true)
	--All shapes associated with body will also be removed
	Delete(body)
end
```

### IsHandleValid

```
exists = IsHandleValid(handle)
```

Arguments
handle (number) – Entity handle
Return value
exists (boolean) – Returns true if the entity pointed to by handle still exists

Doc example:
```lua
function init()
	local body = FindBody("body", true)

	--valid is true if body still exists
	DebugPrint(IsHandleValid(body))
	Delete(body)

	--valid will now be false
	DebugPrint(IsHandleValid(body))
end
```

### GetEntityType

```
type = GetEntityType(handle)
```

Arguments
handle (number) – Entity handle
Return value
type (string) – Type name of the provided entity
Returns the type name of provided entity, for example "body", "shape", "light", etc.

Doc example:
```lua
function init()
	local body = FindBody("body", true)
	DebugPrint(GetEntityType(body))
end
```


### Tags in the editor (index page, verbatim)

> ## Tags
>
> Every object in the editor can have zero, one or more tags associated with it. The tag property is frequently used when scripting in Teardown. Several of the Teardown API functions allows enumerating objects in the scene using the tag name. You may for example want to tag all shapes in a scene that have the tag `foo`. 
>
> ![Tag Property](images/editor_tags_1.png)
>
> Tagging the object with `foo` makes it possible to find all tagged shapes in the scene during runtime using the API function `FindShapes()`
> ```lua
> list = FindShapes("foo", true)
> -- list will contain [box2]
> ```
> Tags can also be assigned a value that can be read from a script. 
>
> ![Tag Value](images/editor_tags_2.png)
>
> ```lua
> handle = FindShape("foo")
> value = GetTagValue(handle, "foo")
> -- value will be "bar"
> ```
>
> #### Built-in Tags
>
> Teardown defines a couple of built-in tags for objects in the Editor that can be used to alter the default object behavior. The tags are listed as context-specific help for the Object 'tag' property in the Property Window. 

### Hierarchy and search scope for Find* (index page, verbatim)

> ## Hierarchy & Inheritance 
>
> All level content is stored as standard XML meaning that everything in the file is a hierarchy of node objects. The structure of the nodes in the file is directly mapped to the view in the Scene Explorer. Teardown implement support for property inheritance in the Editor. Child nodes will inherit the properties of their parent unless the property is explicitly set for the child. Inheritance allows you to put objects you want to share a common property inside of Groups and then set the property only once on the Group node. All the objects within the group will inherit the properties of the Group itself. This makes Groups useful not only as a way to keep the Scene Explorer tidy but as a way to logically group objects with similar properties.   
>
> Hierarchy is also relevant when searching for objects using the API functions in scripts. Functions that allows scripts to "find" objects will by default only return objects matching the search criteria below the script in the hierarchy. When a script wants to find all objects in the scene matching the search criteria regardless of position in the hierarchy the "find" function can be called with an optional "global" parameter. 
>
> ![Object Hierarchy](images/editor_inheritance_1.png)
>
> The scene above shows two voxbox shapes, "box1" and "box2", both having the `foo` tag. The API has a function `FindShapes()`  that allows the script to find shapes using a tag as search criteria. 
>
> ```lua
> list = FindShapes("target")
> -- returns "box2"
> ```
>
> When `FindShapes()` is called from the script the function will only return "box2" as "box1" is above the script in the hierarchy. 
>
> ```lua
> list = FindShapes("target", true)
> -- returns ["box2", "box1"]
> ```
>
> Calling `FindShapes()` with a second optional parameter indicating a global search will return all shapes with the "foo" tag, regardless of their place in the hierarchy. 

## Scene queries: QueryRaycast, QueryRejectBody, QueryRejectShape, QueryRequire, QueryClosestPoint

Query the level in various ways.

### QueryRaycast

```
hit, dist, normal, shape = QueryRaycast(origin, direction, maxDist, [radius], [rejectTransparent])
```

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

Doc example:
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

### QueryRejectBody

```
QueryRejectBody(body)
```

Arguments
body (number) – Body handle
Return value
none
Exclude body from the next query

Doc example:
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

### QueryRejectShape

```
QueryRejectShape(shape)
```

Arguments
shape (number) – Shape handle
Return value
none
Exclude shape from the next query

Doc example:
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

### QueryRequire

```
QueryRequire(layers)
```

Arguments
layers (string) – Space separate list of layers
Return value
none
Set required layers for next query. Available layers are:
 Layer  |  Description
physical	 |  have a physical representation
dynamic		 |  part of a dynamic body
static		 |  part of a static body
large		 |  above debris threshold
small		 |  below debris threshold
visible		 |  only hit visible shapes
animator	 |  part of an animator hierarchy
player       |  part of an player animator hierarchy
tool         |  part of a tool

Doc example:
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

### QueryClosestPoint

```
hit, point, normal, shape = QueryClosestPoint(origin, maxDist)
```

Arguments
origin (TVec) – World space point
maxDist (number) – Maximum distance. Keep this as low as possible for good performance.
Return value
hit (boolean) – True if a point was found
point (TVec) – World space closest point
normal (TVec) – World space normal at closest point
shape (number) – Handle to closest shape
This will query the closest point to all shapes in the world. If you
want to set up a filter for the query you need to do so before every call
to this function.

Doc example:
```lua
function client.tick()
	local vehicle = FindVehicle("vehicle")
	--Find closest point within 10 meters of {0, 5, 0}, excluding any point on myVehicle
	QueryRejectVehicle(vehicle)
	local hit, p, n, s = QueryClosestPoint(Vec(0, 5, 0), 10)
	if hit then
		DebugPrint(p)
	end
end
```


### Related query functions

### QueryRejectPlayer

```
QueryRejectPlayer([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
none
Exclude player from the next query

Doc example:
```lua
--Do not include shape in next raycast
QueryRejectPlayer(1)
QueryRaycast(...)
```

### QueryRaycastRope

```
hit, dist, joint = QueryRaycastRope(origin, direction, maxDist, [radius])
```

Arguments
origin (TVec) – Raycast origin as world space vector
direction (TVec) – Unit length raycast direction as world space vector
maxDist (number) – Raycast maximum distance. Keep this as low as possible for good performance.
radius (number, optional) – Raycast thickness. Default zero.
Return value
hit (boolean) – True if raycast hit something
dist (number) – Hit distance from origin
joint (number) – Handle to hit joint of rope type
This will perform a raycast query that returns the handle of the joint of rope type when if collides with it.
There are no filters for this type of raycast.

Doc example:
```lua
function client.tick()
	local playerCameraTransform = GetPlayerCameraTransform()
	local dir = TransformToParentVec(playerCameraTransform, Vec(0, 0, -1))

	local hit, dist, joint = QueryRaycastRope(playerCameraTransform.pos, dir, 10)
	if hit then
		DebugWatch("distance", dist)
		DebugWatch("joint", joint)
	end
end
```

### QueryAabbBodies

```
list = QueryAabbBodies(min, max)
```

Arguments
min (TVec) – Aabb minimum point
max (TVec) – Aabb maximum point
Return value
list (table) – Indexed table with handles to all bodies in the aabb
Return all bodies within the provided world space, axis-aligned bounding box

Doc example:
```lua
function client.tick()
	local list = QueryAabbBodies(Vec(0, 0, 0), Vec(10, 10, 10))
	for i=1, #list do
		local body = list[i]
		DebugPrint(body)
	end
end
```

### QueryAabbShapes

```
list = QueryAabbShapes(min, max)
```

Arguments
min (TVec) – Aabb minimum point
max (TVec) – Aabb maximum point
Return value
list (table) – Indexed table with handles to all shapes in the aabb
Return all shapes within the provided world space, axis-aligned bounding box

Doc example:
```lua
function client.tick()
	local list = QueryAabbShapes(Vec(0, 0, 0), Vec(10, 10, 10))
	for i=1, #list do
		local shape = list[i]
		DebugPrint(shape)
	end
end
```

### QueryRejectVehicle

```
QueryRejectVehicle(vehicle)
```

Arguments
vehicle (number) – Vehicle handle
Return value
none
Exclude vehicle from the next query

Doc example:
```lua
function client.tick()
	local vehicle = FindVehicle("vehicle")
	QueryRequire("physical dynamic large")
	--Do not include vehicle in next raycast
	QueryRejectVehicle(vehicle)
	local hit, dist = QueryRaycast(Vec(0, 0, 0), Vec(1, 0, 0), 10)
	if hit then
		DebugPrint(dist)
	end
end
```


## Sound: LoadSound, PlaySound, LoadLoop, PlayLoop, PlayMusic

Sound functions are used for playing sounds or loops in the world. There sound functions are
always positioned and will be affected by acoustics simulation. If you want to play dry sounds
without acoustics you should use UiSound and UiSoundLoop in the User Interface section.

### LoadSound

```
handle = LoadSound(path, [nominalDistance])
```

Arguments
path (string) – Path to ogg sound file
nominalDistance (number, optional) – The distance in meters this sound is recorded at. Affects attenuation, default is 10.0
Return value
handle (number) – Sound handle

Doc example:
```lua
function client.init()
	local snd = LoadSound("warning-beep.ogg")
end
```

### PlaySound

```
handle = PlaySound(handle, [pos], [volume], [registerVolume], [pitch])
```

Arguments
handle (number) – Sound handle
pos (TVec, optional) – World position as vector. Default is player position.
volume (number, optional) – Playback volume. Default is 1.0
registerVolume (boolean, optional) – Register position and volume of this sound for GetLastSound. Default is true
pitch (number, optional) – Playback pitch. Default 1.0
Return value
handle (number) – Sound play handle

Doc example:
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

### LoadLoop

```
handle = LoadLoop(path, [nominalDistance])
```

Arguments
path (string) – Path to ogg sound file
nominalDistance (number, optional) – The distance in meters this sound is recorded at. Affects attenuation, default is 10.0
Return value
handle (number) – Loop handle

Doc example:
```lua
local loop
function client.init()
	loop = LoadLoop("radio/jazz.ogg")
end

function client.tick()
	local pos = Vec(0, 0, 0)
	PlayLoop(loop, pos, 1.0)
end
```

### PlayLoop

```
PlayLoop(handle, [pos], [volume], [registerVolume], [pitch])
```

Arguments
handle (number) – Loop handle
pos (TVec, optional) – World position as vector. Default is player position.
volume (number, optional) – Playback volume. Default is 1.0
registerVolume (boolean, optional) – Register position and volume of this sound for GetLastSound. Default is true
pitch (number, optional) – Playback pitch. Default 1.0
Return value
none
Call this function continuously to play loop

Doc example:
```lua
local loop
function client.init()
	loop = LoadLoop("radio/jazz.ogg")
end

function client.tick()
	local pos = Vec(0, 0, 0)
	PlayLoop(loop, pos, 1.0)
end
```

### PlayMusic

```
PlayMusic(path)
```

Arguments
path (string) – Music path
Return value
none

Doc example:
```lua
function client.init()
	PlayMusic("about.ogg")
end
```

### StopMusic

```
StopMusic()
```

Arguments
none
Return value
none

Doc example:
```lua
function client.init()
	PlayMusic("about.ogg")
end

function client.tick()
	if InputDown("interact") then
		StopMusic()
	end
end
```

### UiSound

```
UiSound(path, [volume], [pitch], [panAzimuth], [panDepth])
```

Arguments
path (string) – Path to sound file (OGG format)
volume (number, optional) – Playback volume. Default 1.0
pitch (number, optional) – Playback pitch. Default 1.0
panAzimuth (number, optional) – Playback stereo panning azimuth (-PI to PI). Default 0.0.
panDepth (number, optional) – Playback stereo panning depth (0.0 to 1.0). Default 1.0.
Return value
none
UI sounds are not affected by acoustics simulation. Use LoadSound / PlaySound for that.

Doc example:
```lua
UiSound("click.ogg")
```


## Time

### GetTime

```
time = GetTime()
```

Arguments
none
Return value
time (number) – The time in seconds since level was started
Returns running time of this script. If called from update, this returns
the simulated time, otherwise it returns wall time.

Doc example:
```lua
function client.update()
	local t = GetTime()
	DebugPrint(t)
end
```

### GetTimeStep

```
dt = GetTimeStep()
```

Arguments
none
Return value
dt (number) – The timestep in seconds
Returns timestep of the last frame. If called from update, this returns
the simulation time step, which is always one 60th of a second (0.0166667).
If called from tick or draw it returns the actual time since last frame.

Doc example:
```lua
function client.tick()
	local dt = GetTimeStep()
	DebugPrint("tick dt: " .. dt)
end

function client.update()
	local dt = GetTimeStep()
	DebugPrint("update dt: " .. dt)
end
```


## Registry: GetBool/SetBool/GetInt/SetInt/GetFloat/SetFloat/GetString/SetString, ClearKey

The Teardown engine uses a global key/value-pair registry that scripts
can read and write. The engine exposes a lot of internal information through
the registry, but it can also be used as way for scripts to communicate with
each other.

The registry is a hierarchical node structure and can store a value in each node (parent nodes can also have a value).
The values can be of type floating point number, integer, boolean or string, but all types are automatically converted if another type is requested.
Some registry nodes are reserved and used for special purposes.

Registry node names may only contain the characters a-z, numbers 0-9, dot, dash and underscore.

 Key	 |  Description

options			 |  reserved for game settings (write protected from mods)
game			 |  reserved for the game engine internals (see documentation)
savegame		 |  used for persistent game data (write protected for mods)
savegame.mod	 |  used for persistent mod data. Use only alphanumeric character for key name.
level			 |  not reserved, but recommended for level specific entries and script communication

### GetBool

```
value = GetBool(key)
```

Arguments
key (string) – Registry key
Return value
value (boolean) – Boolean value of registry node or false if not found

Doc example:
```lua
function init()
	SetBool("level.robots.enabled", true)
	DebugPrint(GetBool("level.robots.enabled"))
end
```

### SetBool

```
SetBool(key, value, [sync])
```

Arguments
key (string) – Registry key
value (boolean) – Desired value
sync (boolean, optional) – Synchronize to clients
Return value
none

Doc example:
```lua
function init()
	SetBool("level.robots.enabled", true)
	DebugPrint(GetBool("level.robots.enabled"))
end
```

### GetInt

```
value = GetInt(key)
```

Arguments
key (string) – Registry key
Return value
value (number) – Integer value of registry node or zero if not found

Doc example:
```lua
function init()
	SetInt("score.levels.level1", 4)
	DebugPrint(GetInt("score.levels.level1"))
end
```

### SetInt

```
SetInt(key, value, [sync])
```

Arguments
key (string) – Registry key
value (number) – Desired value
sync (boolean, optional) – Synchronize to clients
Return value
none

Doc example:
```lua
function init()
	SetInt("score.levels.level1", 4)
	DebugPrint(GetInt("score.levels.level1"))
end
```

### GetFloat

```
value = GetFloat(key)
```

Arguments
key (string) – Registry key
Return value
value (number) – Float value of registry node or zero if not found

Doc example:
```lua
function init()
	SetFloat("level.time", 22.3)
	DebugPrint(GetFloat("level.time"))
end
```

### SetFloat

```
SetFloat(key, value, [sync])
```

Arguments
key (string) – Registry key
value (number) – Desired value
sync (boolean, optional) – Synchronize to clients
Return value
none

Doc example:
```lua
function init()
	SetFloat("level.time", 22.3)
	DebugPrint(GetFloat("level.time"))
end
```

### GetString

```
value = GetString(key)
```

Arguments
key (string) – Registry key
Return value
value (string) – String value of registry node or "" if not found

Doc example:
```lua
function init()
	SetString("level.name", "foo")
	DebugPrint(GetString("level.name"))
end
```

### SetString

```
SetString(key, value, [sync])
```

Arguments
key (string) – Registry key
value (string) – Desired value
sync (boolean, optional) – Synchronize to clients
Return value
none

Doc example:
```lua
function init()
	SetString("level.name", "foo")
	DebugPrint(GetString("level.name"))
end
```

### ClearKey

```
ClearKey(key)
```

Arguments
key (string) – Registry key to clear
Return value
none
Remove registry node, including all child nodes.

Doc example:
```lua
function init()
	--If the registry looks like this:
	--	score
	--		levels
	--			level1 = 5
	--			level2 = 4

	ClearKey("score.levels")

	--Afterwards, the registry will look like this:
	--	score
end
```

### HasKey

```
exists = HasKey(key)
```

Arguments
key (string) – Registry key
Return value
exists (boolean) – True if key exists
Returns true if the registry contains a certain key

Doc example:
```lua
function init()
	DebugPrint(HasKey("score.levels"))
	DebugPrint(HasKey("game.tool.rifle"))
end
```


## Debug output: DebugPrint, DebugWatch, DebugLine, DebugCross

### DebugPrint

```
DebugPrint(message, [lineWrapping])
```

Arguments
message (string) – Message to display
lineWrapping (boolean, optional) – True if you need to wrap Table lines. Works only with tables.
Return value
none
Display message on screen. The last 20 lines are displayed.
The function will also recognize tables and convert them to strings automatically.

Doc example:
```lua
function client.init()
	DebugPrint("time")

	DebugPrint(GetPlayerCameraTransform())

	local anyTable = {
		"teardown",
		{
			name = "Alex",
			age = 25,
			child = { name = "Lena" }
		},
		nil,
		version = "1.6.0",
		true,
	}
	DebugPrint(anyTable)
end
```

### DebugWatch

```
DebugWatch(name, value, [lineWrapping])
```

Arguments
name (string) – Name
value (any) – Value
lineWrapping (boolean, optional) – True if you need to wrap Table lines. Works only with tables.
Return value
none
Show a named valued on screen for debug purposes.
Up to 32 values can be shown simultaneously. Values updated the current
frame are drawn opaque. Old values are drawn transparent in white.
The function will also recognize tables and convert them to strings automatically.

Doc example:
```lua
function client.tick()
	DebugWatch("Player camera transform", GetPlayerCameraTransform())

	local anyTable = {
		"teardown",
		{
			name = "Alex",
			age = 25,
			child = { name = "Lena" }
		},
		nil,
		version = "1.6.0",
		true
	}
	DebugWatch("table", anyTable);
end
```

### DebugLine

```
DebugLine(p0, p1, [r], [g], [b], [a])
```

Arguments
p0 (TVec) – World space point as vector
p1 (TVec) – World space point as vector
r (number, optional) – Red
g (number, optional) – Green
b (number, optional) – Blue
a (number, optional) – Alpha
Return value
none
Draw a 3D debug overlay line in the world. Default color is white.

Doc example:
```lua
function server.tick()
	--Draw white debug line
	DebugLine(Vec(0, 0, 0), Vec(-10, 5, -10))

	--Draw red debug line
	DebugLine(Vec(0, 0, 0), Vec(10, 5, 10), 1, 0, 0)
end

-- Or

function client.tick()
	--Draw white debug line
	DebugLine(Vec(0, 0, 0), Vec(-10, 5, -10))

	--Draw red debug line
	DebugLine(Vec(0, 0, 0), Vec(10, 5, 10), 1, 0, 0)
end
```

### DebugCross

```
DebugCross(p0, [r], [g], [b], [a])
```

Arguments
p0 (TVec) – World space point as vector
r (number, optional) – Red
g (number, optional) – Green
b (number, optional) – Blue
a (number, optional) – Alpha
Return value
none
Draw a debug cross in the world to highlight a location. Default color is white.

Doc example:
```lua
function server.tick()
	DebugCross(Vec(10, 5, 5))
end
-- Or
function client.tick()
	DebugCross(Vec(10, 5, 5))
end
```


## User interface: drawing a text label

The user interface functions are used for drawing interactive 2D graphics and can only be
called from the draw function of a script. The ui functions are designed with the immediate
mode gui paradigm in mind and uses a cursor and state stack. Pushing and popping the stack is cheap
and designed to be called often.

Minimal sequence for an on-screen text label (inside `client.draw()` in the 2.x API; `draw()` in the older global style): `UiPush`, `UiTranslate`, `UiAlign`, `UiFont`, `UiColor`, `UiText`, `UiPop`.

### UiPush

```
UiPush()
```

Arguments
none
Return value
none
Push state onto stack. This is used in combination with UiPop to
remember a state and restore to that state later.

Doc example:
```lua
UiColor(1,0,0)
UiText("Red")
UiPush()
	UiColor(0,1,0)
	UiText("Green")
UiPop()
UiText("Red")
```

### UiPop

```
UiPop()
```

Arguments
none
Return value
none
Pop state from stack and make it the current one. This is used in
combination with UiPush to remember a previous state and go back to
it later.

Doc example:
```lua
UiColor(1,0,0)
UiText("Red")
UiPush()
	UiColor(0,1,0)
	UiText("Green")
UiPop()
UiText("Red")
```

### UiTranslate

```
UiTranslate(x, y)
```

Arguments
x (number) – X component
y (number) – Y component
Return value
none
Translate cursor

Doc example:
```lua
UiPush()
	UiTranslate(100, 0)
	UiText("Indented")
UiPop()
```

### UiFont

```
UiFont(path, size)
```

Arguments
path (string) – Path to TTF font file
size (number) – Font size (10 to 100)
Return value
none

Doc example:
```lua
UiFont("bold.ttf", 24)
UiText("Hello")
```

### UiColor

```
UiColor(r, g, b, [a])
```

Arguments
r (number) – Red channel
g (number) – Green channel
b (number) – Blue channel
a (number, optional) – Alpha channel. Default 1.0
Return value
none

Doc example:
```lua
--Set color yellow
UiColor(1,1,0)
```

### UiAlign

```
UiAlign(alignment)
```

Arguments
alignment (string) – Alignment keywords
Return value
none
The alignment determines how content is aligned with respect to the
cursor.
 Alignment  |  Description
left	 |  Horizontally align to the left
right	 |  Horizontally align to the right
center	 |  Horizontally align to the center
top		 |  Vertically align to the top
bottom	 |  Veritcally align to the bottom
middle	 |  Vertically align to the middle
Alignment can contain combinations of these, for instance:
"center middle", "left top", "center top", etc. If horizontal
or vertical alginment is omitted it will depend on the element drawn.
Text, for instance has default vertical alignment at baseline.

Doc example:
```lua
UiAlign("left")
UiText("Aligned left at baseline")

UiAlign("center middle")
UiText("Fully centered")
```

### UiCenter

```
center = UiCenter()
```

Arguments
none
Return value
center (number) – Half width of draw context

Doc example:
```lua
local c = UiCenter()
--Same as
local c = UiWidth()/2
```

### UiMiddle

```
middle = UiMiddle()
```

Arguments
none
Return value
middle (number) – Half height of draw context

Doc example:
```lua
local m = UiMiddle()
--Same as
local m = UiHeight()/2
```

### UiWidth

```
width = UiWidth()
```

Arguments
none
Return value
width (number) – Width of draw context

Doc example:
```lua
local w = UiWidth()
```

### UiHeight

```
height = UiHeight()
```

Arguments
none
Return value
height (number) – Height of draw context

Doc example:
```lua
local h = UiHeight()
```

### UiText

```
w, h, x, y, linkId = UiText(text, [move], [maxChars])
```

Arguments
text (string) – Print text at cursor location
move (boolean, optional) – Automatically move cursor vertically. Default false.
maxChars (number, optional) – Maximum amount of characters. Default 100000.
Return value
w (number) – Width of text
h (number) – Height of text
x (number) – End x-position of text.
y (number) – End y-position of text.
linkId (string) – Link id of clicked link

Doc example:
```lua
UiFont("bold.ttf", 24)
UiText("Hello")

...

--Automatically advance cursor
UiText("First line", true)
UiText("Second line", true)



--Using links
UiFont("bold.ttf", 26)
UiTranslate(100,100)
--Using virtual links
link = "[[link;label=loc@UI_TEXT_FREE_ROAM_OPTIONS_LINK_NAME;id=options/game;color=#DDDD7FDD;underline=true]]"
someText = "Some text with a link: " .. link .. " and some more text"

w, h, x, y, linkId = UiText(someText)
if linkId:len() ~= 0 then
	if linkId == "options/game" then
		DebugPrint(linkId.." link clicked")
	elseif linkId == "options/sound" then
		--Do something else
	end
end
UiTranslate(0,50)

--Using game links, id attribute is required, color is optional, same as virtual links
link = "[[game://options;label=loc@UI_TEXT_FREE_ROAM_OPTIONS_LINK_NAME;id=game;color=#DDDD7FDD;underline=false]]"
someText = "Some text with a link: " .. link .. " and some more text"
w, h, x, y, linkId = UiText(someText)
if linkId:len() ~= 0 then
	DebugPrint(linkId.." link clicked")
end
UiTranslate(0,50)

--Using http/s links is also possible, link will be opened in the default browser
link = "[[http://www.example.com;label=loc@SOME_KEY;]]"
someText = "Goto: " .. link
UiText(someText)
```

### UiTextOutline

```
UiTextOutline(r, g, b, a, [thickness])
```

Arguments
r (number) – Red channel
g (number) – Green channel
b (number) – Blue channel
a (number) – Alpha channel
thickness (number, optional) – Outline thickness. Default is 0.1
Return value
none

Doc example:
```lua
--Black outline, standard thickness
UiTextOutline(0,0,0,1)
UiText("Text with outline")
```

### UiTextShadow

```
UiTextShadow(r, g, b, a, [distance], [blur])
```

Arguments
r (number) – Red channel
g (number) – Green channel
b (number) – Blue channel
a (number) – Alpha channel
distance (number, optional) – Shadow distance. Default is 1.0
blur (number, optional) – Shadow blur. Default is 0.5
Return value
none

Doc example:
```lua
--Black drop shadow, 50% transparent, distance 2
UiTextShadow(0, 0, 0, 0.5, 2.0)
UiText("Text with drop shadow")
```

### UiColorFilter

```
UiColorFilter(r, g, b, [a])
```

Arguments
r (number) – Red channel
g (number) – Green channel
b (number) – Blue channel
a (number, optional) – Alpha channel. Default 1.0
Return value
none
Color filter, multiplied to all future colors in this scope

Doc example:
```lua
UiPush()
	--Draw menu in transparent, yellow color tint
	UiColorFilter(1, 1, 0, 0.5)
	drawMenu()
UiPop()
```


## Vector math

Vector math is used in Teardown scripts to represent 3D positions, directions,
rotations and transforms. The base types are vectors, quaternions and transforms.
Vectors and quaternions are indexed tables with three and four components. Transforms
are tables consisting of one vector (pos) and one quaternion (rot)

### Vec

```
vec = Vec([x], [y], [z])
```

Arguments
x (number, optional) – X value
y (number, optional) – Y value
z (number, optional) – Z value
Return value
vec (TVec) – New vector
Create new vector and optionally initializes it to the provided values.
A Vec is equivalent to a regular lua table with three numbers.

Doc example:
```lua
function init()
	--These are equivalent
	local a1 = Vec()
	local a2 = {0, 0, 0}
	DebugPrint("a1 == a2: " .. tostring(VecStr(a1) == VecStr(a2)))

	--These are equivalent
	local b1 = Vec(0, 1, 0)
	local b2 = {0, 1, 0}
	DebugPrint("b1 == b2: " .. tostring(VecStr(b1) == VecStr(b2)))
end
```

### VecAdd

```
c = VecAdd(a, b)
```

Arguments
a (TVec) – Vector
b (TVec) – Vector
Return value
c (TVec) – New vector with sum of a and b

Doc example:
```lua
function init()
	local a = Vec(1,2,3)
	local b = Vec(3,0,0)
	local c = VecAdd(a, b)
	--c now equals {4,2,3}
	DebugPrint(VecStr(c))
end
```

### VecSub

```
c = VecSub(a, b)
```

Arguments
a (TVec) – Vector
b (TVec) – Vector
Return value
c (TVec) – New vector representing a-b

Doc example:
```lua
function init()
	local a = Vec(1,2,3)
	local b = Vec(3,0,0)
	local c = VecSub(a, b)
	--c now equals {-2,2,3}
	DebugPrint(VecStr(c))
end
```

### VecScale

```
norm = VecScale(vec, scale)
```

Arguments
vec (TVec) – A vector
scale (number) – A scale factor
Return value
norm (TVec) – A scaled version of input vector

Doc example:
```lua
function init()
	local v = Vec(1,2,3)
	local n = VecScale(v, 2)
	--n now equals {2,4,6}
	DebugPrint(VecStr(n))
end
```

### VecLength

```
length = VecLength(vec)
```

Arguments
vec (TVec) – A vector
Return value
length (number) – Length (magnitude) of the vector

Doc example:
```lua
function init()
	local v = Vec(1,1,0)
	local l = VecLength(v)
	--l now equals 1.4142
	DebugPrint(l)
end
```

### VecNormalize

```
norm = VecNormalize(vec)
```

Arguments
vec (TVec) – A vector
Return value
norm (TVec) – A vector of length 1.0
If the input vector is of zero length, the function returns {0,0,1}

Doc example:
```lua
function init()
	local v = Vec(0,3,0)
	local n = VecNormalize(v)
	--n now equals {0,1,0}
	DebugPrint(VecStr(n))
end
```

### VecLerp

```
c = VecLerp(a, b, t)
```

Arguments
a (TVec) – Vector
b (TVec) – Vector
t (number) – fraction (usually between 0.0 and 1.0)
Return value
c (TVec) – Linearly interpolated vector between a and b, using t

Doc example:
```lua
function init()
	local a = Vec(2,0,0)
	local b = Vec(0,4,2)
	local t = 0.5
	
	--These two are equivalent
	local c1 = VecLerp(a, b, t)
	local c2 = VecAdd(VecScale(a, 1-t), VecScale(b, t))
	
	--c1 and c2 now equals {1, 2, 1}
	DebugPrint("c1" .. VecStr(c1) .. " == c2" .. VecStr(c2))
end
```

### VecDot

```
c = VecDot(a, b)
```

Arguments
a (TVec) – Vector
b (TVec) – Vector
Return value
c (number) – Dot product of a and b

Doc example:
```lua
function init()
	local a = Vec(1,2,3)
	local b = Vec(3,1,0)
	local c = VecDot(a, b)
	--c now equals 5
	DebugPrint(c)
end
```

### VecCross

```
c = VecCross(a, b)
```

Arguments
a (TVec) – Vector
b (TVec) – Vector
Return value
c (TVec) – Cross product of a and b (also called vector product)

Doc example:
```lua
function init()
	local a = Vec(1,0,0)
	local b = Vec(0,1,0)
	local c = VecCross(a, b)
	--c now equals {0,0,1}
	DebugPrint(VecStr(c))
end
```

### VecDist

NOT FOUND IN DOCS (no function by that name; no `VecDistance` either). Compute as `VecLength(VecSub(a, b))`.

### Transform

```
transform = Transform([pos], [rot])
```

Arguments
pos (TVec, optional) – Vector representing transform position
rot (TQuat, optional) – Quaternion representing transform rotation
Return value
transform (TTransform) – New transform
A transform is a regular lua table with two entries: pos and rot,
a vector and quaternion representing transform position and rotation.

Doc example:
```lua
function init()
	--Create transform located at {0, 0, 0} with no rotation
	local t1 = Transform()

	--Create transform located at {10, 0, 0} with no rotation
	local t2 = Transform(Vec(10, 0,0))

	--Create transform located at {10, 0, 0}, rotated 45 degrees around Y axis
	local t3 = Transform(Vec(10, 0,0), QuatEuler(0, 45, 0))

	DebugPrint(TransformStr(t1))
	DebugPrint(TransformStr(t2))
	DebugPrint(TransformStr(t3))
end
```

### TransformToParentPoint

```
r = TransformToParentPoint(t, p)
```

Arguments
t (TTransform) – Transform
p (TVec) – Vector representing position
Return value
r (TVec) – Transformed position
Transfom position p out of transform t.

Doc example:
```lua
function init()
	local t = GetBodyTransform(body)
	local bodyPoint = Vec(0, 0, -1)
	local p = TransformToParentPoint(t, bodyPoint)

	--p now represents the local body point {0, 0, -1 } in world space
	DebugPrint(VecStr(p))
end
```

### TransformToLocalPoint

```
r = TransformToLocalPoint(t, p)
```

Arguments
t (TTransform) – Transform
p (TVec) – Vector representing position
Return value
r (TVec) – Transformed position
Transfom position p into transform t.

Doc example:
```lua
function init()
	local t = GetBodyTransform(body)
	local worldOrigo = Vec(0, 0, 0)
	local p = TransformToLocalPoint(t, worldOrigo)

	--p now represents the position of world origo in local body space
	DebugPrint(VecStr(p))
end
```

### TransformToParentVec

```
r = TransformToParentVec(t, v)
```

Arguments
t (TTransform) – Transform
v (TVec) – Vector
Return value
r (TVec) – Transformed vector
Transfom vector v out of transform t only considering rotation.

Doc example:
```lua
function init()
	local t = GetBodyTransform(body)
	local localUp = Vec(0, 1, 0)
	local up = TransformToParentVec(t, localUp)

	--up now represents the local body up direction in world space
	DebugPrint(VecStr(up))
end
```

### TransformToLocalVec

```
r = TransformToLocalVec(t, v)
```

Arguments
t (TTransform) – Transform
v (TVec) – Vector
Return value
r (TVec) – Transformed vector
Transfom vector v into transform t only considering rotation.

Doc example:
```lua
function init()
	local t = GetBodyTransform(body)
	local localUp = Vec(0, 1, 0)
	local up = TransformToParentVec(t, localUp)

	--up now represents the local body up direction in world space
	DebugPrint(VecStr(up))
end
```

### TransformToParentTransform

```
transform = TransformToParentTransform(parent, child)
```

Arguments
parent (TTransform) – Transform
child (TTransform) – Transform
Return value
transform (TTransform) – New transform
Transform child transform out of the parent transform.
This is the opposite of TransformToLocalTransform.

Doc example:
```lua
function init()
	local b = GetBodyTransform(body)
	local s = GetShapeLocalTransform(shape)

	--b represents the location of body in world space
	--s represents the location of shape in body space

	local w = TransformToParentTransform(b, s)

	--w now represents the location of shape in world space
	DebugPrint(TransformStr(w))
end
```

### TransformToLocalTransform

```
transform = TransformToLocalTransform(parent, child)
```

Arguments
parent (TTransform) – Transform
child (TTransform) – Transform
Return value
transform (TTransform) – New transform
Transform one transform into the local space of another transform.
This is the opposite of TransformToParentTransform.

Doc example:
```lua
function init()
	local b = GetBodyTransform(body)
	local w = GetShapeWorldTransform(shape)

	--b represents the location of body in world space
	--w represents the location of shape in world space
	
	local s = TransformToLocalTransform(b, w)

	--s now represents the location of shape in body space.
	DebugPrint(TransformStr(s))
end
```

### QuatEuler

```
quat = QuatEuler(x, y, z)
```

Arguments
x (number) – Angle around X axis in degrees, sometimes also called roll or bank
y (number) – Angle around Y axis in degrees, sometimes also called yaw or heading
z (number) – Angle around Z axis in degrees, sometimes also called pitch or attitude
Return value
quat (TQuat) – New quaternion
Create quaternion using euler angle notation. The order of applied rotations uses the
"NASA standard aeroplane" model:
Rotation around Y axis (yaw or heading)
Rotation around Z axis (pitch or attitude)
Rotation around X axis (roll or bank)

Doc example:
```lua
function init()
	--Create quaternion representing rotation 30 degrees around Y axis and 25 degrees around Z axis
	local q = QuatEuler(0, 30, 25)
end
```

### QuatLookAt

```
quat = QuatLookAt(eye, target)
```

Arguments
eye (TVec) – Vector representing the camera location
target (TVec) – Vector representing the point to look at
Return value
quat (TQuat) – New quaternion
Create a quaternion pointing the negative Z axis (forward) towards
a specific point, keeping the Y axis upwards. This is very useful
for creating camera transforms.

Doc example:
```lua
function init()
	local eye = Vec(0, 10, 0)
	local target = Vec(0, 1, 5)
	local rot = QuatLookAt(eye, target)
	SetCameraTransform(Transform(eye, rot))
end
```

### QuatSlerp

```
c = QuatSlerp(a, b, t)
```

Arguments
a (TQuat) – Quaternion
b (TQuat) – Quaternion
t (number) – fraction (usually between 0.0 and 1.0)
Return value
c (TQuat) – New quaternion
Spherical, linear interpolation between a and b, using t. This is
very useful for animating between two rotations.

Doc example:
```lua
function init()
	local a = QuatEuler(0, 10, 0)
	local b = QuatEuler(0, 0, 45)

	--Create quaternion half way between a and b
	local q = QuatSlerp(a, b, 0.5)
	DebugPrint(QuatStr(q))
end
```

### GetQuatEuler

```
x, y, z = GetQuatEuler(quat)
```

Arguments
quat (TQuat) – Quaternion
Return value
x (number) – Angle around X axis in degrees, sometimes also called roll or bank
y (number) – Angle around Y axis in degrees, sometimes also called yaw or heading
z (number) – Angle around Z axis in degrees, sometimes also called pitch or attitude
Return euler angles from quaternion. The order of rotations uses the "NASA standard aeroplane" model:
Rotation around Y axis (yaw or heading)
Rotation around Z axis (pitch or attitude)
Rotation around X axis (roll or bank)

Doc example:
```lua
function init()
	--Return euler angles from quaternion q
	q = QuatEuler(30, 45, 0)
	rx, ry, rz = GetQuatEuler(q)
	DebugPrint(rx .. " " .. ry .. " " .. rz)
end
```

### Quat

```
quat = Quat([x], [y], [z], [w])
```

Arguments
x (number, optional) – X value
y (number, optional) – Y value
z (number, optional) – Z value
w (number, optional) – W value
Return value
quat (TQuat) – New quaternion
Create new quaternion and optionally initializes it to the provided values.
Do not attempt to initialize a quaternion with raw values unless you know
what you are doing. Use QuatEuler or QuatAxisAngle instead.
If no arguments are given, a unit quaternion will be created: {0, 0, 0, 1}.
A quaternion is equivalent to a regular lua table with four numbers.

Doc example:
```lua
function init()
	--These are equivalent
	local a1 = Quat()
	local a2 = {0, 0, 0, 1}

	DebugPrint(QuatStr(a1) == QuatStr(a2))
end
```

### QuatRotateVec

```
vec = QuatRotateVec(a, vec)
```

Arguments
a (TQuat) – Quaternion
vec (TVec) – Vector
Return value
vec (TVec) – Rotated vector
Rotate a vector by a quaternion

Doc example:
```lua
function init()
	local q = QuatEuler(0, 10, 0)
	local v = Vec(1, 0, 0)
	local r = QuatRotateVec(q, v)
	
	--r is now vector a rotated 10 degrees around the Y axis
	DebugPrint(VecStr(r))
end
```

### QuatAxisAngle

```
quat = QuatAxisAngle(axis, angle)
```

Arguments
axis (TVec) – Rotation axis, unit vector
angle (number) – Rotation angle in degrees
Return value
quat (TQuat) – New quaternion
Create a quaternion representing a rotation around a specific axis

Doc example:
```lua
function init()
	--Create quaternion representing rotation 30 degrees around Y axis
	local q = QuatAxisAngle(Vec(0,1,0), 30)
	DebugPrint(QuatStr(q))
end
```


### Random helpers

### SetRandomSeed

```
SetRandomSeed(seed)
```

Arguments
seed (number) – Random seed
Return value
none

Doc example:
```lua
function init()
	SetRandomSeed(42)
	result = RollDie()
end
```

### GetRandomInt

```
result = GetRandomInt(min, max)
```

Arguments
min (number) – Lower number
max (number) – Upper number
Return value
result (number) – Random number in given range, including max.

Doc example:
```lua
function init()
	dieRoll = GetRandomInt(1,6)
	-- dieRoll is 1,2,3,4,5 or 6
end
```

### GetRandomFloat

```
result = GetRandomFloat(min, max)
```

Arguments
min (number) – Lower number
max (number) – Upper number
Return value
result (number) – Random number in given range, including max.

Doc example:
```lua
function init()
	-- Generate a random angle in range [0, 360]
	randomAngleDeg = GetRandomFloat(0.0f, 360.0f)
end
```

### GetRandomDirection

```
vector = GetRandomDirection([length])
```

Arguments
length (number, optional) – Optional length use to scale the generated direction.
Return value
vector (Vec3) – Random direction with unit length

Doc example:
```lua
function init()
	-- Generate a random direction.
	ricochetDirection = GetRandomDirection()
end
```

### GetRandomBool

```
result = GetRandomBool()
```

Arguments
none
Return value
result (boolean) – Random true/false

Doc example:
```lua
function init()
	isHeads = GetRandomBool()

	if isHeads then
		win = true
	end
end
```


## Particles and explosions (signatures and argument lists only)

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

### ParticleReset

```
ParticleReset()
```

Arguments
none

### ParticleType

```
ParticleType(type)
```

Arguments
type (string) – Type of particle. Can be "smoke" or "plain".

### ParticleTile

```
ParticleTile(type)
```

Arguments
type (number) – Tile in the particle texture atlas (0-15)

### ParticleColor

```
ParticleColor(r0, g0, b0, [r1], [g1], [b1])
```

Arguments
r0 (number) – Red value
g0 (number) – Green value
b0 (number) – Blue value
r1 (number, optional) – Red value at end
g1 (number, optional) – Green value at end
b1 (number, optional) – Blue value at end

### ParticleRadius

```
ParticleRadius(r0, [r1], [interpolation], [fadein], [fadeout])
```

Arguments
r0 (number) – Radius
r1 (number, optional) – End radius
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleAlpha

```
ParticleAlpha(a0, [a1], [interpolation], [fadein], [fadeout])
```

Arguments
a0 (number) – Alpha (0.0 - 1.0)
a1 (number, optional) – End alpha (0.0 - 1.0)
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleGravity

```
ParticleGravity(g0, [g1], [interpolation], [fadein], [fadeout])
```

Arguments
g0 (number) – Gravity
g1 (number, optional) – End gravity
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleDrag

```
ParticleDrag(d0, [d1], [interpolation], [fadein], [fadeout])
```

Arguments
d0 (number) – Drag
d1 (number, optional) – End drag
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleEmissive

```
ParticleEmissive(d0, [d1], [interpolation], [fadein], [fadeout])
```

Arguments
d0 (number) – Emissive
d1 (number, optional) – End emissive
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleRotation

```
ParticleRotation(r0, [r1], [interpolation], [fadein], [fadeout])
```

Arguments
r0 (number) – Rotation speed in radians per second.
r1 (number, optional) – End rotation speed in radians per second.
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleStretch

```
ParticleStretch(s0, [s1], [interpolation], [fadein], [fadeout])
```

Arguments
s0 (number) – Stretch
s1 (number, optional) – End stretch
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleSticky

```
ParticleSticky(s0, [s1], [interpolation], [fadein], [fadeout])
```

Arguments
s0 (number) – Sticky (0.0 - 1.0)
s1 (number, optional) – End sticky (0.0 - 1.0)
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleCollide

```
ParticleCollide(c0, [c1], [interpolation], [fadein], [fadeout])
```

Arguments
c0 (number) – Collide (0.0 - 1.0)
c1 (number, optional) – End collide (0.0 - 1.0)
interpolation (string, optional) – Interpolation method: linear, smooth, easein, easeout or constant. Default is linear.
fadein (number, optional) – Fade in between t=0 and t=fadein. Default is zero.
fadeout (number, optional) – Fade out between t=fadeout and t=1. Default is one.

### ParticleFlags

```
ParticleFlags(bitmask)
```

Arguments
bitmask (number) – Particle flags (bitmask 0-65535)

### SpawnParticle

```
SpawnParticle(pos, velocity, lifetime)
```

Arguments
pos (TVec) – World space point as vector
velocity (TVec) – World space velocity as vector
lifetime (number) – Particle lifetime in seconds

Explosion and SpawnFire (full entries) are under MakeHole above.


## Other helpers possibly relevant

### StartLevel

```
StartLevel(mission, path, [layers], [passThrough])
```

Arguments
mission (string) – An identifier of your choice
path (string) – Path to level XML file
layers (string, optional) – Active layers. Default is no layers.
passThrough (boolean, optional) – If set, loading screen will have no text and music will keep playing
Return value
none
Start a level

Doc example:
```lua
function server.init()
	--Start level with no active layers
	StartLevel("level1", "MOD/level1.xml")

	--Start level with two layers
	StartLevel("level1", "MOD/level1.xml", "vehicles targets")
end
```

### ServerCall

```
ServerCall(function, [param1, param2, .., paramN])
```

Arguments
function (string) – Name of the function to be invoked. This function must exist within issuing script.
param1, param2, .., paramN (any, optional) – Optional parameters to send to the server. Arguments should match the signature of the specified function.
Return value
none

Doc example:
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

### ClientCall

```
ClientCall(playerId, function, [param1, param2, .., paramN])
```

Arguments
playerId (number) – Player ID of the recipient. Use 0 to broadcast to every player.
function (string) – Name of the function to be invoked. This function must exist within issuing script.
param1, param2, .., paramN (any, optional) – Optional parameters to send to the recipent(s). Arguments should match the signature of the specified function.
Return value
none

Doc example:
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

### IsPlayerGrounded

```
isGrounded = IsPlayerGrounded([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
isGrounded (boolean) – Whether the player is grounded

Doc example:
```lua
local isGrounded = IsPlayerGrounded()
```

### GetPlayerGrabBody

```
handle = GetPlayerGrabBody([playerId])
```

Arguments
playerId (number, optional) – Player ID. On client, zero means client player. On server, zero means server (host) player.
Return value
handle (number) – Handle to grabbed body or zero if not grabbing.

Doc example:
```lua
function client.tick()
	local body = GetPlayerGrabBody()
	if body ~= 0 then
		DebugPrint("Player is grabbing a body")
	end
end
```


# 3. XML / level format

## 3a. Mod folder layout and info.txt

> ## Building a Mod
>
> A Teardown mod is a single Windows folder where all the files needed by the mod are stored. A mod folder typically contains a text file with information about the mod, script files that extend or override game play, editor XML files with the level environment information plus all the other resources used by the mod such as vox, image and sound files. 
> ``` 
> "My Documents"
> ├── Teardown
>     ├── Mods
>         ├── MyMod1                      # Custom mod 1
>             ├── info.txt                # Mod info
>             ├── main.lua                # Mod main lua script 
>             ├── main.xml                # Content mod main XML file 
>             ├── mylevel2.xml            # Content mod XML file
>             ├── options.lua             # Mod options
>             ├── preview.jpg             # Steam Workshop thumbnail image
>             ├── images                  # Image resources
>             ├── scripts               	# Mod Lua scripts
>             ├── sound                   # Sound resources
>             ├── vox                     # Vox files
>             |   └── bench.vox           # Mod specific vox file(s)
>             └── ...
>         ├── MyMod2                      # Custom mod 2
> 			└── ...
> ```
> Please take care to only use Latin alphanumerical characters (a-z 0-9 and space) as the game might otherwise have issues loading your mod. You can choose your own directory structure within the mod but *info.txt*, *main.xml*, *main.lua*, *options.lua* and *preview.jpg* should always be placed in the mod root folder. 
>
> ####	info.txt 
>
> All mods need a info.txt file. This file contains the name of the mod, the name of the author, and a short description of the mod.
> The tags key is an optional comma separated list of tags used to categorize the mod in the Steam Workshop. 
> Valid tags are: **Map, Gameplay, Asset, Vehicle, Tool**.
> ```markdown
> name = Laser Gun
> author = Tuxedo Labs
> description = Custom tool example mod. Laser gun that cuts through most materials
> tags = Tool
> ```
> This is the full contents of the *info.txt* file for the Laser Gun mod. This information is shown when a mod is selected in the **Mod manager**.

Also (index page):

> ####	main.xml
> If the mod has a *main.xml* file, the game will classify the mod as a Content mod. The *main.xml* file contains the level data for the environment in the mod. In the *main.xml* file (and all xml-files for levels) the keyword **MOD** is used as a reference to the mods folder. For example, if you are using a vox file in your *main.xml*:
>
> ![MOD/ contains the path to your mod in the filesystem](images/mod_path.jpg)
>
> The above path would point to the voxel file *tree-pine-small.vox* in the vox folder you created for your mod.

> ####	main.lua
> Any *main.lua* file in your mods folder will be run whenever your mod is active. For Global mods, whenever the game is played and the mod is enabled, or for Content mods, whenever that mod is played. See chapter [Scripting](#Scripting) for more info on scripting with Lua in Teardown
>
> #### options.lua
> If the mod has an *options.lua* file, an **Options** button will be shown when the mod is selected in the Mod manager.
> ![Options Button](images/mod_options_button.png)![Speedometer Options](images/speedometer_options.png)
> When the Options button is clicked, the game will run the *options.lua* file in the mods folder. The *options.lua* file should contain a `draw()` function, containing the code for the options screen. Take a look at the *options.lua* file in the Speedometer mod to start getting an insight into how this is done. 
>
> ####	main.lua (from base game)  
> To equip the player with the same tools they have unlocked and upgraded in the main game, include the main.lua script from the main game.
> ![Pressing the "..." button will show all scripts available from the base game](images/main_lua.jpg)
>
> ####	spawn.txt
> This is an optional file that is used for exporting prefabs as [spawnable assets](#Modding/spawnableassets)

**info.txt keys:** from the docs, exactly: `name`, `author`, `description`, `tags` (tags is "an optional comma separated list ... Valid tags are: **Map, Gameplay, Asset, Vehicle, Tool**"). **`version`: NOT FOUND IN DOCS** (the word does not appear as an info.txt key; the shown example has only name, author, description, tags). Also from the Workshop section: "You also need to have a **preview.jpg** image file in the mod folder" and "To publish your mod fill out the information in info.txt in your mod folder and add a file named preview.jpg (max file size 1mb)"; on first publish "the file id.txt is created in the mod folder".

### Mod types (Global vs Content), verbatim

> ## Mod Types
>
> There are two kind of mods that can be implemented for Teardown; **Global mods** and **Content mods**.
>
> **Global mods** are mods which have an effect during all gameplay in the game. When enabled, they are active during all gameplay in Teardown, whether that's the Campaign, Sandbox or other people's Content mods. All enabled Global mods are also listed on the the loading screen when loading an environment or a mission.
>
> **Content mods** are mods which contains playable environments, such as custom sandbox environments or environments with missions.  Unlike **Global mods** the **Content mods** can be played as their own experiences, and they do not have an effect when playing other content, such as Sandbox environments or the campaign. Unlike Global mods, a Content mod must have a *main.xml* file containing the level data for the mod. A play button is shown in the info pane when a Content mod is selected in the Mod manager. Clicking the **Play** button loads and starts the mod. 

### Replacing default content, verbatim

> ## Default Content Replacement 
> Mods can replace the default content of the game by replicating the data structure of the games "data" folder. For example, to replace the model for the pipebomb, put your vox model in the "*data\vox\pipebomb.vox*" folder in your mod folder.
>
> ![Vox Replacement](images/vox_replacement.png)
>
> Now this vox model will replace the default model for the thrown pipebomb whenever your mod is played, or, if it is an enabled Global mod, whenever the game is played at all.
>
> The banana *pipebomb.vox* can be downloaded [here](downloadable/pipebomb.vox).
>
> Sound effects and music in Teardown is using the .ogg audio format. Each song and sound effect is available as an individual file in the game file structure. Due to licensing reasons all .ogg audio files that comes with Teardown have been encrypted into .tde files that can only be read by the game. It is possible to override an encrypted .tde files by adding a new .ogg file with the same filename (excluding the .tde extension) to the same directory. The game will automatically load the file with the expected name and the .ogg extension prior to loading a file with the .tde extension.  

### Spawnable assets / spawn.txt, verbatim

> ## Spawnable assets
>
> When making a mod you can choose to export assets that become available through the built-in spawn menu. In order to export an asset, you must first convert it to a prefab, so the asset has a separate XML file. Check the [prefabs](#Editor/Prefabs) section of editor documentation for details. Note that static objects will be converted to dynamic when using the built-in spawn menu.
>
> Once you have the prefab file, you can list it in the spawn.txt text file in your mod folder. Create the text file if it does not already exist and add one line for each spawnable prefab in the following format:
>
> ```txt
> path/to/mycar.xml : Cars/My car
> ```
>
> This will export the prefab so that it becomes available in the built in spawn menu as "My car" under the "Cars" category. The path is relative you mod root folder, so if your mod folder is **Documents/Teardown/mods/mymod**, the prefab file in the above example should be in **Documents/Teardown/mods/mymod/path/to/mycar.xml**
>

### Multi-scene mods / StartLevel, verbatim

> ## Multi-Scene mods
>
> A Content mod in Teardown always implement at least one playable level in the *main.xml* file. The mod may also implement additional levels that can be loaded at run-time. Each level is implemented a separate XML file using the [Editor](#Editor). When a user clicks the "Play" button in the The Mod Manager the game loads the *main.xml* and invokes the *main.lua* script. Loading a different level from within the Mod is done with the script API function`StartLevel()`
> ```lua
> -- Load level 2 
> StartLevel("level2", "MOD/mymodlevel2.xml")
> ```

### MOD and LEVEL path keywords, verbatim

> ## File paths
> Paths in the editor uses two keywords, MOD and LEVEL, to reference context specific paths when working with mods.
> **MOD** references the root folder of the current mod.
> **LEVEL** references the folder with the same name as the currently open XML file. The folder and the xml file must be in the same folder in the hierarchy.
>
> ```
> "My Documents"
> ├── Teardown
>     ├── Mods
>         ├── MyMod1                  # MOD references this folder
>             ├── main.xml            # Content mod main XML file 
>             ├── mylevel2.xml        # Content mod XML file
>             ├── mythirdlevel.xml    # Content mod XML file
>             ├── main                # LEVEL references this folder IF the main.xml is open in the editor
>             |   └── ...
>             ├── mylevel2            # LEVEL references this folder IF the mylevel2.xml is open in the editor
>             |   └── ...
>             ├── mythirdlevel        # LEVEL references this folder IF the mythirdlevel.xml is open in the editor
>             |   └── ...
>             └── ...

### Layers (groups for level variants), verbatim

> ## Layers 
>
> Layers in the Editor is a feature that can be used to create multiple variants of the same level. A [Group](#groups) can be configured to only show up for a particular layer. A level can be run with no or with any combination of enabled layers to provide different types of gameplay. Create a layer by editing the "layer" property on a Group. The layer will automatically occur in the Layers Window in the Editor. You can choose to disable or enable any combination of layers by clicking the layers in the Window. When the level is played from the Editor File &rightarrow; Play all enabled layers in the Layers Window are loaded. Disabling a Layer in the Editor will hide that particular group from the Scene Explorer. When a Group is hidden in the "Layers" window the objects within the Group are hidden in the 3D view as well.  
>
> ![Heist and secrets layer enabled](images/editor_layers.jpg)
>
> The image above shows the layers "heist" and "secrets" as enabled and "sandbox" as disabled. The disabled "sandbox" layer is muted in the Scene Explorer and hidden from the 3D view to reduce clutter, press V to toggle the visiblilty of hidden layers in the 3D view. It is possible to choose which layers to enable when loading a level from a script with `StartLevel()`
>
> ```lua
> -- Load level 2 with Layers 'heist' and 'secrets' active
> StartLevel("level2", "MOD/mymodlevel2.xml", "heist secrets")
> ```
>
> ```lua
> -- Load level 2 with Layer 'sandbox' active
> StartLevel("level2", "MOD/mymodlevel2.xml", "sandbox")
> ```
>
> It is also possible to disable Groups for specific layers. The image below show a Content Mod that implement three missions as three different layers (car_theft, drag_race, running_man). The level has put all the car objects in a group called "Cars". The "Cars" Group is not a layer on it's own and is visible by default for all layers. Let's say that the mission "running_man" should be played without cars. By using a "minus layer" the "Cars" group can be excluded when a specific layer is loaded. A "minus layer" is the name of the layer to be excluded from prefixed with a "-" character. Adding "-running_man" to  the Car Group will exclude all objects from that Group when the "running_man" layer is loaded.
>
> ![Excluding Layers](images/minus_layer.png)

### Editor help system pointer, verbatim

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

### Level XML hierarchy and inheritance, verbatim

> All level content is stored as standard XML meaning that everything in the file is a hierarchy of node objects. The structure of the nodes in the file is directly mapped to the view in the Scene Explorer. Teardown implement support for property inheritance in the Editor. Child nodes will inherit the properties of their parent unless the property is explicitly set for the child. Inheritance allows you to put objects you want to share a common property inside of Groups and then set the property only once on the Group node. All the objects within the group will inherit the properties of the Group itself. This makes Groups useful not only as a way to keep the Scene Explorer tidy but as a way to logically group objects with similar properties.   

## 3b. XML elements

The index page states: "All level content is stored as standard XML meaning that everything in the file is a hierarchy of node objects. The structure of the nodes in the file is directly mapped to the view in the Scene Explorer." and "The Property Window shows all valid properties for the specific type of object currently selected in the Scene Explorer." The public docs contain **no written element or attribute reference**; the closest thing is the doc screenshots, transcribed in 3c. Per element:

| Element | Status in docs |
|---|---|
| `<scene>` | NOT FOUND IN DOCS as written text. Screenshots show a root node typed `[scene]` (named `main` or `main.xml`). |
| `<environment>` (all attributes) | NOT FOUND IN DOCS. A node typed `[environment]` appears in screenshots (named "Environment" or unnamed) but its properties are never shown. The Lua `SetEnvironmentProperty`/`GetEnvironmentProperty` say the properties are "exactly the same as in the editor" (see Environment section). |
| `<spawnpoint>` | NOT FOUND IN DOCS as written text (zero hits for "spawnpoint" in api.html, index.html, api.xml). Screenshots show a node typed `[spawnpoint]` ("Player spawn [spawnpoint]", "spawnpoint [spawnpoint]"); properties not shown. Lua side: `SetPlayerSpawnTransform`. |
| `<body>` | NOT FOUND IN DOCS as written text. A node typed `[body]` appears in screenshots (e.g. "Target [body]"); properties not shown. |
| `<shape>` / `<vox>` (file, object, scale, texture, density, strength) | NOT FOUND IN DOCS as written text. The node type is `[vox]` (not `shape`). Its property list and defaults ARE visible in two doc screenshots: see 3c. |
| `<voxbox>` | Node type `[voxbox]` appears in screenshots (property list not shown). In text it appears only in the Spawn example string: `<voxbox size='10 10 10' prop='true' material='wood'/>` (attributes `size`, `prop`, `material`; no attribute list). |
| `<boundary>` | NOT FOUND IN DOCS as written text. Node typed `[boundary]` appears in screenshots; properties not shown. |
| `<script>` | NOT FOUND IN DOCS as written text. Node typed `[script]` appears in screenshots (children of a `Script [group]`, named `main`, `sandbox`, `heist`, `alarmbox`). api.html "Parameters" section says: "Scripts can have parameters defined in the level XML file." (syntax not shown) |
| `<prefab>` | NOT FOUND IN DOCS as an element name. Concept only (see Spawn section). Screenshots show prefab uses as `[instance]` nodes (e.g. `designer_lamp [instance]`, `pickup1 [instance]`); the Property Window mentions a `template` property. |
| `<location>` | NOT FOUND IN DOCS as XML. Editor Help topic list has "Location". Lua: "Locations are transforms placed in the editor as markers. Location transforms are always expressed in world space coordinates." |
| `<trigger>` | NOT FOUND IN DOCS as XML. Editor Help topic list has "Trigger". Lua: "Triggers can be placed in the scene and queried by scripts to see if something is within a certain part of the scene." |
| `<light>` | NOT FOUND IN DOCS as XML. Editor Help topic list has "Light"; api.html has a "Light" Lua section. |


## 3c. Facts visible only in documentation screenshots (images the docs link to)

Fetched from https://www.teardowngame.com/modding/images/ and read by eye. These are NOT text quotes; treat as "what the docs' pictures show".

**Editor Help window (`editor_help.png`)**: the left list is "General, Controls, Nodes and properties, Paths, Bodies and shapes, Layers", then a second list of node types: **Scene, Body, Boundary, Compound, Environment, Group, Instance, Joint, Light, Location, Rope, Screen, Script, Spawnpoint, Trigger, Vehicle, Vox, Voxbox, Voxagon, Voxscript, Water, Wheel**. The General page reads: "The teardown editor is used in combination with MagicaVoxel to create content for Teardown. The scene explorer on the left shows the scene structure, while the graphical 3D view gives a visual representation. When selecting an object in the scene explorer, the corresponding object will be highlighted in the 3D view and vice versa."

**Scene explorer (`editor_scene_explorer_1.png`)**: `main [scene]` contains `Script [group]` (with `main [script]`, `sandbox [script]`), `Scene [group]` (`Ground [group]`, `Trees [group]`, `House [group]` ... `Car [group]` with `saloncar [instance]`), then siblings `Environment [environment]`, `Player spawn [spawnpoint]`, `Boundary [boundary]`.

**`[vox]` node property window (`mod_path.jpg`, `editor_help_tooltip.png`)**, in display order: `name`, `template`, `tags`, `pos`, `rot`, `desc`, `texture`, `blendtexture`, `density`, `strength`, `collide`, `prop`, `file`, `object`, `scale`. Values/defaults shown: `pos` "21.0 1.0 23.0"; `rot` "0.0 0.0 0.0" (another vox shows "-6.8 -166.2 -24.5" and a joint shows "-90.0 180.0 0.0", values look like degrees but units are not stated in text); `density` default (greyed) 1.0; `strength` default (greyed) 1.0; `collide` default (greyed) true; `prop` default (greyed) false (set to true on `small_junk1`, shown highlighted); `file` "MOD/vox/tree-pine-small.vox" or "MOD/vox/junk.vox"; `object` empty or "small_junk1" (the object name inside the .vox); `scale` 1. Node label example: `junk:small_junk1 [vox]`.

**Tooltip text on `texture` (verbatim from `editor_help_tooltip.png`)**: "Texture tile 0-15. Optional second argument is texture weight 0.0-1.0)".

**Group node (`minus_layer.png`)**: properties `name`, `template`, `tags`, `pos`, `rot`, `layer`, `prop0`, ... ; `layer` value "-running_man" (leading "-" = minus layer, see Layers text). Label shown: `Cars [group] (-running_man)`.

**Joint node (`editor_properties.png`)**: `name`, `template`, `tags`, `pos` "17 4 6", `rot` "-90.0 180.0 0.0", `type` "hinge", `size` 0.125, `rotstrength` (default 0.025), `rotspring` (default 0.1), `collide` (default false), `limits` "0 150", `sound` (default false).

**Tags (`editor_tags_2.png`, `search_window.jpg`)**: a tag with a value is entered in the `tags` property as `foo=bar`; several tags are shown space-separated in the Search window results (e.g. "target unbreak..."). A `voxbox` child named `box2` of a `[script]` under `scripts [group]` appears in the tag example. Search window fields: Type, Name, Tag, Property, Explicit property, and options "Search selected", "Search hidden", "Search instances".

**Environment properties**: NOT shown in any screenshot.


### Light-related Lua section intro (for reference only)

Light sources can be of several differnt types and configured in the editor. If a light source is owned
by a shape, the intensity of the light source is scaled by the emissive scale of that shape. If the
parent shape breaks, the emissive scale is set to zero and the light source is disabled. A light source
without a parent shape will always emit light, unless exlicitly disabled by a script.

# 4. Materials: palette index to material mapping

## 4a. What the docs say about how material is detected

Verbatim:

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

Also verbatim (material appearance does not affect material type):

> The different material appearances in Teardown can be described as dull metal, shiny metal, diffuse, emissive and glass, as shown in  the image above. Observe that the material appearance doesn't affect what material Teardown assigns to a voxel. An object made of colors in the  wood group (indices 57 - 72) will still be wood in the game, even if you make it look like metal.

Also (hard vs soft ordering in objects), verbatim:

> Softer materials should never be placed inside or between harder material as they risk becoming loose and get stuck between the hard surrounding material, causing problems for the physics. Especially in situations where the space available for the softer material is very tight. One example is when making brick walls. It might feel natural to make the grout between the individual bricks in a softer material, like plaster. But this causes issues when the wall is damaged and pieces of the softer plaster is broken and get stuck between the bricks. It is better to also make the grout out of the brick material, but in an appropriately lighter color. Metal rebar in concrete is a good example of the opposite situation, where a harder material is encapsulated by a softer material. As long as the hard material doesn't create pockets of soft material inside hard material. 

## 4b. Hardness table (verbatim from the index page)

The following is a list of all materials, their respective hardness from softest to hardest, and whether the sledgehammer, blowtorch, explosives and guns (handgun and shotgun) affects them.

| Material     | Hardness    | Sledge | Blowtorch | Guns  | Explosives |
| :----------- | :---------- | :----- | :-------- | :---- | :--------- |
| Glass        | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
| Grass        | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
| Dirt         | Soft        | **✓**  | ✗         | **✓** | **✓**      |
| Plastic      | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
| Wood         | Soft        | **✓**  | **✓**     | **✓** | **✓**      |
| Plaster      | Soft        | **✓**  | ✗         | **✓** | **✓**      |
| Concrete     | Medium      | ✗      | ✗         | **✓** | **✓**      |
| Brick        | Medium      | ✗      | ✗         | **✓** | **✓**      |
| Weak Metal   | Medium      | ✗      | **✓**     | **✓** | **✓**      |
| Hard Masonry | Hard        | ✗      | ✗         | ✗     | **✓**      |
| Hard Metal   | Hard        | ✗      | ✗         | ✗     | **✓**      |
| Heavy Metal  | Unbreakable | ✗      | ✗         | ✗     | ✗          |
| Rock         | Unbreakable | ✗      | ✗         | ✗     | ✗          |

## 4c. Palette index ranges per material

**The docs contain no text table of index ranges.** They show an image (`images/teardown_palette.png`, 219x417) and say "The palette can be downloaded [here](downloadable/teardown_palette.vox)". The only index numbers stated in prose are: "the color at index 9 is always grass" and "the wood group (indices 57 - 72)".

The downloaded `teardown_palette.vox` stores the annotation as a MagicaVoxel `NOTE` chunk with 32 entries (one per row of 8 palette colours, listed top row first, exactly as drawn in the image):

```
row  1 reserved      row 17 weak metal
row  2 reserved      row 18 plaster
row  3 unphysical    row 19 plaster
row  4 unphysical    row 20 brick
row  5 reserved      row 21 brick
row  6 reserved      row 22 concrete
row  7 reserved      row 23 concrete
row  8 reserved      row 24 wood
row  9 reserved      row 25 wood
row 10 hard masonry  row 26 rock
row 11 hard metal    row 27 rock
row 12 plastic       row 28 dirt
row 13 plastic       row 29 dirt
row 14 heavy metal   row 30 grass
row 15 heavy metal   row 31 grass
row 16 weak metal    row 32 glass
```

**Derived (NOT quoted, inferred) index ranges.** If the palette is numbered from the bottom row upward, starting at 1 (so the glass row is indices 1-8), then the two prose anchors both hold: grass starts at index 9 and wood spans 57-72. A top-down numbering would put wood at about 185-200 and index 9 in a `reserved` row, contradicting the docs, so bottom-up is the reading that fits. (The vox file also contains a non-identity `IMAP` chunk, so the file alone cannot confirm it.) Applying bottom-up numbering to the 32 rows above gives:

| Material (palette label) | Indices (derived) | Hardness per docs table |
|---|---|---|
| glass | 1-8 | Soft |
| grass (MakeHole calls it "foliage") | 9-24 | Soft |
| dirt | 25-40 | Soft |
| rock | 41-56 | Unbreakable |
| wood | 57-72 (stated in docs) | Soft |
| concrete | 73-88 | Medium |
| brick | 89-104 | Medium |
| plaster | 105-120 | Soft |
| weak metal | 121-136 | Medium |
| heavy metal | 137-152 | Unbreakable |
| plastic | 153-168 | Soft |
| hard metal | 169-176 | Hard |
| hard masonry | 177-184 | Hard |
| reserved | 185-224 | (no hardness listed) |
| unphysical | 225-240 | (no hardness listed; the docs mention "unphysical voxels" only in `GetShapeMaterialAtPosition`'s `includeUnphysical` argument: "Include unphysical voxels in the search. Default false.") |
| reserved | 241-255 | (no hardness listed) |

Treat the ranges as derived-from-the-docs-files, not as a literal quote; verify in game or by opening `teardown_palette.vox` in MagicaVoxel and hovering a colour ("The index will be shown in the console at the bottom of the screen"). Names the docs use for a few of these elsewhere: the Lua `GetShapeMaterialAtPosition` returns a material name string (see Shape section).

## 4d. Rendering properties (glass, emissive, metal), verbatim

> Apart from color and material, voxels can also have properties which define how they are rendered in the game, such as: metal, glass  and emissive voxels. To access these settings you need to switch MagicaVoxel to render mode. This is done by pressing the **Render** button on the top left.
>
> ![](images/magicavoxel_render_button.png)
>
> Once in **Render** mode a new set of options is shown to the right of the 3D view.
>
> ![](images/magicavoxel_material_settings.png)
>
> In most cases, a material should be of the type **Metal**, as shown in the image above. The only exceptions being glass and emissive materials. (Diffuse is the same as Metal with max roughness  and hence also ok). The roughness value controls how rough contra smooth a surface is. It is very uncommon for materials to have 0 roughness. The metallic value controls how metallic a material is, but  also how specular it is. Metallic materials tint the specular color, the highlights in a material. While not exactly correct, you can think of  this as reflectivity. At 0 the material is non-reflective, at 100 it is  totally reflective. Like a mirror (even though real mirrors are never  100% reflective).  
>
> For **Emissive** materials (Emit) we have emission which controls  how emissive the material is, and power, which acts like a factor making the emission stronger.
>
> For **Glass** materials the settings are the same as for metallic  materials, but the metallic value is replaced by transparency. The  transparency value only matters whether it is 100 or not. 100 means  non-transparent, and any other value means transparent. The actual value between 0-99 doesn't matter, they are all as transparent. The roughness value has no impact on glass.
>
> Be aware that the appearance of the materials  does not match 1:1 between MagicaVoxel and Teardown. For best results,  save your project and check it in the game.

# 5. Scale and size limits

## Metres per voxel

- `GetShapeSize` return value: "`scale` (number) – The size of one voxel in meters (with default scale it is 0.1)". So **one voxel = 0.1 m by default**, and a shape-level scale can change it. (`GetShapeSize` is quoted in full in the Shape section.)
- The `[vox]` node's `scale` property is shown with value `1` in the doc screenshots (see 3c). The docs never state its unit in text, but `GetShapeSize` calls the returned value "The size of one voxel in meters", so a node `scale` of 1 is consistent with the 0.1 m default. (The doc's `SpawnTool` has an unrelated `voxScale` argument: "Applies a scale to voxels (default 1.0)".)


## Can a vox shape exceed 256 voxels per axis?

The only stated limit is for MagicaVoxel objects (index page, verbatim):

> Each individual object can be a maximum of 256 * 256 * 256 voxels in size. But you can create more objects to make bigger levels. For performance reasons we recommend that you don't use objects at the maximum size, as it might cause stutters in the game. Objects of half that size in all axis (128 * 128 * 128) are generally OK. Very big but flat objects are also OK., i.e., 256 * 256 * 10.

The docs state no limit on shapes created at runtime. `CreateShape` makes a 1x1x1 shape and `ResizeShape` takes arbitrary min/max coordinates with no stated maximum; neither entry mentions 256. So whether a runtime-resized shape can exceed 256 per axis: **NOT FOUND IN DOCS**.

### CreateShape

```
newShape = CreateShape(body, transform, refShape)
```

Arguments
body (number) – Body handle
transform (TTransform) – Shape transform in body space
refShape (number or string) – Handle to reference shape or path to vox file
Return value
newShape (number) – Handle of new shape
Create new, empty shape on existing body using the palette of a reference shape.
The reference shape can be any existing shape in the scene or an external vox file.
The size of the new shape will be 1x1x1.

Doc example:
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

### ResizeShape

```
resized, offset = ResizeShape(shape, xmi, ymi, zmi, xma, yma, zma)
```

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

Doc example:
```lua
function server.init()
	ResizeShape(FindShape("shape", true), -5, 0, -5, 5, 5, 5)
end
```


Empty-space advice (index page, verbatim) relevant to building a large village in few objects:

> #### Empty Space in Objects
>
> ![](images/magicavoxel_tree.png)
>
> Objects with a lot of empty space should be divided into several objects. This helps the engine avoid spending time traversing empty space inside objects. The tree above is separated into two objects. One for the crown, and one for the trunk. Thereby eliminating unnecessary empty space around the trunk. Another good example is a house. A house should never be built in one single object. Instead walls and floors should be divided into thinner objects.
>
> ![](images/magicavoxel_house_objects.png)
>
> In this image, the house to the left is divided into four separate objects, which is the correct way to do it. In the house to the right all walls are built in one single object, creating a lot of unnecessary empty space. Building assets the right way can greatly impact the performance of your levels positively. 

Voxel connectivity (index page, verbatim):

> #### Voxel Connectivity
> For voxels to correctly "stick" together in the game, they need to connect on their sides. Voxels touching only through their edges or corners will not stay together in the game. Such constructions will fall apart the moment the are damaged or otherwise become dynamic in the game.
>
> ![](images/magicavoxel_voxel_connectivity.png)
>
> In the image above, the red/green voxel pairs are incorrectly connected. The blue/purple voxel pair is correctly connected along the voxels sides.
