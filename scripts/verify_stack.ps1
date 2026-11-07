$ErrorActionPreference = "Continue"
$projDir = Split-Path -Parent $PSScriptRoot
& powershell -NoProfile -ExecutionPolicy Bypass -File "$projDir\start-caelestia.ps1"
Start-Sleep -Seconds 2
Get-Process -Name zebar, glazewm, Flow.Launcher -ErrorAction SilentlyContinue | Select-Object Name, Id
& "$projDir\bin\glazewm-extract\PFiles64\glzr.io\GlazeWM\cli\glazewm.exe" query workspaces
