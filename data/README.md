# CLIPS.BIN 格式

`CLIPS.BIN` 为 1,611 段 Jester 三类验证数据，供板端 FatFs 读取。

| 偏移 | 类型 | 含义 |
|---|---|---|
| 0 | char[4] | magic `JCLP` |
| 4 | uint32 LE | N = 1611 |
| 8 | uint32 LE | T = 8 |
| 12 | uint32 LE | S = 32 |
| 16 | uint8[N] | 标签（0=Stop Sign，1=Thumb Up，2=Thumb Down） |
| 16+N | uint8[N*T*S*S] | 帧差数据，每段 8×1024 字节 |

文件大小：16 + 1611 + 1611×8192 = 13,198,939 字节。
