$ErrorActionPreference = 'Stop'
$record = Get-Content "$env:USERPROFILE\mobi-actuator-route-40s-server.json" | ConvertFrom-Json
if ($record.experiment -ne 'actuator_route_40s_20261011') { throw 'Ownership mismatch' }
$owned = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if ($owned) {
  if ($owned.Path -ne $record.executable) { throw 'Executable mismatch' }
  if ($owned.StartTime.ToUniversalTime().ToString('o') -ne $record.start_time_utc) { throw 'PID identity mismatch' }
  Stop-Process -Id $record.pid
  $null = $owned.WaitForExit(10000)
}
@{pid=$record.pid; executable=$record.executable; start_time_utc=$record.start_time_utc; experiment=$record.experiment; stopped=$true} | ConvertTo-Json | Set-Content "$env:USERPROFILE\mobi-actuator-route-40s-stopped.json"
Get-Content "$env:USERPROFILE\mobi-actuator-route-40s-stopped.json"
