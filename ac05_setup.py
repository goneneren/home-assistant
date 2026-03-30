import json, urllib.request

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
BASE = "http://localhost:8123"
ALL_ACS = ["climate.ac_01","climate.ac_02","climate.ac_04","climate.ac_05","climate.ac_06","climate.ac_07","climate.ac_08","climate.ac_10"]
ALL_AC_IDS = ["ac_01","ac_02","ac_04","ac_05","ac_06","ac_07","ac_08","ac_10"]

def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=body,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

e = "climate.ac_05"
ac = "AC_05"
px = "ac05"

automations = [
    {
        "id": px + "_auto_off_2h",
        "alias": ac + " Auto-off after 2h (09:00-21:00)",
        "description": "If " + ac + " is turned on between 09:00 and 21:00, turn it off after 2 hours",
        "triggers": [
            {"platform": "state", "entity_id": e, "from": "off", "not_to": ["off","unavailable","unknown"]},
            {"trigger": "time", "at": "09:00:00"}
        ],
        "conditions": [{"condition": "time", "after": "09:00:00", "before": "21:00:00"}],
        "actions": [
            {"delay": {"hours": 2}},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]},
            {"target": {"entity_id": e}, "action": "climate.turn_off"}
        ],
        "mode": "restart"
    },
    {
        "id": px + "_night_auto_26",
        "alias": ac + " Night Mode - Auto 26C (21:00-00:00)",
        "description": "Between 21:00-00:00, if " + ac + " is on and fan is not Low or Quiet, set fan to Auto and temp to 26C after 10 min",
        "triggers": [
            {"trigger": "state", "entity_id": e, "from": "off", "not_to": ["off","unavailable","unknown"]},
            {"trigger": "state", "entity_id": e, "attribute": "fan_mode", "not_to": ["Low","Quiet",None]}
        ],
        "conditions": [
            {"condition": "time", "after": "21:00:00", "before": "00:00:00"},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "fan_mode", "state": "Low"}]},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "fan_mode", "state": "Quiet"}]}
        ],
        "actions": [
            {"delay": {"minutes": 10}},
            {"condition": "and", "conditions": [
                {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]},
                {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "fan_mode", "state": "Low"}]},
                {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "fan_mode", "state": "Quiet"}]}
            ]},
            {"action": "climate.set_fan_mode", "target": {"entity_id": e}, "data": {"fan_mode": "Auto"}},
            {"action": "climate.set_temperature", "target": {"entity_id": e}, "data": {"temperature": 26}}
        ],
        "mode": "restart"
    },
    {
        "id": px + "_night_quiet_27",
        "alias": ac + " Deep Night Mode - Quiet 27C (00:00-09:00)",
        "description": "Between 00:00-09:00, if " + ac + " is on and fan is not Quiet, set fan to Quiet and temp to 27C after 30 min",
        "triggers": [
            {"trigger": "state", "entity_id": e, "from": "off", "not_to": ["off","unavailable","unknown"]},
            {"trigger": "state", "entity_id": e, "attribute": "fan_mode", "not_to": ["Quiet", None]},
            {"trigger": "time", "at": "00:00:00"}
        ],
        "conditions": [
            {"condition": "time", "after": "00:00:00", "before": "09:00:00"},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "fan_mode", "state": "Quiet"}]}
        ],
        "actions": [
            {"delay": {"minutes": 30}},
            {"condition": "and", "conditions": [
                {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]},
                {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "fan_mode", "state": "Quiet"}]}
            ]},
            {"action": "climate.set_fan_mode", "target": {"entity_id": e}, "data": {"fan_mode": "Quiet"}},
            {"action": "climate.set_temperature", "target": {"entity_id": e}, "data": {"temperature": 27}}
        ],
        "mode": "restart"
    },
    {
        "id": px + "_set_fan_medium_low",
        "alias": ac + " Set Fan by Temperature (09:00-21:00)",
        "description": "When " + ac + " is on during 09:00-21:00, set fan based on temp: >29=Medium, 26-29=Medium Low, <26=Low.",
        "triggers": [
            {"trigger": "state", "entity_id": e, "from": "off", "not_to": ["off","unavailable","unknown"]},
            {"trigger": "state", "entity_id": e, "attribute": "fan_mode", "not_to": ["Medium","Medium Low","Low",None]},
            {"trigger": "state", "entity_id": e, "attribute": "current_temperature"},
            {"trigger": "time", "at": "09:00:00"}
        ],
        "conditions": [
            {"condition": "time", "after": "09:00:00", "before": "21:00:00"},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]}
        ],
        "actions": [
            {"delay": {"minutes": 10}},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "off"}]},
            {"choose": [
                {"conditions": [{"condition": "numeric_state", "entity_id": e, "attribute": "current_temperature", "above": 29}],
                 "sequence": [{"action": "climate.set_fan_mode", "target": {"entity_id": e}, "data": {"fan_mode": "Medium"}}]},
                {"conditions": [{"condition": "numeric_state", "entity_id": e, "attribute": "current_temperature", "above": 26}],
                 "sequence": [{"action": "climate.set_fan_mode", "target": {"entity_id": e}, "data": {"fan_mode": "Medium Low"}}]}
            ],
            "default": [{"action": "climate.set_fan_mode", "target": {"entity_id": e}, "data": {"fan_mode": "Low"}}]}
        ],
        "mode": "restart"
    },
    {
        "id": px + "_set_to_50_power",
        "alias": ac + " Set to 50% Power",
        "description": "",
        "triggers": [
            {"trigger": "state", "entity_id": e, "from": "off", "not_to": ["off","unavailable","unknown"]},
            {"trigger": "state", "entity_id": e, "attribute": "preset_mode", "not_to": ["Power 50", None], "for": {"seconds": 5}}
        ],
        "conditions": [
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "attribute": "preset_mode", "state": "Power 50"}]},
            {"condition": "not", "conditions": [{"condition": "state", "entity_id": e, "state": "unavailable"}]}
        ],
        "actions": [
            {"target": {"entity_id": e}, "data": {"preset_mode": "Power 50"}, "action": "climate.set_preset_mode", "continue_on_error": True}
        ],
        "mode": "single"
    }
]

