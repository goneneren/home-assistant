# WiZ Device Scanner
# Scans 192.168.68.0/24 for WiZ devices and retrieves name/room info via UDP

param(
    [string]$Subnet  = "192.168.68",
    [int]   $Port    = 38899,
    [int]   $Timeout = 1500
)

$payloads = @{
    getDevInfo      = '{"method":"getDevInfo","env":"pro","params":{}}'
    getSystemConfig = '{"method":"getSystemConfig","env":"pro","params":{}}'
    getPilot        = '{"method":"getPilot","env":"pro","params":{}}'
}

$devices = [System.Collections.Concurrent.ConcurrentBag[object]]::new()

$pool = [runspacefactory]::CreateRunspacePool(1, 50)
$pool.Open()

Write-Host "`nScanning $Subnet.1-254 for WiZ devices (parallel)..." -ForegroundColor Cyan

$runspaces = 1..254 | ForEach-Object {
    $ip = "$Subnet.$_"
    $ps = [powershell]::Create()
    $ps.RunspacePool = $pool

    [void]$ps.AddScript({
        param($ip, $port, $timeout, $payloads, $devices)

        function Invoke-WizUdp([string]$ip, [string]$payload) {
            try {
                $udp   = New-Object System.Net.Sockets.UdpClient
                $udp.Client.ReceiveTimeout = $timeout
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
                $udp.Send($bytes, $bytes.Length, $ip, $port) | Out-Null
                $ep    = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 0)
                $data  = $udp.Receive([ref]$ep)
                $udp.Close()
                return ([System.Text.Encoding]::UTF8.GetString($data) | ConvertFrom-Json).result
            } catch { return $null }
        }

        $dev = Invoke-WizUdp $ip $payloads.getDevInfo
        if (-not $dev) { return }

        $obj = [ordered]@{ ip = $ip }
        $dev.PSObject.Properties | ForEach-Object { $obj[$_.Name] = $_.Value }

        $sys = Invoke-WizUdp $ip $payloads.getSystemConfig
        if ($sys) { $sys.PSObject.Properties | ForEach-Object { $obj[$_.Name] = $_.Value } }

        $pilot = Invoke-WizUdp $ip $payloads.getPilot
        if ($pilot) {
            $obj["state"]      = if ($pilot.state) { "ON" } else { "OFF" }
            $obj["brightness"] = "$($pilot.dimming)%"
        }

        $devices.Add([PSCustomObject]$obj)
    })

    [void]$ps.AddParameters(@{
        ip       = $ip
        port     = $Port
        timeout  = $Timeout
        payloads = $payloads
        devices  = $devices
    })

    @{ ps = $ps; handle = $ps.BeginInvoke() }
}

$runspaces | ForEach-Object { $_.ps.EndInvoke($_.handle); $_.ps.Dispose() }
$pool.Close()

$results = @($devices) | Sort-Object { [System.Version]$_.ip }

if ($results.Count -eq 0) {
    Write-Host "No WiZ devices found on $Subnet.0/24`n" -ForegroundColor Red
    exit
}

Write-Host "Found $($results.Count) WiZ device(s)`n" -ForegroundColor Green

$fmt = "{0,-18} {1,-17} {2,-26} {3,-12} {4,-12} {5}"
Write-Host ($fmt -f "IP", "MAC", "Module", "HomeID", "RoomID", "State")
Write-Host ("-" * 100)
foreach ($d in $results) {
    Write-Host ($fmt -f $d.ip, $d.mac, $d.moduleName, $d.homeId, $d.roomId, "$($d.state) $($d.brightness)")
}
Write-Host ("-" * 100)

$outPath = Join-Path $PSScriptRoot "wiz_devices.json"
$results | ConvertTo-Json -Depth 5 | Out-File $outPath -Encoding utf8
Write-Host "`nFull results saved to: $outPath`n" -ForegroundColor Yellow
