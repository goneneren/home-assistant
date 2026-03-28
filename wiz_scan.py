#!/usr/bin/env python3
"""
WiZ Device Scanner
Scans subnet for WiZ devices and retrieves their names and room assignments.
"""

import socket
import json
import ipaddress
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

SUBNET = "192.168.68.0/24"
WIZ_PORT = 38899
TIMEOUT = 1.5

QUERIES = {
    "getDevInfo":     '{"method":"getDevInfo","env":"pro","params":{}}',
    "getSystemConfig": '{"method":"getSystemConfig","env":"pro","params":{}}',
    "getPilot":       '{"method":"getPilot","env":"pro","params":{}}',
}

def query_device(ip: str, method: str, payload: str) -> dict | None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT)
        sock.sendto(payload.encode(), (ip, WIZ_PORT))
        data, _ = sock.recvfrom(4096)
        sock.close()
        resp = json.loads(data.decode())
        if "result" in resp:
            return resp["result"]
    except Exception:
        pass
    return None

def scan_ip(ip: str) -> dict | None:
    # Quick check with getDevInfo first
    dev = query_device(ip, "getDevInfo", QUERIES["getDevInfo"])
    if dev is None:
        return None

    result = {"ip": ip}
    result.update(dev)

    # Get system config for room/home info
    sys_cfg = query_device(ip, "getSystemConfig", QUERIES["getSystemConfig"])
    if sys_cfg:
        result.update(sys_cfg)

    # Get current state
    pilot = query_device(ip, "getPilot", QUERIES["getPilot"])
    if pilot:
        result["state"] = "ON" if pilot.get("state") else "OFF"
        result["brightness"] = pilot.get("dimming", "?")

    return result

def fetch_wiz_rooms(home_id: int, rgn: str = "eu") -> dict:
    """Try to fetch room names from WiZ cloud API (no auth needed for basic home info)."""
    import urllib.request
    room_map = {}
    try:
        base = "https://wiz.cloud" if rgn == "eu" else "https://wiz.cloud"
        url = f"{base}/api/home/{home_id}/rooms"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            for room in data.get("result", {}).get("rooms", []):
                room_map[room["id"]] = room["name"]
    except Exception as e:
        pass  # Cloud API may require auth; will show room IDs instead
    return room_map

def main():
    print(f"\n🔍 Scanning {SUBNET} for WiZ devices...\n")
    hosts = list(ipaddress.IPv4Network(SUBNET, strict=False).hosts())

    devices = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(scan_ip, str(ip)): str(ip) for ip in hosts}
        for future in as_completed(futures):
            result = future.result()
            if result:
                devices.append(result)
                print(f"  ✓ Found WiZ device at {result['ip']}")

    if not devices:
        print("  ✗ No WiZ devices found.\n")
        return

    # Try to resolve room names from cloud
    room_map = {}
    home_ids = {d.get("homeId") for d in devices if d.get("homeId")}
    for home_id in home_ids:
        rgn = next((d.get("rgn", "eu") for d in devices if d.get("homeId") == home_id), "eu")
        room_map.update(fetch_wiz_rooms(home_id, rgn))

    # Print results
    print(f"\n{'─'*72}")
    print(f"{'IP':<18} {'MAC':<15} {'Module':<22} {'Room':<20} {'State'}")
    print(f"{'─'*72}")

    # Group by room
    devices.sort(key=lambda d: (d.get("roomId", 0), d.get("ip", "")))

    for d in devices:
        ip       = d.get("ip", "?")
        mac      = d.get("mac", "?")
        module   = d.get("moduleName", "?")
        room_id  = d.get("roomId")
        room     = room_map.get(room_id, f"Room ID: {room_id}" if room_id else "Unassigned")
        state    = f"{d.get('state','?')} @ {d.get('brightness','?')}%"
        print(f"{ip:<18} {mac:<15} {module:<22} {room:<20} {state}")

    print(f"{'─'*72}")
    print(f"\nTotal WiZ devices found: {len(devices)}")

    # Output JSON for further use
    out_file = "/config/wiz_devices.json"
    with open(out_file, "w") as f:
        json.dump(devices, f, indent=2)
    print(f"Full data saved to: {out_file}\n")

if __name__ == "__main__":
    main()
