$token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
$headers = @{ Authorization = "Bearer $token" }
$base    = "http://localhost:8123"

# WebSocket helpers
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
Write-Host "Auth: $((WsRecv).type)"

# Get device_id for each entity so we can rename the device
$states = Invoke-RestMethod -Uri "$base/api/states" -Headers $headers

# Map entity_id -> desired device name
$entityToDeviceName = [ordered]@{
    "light.bungalow_04_room_led_strip"  = "Bungalow 04 Room LED Strip"
    "light.bungalow_04_bathroom_01"     = "Bungalow 04 Bathroom 01"
    "light.bungalow_04_bathroom_02"     = "Bungalow 04 Bathroom 02"
    "light.bungalow_04_room_01"         = "Bungalow 04 Room 01"
    "light.bungalow_04_room_02"         = "Bungalow 04 Room 02"
    "light.bungalow_04_room_03"         = "Bungalow 04 Room 03"
    "light.bungalow_04_room_04"         = "Bungalow 04 Room 04"
    "light.bungalow_04_terrace_up_01"   = "Bungalow 04 Terrace Up 01"
    "light.bungalow_04_terrace_up_02"   = "Bungalow 04 Terrace Up 02"
    "light.bungalow_04_terrace_down_01" = "Bungalow 04 Terrace Down 01"
    "light.bungalow_04_terrace_down_02" = "Bungalow 04 Terrace Down 02"
}

# Look up device_id for each entity via entity registry
$msgId = 1
$renamedDevices = @{}

foreach ($eid in $entityToDeviceName.Keys) {
    $devName = $entityToDeviceName[$eid]

    WsSend @{ id = $msgId; type = "config/entity_registry/get"; entity_id = $eid }
    $r = WsRecv
    $msgId++
    $deviceId = $r.result.device_id

    if (-not $deviceId) {
        Write-Host "  [no device_id] $eid" -ForegroundColor Yellow
        continue
    }

    if ($renamedDevices.ContainsKey($deviceId)) { continue }

    WsSend @{ id = $msgId; type = "config/device_registry/update"; device_id = $deviceId; name_by_user = $devName }
    $r2 = WsRecv
    $msgId++
    if ($r2.success) {
        Write-Host "  OK: $eid -> device '$devName'" -ForegroundColor Green
        $renamedDevices[$deviceId] = $devName
    } else {
        Write-Host "  FAIL: $eid - $($r2.error.message)" -ForegroundColor Red
    }
}

$ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "", $cts.Token).Wait()
Write-Host "Done."
