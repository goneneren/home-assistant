#!/usr/bin/env python3
"""Toshiba AC re-authentication script.
Safe version: never deletes the existing config entry.
- If entry exists: reload it (reconnects with stored credentials)
- If no entry exists: create a new one via config flow
"""
import sys, json, urllib.request

CREDS_FILE = "/config/toshiba_creds.json"
HA_URL = "http://localhost:8123"

with open(CREDS_FILE) as f:
    creds = json.load(f)

TOKEN = creds["ha_token"]
USERNAME = creds["username"]
PASSWORD = creds["password"]

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def api(method, path, data=None):
    req = urllib.request.Request(f"{HA_URL}{path}", headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

entries = api("GET", "/api/config/config_entries/entry")
toshiba = next((e for e in entries if e["domain"] == "toshiba_ac"), None)

if toshiba:
    entry_id = toshiba["entry_id"]
    state = toshiba["state"]
    print(f"Found existing entry {entry_id} (state={state}), reloading...")
    result = api("POST", f"/api/config/config_entries/entry/{entry_id}/reload")
    print(f"Reload result: {result}")
    sys.exit(0)

# No entry exists - create one via config flow
print(f"No existing entry found. Creating new entry for {USERNAME}...")
flow = api("POST", "/api/config/config_entries/flow", {"handler": "toshiba_ac"})
flow_id = flow["flow_id"]

result = api("POST", f"/api/config/config_entries/flow/{flow_id}", {"username": USERNAME, "password": PASSWORD})

if result.get("type") == "create_entry":
    new_id = result["result"]["entry_id"]
    print(f"Success! New entry: {new_id}")
    sys.exit(0)
else:
    print(f"Failed: {result}")
    sys.exit(1)
