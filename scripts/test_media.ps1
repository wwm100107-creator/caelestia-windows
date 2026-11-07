Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }

function Await($winRtTask, $resultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($resultType)
    $netTask = $asTask.Invoke($null, @($winRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media, ContentType = WindowsRuntime] | Out-Null
$asyncOp = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
$mgr = Await $asyncOp ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
$s = $mgr.GetCurrentSession()
Write-Output "Session: $($s -ne $null)"
if ($s) {
    $asyncProp = $s.TryGetMediaPropertiesAsync()
    $p = Await $asyncProp ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
    Write-Output "Thumbnail ref: $($p.Thumbnail -ne $null)"
    if ($p.Thumbnail) {
        $streamOp = $p.Thumbnail.OpenReadAsync()
        Write-Output "StreamOp: $($streamOp -ne $null)"
        $stream = Await $streamOp ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
        Write-Output "Stream: $($stream -ne $null), Size: $($stream.Size)"
        $size = [int]$stream.Size
        if ($size -gt 0) {
            $netStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
            $bytes = New-Object byte[] $size
            $read = $netStream.Read($bytes, 0, $size)
            $outPath = "C:\Users\uypc1\.gemini\antigravity\scratch\caelestia-windows\zebar-pack\assets\media_thumb.jpg"
            [System.IO.File]::WriteAllBytes($outPath, $bytes)
            Write-Output "Saved $read bytes to $outPath"
        }
    }
}
