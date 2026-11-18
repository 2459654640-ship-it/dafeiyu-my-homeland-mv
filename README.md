# Vice City, My Home · 罪城，我的家乡

**音乐 / 歌词：梨茗子。**

16:9 音乐 MV。黑色基底、霓虹人物蒙版、城市线框、动力字体与程序动画；全片使用统一的霓虹轮廓与栅格处理，官方片段没有直接作为未经处理的成片画面播放。

## 成片与素材

本次交付包含高清成片、完整可编辑工程和 AI 图片素材包。工程的 `assets/footage/` 为已剪出的官方来源片段；最终画面还会经过 `media_style.py` 的霓虹化处理及 `film.py` 的动画合成。

- 完整人物先亮相，再用连续扫描转换成同轮廓蒙版。
- 原始抱拳人物只出现在开场；后续以 Jason / Lucia 的抱拳、行走、倚靠和回身姿态展开。
- 70 个剪辑段；30 段官方来源选段的原片时间区间互不重叠。
- 中文主标题按音乐瞬态分批入场；64 px 加粗中文字幕为主，40 px 英文字幕为辅。英文逐词高亮，字幕时间取自实际人声的声学对齐结果。
- 音频第二次副歌实际唱出的两句已补入字幕；音乐没有变速。
- 原生 1920×1080、60 fps；高质量 H.264，AAC 320 kbps，BT.709。

## 重新渲染

需要 Python 3.11 或更新版本，以及可从终端调用的 FFmpeg / FFprobe。

```bash
python -m venv .venv
# 激活虚拟环境后执行：
pip install -r requirements.txt
python source/prepare.py
python source/render.py --workers 4
```

`prepare.py` 从随工程提供的短片构建霓虹效果缓存，约需 7 GB 临时磁盘空间。完整渲染建议 16 GB 以上内存；内存或 CPU 较少时改为 `--workers 1`。

输出：`output/Vice_City_My_Home_1080p60_HQ.mp4`。

只渲染一个时间段：

```bash
python source/render.py --start 70 --end 85 --workers 2 --name excerpt
```

## 编辑位置

| 文件 | 内容 |
| --- | --- |
| `source/film.py` | 镜头编排、角色布局、歌词意象、字幕样式 |
| `source/visuals.py` | 程序道路、建筑、棕榈、空间隧道、光带、蒙版与合成 |
| `source/media_style.py` | 所有官方片段统一使用的霓虹印刷与轮廓效果 |
| `analysis/lyrics.json` | 实际演唱的逐词时间、中英文字幕 |
| `analysis/hits.json` | 鼓、贝斯等分轨检测到的瞬态事件 |
| `analysis/shot-sources.json` | 原片地址、入出点、成片位置与唯一选段记录 |
| `assets/*.png` | 可替换的透明角色、姿态图集和完整人物蒙版 |
| `source/prepare.py` | 从已包含的选段重建效果缓存 |

修改歌词显示或时间请直接编辑 `analysis/lyrics.json`；只修改 `lyrics_data.py` 不会自动改变已对齐的字幕。更换音乐后可使用 `requirements-analysis.txt` 中的可选依赖与 `separate.py` / `align.py` / `analyze_beats.py` 重新分析；模型权重由相应的公开模型发行源获取。

本工程采用 Python 程序渲染。字体已附带，重新渲染不依赖生成图片服务。电影素材、音乐及字体的来源与权利归属见 [SOURCES.md](SOURCES.md)。
