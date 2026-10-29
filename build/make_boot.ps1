$ErrorActionPreference = "Stop"
$bootgen = "E:\vivado2026.1\2026.1\Vivado\bin\bootgen.bat"
if (-not (Test-Path $bootgen)) {
    throw "bootgen not found: $bootgen"
}

Push-Location $PSScriptRoot
try {
    & $bootgen -image "boot.bif" -arch zynq -o "BOOT.BIN" -w on
    if ($LASTEXITCODE -ne 0) { throw "bootgen failed: $LASTEXITCODE" }
    Copy-Item "BOOT.BIN" "..\board\BOOT.BIN" -Force
    Write-Host "BOOT.BIN generated and copied to board/BOOT.BIN"
} finally {
    Pop-Location
}
