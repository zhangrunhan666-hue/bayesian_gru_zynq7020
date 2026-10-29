# Bayesian GRU Accelerator on Zynq-7020

面向资源受限边缘设备的 Jester 三类手势识别系统。PS 负责 FatFs 读取、MC Dropout、W_hh/门控/FC 与不确定性评估；PL 中的 HLS 加速核完成 W_ih × x。

## 关键结果

| 项目 | 数值 |
|---|---|
| 数据集 | Jester 3 类（Stop Sign / Thumb Up / Thumb Down） |
| 训练 / 验证 | 13,100 / 1,611 |
| 板上 MC 准确率 | 78.96%（1272/1611） |
| 接受 / 拒识 | 86.8% / 56.1% |
| 自适应 K | K3=1061，K4=19，K5=531 |
| 时延 | 51.0 s / 1611 段，31 ms/段 |
| 确定性硬件加速比 | 3.27×（PS-only 27 ms → PS+PL 8 ms） |
| 资源 | BRAM 130/140，DSP 24/220，Fmax 140 MHz |

> 说明：本实现采用 MC Dropout 作为近似贝叶斯推理，并使用基于 entropy 的自适应 K 采样；不是完整稀疏变分推断或全硬件贝叶斯采样。多目标贝叶斯优化与稀疏先验属于后续工作。

## 快速运行

1. SD 卡格式化为 FAT32；
2. 将 `board/BOOT.BIN` 与 `data/CLIPS.BIN` 复制到 SD 卡根目录；
3. SD 卡插入 SD0，BOOT 开关设为 `11`；
4. USB-UART 连接 PC，串口 115200，8N1；
5. 上电，串口输出分类结果、entropy、自适应 K 分布和耗时。

## 目录

```text
src/        HLS、Vitis、Vivado、PC 训练/量化源码
sim/        HLS C 仿真日志与板端/PC 对比
build/      构建脚本、boot.bif、综合/实现报告
board/      可启动 BOOT.BIN 与串口说明
data/       CLIPS.BIN 与数据格式说明
skill/      可复用技能包
report/     设计报告、最终结果、演示指南、LLM 协作记录
```

## 构建

见 `build/build_steps.md`。工具链：Vivado/Vitis/HLS 2026.1，Vitis 2026.1，目标器件 `xc7z020clg400-2`。

## 开源地址

https://github.com/zhangrunhan666-hue/bayesian_gru_zynq7020

## 许可

MIT，见 `LICENSE`。
