import socket, json, base64, hashlib, struct, time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"

# --- Minimal WebSocket client ---
def ws_connect(host, port, path):
    s = socket.socket()
    s.connect((host, port))
    key = base64.b64encode(b'HomeAssistant16b').decode()
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    s.sendall(handshake.encode())
    # Read HTTP response
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += s.recv(4096)
    return s

def ws_send(s, msg):
    data = msg.encode()
    length = len(data)
    mask = b'\x00\x00\x00\x00'
    if length < 126:
        header = bytes([0x81, 0x80 | length]) + mask
    else:
        header = bytes([0x81, 0xFE, length >> 8, length & 0xFF]) + mask
    s.sendall(header + data)

def ws_recv(s):
    # Read frame header
    buf = b""
    while len(buf) < 2:
        buf += s.recv(2 - len(buf))
    b1, b2 = buf[0], buf[1]
    masked = (b2 & 0x80) != 0
    length = b2 & 0x7F
    if length == 126:
        lb = b""
        while len(lb) < 2: lb += s.recv(2 - len(lb))
        length = struct.unpack(">H", lb)[0]
    elif length == 127:
        lb = b""
        while len(lb) < 8: lb += s.recv(8 - len(lb))
        length = struct.unpack(">Q", lb)[0]
    payload = b""
    while len(payload) < length:
        chunk = s.recv(min(65536, length - len(payload)))
        if not chunk:
            break
        payload += chunk
    return payload.decode()

def rpc(s, msg_id, msg_type, **kwargs):
    payload = {"id": msg_id, "type": msg_type}
    payload.update(kwargs)
    ws_send(s, json.dumps(payload))
    return json.loads(ws_recv(s))

# Connect and auth
s = ws_connect("localhost", 8123, "/api/websocket")
ws_recv(s)  # auth_required
ws_send(s, json.dumps({"type": "auth", "access_token": TOKEN}))
ws_recv(s)  # auth_ok

msg_id = 1

# --- Get entity registry (only climate entities) ---
resp = rpc(s, msg_id, "config/entity_registry/list")
msg_id += 1
all_entities = resp["result"]
ac_entities = [e for e in all_entities if e["entity_id"].startswith("climate.ac_")]
print(f"Found {len(ac_entities)} AC entities:")
for e in sorted(ac_entities, key=lambda x: x["entity_id"]):
    print(f"  {e['entity_id']} | icon={e.get('icon')}")

# --- Update AC entity icons to mdi:air-conditioner ---
print("\nUpdating AC entity icons to mdi:air-conditioner...")
for e in sorted(ac_entities, key=lambda x: x["entity_id"]):
    resp = rpc(s, msg_id, "config/entity_registry/update",
               entity_id=e["entity_id"], icon="mdi:air-conditioner")
    msg_id += 1
    result = resp.get("result", {})
    print(f"  {e['entity_id']}: icon={result.get('entity_entry', {}).get('icon')}")

# --- Get areas ---
resp = rpc(s, msg_id, "config/area_registry/list")
msg_id += 1
all_areas = resp["result"]
bungalow_areas = [a for a in all_areas if "bungalow" in a.get("name", "").lower()]
print(f"\nFound {len(bungalow_areas)} bungalow areas:")
for a in sorted(bungalow_areas, key=lambda x: x["name"]):
    print(f"  {a['area_id']} | {a['name']} | icon={a.get('icon')}")

# --- Update bungalow area icons to mdi:home ---
print("\nUpdating bungalow area icons to mdi:home...")
for a in sorted(bungalow_areas, key=lambda x: x["name"]):
    resp = rpc(s, msg_id, "config/area_registry/update",
               area_id=a["area_id"], icon="mdi:home")
    msg_id += 1
    result = resp.get("result", {})
    print(f"  {a['name']}: icon={result.get('icon')}")

s.close()
print("\nDone.")
