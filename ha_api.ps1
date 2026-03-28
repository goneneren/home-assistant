$token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$base    = "http://localhost:8123"

# Bungalow 04 lights to add (IP -> friendly name)
# Rename WiZ light entities to Bungalow 04 Light 01-10 by IP (via MAC suffix in entity_id)
# MAC suffixes in order of IP: .52=413752, .81=41362c, .127=3f7354, .128=41392e, .129=3f72f8
#                               .130=413726, .138=449406, .139=4493b4, .140=449314, .141=449466
# Check all WiZ config entries
$entries = Invoke-RestMethod -Uri "$base/api/config/config_entries/entry" -Headers $headers
$wizEntries = $entries | Where-Object { $_.domain -eq "wiz" }
Write-Host "WiZ config entries ($($wizEntries.Count)):"
$wizEntries | ForEach-Object { Write-Host "  $($_.title)  state=$($_.state)  id=$($_.entry_id)" }

Write-Host ""

# Rename the 6 that loaded successfully using POST (HA's correct verb)
$macToName = @{
    "413752" = "Bungalow 04 Light 01"
    "41362c" = "Bungalow 04 Light 02"
    "3f7354" = "Bungalow 04 Light 03"
    "41392e" = "Bungalow 04 Light 04"
    "3f72f8" = "Bungalow 04 Light 05"
    "413726" = "Bungalow 04 Light 06"
    "449406" = "Bungalow 04 Light 07"
    "4493b4" = "Bungalow 04 Light 08"
    "449314" = "Bungalow 04 Light 09"
    "449466" = "Bungalow 04 Light 10"
}

$states = Invoke-RestMethod -Uri "$base/api/states" -Headers $headers
$wizLights = $states | Where-Object { $_.entity_id -match "^light\.wiz_" }

Write-Host "Renaming $($wizLights.Count) found entities..."
foreach ($mac in $macToName.Keys) {
    $name   = $macToName[$mac]
    $entity = $wizLights | Where-Object { $_.entity_id -match $mac } | Select-Object -First 1
    if ($entity) {
        $eid = $entity.entity_id
        try {
            Invoke-RestMethod -Uri "$base/api/config/entity_registry/$eid" -Method Post -Headers $headers `
                -Body (ConvertTo-Json @{ name = $name }) | Out-Null
            Write-Host "  $eid -> '$name'" -ForegroundColor Cyan
        } catch {
            Write-Host "  RENAME FAILED $eid : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "  [missing] $name (MAC: $mac)" -ForegroundColor Yellow
    }
}
