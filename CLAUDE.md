# Home Assistant — Claude Session Context

## Infrastructure

| Item | Value |
|---|---|
| HA URL | http://localhost:8123 |
| HA Version | Docker (ghcr.io/home-assistant/home-assistant:stable) |
| Docker Compose | `docker-compose.yml` in repo root |
| HA Token | `~/.claude/projects/C--repos-home-assistant/memory/reference_ha_token.md` |
| WiZ Subnet | 192.168.68.0/24 |
| WiZ Home ID | 19299149 |
| WiZ Devices | 59 lights across 10 bungalows |

**Docker networking:** `network_mode: host` does NOT work on Windows Docker Desktop — WiZ UDP broadcast discovery is broken. Always add devices manually by IP. Unicast UDP (control/state) works fine once added. Ports `38899/udp` and `38900/udp` in docker-compose.yml.

## HA API Access

```powershell
$token   = "<see memory/reference_ha_token.md>"
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$base    = "http://localhost:8123"
```

**WebSocket** (entity/device registry ops): connect to `ws://localhost:8123/api/websocket`, auth with `{type:"auth", access_token:$token}`, increment `$msgId` every send.

Key WS commands:
- Rename entity: `config/entity_registry/update` → `entity_id`, `new_entity_id`, `name`
- Rename device: `config/device_registry/update` → `device_id`, `name_by_user`
- Assign labels: `config/entity_registry/update` → `labels` (array, always use `@()`)
- Create label: `config/label_registry/create` → `name`, `color`, `icon`
- Get entity: `config/entity_registry/get` → `entity_id`

## Bungalow Layout

10 lights per bungalow: 4× Room bulbs, 2× Bathroom, 2× Terrace Up, 2× Terrace Down.
Some bungalows have additional lamps — these are added separately.
Not yet in HA: 1× WiZ Remote, 1× Contact sensor per bungalow.

## WiZ Room ID Mapping

| Room ID | Bungalow |
|---|---|
| 33053946 | Bungalow 04 ✅ |
| 32321316 | Unknown |
| 33053180 | Unknown |
| 34114932 | Unknown |
| 33306107 | Unknown |
| 32474714 | Unknown |
| 32702356 | Unknown |
| 33132627 | Unknown |
| 33306693 | Unknown |
| 33436589 | Unknown |

Run `identify_rooms.ps1` to identify unknowns (blinks lights per room).

## Naming Conventions (`XX` = zero-padded: `01`–`10`)

| Type | Entity ID | Friendly Name |
|---|---|---|
| Room bulbs | `light.bungalow_XX_room_01`–`_04` | `Bungalow XX Room 01`–`04` |
| Bathroom | `light.bungalow_XX_bathroom_01`–`_02` | `Bungalow XX Bathroom 01`–`02` |
| Terrace Up | `light.bungalow_XX_terrace_up_01`–`_02` | `Bungalow XX Terrace Up 01`–`02` |
| Terrace Down | `light.bungalow_XX_terrace_down_01`–`_02` | `Bungalow XX Terrace Down 01`–`02` |

## Labels

Each light gets: `Bungalow XX` + location type (`room`/`bathroom`/`terrace`). Terrace lights also get `terrace_up` or `terrace_down`.

| Label ID | Name | Icon | Color |
|---|---|---|---|
| `bungalow_04` | Bungalow 04 | mdi:home | green |
| `room` | Room | mdi:bed | blue |
| `bathroom` | Bathroom | mdi:shower | cyan |
| `terrace` | Terrace | mdi:string-lights | amber |
| `terrace_up` | Terrace Up | mdi:arrow-up-circle | amber |
| `terrace_down` | Terrace Down | mdi:arrow-down-circle | orange |

New bungalow: create label first → `config/label_registry/create` with `name="Bungalow XX"`, `color="green"`, `icon="mdi:home"`.

## Scripts

| Script | Purpose |
|---|---|
| `scan_wiz.ps1` | Parallel UDP scan → finds all WiZ devices, saves to `wiz_devices.json` |
| `probe_wiz.ps1` | Deep probe of devices (modelConfig, state) |
| `identify_rooms.ps1` | Blinks lights per room to identify roomId → bungalow |
| `ha_api.ps1` | Add WiZ devices to HA via config flow |
| `ha_rename.ps1` | Rename entity IDs + friendly names via WebSocket |
| `ha_rename_devices.ps1` | Rename devices in HA device registry via WebSocket |
| `ha_labels.ps1` | Create labels and assign to entities |
| `ha_check.ps1` | Check entity states (used for bathroom identification) |
| `wiz_devices.json` | Last scan — 59 devices with IP/MAC/roomId |

## Workflow: Adding a New Bungalow

1. Find roomId in `wiz_devices.json` (or re-run `scan_wiz.ps1`)
2. Filter IPs by roomId
3. Add each light to HA: Settings → Devices & Services → WiZ → enter IP (or use `ha_api.ps1`)
4. Rename entities + IDs → `ha_rename.ps1`
5. Rename devices → `ha_rename_devices.ps1`
6. Identify bathroom lights: turn off physically, run `ha_check.ps1` — `UNAVAILABLE` = bathroom, `ON` = room (Docker UDP push issue causes this)
7. Assign labels → `ha_labels.ps1` (create `Bungalow XX` label first)

## Progress

| Bungalow | Lights Added | Named | Labelled |
|---|---|---|---|
| Bungalow 04 | 11/11 | Done | Done |
| Bungalow 01–03, 05–10 | 0/11 each | — | — |
