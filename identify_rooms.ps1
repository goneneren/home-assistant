# WiZ Room Identifier
# Blinks all lights in one room at a time so you can name each room

$port    = 38899
$timeout = 1000

# Room IDs found in the scan
$roomIds = @(
    32321316, 32474714, 32702356,
    33053180, 33053946, 33132627,
    33306107, 33306693, 33436589, 34114932
)

# Load scan results
$devices = Get-Content "$PSScriptRoot\wiz_devices.json" | ConvertFrom-Json

function Send-WizUdp([string]$ip, [string]$payload) {
    try {
        $udp   = New-Object System.Net.Sockets.UdpClient
        $udp.Client.ReceiveTimeout = $timeout
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
        $udp.Send($bytes, $bytes.Length, $ip, $port) | Out-Null
        $udp.Close()
    } catch {}
}

function Set-RoomState([int]$roomId, [bool]$on) {
    $state   = if ($on) { "true" } else { "false" }
    $payload = "{`"method`":`"setPilot`",`"env`":`"pro`",`"params`":{`"state`":$state}}"
    $roomDevices = $devices | Where-Object { $_.roomId -eq $roomId }
    foreach ($d in $roomDevices) {
        Send-WizUdp $d.ip $payload
    }
}

$roomMap = @{}

Write-Host "`nWiZ Room Identifier" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "Each room's lights will blink OFF then ON."
Write-Host "Tell me which bungalow blinked.`n"

foreach ($roomId in $roomIds) {
    $count = ($devices | Where-Object { $_.roomId -eq $roomId }).Count

    Write-Host "Testing Room ID: $roomId  ($count lights)" -ForegroundColor Yellow
    Write-Host "  >> Blinking now..." -NoNewline

    # Blink: off for 1.5s, then back on
    Set-RoomState $roomId $false
    Start-Sleep -Milliseconds 1500
    Set-RoomState $roomId $true
    Start-Sleep -Milliseconds 500

    Write-Host " done."
    $name = Read-Host "  Which bungalow blinked? (e.g. 'Bungalow 03', or Enter to skip)"

    if ($name -ne "") {
        $roomMap[$roomId] = $name.Trim()
    }

    Write-Host ""
}

# Save mapping
Write-Host "`nRoom mapping:" -ForegroundColor Cyan
$roomMap.GetEnumerator() | Sort-Object Value | ForEach-Object {
    Write-Host ("  {0,-12} = {1}" -f $_.Key, $_.Value)
}

$outPath = "$PSScriptRoot\room_map.json"
$roomMap | ConvertTo-Json | Out-File $outPath -Encoding utf8
Write-Host "`nSaved to: $outPath" -ForegroundColor Yellow
