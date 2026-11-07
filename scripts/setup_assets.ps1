$ErrorActionPreference = "Stop"
$projDir = "C:\Users\uypc1\.gemini\antigravity\scratch\caelestia-windows"
$shellSrc = "C:\Users\uypc1\.gemini\antigravity\scratch\caelestia-shell\assets"
$packAssets = Join-Path $projDir "zebar-pack\assets"
$binDir = Join-Path $projDir "bin"

New-Item -ItemType Directory -Force -Path $packAssets | Out-Null
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

Copy-Item (Join-Path $shellSrc "logo.svg") (Join-Path $packAssets "logo.svg") -Force
Copy-Item (Join-Path $shellSrc "bongocat.gif") (Join-Path $packAssets "bongocat.gif") -Force
Copy-Item (Join-Path $shellSrc "kurukuru.gif") (Join-Path $packAssets "kurukuru.gif") -Force
Copy-Item (Join-Path $shellSrc "wallpaper.webp") (Join-Path $packAssets "wallpaper.webp") -Force
Copy-Item (Join-Path $shellSrc "google-sans-flex\GoogleSansFlex-VariableFont_GRAD,ROND,opsz,slnt,wdth,wght.ttf") (Join-Path $packAssets "GoogleSansFlex.ttf") -Force

$userFonts = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $userFonts | Out-Null
$destFont = Join-Path $userFonts "GoogleSansFlex.ttf"
Copy-Item (Join-Path $packAssets "GoogleSansFlex.ttf") $destFont -Force
$regPath = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}
Set-ItemProperty -Path $regPath -Name "Google Sans Flex (TrueType)" -Value $destFont

$msiPath = Join-Path $env:TEMP "standalone-glazewm-v3.10.1-x64.msi"
if (-not (Test-Path $msiPath)) {
    & curl.exe -sL --max-time 30 "https://github.com/glzr-io/glazewm/releases/download/v3.10.1/standalone-glazewm-v3.10.1-x64.msi" -o $msiPath
}
$extractDir = Join-Path $binDir "glazewm-extract"
if (Test-Path $extractDir) {
    Remove-Item -Recurse -Force $extractDir
}
Start-Process msiexec.exe -ArgumentList "/a `"$msiPath`" /qn TARGETDIR=`"$extractDir`"" -Wait
$glazeExe = Get-ChildItem -Path $extractDir -Filter "glazewm.exe" -Recurse | Select-Object -First 1
if ($glazeExe) {
    Copy-Item $glazeExe.FullName (Join-Path $binDir "glazewm.exe") -Force
    Write-Output "[OK] Extracted glazewm.exe to $binDir\glazewm.exe"
}

Write-Output "[OK] Assets and GlazeWM ready"
