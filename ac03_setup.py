#!/usr/bin/env python3
"""Create all automations for AC_03 and update general automations/scripts."""
import json, urllib.request

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
BASE = "http://localhost:8123"

def get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=body,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def insert_after(lst, match_key, match_val, new_item):
    """Insert new_item after the first item where item[match_key] == match_val."""
    for i, item in enumerate(lst):
        if item.get(match_key) == match_val:
            lst.insert(i + 1, new_item)
            return True
    return False

# ── 1. Per-AC automations (clone from AC_01) ─────────────────────────────────
templates = [
    ("ac01_auto_off_2h",    "ac03_auto_off_2h"),
    ("ac01_set_to_50_power","ac03_set_to_50_power"),
    ("ac01_night_auto_26",  "ac03_night_auto_26"),
    ("ac01_night_quiet_27", "ac03_night_quiet_27"),
]

print("=== Per-AC Automations ===")
for src, dst in templates:
    config = get(f"/api/config/automation/config/{src}")
    s = json.dumps(config)
    s = s.replace("ac_01", "ac_03").replace("ac01", "ac03").replace("AC_01", "AC_03")
    config = json.loads(s)
    r = post(f"/api/config/automation/config/{dst}", config)
    print(f"  {dst}: {r.get('result')} | {config['alias']}")

# ── 2. Update auto_reconnect: add ac_03 to OR conditions ─────────────────────
print("\n=== General Automations ===")
config = get("/api/config/automation/config/toshiba_ac_auto_reconnect")
or_conditions = config["conditions"][0]["conditions"]
new_cond = {"condition": "state", "entity_id": "climate.ac_03", "state": "unavailable"}
if not any(c.get("entity_id") == "climate.ac_03" for c in or_conditions):
    insert_after(or_conditions, "entity_id", "climate.ac_02", new_cond)
r = post("/api/config/automation/config/toshiba_ac_auto_reconnect", config)
print(f"  toshiba_ac_auto_reconnect: {r.get('result')}")

# ── 3. Update daily_reauth: same OR condition structure ───────────────────────
config = get("/api/config/automation/config/toshiba_ac_daily_reauth")
# Find the or-condition block that lists ACs
def find_or_conditions(obj):
    if isinstance(obj, list):
        for item in obj:
            result = find_or_conditions(item)
            if result is not None:
                return result
    elif isinstance(obj, dict):
        if obj.get("condition") == "or" and "conditions" in obj:
            conds = obj["conditions"]
            if any(c.get("entity_id", "").startswith("climate.ac_") for c in conds):
                return conds
        for v in obj.values():
            result = find_or_conditions(v)
            if result is not None:
                return result
    return None

or_conditions = find_or_conditions(config)
if or_conditions is not None:
    new_cond = {"condition": "state", "entity_id": "climate.ac_03", "state": ["unavailable", "unknown"]}
    if not any(c.get("entity_id") == "climate.ac_03" for c in or_conditions):
        insert_after(or_conditions, "entity_id", "climate.ac_02", new_cond)
r = post("/api/config/automation/config/toshiba_ac_daily_reauth", config)
print(f"  toshiba_ac_daily_reauth: {r.get('result')}")

# ── 4. Update all_acs_turn_off: add ac_03 to entity_id list ──────────────────
print("\n=== Scripts ===")
config = get("/api/config/script/config/all_acs_turn_off")
entity_list = config["sequence"][0]["target"]["entity_id"]
if "climate.ac_03" not in entity_list:
    insert_after(entity_list, None, "climate.ac_02", "climate.ac_03")
    # insert_after won't work on strings, do it manually
    idx = entity_list.index("climate.ac_02")
    entity_list.insert(idx + 1, "climate.ac_03")
    entity_list = list(dict.fromkeys(entity_list))  # deduplicate
    config["sequence"][0]["target"]["entity_id"] = entity_list
r = post("/api/config/script/config/all_acs_turn_off", config)
print(f"  all_acs_turn_off: {r.get('result')}")

# ── 5. Update all_acs_set_low_fan: insert ac_03 block after ac_02 ─────────────
config = get("/api/config/script/config/all_acs_set_low_fan")
sequence = config["sequence"]

def make_low_fan_block(entity_id):
    return {
        "if": [{"condition": "not", "conditions": [
            {"condition": "state", "entity_id": entity_id, "state": ["off", "unavailable", "unknown"]}
        ]}],
        "then": [{"action": "climate.set_fan_mode", "target": {"entity_id": entity_id},
                  "data": {"fan_mode": "Low"}, "continue_on_error": True}]
    }

def find_ac_block_index(seq, entity_id):
    for i, step in enumerate(seq):
        conds = step.get("if", [{}])[0].get("conditions", [{}]) if step.get("if") else []
        if any(c.get("entity_id") == entity_id for c in conds):
            return i
    return -1

if find_ac_block_index(sequence, "climate.ac_03") == -1:
    idx = find_ac_block_index(sequence, "climate.ac_02")
    sequence.insert(idx + 1, make_low_fan_block("climate.ac_03"))
r = post("/api/config/script/config/all_acs_set_low_fan", config)
print(f"  all_acs_set_low_fan: {r.get('result')}")

print("\nAll done!")
