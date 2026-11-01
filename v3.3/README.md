# 大肥鱼我的家乡 · v3.3 中文字幕增强版

非终端歌词改为 48 号中文主字幕与 30 号英文辅字幕；间奏历史与后半段英文叙事补充中文说明。保持片头片尾、画面、转场与歌曲时间轴。无新增生图。

完整工程含 v3.2 原生画面生成代码、全部运行素材、音频、特征、歌词时间轴，以及 v3.3 字幕层。

## 独立重渲染

安装 Python 3.12、FFmpeg（含 libass）、Noto Sans/Serif CJK 和 DejaVu 字体。

```bash
python -m venv .venv
.venv/bin/pip install -r v3.2/requirements.txt
.venv/bin/python v3.2/source/render_complete.py
.venv/bin/python v3.3/source/apply_subtitles.py
```

已有 v3.2 高清视频时，可直接将其绝对路径作为 apply_subtitles.py 参数，省略原生画面重渲染。

修改 v3.3/source/subtitles.py 可调整中文、字号、时间和样式；输出的 ASS 与 subtitle-events.json 可直接编辑。交付视频已将双语字幕烧录，无需播放器外挂。

音乐原作：《大东北我的家乡》；改编：梨茗子。角色署名与美术条款沿用 CHARACTER-NOTICE.txt。
