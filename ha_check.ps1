$token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
$headers = @{ Authorization = "Bearer $token" }
$states  = Invoke-RestMethod -Uri "http://localhost:8123/api/states" -Headers $headers
$lights  = $states | Where-Object { $_.entity_id -match "bungalow_04_light_0[1-6]|bungalow_04_led_strip" } | Sort-Object entity_id

$fmt = "{0,-35} {1,-5} {2}"
Write-Host ($fmt -f "Entity", "State", "Friendly Name")
Write-Host ("-" * 70)
$lights | ForEach-Object {
    $color = if ($_.state -eq "on") { "Green" } else { "Red" }
    Write-Host ($fmt -f $_.entity_id, $_.state.ToUpper(), $_.attributes.friendly_name) -ForegroundColor $color
}
