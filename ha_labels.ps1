$token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"

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

$msgId = 1

# Step 1: Create labels (skip if already exists)
$labelDefs = @(
    @{ name = "Bungalow 04";  color = "green";  icon = "mdi:home" }
    @{ name = "Terrace";      color = "amber";  icon = "mdi:string-lights" }
    @{ name = "Terrace Up";   color = "amber";  icon = "mdi:arrow-up-circle" }
    @{ name = "Terrace Down"; color = "orange"; icon = "mdi:arrow-down-circle" }
    @{ name = "Room";         color = "blue";   icon = "mdi:bed" }
    @{ name = "Bathroom";     color = "cyan";   icon = "mdi:shower" }
)

$labelIds = @{}
Write-Host "`nCreating labels..."
foreach ($ldef in $labelDefs) {
    WsSend @{ id = $msgId; type = "config/label_registry/create"; name = $ldef.name; color = $ldef.color; icon = $ldef.icon }
    $r = WsRecv
    $msgId++
    if ($r.success) {
        $labelIds[$ldef.name] = $r.result.label_id
        Write-Host "  Created: '$($ldef.name)' -> $($r.result.label_id)" -ForegroundColor Green
    } else {
        # Label might already exist — list and find it
        WsSend @{ id = $msgId; type = "config/label_registry/list" }
        $list = WsRecv
        $msgId++
        $existing = $list.result | Where-Object { $_.name -eq $ldef.name }
        if ($existing) {
            $labelIds[$ldef.name] = $existing.label_id
            Write-Host "  Exists:  '$($ldef.name)' -> $($existing.label_id)" -ForegroundColor Yellow
        }
    }
}

# Step 2: Assign labels to entities
# entity_id -> list of label names to assign
$assignments = @{
    "light.bungalow_04_room_led_strip"  = @("Bungalow 04", "Room")
    "light.bungalow_04_room_01"         = @("Bungalow 04", "Room")
    "light.bungalow_04_room_02"         = @("Bungalow 04", "Room")
    "light.bungalow_04_room_03"         = @("Bungalow 04", "Room")
    "light.bungalow_04_room_04"         = @("Bungalow 04", "Room")
    "light.bungalow_04_bathroom_01"     = @("Bungalow 04", "Bathroom")
    "light.bungalow_04_bathroom_02"     = @("Bungalow 04", "Bathroom")
    "light.bungalow_04_terrace_up_01"   = @("Bungalow 04", "Terrace", "Terrace Up")
    "light.bungalow_04_terrace_up_02"   = @("Bungalow 04", "Terrace", "Terrace Up")
    "light.bungalow_04_terrace_down_01" = @("Bungalow 04", "Terrace", "Terrace Down")
    "light.bungalow_04_terrace_down_02" = @("Bungalow 04", "Terrace", "Terrace Down")
}

Write-Host "`nAssigning labels..."
foreach ($eid in $assignments.Keys) {
    $ids = @($assignments[$eid] | ForEach-Object { $labelIds[$_] } | Where-Object { $_ })
    WsSend @{ id = $msgId; type = "config/entity_registry/update"; entity_id = $eid; labels = $ids }
    $r = WsRecv
    $msgId++
    if ($r.success) {
        Write-Host "  OK: $eid -> [$($assignments[$eid] -join ', ')]" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: $eid - $($r.error.message)" -ForegroundColor Red
    }
}

$ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "", $cts.Token).Wait()
Write-Host "`nDone."
