$ErrorActionPreference = 'Stop'
$record = Get-Content "$env:USERPROFILE\mobi-near-expiry-live-server.json" | ConvertFrom-Json
if ($record.experiment -ne 'near_expiry_live_20261004') { throw 'Ownership mismatch' }
$owned = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if ($owned) {
  if ($owned.Path -ne $record.executable) { throw 'Executable mismatch' }
  if ($owned.StartTime.ToUniversalTime().ToString('o') -ne $record.start_time_utc) { throw 'PID identity mismatch' }
  Stop-Process -Id $record.pid
  $null = $owned.WaitForExit(10000)
}
@{pid=$record.pid; executable=$record.executable; start_time_utc=$record.start_time_utc; experiment=$record.experiment; stopped=$true} | ConvertTo-Json | Set-Content "$env:USERPROFILE\mobi-near-expiry-live-stopped.json"
Get-Content "$env:USERPROFILE\mobi-near-expiry-live-stopped.json"
