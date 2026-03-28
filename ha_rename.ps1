$token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
$headers = @{ Authorization = "Bearer $token" }
$base    = "http://localhost:8123"

# -- WebSocket helpers --
$ws  = New-Object System.Net.WebSockets.ClientWebSocket
$cts = New-Object System.Threading.CancellationTokenSource
$ws.ConnectAsync((New-Object System.Uri("ws://localhost:8123/api/websocket")), $cts.Token).Wait()

function WsSend($obj) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes((ConvertTo-Json $obj -Compress -Depth 5))
    $seg   = New-Object System.ArraySegment[byte] (, $bytes)
    $ws.SendAsync($seg, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $cts.Token).Wait()
}
function WsRecv {
    $sb  = New-Object System.Text.StringBuilder
    $buf = New-Object byte[] 65536
    do {
        $seg = New-Object System.ArraySegment[byte] (, $buf)
        $res = $ws.ReceiveAsync($seg, $cts.Token).GetAwaiter().GetResult()
        $sb.Append([System.Text.Encoding]::UTF8.GetString($buf, 0, $res.Count)) | Out-Null
    } while (-not $res.EndOfMessage)
    return $sb.ToString() | ConvertFrom-Json
}

WsRecv | Out-Null
WsSend @{ type = "auth"; access_token = $token }
$auth = WsRecv
Write-Host "Auth: $($auth.type)"

# Find all light states
$states   = Invoke-RestMethod -Uri "$base/api/states" -Headers $headers
$allLights = $states | Where-Object { $_.entity_id -like "light.*" } | Sort-Object entity_id

Write-Host "All lights in HA:"
$allLights | ForEach-Object {
    Write-Host ("  {0,-45} {1}" -f $_.entity_id, $_.attributes.friendly_name)
}

# Bungalow 04 final rename: entity_id -> [new_entity_id, friendly_name]
$renames = [ordered]@{
    "light.bungalow_04_led_strip"   = @("light.bungalow_04_room_led_strip",   "Bungalow 04 Room LED Strip")
    "light.bungalow_04_light_01"    = @("light.bungalow_04_bathroom_01",      "Bungalow 04 Bathroom 01")
    "light.bungalow_04_light_02"    = @("light.bungalow_04_bathroom_02",      "Bungalow 04 Bathroom 02")
    "light.bungalow_04_light_03"    = @("light.bungalow_04_room_01",          "Bungalow 04 Room 01")
    "light.bungalow_04_light_04"    = @("light.bungalow_04_room_02",          "Bungalow 04 Room 02")
    "light.bungalow_04_light_05"    = @("light.bungalow_04_room_03",          "Bungalow 04 Room 03")
    "light.bungalow_04_light_06"    = @("light.bungalow_04_room_04",          "Bungalow 04 Room 04")
    "light.bungalow_04_light_07"    = @("light.bungalow_04_terrace_up_01",    "Bungalow 04 Terrace Up 01")
    "light.bungalow_04_light_08"    = @("light.bungalow_04_terrace_up_02",    "Bungalow 04 Terrace Up 02")
    "light.bungalow_04_light_09"    = @("light.bungalow_04_terrace_down_01",  "Bungalow 04 Terrace Down 01")
    "light.bungalow_04_light_10"    = @("light.bungalow_04_terrace_down_02",  "Bungalow 04 Terrace Down 02")
}

Write-Host ""
Write-Host "Updating entity IDs and names..."
$i = 20
foreach ($eid in $renames.Keys) {
    $newEid = $renames[$eid][0]
    $name   = $renames[$eid][1]
    WsSend @{ id = $i; type = "config/entity_registry/update"; entity_id = $eid; new_entity_id = $newEid; name = $name }
    $r = WsRecv
    if ($r.success) {
        Write-Host "  OK: $eid -> $newEid ('$name')" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: $eid - $($r.error.message)" -ForegroundColor Red
    }
    $i++
}

$ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "", $cts.Token).Wait()
Write-Host "Done."
