$ErrorActionPreference = 'Stop'
$record = Get-Content "$env:USERPROFILE\mobi-causal-state-server.json" | ConvertFrom-Json
if ($record.experiment -ne 'causal_state_20261003') { throw 'Ownership mismatch' }
$owned = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if ($owned) {
    if ($owned.Path -ne $record.executable) { throw 'Executable mismatch; refusing to stop process' }
    Stop-Process -Id $record.pid
    $null = $owned.WaitForExit(10000)
}
@{pid=$record.pid; executable=$record.executable; experiment=$record.experiment; stopped=$true} | ConvertTo-Json | Set-Content "$env:USERPROFILE\mobi-causal-state-stopped.json"
Get-Content "$env:USERPROFILE\mobi-causal-state-stopped.json"
