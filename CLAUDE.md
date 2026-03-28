# Home Assistant — Claude Session Context

## Infrastructure

| Item | Value |
|---|---|
| HA URL | http://localhost:8123 |
| HA Version | Docker (ghcr.io/home-assistant/home-assistant:stable) |
| Docker Compose | `docker-compose.yml` in repo root |
| HA Token | Stored in `~/.claude/projects/C--repos-home-assistant/memory/reference_ha_token.md` |
| WiZ Subnet | 192.168.68.0/24 |
| WiZ Home ID | 19299149 |
| Total WiZ Devices | 59 lights across 10 bungalows |

## Docker Networking Note
`network_mode: host` does NOT work on Windows Docker Desktop.
WiZ UDP broadcast discovery is broken — **always add devices manually by IP**.
Unicast UDP (control/state) works fine once added.
Port mappings `38899/udp` and `38900/udp` are in docker-compose.yml.

---

## HA API Access

```powershell
$token   = "<see memory/reference_ha_token.md>"
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$base    = "http://localhost:8123"
```

**WebSocket pattern** (used for entity/device registry operations):
```powershell
$ws  = New-Object System.Net.WebSockets.ClientWebSocket
$cts = New-Object System.Threading.CancellationTokenSource
$ws.ConnectAsync((New-Object System.Uri("ws://localhost:8123/api/websocket")), $cts.Token).Wait()
# Auth: send {type:"auth", access_token:$token}, recv auth_ok
# Always increment $msgId for every send
```

Key WebSocket commands:
- Rename entity: `config/entity_registry/update` with `entity_id`, `new_entity_id`, `name`
- Rename device: `config/device_registry/update` with `device_id`, `name_by_user`
- Assign labels: `config/entity_registry/update` with `labels` (array of label IDs, always use `@()`)
- Create label: `config/label_registry/create` with `name`, `color`, `icon`
- Get entity info: `config/entity_registry/get` with `entity_id`

---

## Bungalow Layout

Each bungalow has the same light setup:
- 1 × LED Strip (Room)
- 4 × Room bulbs
- 2 × Bathroom bulbs
- 2 × Terrace Up bulbs
- 2 × Terrace Down bulbs
- **Total: 11 lights per bungalow**

Additionally (not yet added to HA):
- 1 × WiZ Remote
- 1 × Contact sensor

---

## WiZ Room ID Mapping

| Room ID | Bungalow |
|---|---|
| 33053946 | Bungalow 04 ✅ done |
| 32321316 | Unknown |
| 33053180 | Unknown |
| 34114932 | Unknown |
| 33306107 | Unknown |
| 32474714 | Unknown |
| 32702356 | Unknown |
| 33132627 | Unknown |
| 33306693 | Unknown |
| 33436589 | Unknown |

To identify unknown rooms run `identify_rooms.ps1` (blinks lights per room).

---

## Naming Conventions

### Entity IDs
```
light.bungalow_XX_room_led_strip
light.bungalow_XX_room_01 ... _04
light.bungalow_XX_bathroom_01 ... _02
light.bungalow_XX_terrace_up_01 ... _02
light.bungalow_XX_terrace_down_01 ... _02
```

### Friendly Names
```
Bungalow XX Room LED Strip
Bungalow XX Room 01 ... 04
Bungalow XX Bathroom 01 ... 02
Bungalow XX Terrace Up 01 ... 02
Bungalow XX Terrace Down 01 ... 02
```

Where `XX` = zero-padded number: `01`, `02` ... `10`

---

## Label Structure

Labels are reused across all bungalows. Each light gets:
- `Bungalow XX` — bungalow-specific (e.g. `bungalow_04`)
- `Room` / `Bathroom` / `Terrace` — location type
- `Terrace Up` / `Terrace Down` — terrace sub-direction (in addition to `Terrace`)

This allows automation targeting like:
- All Bungalow 04 lights → label: `Bungalow 04`
- All Room lights (all bungalows) → label: `Room`
- Bungalow 04 Room lights only → labels: `Bungalow 04` + `Room`

### Existing Labels (already created in HA)
| Label ID | Name | Icon | Color |
|---|---|---|---|
| `bungalow_04` | Bungalow 04 | mdi:home | green |
| `room` | Room | mdi:bed | blue |
| `bathroom` | Bathroom | mdi:shower | cyan |
| `terrace` | Terrace | mdi:string-lights | amber |
| `terrace_up` | Terrace Up | mdi:arrow-up-circle | amber |
| `terrace_down` | Terrace Down | mdi:arrow-down-circle | orange |

When adding a new bungalow, create its label first:
```powershell
WsSend @{ id = $msgId; type = "config/label_registry/create"; name = "Bungalow XX"; color = "green"; icon = "mdi:home" }
```

---

## Scripts

| Script | Purpose |
|---|---|
| `scan_wiz.ps1` | Parallel UDP scan of subnet — finds all WiZ devices, saves to `wiz_devices.json` |
| `probe_wiz.ps1` | Deep probe of Bungalow 04 devices (modelConfig, state) |
| `identify_rooms.ps1` | Blinks lights per room to identify which roomId = which bungalow |
| `ha_api.ps1` | Add WiZ devices to HA via config flow, check config entries |
| `ha_rename.ps1` | Rename entity IDs + friendly names via WebSocket |
| `ha_rename_devices.ps1` | Rename devices in HA device registry via WebSocket |
| `ha_labels.ps1` | Create labels and assign to entities |
| `ha_check.ps1` | Check current entity states (useful for bathroom-off trick) |
| `wiz_devices.json` | Last scan results — 59 devices with IP/MAC/roomId |

---

## Workflow for Adding a New Bungalow

1. **Identify the bungalow's roomId** from `wiz_devices.json` (or run `scan_wiz.ps1`)
2. **Find device IPs** by filtering `wiz_devices.json` by roomId
3. **Add each light to HA** via Settings → Devices & Services → WiZ → enter IP
   - Or automate via `ha_api.ps1` config flow
4. **Rename entities + entity IDs** using `ha_rename.ps1`
5. **Rename devices** using `ha_rename_devices.ps1`
6. **Identify Bathroom vs Room lights**: turn off bathroom lights, run `ha_check.ps1` to see which are UNAVAILABLE
7. **Assign labels** using `ha_labels.ps1` (create `Bungalow XX` label first)

### Bathroom Identification Trick
Turn off bathroom lights physically, then check states:
- `ON` = Room light
- `UNAVAILABLE` = Bathroom light (HA shows unavailable instead of off due to Docker UDP push issue)

---

## Progress

| Bungalow | Lights Added | Named | Labelled |
|---|---|---|---|
| Bungalow 04 | 11/11 | Done | Done |
| Bungalow 01-03, 05-10 | 0/11 each | - | - |
