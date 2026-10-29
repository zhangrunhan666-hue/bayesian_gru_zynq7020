# HLS AXI-Lite 上板排查

## 适用场景

HLS IP 已综合、bitstream 已烧写，但 PS 读 IP 寄存器挂起，或 `AP_START` 写不进去、`AP_DONE` 读不到。

## 检查顺序

1. **确认 bitstream 里真的有 IP**：看实现利用率报告，BRAM/DSP 不应为 0；不要只看 bit 文件大小（同器件 bit 文件大小固定）。
2. **确认 FCLK 在跑、复位已释放**：读 `SLCR.FPGA_RST_CTRL`；必要时在 BD 中把 `ap_rst_n` 接常量 1 做隔离测试。
3. **读 AP_CTRL**：`0x4` 表示 IDLE；写入 `0x1` 后应看到 AP_START/AP_DONE 变化。
4. **写已知 pattern 到 x 缓冲区并读回**：先确认 AXI 写通道，不要只写全 0 帧（全 0 无法判断）。
5. **注意 AP_DONE 是 clear-on-read**：`XGru_mv_IsDone()` 读一次就会清掉；不要连续调用两次，否则第二次误判 TIMEOUT。
6. **逐帧打印 gi 前几个值**：与 PC 参考对比，定位是输入、权重还是 PS 后处理。

## 常见失效条件

- 只复位了 impl，没有复位 synth，bitstream 仍是旧 PS-only；
- `FPGA_RST_CTRL` 写 0xF 反而断言复位；
- `XGru_mv_IsDone` 连续调用两次；
- HLS 归一化标定与 PS 不一致（首帧全 0 时看起来正常，后续帧偏差放大）。

## 证据

本作品曾出现 `IP read ctrl...` 挂起、`IP TIMEOUT ctrl=0x4`、首帧 gi 正确但后续帧异常；按上述顺序定位到 bitstream、复位、AP_DONE COR 和归一化标定问题。