for a in automations:
    r = post("/api/config/automation/config/" + a["id"], a)
    print("  " + a["id"] + ": " + str(r))

# Update auto-reconnect
r = post("/api/config/automation/config/toshiba_ac_auto_reconnect", {
    "id": "toshiba_ac_auto_reconnect",
    "alias": "Toshiba AC - Auto Reconnect on Unavailable",
    "description": "When any AC goes unavailable for 5min: 1) reload integration, 2) if still unavailable after 3min, run full re-auth",
    "triggers": [{"trigger": "state", "entity_id": "climate." + ac_id, "to": "unavailable", "for": {"minutes": 5}} for ac_id in ALL_AC_IDS],
    "conditions": [{"condition": "or", "conditions": [{"condition": "state", "entity_id": "climate." + ac_id, "state": "unavailable"} for ac_id in ALL_AC_IDS]}],
    "actions": [
        {"action": "homeassistant.reload_config_entry", "data": {"entry_id": "01KMZ3JPFN83S4C92WETER428D"}},
        {"delay": {"minutes": 3}},
        {"condition": "or", "conditions": [{"condition": "state", "entity_id": "climate." + ac_id, "state": "unavailable"} for ac_id in ALL_AC_IDS]},
        {"action": "shell_command.toshiba_reauth"}
    ],
    "mode": "single"
})
print("  toshiba_ac_auto_reconnect: " + str(r))

# Update Set Low Fan script
r = post("/api/config/script/config/all_acs_set_low_fan", {
    "alias": "All ACs - Set Low Fan",
    "description": "Sets fan to Low on all ACs that are currently running (not off/unavailable)",
    "sequence": [
        {"if": [{"condition": "not", "conditions": [{"condition": "state", "entity_id": entity, "state": ["off","unavailable","unknown"]}]}],
         "then": [{"action": "climate.set_fan_mode", "target": {"entity_id": entity}, "data": {"fan_mode": "Low"}, "continue_on_error": True}]}
        for entity in ALL_ACS
    ],
    "mode": "single",
    "icon": "mdi:fan"
})
print("  all_acs_set_low_fan: " + str(r))

# Update Turn Off script
r = post("/api/config/script/config/all_acs_turn_off", {
    "alias": "All ACs - Turn Off",
    "description": "Turns off all ACs",
    "sequence": [{"action": "climate.turn_off", "target": {"entity_id": ALL_ACS}, "continue_on_error": True}],
    "mode": "single",
    "icon": "mdi:fan-off"
})
print("  all_acs_turn_off: " + str(r))
