# 素材与研究记录

## 用户提供

- `assets/song.mp3`：用户上传「6月20日 (5).mp3」，48 kHz 双声道，解码时长 195.000 秒；成片不改速、不剪短。用户确认以所贴 16 行英文歌词为最终歌词。
- 两张蓝发鲸鱼娘／女仆角色图片：用户在对话中提供的形象参考。
- 片名「大肥鱼我的家乡」及开场抱拳造型：用户指定。

## 本次生成的关键帧美术

六张图均由本次会话的 OpenAI imagegen 生成。原文件留在 `/workspace/generated_images`，工程保留同字节副本。

| 工程资产 | 生成原文件 | 用途 |
|---|---|---|
| `hero.png` | `exec-12dfec33-03e3-40c2-ab10-53a4a2009ece.png` | 伸手、漂浮的全身角色 |
| `awakening.png` | `exec-9eb9c1db-fa23-4464-96d8-3ba11c9c1f32.png` | 闭眼特写 |
| `greeting.png` | `exec-2b96faf5-fc33-430b-8b5b-9ee2adb6e34b.png` | 抱拳开场与结尾 |
| `ocean.png` | `exec-6245a63f-f6eb-47dc-ba5a-3f5b2575db6e.png` | 星鲸、海洋、轨道世界 |
| `awake.png` | `exec-a45e609d-b80a-4202-b1f3-ff1cb7c57b08.png` | 与闭眼画面匹配的睁眼特写 |
| `hands.png` | `exec-2674c7f4-372e-405e-837f-7703ba49c83f.png` | 人类与角色共同创造的指尖接触 |

角色沿用用户参考的上游设计：原作上善、女仆再设计 ZipZipPipe。上游完整说明：

- https://github.com/Small-tailqwq/dsh-deep-whale/blob/main/maid-atelier/NOTICE
- https://github.com/Small-tailqwq/dsh-deep-whale/blob/main/maid-atelier/LICENSE-ARTWORK
- https://www.pixiv.net/users/62155430
- https://www.pixiv.net/users/18604994

相关角色美术及其改编保留完整署名链，并遵循上游 CC BY-NC-SA 4.0 的非商业与相同方式共享要求。该说明不为歌曲另行授予权利。

## 技术与视觉研究

- DeepSeek Harness 官方：https://github.com/deepseek-ai/deepseek-harness （master README、用户使用指南）。仅研究交互概念，没有运行真实代理或调用任何 DeepSeek 服务。
- 用户给出的参考片：https://www.bilibili.com/video/BV1xCai6aE9g/ 。当前环境请求该页面收到代理 403，不能把此请求记录写成已观看成片。
- 用户给出的代码：https://github.com/MisakaZentai/world-execute-me-dsh-pv ，研究时 HEAD 为 `a598092a1b1db91fa43961a81269353d13419f6f`。本地只读参考保留于 `references/world-execute-me-dsh-pv/`；不包含在本工程交付源码压缩包中，以免混淆原创与参考。
- 重点阅读：`docs/HOW_IT_WORKS.md`、`docs/ASSET_SOURCES.md`、`continuity_full_v2/cuts.py`、`kit.py`、`words.py`。查看了 `docs/preview.jpg`。
- 本片代码自行实现，没有采用参考仓库的舞蹈、MMD、音乐、窗口截图或角色图像资源。

## 计算模型

- Meta / torchaudio `HDEMUCS_HIGH_MUSDB_PLUS`：仅人声分离用于时间分析，官方 PyTorch 下载源。
- Meta / torchaudio `WAV2VEC2_ASR_BASE_960H`：仅歌词音素对齐，官方 PyTorch 下载源。
- 曾尝试访问 Hugging Face 的 Whisper 模型但被网络策略拦截；没有使用未经获取或未经验证的模型，也没有关闭 TLS 或模型校验。后续改用上述已允许的官方源，因而无需保留额外 Hugging Face 网络要求。

## 字体

Noto Sans CJK、Noto Serif CJK、DejaVu Sans Mono，使用机器已有字体；工程打包不分发字体。安装依赖见 README。
