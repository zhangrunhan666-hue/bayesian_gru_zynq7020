# 板端运行

## 硬件

- ZYNQ-7000 XC7Z020-2CLG400I
- SD0 启动，BOOT=11
- USB-UART 115200，8N1

## SD 卡根目录

```text
BOOT.BIN     4,284,876 字节
CLIPS.BIN   13,198,939 字节
```

两个文件必须同时存在。`BOOT.BIN` 已包含 FSBL、bitstream 和 PS 应用；`CLIPS.BIN` 为验证数据。

## 预期串口输出

见 `uart_output.txt`。上电到结果约 55–60 秒。
