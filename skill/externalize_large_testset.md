# 大验证集外置 SD

## 适用场景

验证集/测试图片编译进 ELF 后，BOOT.BIN 超过启动镜像可加载范围，出现 DONE 不亮、串口无输出。

## 方法

1. 把验证数据打包成二进制 `CLIPS.BIN`，不要生成巨大的 `clips.h`；
2. 文件头：magic、N、T、S；随后标签数组和 `N*T*S*S` 字节数据；
3. 应用只保留权重和读取/推理代码；
4. Vitis 应用加 FatFs（`ff.c`、`diskio.c`、`ffsystem.c` + `xilffs_config.h`）；
5. 启动后 `f_mount("0:",1)`、`f_open("0:/CLIPS.BIN")`，逐段 `f_read` 到 DDR 缓冲；
6. 先校验头，再读标签，最后按段读取。

## 失效条件

- SD 卡不是 FAT32；
- `CLIPS.BIN` 没有放到根目录；
- 只复制 BOOT.BIN，忘记复制 CLIPS.BIN；
- 文件头字节序/长度不一致（本作品为 little-endian）。

## 证据

本作品 1,611 段数据嵌入 ELF 时 BOOT 17.4 MB，DONE 不亮；改为 4.3 MB BOOT + 13.2 MB CLIPS.BIN 后正常启动。
