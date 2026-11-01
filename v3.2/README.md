# 大肥鱼我的家乡 · v3.2 最终修改版

片头、片尾采用思源宋体风格衬线标题，片尾直接列出音乐原作《大东北我的家乡》、改编梨茗子、角色原作上善、女仆设计 ZipZipPipe，以及视觉制作与参考。其余内容沿用 v3.1。

## 独立渲染

Python 3.12、FFmpeg、Noto Sans/Serif CJK 与 DejaVu Sans Mono 字体；字体路径见 source。

```bash
python -m venv .venv
.venv/bin/pip install -r v3.2/requirements.txt
.venv/bin/python v3.2/source/render_complete.py
```

ZIP 已含原歌曲、全部运行素材、预计算光流、节奏事件和逐词歌词，不需要下载旧版视频、模型或调用 API。每帧由绝对歌曲时间生成，可编辑 source/director.py、opening.py、monochrome.py 等。

交付 MP4 为保留 v3.1 正片而局部替换的合成母版；render_complete.py 是从素材直接重渲染全片的独立入口，压缩代际会与交付文件略有区别。finish.py 保留了局部替换流程，使用它时才需要 v3.1 母版。

音乐原作：《大东北我的家乡》；改编：梨茗子。角色原作上善；女仆设计 ZipZipPipe。美术署名与条款详见 CHARACTER-NOTICE.txt。
