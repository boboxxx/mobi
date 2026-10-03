$ErrorActionPreference = 'Stop'
$existing = Get-Process *Carla* -ErrorAction SilentlyContinue
if ($existing) { throw 'Existing CARLA process: refusing to start another server.' }
$exe = 'C:\App\CARLA_0.9.15\WindowsNoEditor\CarlaUE4\Binaries\Win64\CarlaUE4-Win64-Shipping.exe'
if (-not (Test-Path $exe)) { throw 'Expected installed CARLA 0.9.15 not found.' }
$info = New-Object System.Diagnostics.ProcessStartInfo
$info.FileName = $exe
$info.Arguments = 'Town10HD_Opt -RenderOffScreen -nosound -unattended -quality-level=Low -carla-rpc-port=2000'
$info.WorkingDirectory = 'C:\App\CARLA_0.9.15\WindowsNoEditor'
$info.UseShellExecute = $false
$process = [System.Diagnostics.Process]::Start($info)
@{pid=$process.Id; executable=$exe; experiment='shape_availability_20261003'} | ConvertTo-Json | Set-Content "$env:USERPROFILE\mobi-shape-availability-server.json"
$process | Select-Object Id,ProcessName

# Hold the SSH launch session; enforce a finite server lifetime.
if (-not $process.WaitForExit(1800000)) { $process.Kill() }
