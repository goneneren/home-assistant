import json, urllib.request

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
BASE = "http://localhost:8123"

AC_NUMS = ["01", "02", "04", "05", "06", "07", "08", "10"]
SUFFIXES = ["auto_off_2h", "set_fan_medium_low", "night_quiet_27"]

def get(path):
    req = urllib.request.Request(f"{BASE}{path}",
        headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=body,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def patch(obj):
    """Replace 00:00 end time with 01:00 in night_auto_26 automations"""
    if isinstance(obj, str):
        return obj.replace("00:00:00", "01:00:00").replace("21:00-00:00", "21:00-01:00")
    elif isinstance(obj, dict):
        return {k: patch(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [patch(i) for i in obj]
    return obj

results = []
for nn in AC_NUMS:
    for suffix in ["night_auto_26"]:
        auto_id = f"ac{nn}_{suffix}"
        config = get(f"/api/config/automation/config/{auto_id}")
        original = json.dumps(config)
        patched = patch(config)
        patched_str = json.dumps(patched)

        if original == patched_str:
            print(f"  {auto_id}: no changes needed")
            continue

        r = post(f"/api/config/automation/config/{auto_id}", patched)
        status = r.get("result", r)
        print("  " + auto_id + ": " + str(status))
        results.append((auto_id, patched))

print("\nUpdated " + str(len(results)) + " automations.")
