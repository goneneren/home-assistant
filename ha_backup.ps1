$token   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0ZGY5OWNkYWY3ZTg0ZDdiYTI1OTVjZjM3ZmMyZjk0MSIsImlhdCI6MTc3NDcxMjI1NSwiZXhwIjoyMDkwMDcyMjU1fQ.14i3ydmylDyRcgVXyU8Xl8_6NVk1YQg6kRU4dSN-NTE"
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$base    = "http://localhost:8123"

Write-Host "Triggering HA backup..." -ForegroundColor Cyan
$r = Invoke-RestMethod -Uri "$base/api/services/backup/create" -Method Post -Headers $headers -Body "{}"
Write-Host "Backup job started. Waiting for completion..."

# Poll backup list until a new one appears
$before  = (Invoke-RestMethod -Uri "$base/api/backups" -Headers $headers).backups
$timeout = 120
$elapsed = 0
do {
    Start-Sleep -Seconds 5
    $elapsed += 5
    $after = (Invoke-RestMethod -Uri "$base/api/backups" -Headers $headers).backups
    $new   = $after | Where-Object { $_.slug -notin ($before.slug) }
    if ($new) {
        Write-Host "Backup complete!" -ForegroundColor Green
        Write-Host "  Name : $($new.name)"
        Write-Host "  Slug : $($new.slug)"
        Write-Host "  Date : $($new.date)"
        Write-Host "  Size : $([math]::Round($new.size/1MB, 1)) MB"
        break
    }
    Write-Host "  ...waiting ($elapsed s)"
} while ($elapsed -lt $timeout)

if (-not $new) {
    Write-Host "Timed out waiting for backup. Check HA UI under Settings > System > Backups." -ForegroundColor Yellow
}
