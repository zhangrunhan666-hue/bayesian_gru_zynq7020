# Jester GRU 硬件加速演示视频指南

## 0. 最终固件

```text
数据集：Jester 3 类
训练：13,100 段
验证：1,611 段

准确率：1272/1611 = 78.96%
Stop Sign：389/536
Thumb Up：417/539
Thumb Down：466/536

自适应 K：K3=1061，K4=19，K5=531
时间：51,047 ms，31 ms/clip

accept H<=0.50：1042/1201 = 86.8%
reject H>0.50 ： 230/410  = 56.1%
mean entropy correct：0.184
mean entropy wrong：  0.467
```

SD 卡根目录：

```text
BOOT.BIN     4,284,876 字节
CLIPS.BIN   13,198,939 字节
```

两个文件必须同时存在。

## 1. 录制前检查

- 板子、5V 电源、USB-UART；
- SD0 插卡，BOOT=11；
- XCOM 选 CH340 COM 口，115200，8N1；
- 手机/相机固定，拍板子；
- OBS 录屏 + 麦克风；
- 先按 POR 跑一遍，确认输出正常。

## 2. 推荐视频结构（3–5 分钟）

| 时间 | 画面 | 内容 |
|---|---|---|
| 0:00–0:20 | 板子特写 | ZYNQ 7020、SD0、BOOT=11 |
| 0:20–0:40 | 板子 + 电脑 | 上电，DONE 灯亮，串口开始输出 |
| 0:40–1:20 | XCOM | 78.96%、逐类、31 ms/clip、3.27× |
| 1:20–1:50 | 按 POR 重跑 | 展示可重复性 |
| 1:50–3:00 | PPT/架构图 | PS+PL 分工、HLS W_ih、资源 |
| 3:00–3:30 | 结果页 | 78.96%、接受 86.8%、总结 |

## 3. 镜头 1：板子与启动方式

拍：

- 板子全景；
- SD0 卡槽；
- BOOT 开关 `11`；
- DONE 灯。

旁白：

> 这是基于 ZYNQ 7020 的贝叶斯 GRU 手势识别加速系统。程序从 SD 卡启动，BOOT 开关设置为 11，SD 卡里同时放了 BOOT.BIN 和验证数据 CLIPS.BIN。

## 4. 镜头 2：上电与串口

先开 OBS，再上电；画面同时有板子和 XCOM。

旁白：

> 上电后 PS 完成配置，PL 中的 GRU 加速核开始工作。串口正在读取 1,611 段 Jester 验证数据。

## 5. 镜头 3：结果特写

XCOM 字体调大，镜头对准：

```text
done: 1272/1611 correct
Stop Sign: 389/536
Thumb Up: 417/539
Thumb Down: 466/536
adaptive K counts: K3=1061 K4=19 K5=531
time: 51047 ms total, 31 ms/clip
accept H<=0.50: 1042/1201, acc=867/1000
reject H>0.50: 230/410, acc=560/1000
```

旁白：

> 在 Jester 三类手势上，板上准确率 78.96%。同样的模型和输入，纯 PS 需要 27 毫秒一段，PS+PL 确定性推理只要 8 毫秒，加速 3.27 倍。加入自适应 MC 采样后，完整 1,611 段用时 51 秒，平均 31 毫秒一段。

## 6. 镜头 4：复现

按 POR，再跑一遍，结果一致。

旁白：

> 复位后重新运行，结果一致，说明系统可重复。

## 7. 镜头 5：架构页

讲：

- PL：`W_ih × x`，16 路 MAC，BRAM 130/140，DSP 24；
- PS：`W_hh`、门控、FC、MC Dropout、entropy；
- 自适应 K：先 K=3，entropy<0.30 停止，否则补到 K=5；
- 接受子集 86.8%，拒识子集 56.1%。

## 8. 字幕卡

```text
Jester 3 类：Stop Sign / Thumb Up / Thumb Down
板上准确率：1272/1611 = 78.96%
接受子集：86.8%，拒识子集：56.1%
PS-only 27 ms → PS+PL 8 ms，3.27×
```

不要在视频里写：

```text
实时摄像头识别
官方 test 准确率
```

当前是 **验证集批量推理**，不是官方 test，也不是摄像头实时输入。

## 9. 保存串口日志

XCOM 点“保存窗口”，保存：

```text
report/jester_demo_uart.log
```

## 10. 常见问题

- 串口没输出：BOOT=11、SD0、DONE 灯、COM 口 115200；
- 输出 1,200 段：SD 卡里是旧 BOOT，换 `BOOT_jester_sd_adaptive.bin`；
- `ERROR: f_open`：CLIPS.BIN 没放根目录或不是 FAT32；
- 画面太糊：XCOM 字体调大，录屏 1080p；
- 结果一闪而过：先清屏再上电，或按 POR 重跑。
