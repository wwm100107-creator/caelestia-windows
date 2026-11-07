$ErrorActionPreference = "Continue"
$projDir = $PSScriptRoot
if (-not $projDir) { $projDir = "C:\VỌC VẠCH TẬP CODING\caelestia-windows" }
$zebarDest = Join-Path $env:USERPROFILE ".glzr\zebar\caelestia-shell"
$glazeDir = Join-Path $env:USERPROFILE ".glzr\glazewm"

New-Item -ItemType Directory -Force -Path $zebarDest | Out-Null
New-Item -ItemType Directory -Force -Path $glazeDir | Out-Null

Copy-Item -Path "$projDir\zebar-pack\*" -Destination $zebarDest -Recurse -Force
Remove-Item -Path (Join-Path $zebarDest "bar.html") -Force -ErrorAction SilentlyContinue

$zebarSettings = Join-Path $env:USERPROFILE ".glzr\zebar\settings.json"
$settingsJson = @'
{
  "$schema": "https://github.com/glzr-io/zebar/raw/v3.3.1/resources/settings-schema.json",
  "startupConfigs": [
    {
      "pack": "caelestia-shell",
      "widget": "dashboard",
      "preset": "default"
    }
  ]
}
'@
[System.IO.File]::WriteAllText($zebarSettings, $settingsJson, [System.Text.UTF8Encoding]::new($false))

if (Test-Path "$projDir\glazewm-config.yaml") {
    Copy-Item -Path "$projDir\glazewm-config.yaml" -Destination (Join-Path $glazeDir "config.yaml") -Force
}

& python "$projDir\scripts\sync_palette.py"
& python "$projDir\scripts\taskbar_ctl.py" --autohide

function Start-Detached([string]$exePath, [string]$argStr = "") {
    if (Test-Path $exePath) {
        $workDir = Split-Path -Parent $exePath
        $cmdLine = if ($argStr) { "`"$exePath`" $argStr" } else { "`"$exePath`"" }
        ([wmiclass]"Win32_Process").Create($cmdLine, $workDir) | Out-Null
    }
}

$flowExe = Join-Path $env:LOCALAPPDATA "FlowLauncher\Flow.Launcher.exe"
if (-not (Get-Process -Name "Flow.Launcher" -ErrorAction SilentlyContinue)) {
    Start-Detached $flowExe
}

$glazeExe = "$projDir\bin\glazewm-extract\PFiles64\glzr.io\GlazeWM\cli\glazewm.exe"
if (-not (Get-Process -Name "glazewm" -ErrorAction SilentlyContinue)) {
    Start-Detached $glazeExe "start"
}

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

$zebarExe = "C:\Program Files\glzr.io\Zebar\zebar.exe"
if (Get-Process -Name "zebar" -ErrorAction SilentlyContinue) {
    Stop-Process -Name "zebar" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}
Start-Detached $zebarExe

Write-Output "[OK] Caelestia Windows Shell launched cleanly from: $projDir"
