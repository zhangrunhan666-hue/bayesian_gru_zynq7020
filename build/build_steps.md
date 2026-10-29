# 复现构建步骤

工具：Vivado / Vitis / Vitis HLS 2026.1，器件 `xc7z020clg400-2`，板卡 ZYNQ MINI 7020。

## 1. HLS

1. 打开 Vitis，选择 `src/hls` 下的 `gru_mv.cpp`、`gru_mv.h`、`weights_hls.h`；
2. top = `gru_mv`，part = `xc7z020clg400-2`，clock = 10 ns；
3. C SYNTHESIS → PACKAGE，导出 IP catalog；
4. 记录 `build/csynth.rpt`。

## 2. Vivado

1. 可直接打开已归档工程 `src/vivado/project/ps7020.xpr`；若路径变化，重新指定 HLS IP 仓库；
2. PS 配置：DDR3 MT41J256M16 RE-125、16-bit、533.333333 MHz；FCLK0 50 MHz；
3. 添加 HLS IP，AXI-Lite 地址 `0x43C00000`；
4. `ap_clk` 接 FCLK0，`ap_rst_n` 接常量 1；
5. 综合、实现、生成 bitstream，导出 XSA；
6. 资源/时序参考 `build/impl_utilization.rpt`、`build/timing_summary.rpt`。

## 3. Vitis 应用

1. 平台使用上述 XSA；
2. 源文件：`src/vitis/gru_ip.c`、`src/vitis/weights.h`、`src/vitis/xilffs_config.h`、`src/vitis/lscript.ld`；
3. 额外编译 FatFs 源：`ff.c`、`diskio.c`、`ffsystem.c`（Vitis 2026.1 安装目录 `data/embeddedsw/lib/sw_services/xilffs_v5_4/src`）；
4. 编译选项：`-DSDT -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -O2`；
5. 链接 `-lxilstandalone -lxiltimer -lxil -lgcc -lc -lm`。

## 4. BOOT.BIN

在 `build/` 目录执行：

```powershell
cd build
bootgen -image boot.bif -arch zynq -o BOOT.BIN -w on
```

或直接运行 `build/make_boot.ps1`。

`boot.bif` 中依次为 `fsbl.elf`、`system_wrapper.bit`、`app.elf`。

## 5. SD 卡

FAT32，根目录放 `BOOT.BIN` 与 `CLIPS.BIN`；BOOT=11，SD0，UART 115200。
