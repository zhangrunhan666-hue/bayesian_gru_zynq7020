# Build the PS application (Jester, FatFs + adaptive MC).
# Run from this build directory or anywhere; paths are derived from $PSScriptRoot.

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$src = Join-Path $root "src\vitis"
$build = $PSScriptRoot

$vitis = "D:\AMD\2026.1\2026.1\Vitis"
$gcc = Join-Path $vitis "gnu\aarch32\nt\gcc-arm-none-eabi\bin\arm-none-eabi-gcc.exe"
$plat = "D:\dsh-projects\kth_fpga\vitis_ws\ps7020_platform\export\ps7020_platform"
$inc = Join-Path $plat "sw\standalone_ps7_cortexa9_0\include"
$lib = Join-Path $plat "sw\standalone_ps7_cortexa9_0\lib"
$spec = (Join-Path $plat "sw\standalone_ps7_cortexa9_0\Xilinx.spec") -replace '\\','/'
$fatfs = Join-Path $vitis "..\data\embeddedsw\lib\sw_services\xilffs_v5_4\src"

$common = @(
    "-DSDT", "-mcpu=cortex-a9", "-mfpu=vfpv3", "-mfloat-abi=hard",
    "-specs=$spec", "-I$inc", "-I$src", "-I$fatfs\include",
    "-Wall", "-Wextra", "-O2", "-g3", "-U__clang__"
)

foreach ($f in @("ff.c", "diskio.c", "ffsystem.c")) {
    $obj = Join-Path $build (($f -replace '\.c$', '.o'))
    & $gcc @common -c (Join-Path $fatfs $f) -o $obj
    if ($LASTEXITCODE -ne 0) { throw "compile $f failed" }
}

$appobj = Join-Path $build "gru_ip_app.o"
& $gcc @common -c (Join-Path $src "gru_ip.c") -o $appobj
if ($LASTEXITCODE -ne 0) { throw "compile app failed" }

$objs = @($appobj, (Join-Path $build "ff.o"), (Join-Path $build "diskio.o"), (Join-Path $build "ffsystem.o"))
$elf = Join-Path $build "app.elf"
$args = $objs + @(
    "-o", $elf, "-Wl,-T,$src\lscript.ld", "-L$src", "-L$lib",
    "-Wl,--start-group", "-lxilstandalone", "-lxiltimer", "-lxil", "-lgcc", "-lc", "-lm", "-Wl,--end-group"
)
& $gcc @common @args
if ($LASTEXITCODE -ne 0) { throw "link failed" }
Write-Host "built $elf"
