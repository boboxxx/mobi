$ErrorActionPreference = 'Stop'
$existing = Get-Process *Carla* -ErrorAction SilentlyContinue
if ($existing) { throw 'Existing CARLA process; no new server started.' }
$exe = 'C:\App\CARLA_0.9.15\WindowsNoEditor\CarlaUE4\Binaries\Win64\CarlaUE4-Win64-Shipping.exe'
if (-not (Test-Path $exe)) { throw 'Installed CARLA0.9.15 absent.' }
$info = New-Object System.Diagnostics.ProcessStartInfo
$info.FileName = $exe
$info.Arguments = 'Town10HD_Opt -RenderOffScreen -nosound -unattended -quality-level=Low -carla-rpc-port=2000'
$info.WorkingDirectory = 'C:\App\CARLA_0.9.15\WindowsNoEditor'
$info.UseShellExecute = $false
$process = [System.Diagnostics.Process]::Start($info)
@{pid=$process.Id; executable=$exe; start_time_utc=$process.StartTime.ToUniversalTime().ToString('o'); experiment='receiver_budget_live_20261004'} | ConvertTo-Json | Set-Content "$env:USERPROFILE\mobi-receiver-budget-server.json"
$process | Select-Object Id,ProcessName
if (-not $process.WaitForExit(10800000)) {
  $owned = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
  if ($owned -and $owned.Path -eq $exe -and $owned.StartTime.ToUniversalTime() -eq $process.StartTime.ToUniversalTime()) { $owned.Kill() }
}
