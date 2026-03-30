import json, urllib.request

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
BASE = "http://localhost:8123"
AC_NUMS = ["01", "02", "04", "05", "06", "07", "08", "10"]

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

def patch(obj):
    if isinstance(obj, str):
        # Update alias and description text
        obj = obj.replace("Quiet 27C", "Auto 25C")
        obj = obj.replace("fan is not Quiet", "fan is not Auto")
        obj = obj.replace("fan to Quiet", "fan to Auto")
        obj = obj.replace("temp to 27C", "temp to 25C")
        return obj
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # Fix not_to list: ["Quiet", null] -> ["Auto", null]
            if k == "not_to" and isinstance(v, list) and "Quiet" in v:
                result[k] = ["Auto" if x == "Quiet" else x for x in v]
            # Fix fan_mode state checks: "Quiet" -> "Auto"
            elif k == "state" and v == "Quiet":
                result[k] = "Auto"
            # Fix fan_mode action data: "Quiet" -> "Auto"
            elif k == "fan_mode" and v == "Quiet":
                result[k] = "Auto"
            # Fix temperature: 27 -> 25
            elif k == "temperature" and v == 27:
                result[k] = 25
            else:
                result[k] = patch(v)
        return result
    elif isinstance(obj, list):
        return [patch(i) for i in obj]
    return obj

for nn in AC_NUMS:
    auto_id = f"ac{nn}_night_quiet_27"
    config = get(f"/api/config/automation/config/{auto_id}")
    patched = patch(config)
    r = post(f"/api/config/automation/config/{auto_id}", patched)
    print(auto_id + ": " + str(r.get("result")) + " | alias: " + patched["alias"])
