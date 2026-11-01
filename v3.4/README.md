# 大肥鱼我的家乡 · v3.4 历史间奏更新

将 110.50–129.55 秒原演奏与早期 DeepSeek 段落，改为五个连续关键节点：2022 ChatGPT → 2023 DeepSeek 早期模型 → 2025 R1 → 2026 DeepSeek Harness → 2026.10 V4.1-Flash-1017。保留其他画面、原音轨及 v3.3 大号中英字幕。

Harness 明确标为开发者预览阶段的插件化智能体框架；V4.1-Flash-1017 标为最新公开模型更新。模型及框架节点依据 2026-11-02 核查的官方仓库和模型卡。动画是叙事演绎，不是实际系统运行录像或真实模型结构图。

## 独立重渲染

工程含全部音频、素材、预计算特征与时间轴，不需要下载旧版成片。依赖 Python 3.12、FFmpeg/libass、Noto CJK Sans/Serif 和 DejaVu 字体。

```bash
python -m venv .venv
.venv/bin/pip install -r v3.2/requirements.txt
.venv/bin/python v3.2/source/render_complete.py
.venv/bin/python v3.4/source/apply_subtitles.py
```

新的历史动画由 v3.2/source/modern_history.py 生成，其余画面使用原始生成器；最后应用大号字幕。v3.4/source/finish.py 另外保留了基于 v3.3 成片局部替换的交付流程，此路径才需要旧版成片。

## 官方事实来源

- ChatGPT：https://openai.com/index/chatgpt/
- DeepSeek 早期公开代码模型：https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base （官方模型仓库创建于 2023 年，画面只标年份。）
- R1：https://github.com/deepseek-ai/DeepSeek-R1
- Harness：https://github.com/deepseek-ai/deepseek-harness/blob/master/README.zh.md （开发者预览；一切皆插件。）
- 最新公开模型更新：https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017 （官方模型卡明确为 V4.1-Flash 的小版本更新；公开模型仓库创建时间为 2026-10-17。）

音乐原作：《大东北我的家乡》；改编：梨茗子。角色与美术条款沿用 CHARACTER-NOTICE.txt。
