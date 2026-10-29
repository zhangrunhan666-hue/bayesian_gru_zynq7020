# 发布到 GitHub

仓库目录：

```text
D:\dsh-projects\kth_fpga\submission\bayesian_gru_zynq7020
```

建议仓库名：

```text
bayesian-gru-zynq7020
```

## 方式 A：GitHub Desktop（推荐，无需命令行）

1. 打开 https://desktop.github.com/ ，下载并安装 GitHub Desktop；
2. 启动后 **Sign in to GitHub.com**，登录你的账号；
3. 菜单 **File → Add local repository**；
4. 选择上面的目录：
   ```text
   D:\dsh-projects\kth_fpga\submission\bayesian_gru_zynq7020
   ```
5. 如果提示 “not a Git repository”，点 **create a repository**；
6. Name 填 `bayesian-gru-zynq7020`，Local path 保持该目录，点 **Create repository**；
7. 左下角 Summary 填：
   ```text
   Initial commit: Bayesian GRU accelerator on Zynq-7020
   ```
8. 点 **Commit to main**；
9. 点右上角 **Publish repository**；
10. **取消勾选 “Keep this code private”**，点 **Publish repository**；
11. 发布完成后复制仓库网址，例如：
    ```text
    https://github.com/<你的用户名>/bayesian-gru-zynq7020
    ```

## 方式 B：Git for Windows + 命令行

1. 安装 Git for Windows：https://git-scm.com/download/win
2. 打开 PowerShell，执行：

```powershell
cd "D:\dsh-projects\kth_fpga\submission\bayesian_gru_zynq7020"

git init
git config user.name "你的名字"
git config user.email "你的邮箱"

git add .
git commit -m "Initial commit: Bayesian GRU accelerator on Zynq-7020"
git branch -M main

# 先在 github.com 新建空仓库 bayesian-gru-zynq7020，不要勾选 README
git remote add origin https://github.com/<你的用户名>/bayesian-gru-zynq7020.git
git push -u origin main
```

首次 push 会弹出浏览器登录，按提示授权即可。

## 关于 CLIPS.BIN

`.gitignore` 已忽略：

```text
data/CLIPS.BIN
```

原因：

- 文件 13 MB，是 Jester 派生验证数据；
- 公开仓库不重复分发数据集更稳妥；
- 本地 SD 卡仍保留该文件；
- 需要时用 `src/python/pack_clips_bin.py` 重新生成。

如果评委要求仓库自带完整验证数据，可以把这个文件放到 **GitHub Releases**，不要直接提交进 Git 历史。

## 发布后

把仓库地址补到：

- 根目录 `README.md`
- `SUBMISSION_CHECKLIST.md`
- 比赛提交页的“开源地址”栏

## 检查

发布后打开仓库，确认能看到：

```text
README.md
LICENSE
src/
sim/
build/
board/
data/README.md
skill/
report/
```

`data/CLIPS.BIN` 不出现是正常的。
