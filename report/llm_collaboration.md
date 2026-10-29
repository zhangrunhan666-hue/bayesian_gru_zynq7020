# 大模型协作记录
项目：贝叶斯循环神经网络硬件加速设计  
日期：2026-10-29
本记录整理关键提示词、模型回答/动作、自我纠错与验证结果。原始会话界面较长，正文保留关键节点。
## 协作原则
AI 提出方案和排查顺序，所有关键结论必须用板端串口、寄存器读回、综合利用率或 PC/板端逐类计数验证；发现错误时记录并修正。
## 阶段总览
| 阶段 | 用户目标 | AI 作用 | 验证 |
|---|---|---|---|
| 数据检查 | Jester 数据打不开/缺标签 | 检查 gzip/tar/CSV，补 3 类标注 | 13,100/1,611 |
| IP 启动 | IP read ctrl 挂起 | 查 bitstream、FCLK 复位、synth 重跑 | IP 正常出 gi |
| AP_DONE | done 读不到/误报 TIMEOUT | 查 clear-on-read，只读一次并保存 | 431 段完整 |
| 归一化 | 首帧对、后续 gi 异常 | 逐帧对比，PS 端补偿 1/255 | gi 恢复正常 |
| BOOT | 全量验证集 DONE 不亮 | 判断镜像过大，改 SD CLIPS.BIN | 4.3 MB 启动 |
| C 仿真 | testbench 不可用/跑不过 | 恢复 tb.file、换 Jester tb_data | 0 errors |

## 二、案例 1：Jester 数据检查与扩充
> 用户提示：我在网上下载了 jester 数据集，在 D:\datasets\20bnjester-v1-00，你帮我看一下对不对。
**模型回答/动作：** 模型检查文件头为 gzip、tar 列表为 20bn-jester-v1/<id>/*.jpg；指出它是分片压缩包不是文件夹，且缺 train/validation/labels CSV。后续生成 3 类 13,100/1,611 数据。
**自我纠错：** 最初把 10GB 单文件误判为“截断”，后通过 tar 列表和分片合并纠正；训练从 1,200 段扩到 13,100 段。
**验证/结果：** 准确率从 69.0% 提升到 78.96%。

## 三、案例 2：HLS IP 读挂起
> 用户提示：串口只打印到 IP 初始化，IP read ctrl 后就停了。
**模型回答/动作：** 模型加入寄存器打印、超时、x 缓冲区回读；先怀疑复位，再检查 bitstream 利用率，发现 BRAM/DSP=0，说明实现复用了旧 PS-only 综合结果。
**自我纠错：** 曾把 0xF 写入 FPGA_RST_CTRL 导致 AXI 读挂起，后改为只读；确认必须先 reset synth_1 再 impl_1；ap_rst_n 接常量 1。
**验证/结果：** IP 可正常读写，gi 输出正确。

## 四、案例 3：AP_DONE 的 clear-on-read
> 用户提示：IP TIMEOUT ctrl=00000004，但 IP 实际已经跑完。
**模型回答/动作：** 模型查看 HLS 生成的 control_s_axi.v，发现 AP_DONE 是 Read/COR（读后清除）；原代码连续调用两次 IsDone，第二次把 done 清掉，误报 TIMEOUT。
**自我纠错：** 改为只读一次并保存 done；不再重复调用 IsDone。
**验证/结果：** 431/1,611 段可完整跑完。

## 五、案例 4：HLS 归一化标定不一致
> 用户提示：第一帧 gi 正确，后续帧 gi 变成几千万。
**模型回答/动作：** 模型逐帧对比 gi，发现 HLS MAC 使用原始 x，而训练/PS 使用 x/255；第一帧全 0 时看不出来，后续帧被放大。
**自我纠错：** 先尝试改 HLS 综合，后采用 PS 端补偿：gi=(gi-b)/255+b；保留 HLS IP 不变。
**验证/结果：** gi 与 PC 参考恢复到 1e-3 量级；准确率恢复。

## 六、案例 5：全量验证集 BOOT 过大
> 用户提示：换成全量 1,611 段后 DONE 灯不亮、串口没输出。
**模型回答/动作：** 模型对比旧版 14.1 MB 与全量 17.4 MB，判断镜像超出启动加载范围；建议把验证集外置为 CLIPS.BIN，应用用 FatFs 逐段读取。
**自我纠错：** 最初只怀疑 bitstream，后通过旧 BOOT 能启动排除板子问题；改为 4.3 MB BOOT + 13.2 MB CLIPS.BIN。
**验证/结果：** 全量 1,611 段正常启动并跑完。

## 七、案例 6：HLS C 仿真 testbench 不匹配
> 用户提示：C SIMULATION 报 Test bench is not available，或者 testbench 跑不过。
**模型回答/动作：** 模型检查 Vitis HLS 组件配置，发现之前为避免旧 KTH testbench 冲突删掉了 tb.file；随后恢复 tb.file，并把 tb_data.h 换成 Jester 帧 1 的参考数据。
**自我纠错：** 最初直接删 tb.file 绕开问题，导致 C SIMULATION 不可用；改为保留 testbench 并更新参考数据。
**验证/结果：** C 仿真通过：max_gi_err=0.000015，errors=0。

## 协作边界
多目标贝叶斯优化、稀疏变分推断未实现，报告写成后续工作；贝叶斯为 MC Dropout 近似，动态推理为自适应 K 采样。
