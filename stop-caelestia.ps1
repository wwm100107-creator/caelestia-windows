$ErrorActionPreference = "Continue"
$projDir = $PSScriptRoot
if (-not $projDir) { $projDir = "C:\VỌC VẠCH TẬP CODING\caelestia-windows" }
$glazeCli = "$projDir\bin\glazewm-extract\PFiles64\glzr.io\GlazeWM\cli\glazewm.exe"

if ((Test-Path $glazeCli) -and (Get-Process -Name "glazewm" -ErrorAction SilentlyContinue)) {
    & $glazeCli command wm-exit 2>$null
    Start-Sleep -Milliseconds 500
}
Stop-Process -Name "glazewm" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "zebar" -Force -ErrorAction SilentlyContinue

$pidFile = Join-Path $projDir "mouse_edge.pid"
if (Test-Path $pidFile) {
    try {
        $daemonPid = [int](Get-Content $pidFile -Raw).Trim()
        Stop-Process -Id $daemonPid -Force -ErrorAction SilentlyContinue
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    } catch {}
}
Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%mouse_edge.py%'" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
$flagFile = Join-Path $projDir "dashboard.open"
if (Test-Path $flagFile) { Remove-Item $flagFile -Force -ErrorAction SilentlyContinue }

& python "$projDir\scripts\taskbar_ctl.py" --restore

Write-Output "[OK] Restored original Windows desktop!"
