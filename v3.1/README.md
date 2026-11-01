# v3.1 最小修改版

仅调整开屏粗体标题、场景短叠化、冷蓝字符剪影，删除人工绘制的简化吉他与拨弦条。沿用 v3 的音乐、分镜和所有素材，不新增生成图。完整 195 秒，1080p60，CRF 13 高质量编码，音轨直接复制 v3。

[高清完整版](https://github.com/2459654640-ship-it/dafeiyu-my-homeland-mv/raw/refs/heads/main/masters/Dafeiyu-My-Homeland-v3.1-1080p60-Master.mp4)

复现：解压 v3 工程，将 v3 复制为 v3.1，再覆盖本目录源码。把 v3 完整母版保存到 v3/output/Dafeiyu-My-Homeland-v3-1080p60-Master.mp4。运行下列命令：

```bash
python v3.1/source/render.py --ranges 0:10.6 --video-only --output v3.1/output/opening.mp4
python v3.1/source/render.py --ranges 110.5:125.75 --video-only --output v3.1/output/code.mp4
python v3.1/source/finish.py
```

新标题使用系统 Noto Sans CJK Bold 字体；其他依赖同 v3。finish.py 保留整首音乐时间轴，只替换两个画面片段并处理约三分之一秒的转场。角色署名与美术条款同 v3。
