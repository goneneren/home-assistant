# Probe all Bungalow 04 devices for type, name, and state
$roomId = 33053946
$port   = 38899

$devices = Get-Content "$PSScriptRoot\wiz_devices.json" | ConvertFrom-Json
$room4   = $devices | Where-Object { $_.roomId -eq $roomId } | Sort-Object { [System.Version]$_.ip }

Write-Host "`nBungalow 04 (roomId $roomId) - $($room4.Count) devices`n" -ForegroundColor Cyan

function Invoke-WizUdp([string]$ip, [string]$payload) {
    try {
        $udp   = New-Object System.Net.Sockets.UdpClient
        $udp.Client.ReceiveTimeout = 1500
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
        $udp.Send($bytes, $bytes.Length, $ip, $port) | Out-Null
        $ep    = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 0)
        $data  = $udp.Receive([ref]$ep)
        $udp.Close()
        return ([System.Text.Encoding]::UTF8.GetString($data) | ConvertFrom-Json).result
    } catch { return $null }
}

foreach ($d in $room4) {
    Write-Host "-- $($d.ip)  [$($d.mac)]" -ForegroundColor Yellow

    $model = Invoke-WizUdp $d.ip '{"method":"getModelConfig","env":"pro","params":{}}'
    if ($model) { Write-Host "   modelConfig : $($model | ConvertTo-Json -Compress)" }

    $user = Invoke-WizUdp $d.ip '{"method":"getUserConfig","env":"pro","params":{}}'
    if ($user)  { Write-Host "   userConfig  : $($user | ConvertTo-Json -Compress)" }

    $pilot = Invoke-WizUdp $d.ip '{"method":"getPilot","env":"pro","params":{}}'
    if ($pilot) {
        $state = if ($pilot.state) { "ON" } else { "OFF" }
        Write-Host "   state       : $state  brightness=$($pilot.dimming)%  r=$($pilot.r) g=$($pilot.g) b=$($pilot.b) w=$($pilot.w) c=$($pilot.c)"
    }

    Write-Host "   module      : $($d.moduleName)"
    Write-Host ""
}
