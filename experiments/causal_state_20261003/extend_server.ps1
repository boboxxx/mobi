$ErrorActionPreference = 'Stop'
$record = Get-Content "$env:USERPROFILE\mobi-causal-state-server.json" | ConvertFrom-Json
if ($record.experiment -ne 'causal_state_20261003') { throw 'Ownership mismatch' }
$owned = Get-Process -Id $record.pid
if ($owned.Path -ne $record.executable) { throw 'Executable mismatch' }
$serverInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($record.pid)"
$launcherId = $serverInfo.ParentProcessId
$launcherInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$launcherId"
if (-not $launcherInfo -or $launcherInfo.Name -ne 'powershell.exe' -or $launcherInfo.CommandLine -notlike '*mobi-causal-start.ps1*') { throw 'Launcher ownership mismatch' }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class MobiOwnedLauncher {
 [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr handle);
 [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr handle);
}
'@
$launcher = Get-Process -Id $launcherId
if ([MobiOwnedLauncher]::NtSuspendProcess($launcher.Handle) -ne 0) { throw 'Cannot suspend owned launch timer' }
@{experiment=$record.experiment; pid=$record.pid; launcherId=$launcherId; finiteGuardMs=2700000; reason='Full frozen dynamic schedule projected beyond original 30min timer'; timestampUtc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content "$env:USERPROFILE\mobi-causal-state-extension.json"
Get-Content "$env:USERPROFILE\mobi-causal-state-extension.json"
try {
 if (-not $owned.WaitForExit(2700000)) { Stop-Process -Id $record.pid; $null=$owned.WaitForExit(10000) }
} finally {
 if (Get-Process -Id $launcherId -ErrorAction SilentlyContinue) { $null=[MobiOwnedLauncher]::NtResumeProcess($launcher.Handle) }
}
