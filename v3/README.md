# 大肥鱼我的家乡 · v3 / Beyond the Terminal

完整 195 秒音乐 MV。画面以终端、字符几何和程序动画为主，原生输出 1920×1080 / 60 fps。

本版在 v2 方向上扩展：巨大抱拳开屏与「大东北 → 大肥鱼」改字、脱离固定窗口的空间、歌词构成的几何体、吉他演奏、黑白负形轮廓变换，以及 AI 历史间奏。

## 下载与播放

- [完整高清高码率 MP4](https://github.com/2459654640-ship-it/dafeiyu-my-homeland-mv/raw/refs/heads/main/masters/Dafeiyu-My-Homeland-v3-1080p60-Master.mp4)
- [包含输入素材的可编辑工程 ZIP](https://github.com/2459654640-ship-it/dafeiyu-my-homeland-mv/raw/refs/heads/main/downloads/Dafeiyu-v3-Editable-Project.zip)

大视频使用 Git LFS 保存，上面的 `raw` 链接提供实际媒体。GitHub 文件页可能只显示 LFS 指针；可直接下载，或用 `git lfs pull` 获取媒体。完整 MP4 是 H.264 高质量编码，CRF 14、峰值上限 45 Mb/s，AAC 320 kb/s；不是无损视频。没有为满足普通 Git 文件大小限制而再转码一份小文件。

## 复现

解压 ZIP 后，在 `dafeiyu-mv-v3` 目录执行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r v3/requirements.txt
mkdir -p v3/output v3/analysis v3/frames
.venv/bin/python v3/source/render.py --parallel-master
```

系统需要 FFmpeg / FFprobe、DejaVu Sans Mono 和 Noto Sans CJK 字体。Linux 字体路径在 `v3/source/ui.py` 中。音频分析、事件时间轴和插值数据已包含，不需要模型下载、API 密钥、游戏工程或云服务。

```bash
# 只重渲染一段，仍为原生 1080p60 高质量编码
.venv/bin/python v3/source/render.py --ranges 110.5:125.74 --output v3/output/performance.mp4
# 按时间检查静帧
.venv/bin/python v3/source/render.py --stills --times 2,7.7,35,64.5,105,112,120,123.1,153.7
# 完整影片生成后进行媒体与音频同步验证
.venv/bin/python v3/source/validate.py
```

每帧由绝对歌曲时间与固定随机种子决定，可独立修改、重渲染片段并无损拼接已编码的画面。

## 主要源码

| 文件 | 功能 |
| --- | --- |
| `director.py` | 35 个段落的布局、场景、歌词事件与分层合成 |
| `opening.py` | 抱拳开屏、局部改字、开屏折叠到终端 |
| `performer.py` | 八个演奏关键姿态的双向光流插值、轮廓与手部／发尾形变 |
| `monochrome.py` | 吉他 → 鲸 → FREE → 角色的黑白负形演出 |
| `spectacle.py` | 无限窗口走廊、三维结、轨道、世界生成图与镜头冲击 |
| `lyric_space.py` | 歌词字形点云、字串流线、逐词阅读层 |
| `history.py` | 历史版本树、神经连接、搜索树、棋盘与注意力网络 |
| `rhythm.py` | 分离声部的起音事件与逐词时间轴 |
| `fields.py` / `ui.py` / `fx.py` / `film.py` | 延用和扩展 v2 的字符渲染、终端舞台、资产变形与场景组件 |
| `render.py` | 原生 60 fps 分段渲染、单次画面编码与流复制拼接 |

完整分镜见 `analysis/shot-plan.json`，主要音画事件见 `CUES.md`，历史出处见 `HISTORY-SOURCES.md`，验证结果见 `output/validation-v3.json`。

## 素材、参考与署名

角色原作：上善；女仆二次设计：ZipZipPipe。完整上游署名链见工程的 `references/character-NOTICE.txt`。用户提供角色参考与音乐；新增角色／物件图集由 OpenAI imagegen 生成。角色相关美术沿用上游 CC BY-NC-SA 4.0 要求。音乐权利不因源码公开而改变。

视觉研究参考 [MisakaZentai/world-execute-me-dsh-pv](https://github.com/MisakaZentai/world-execute-me-dsh-pv)。黑白段只借鉴《Bad Apple!!》常见的剪影、负形和轮廓变换语言，演奏动作、画面、音乐和构图为本项目内容；未导入东方角色、舞蹈镜头或《Bad Apple!!》音频。

本片为含 AI 生成素材与程序渲染的非官方同人作品。角色演出使用生成关键姿态与代码插值，不是完整三维人体绑定或生成式视频。终端工具调用和世界生成日志是叙事界面，并非真实 AI 内部计算记录。
