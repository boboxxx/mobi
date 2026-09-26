$ErrorActionPreference = 'Stop'
$install = 'C:\App\CARLA_0.9.15\WindowsNoEditor'
$binary = Join-Path $install 'CarlaUE4\Binaries\Win64\CarlaUE4-Win64-Shipping.exe'
if (!(Test-Path $binary)) { throw "CARLA binary missing: $binary" }
$existing = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^CarlaUE4' }
if ($existing) { throw 'CARLA is already running; inspect the existing instance before launching another.' }
Set-Location $install
# Foreground process: keep this SSH/terminal session open while using the simulator.
& $binary CarlaUE4 -dx12 -RenderOffScreen -nosound -unattended -carla-rpc-port=2000 -quality-level=Epic -ResX=640 -ResY=360
exit $LASTEXITCODE
