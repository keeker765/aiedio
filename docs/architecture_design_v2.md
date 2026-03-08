# AI Video Generation Pipeline (Auto Content Factory) 架构设计文档 V2.0

## 1. 项目概述

本项目旨在构建一个完全自动化的“AI 内容工厂”（Auto Content Factory）。系统不仅能根据人工输入的提示词生成视频，还能通过网络爬虫自动捕捉社交平台热点，结合大语言模型（LLM）进行创意生成，最终利用多模态大模型（如 Seedance 2.0）完成包含统一画风、原生音效和配音的高质量短视频生成与拼接。

## 2. 核心架构演进：从被动工具到自动引擎

引入了**“热点挖掘模块”**和基于 Seedance 2.0 的**“多模态联合装填策略”**后，整个系统从单向的 `文本 -> 视频` 工具，升级为具备自我驱动能力的闭环生产引擎。

### 核心工作流 (Workflow V2)

1. **模块 0（自动触发与热点创意）**：定时触发爬虫抓取各大平台（微博、Twitter、抖音等）榜单，交由 LLM 筛选并结合特定画风生成视频创意大纲。
2. **模块 1（剧本拆解与分镜）**：LangChain 接管创意，扩写为详细的故事剧本，并拆解为多个独立的分镜（每个分镜控制在 5-15 秒，包含画面描述、动态指令、旁白台词）。
3. **模块 2（视觉定调与素材准备）**：根据分镜需求，调用外部 API（如 Midjourney/SD）生成角色和场景的关键帧图片，或者提取爬虫抓取的源视频/图片素材。
4. **模块 3（多模态联合生成 - 核心层）**：将模块 2 准备的素材（图片/视频）、分镜提示词、台词和音效需求进行“策略化组装”，并发调用 **Seedance 2.0** API，直接产出**自带口型同步配音和音效**的视频片段。
5. **模块 4（自动剪辑与合成）**：使用 MoviePy/FFmpeg 将返回的各分镜视频片段（由于原生带音频，无需二次对齐）直接首尾相连，渲染输出最终的高清视频。

## 3. 核心设计：素材组装策略引擎 (Asset Strategy Engine)

为打破“只能用 AI 生成图片作为参考”的局限，系统在模块 3 之前抽象出了一层**策略工厂（Strategy Pattern）**，用于动态决定当前分镜如何向视频模型喂入参考素材（图片、上次生成的视频、爬虫原视频等）。

### 策略 1：纯原创/风格一致性策略 (Original & Consistent Strategy)
- **适用场景**：虚构故事、科幻短片、绘本动画等从零开始的内容。
- **输入组合**：`【Midjourney 生成的关键帧图片】 + 动作提示词 + 台词文本`
- **优势**：保证长篇叙事中的人物长相和整体画风绝对一致。

### 策略 2：热点二创/缝合策略 (Trend Remix Strategy)
- **适用场景**：社会热点解读、新闻二次创作、搞笑鬼畜。
- **输入组合**：`【爬虫抓取的热搜原视频/新闻截图】 + 二创剧本台词 + 风格化重绘指令`
- **优势**：利用视频模型的 Video-to-Video 能力，对真实热点素材进行快速风格化（如转成赛博朋克风）或动作延续，极具现实相关性和爆款潜质。

### 策略 3：时间轴顺延长镜头策略 (Timeline Extension Strategy)
- **适用场景**：需要突破单次 15 秒限制，生成极度连贯的长镜头动作。
- **输入组合**：`【上一段刚刚生成的视频的最后一帧/最后3秒】 + 下一步动作指令 + 延续台词`
- **优势**：让下一段视频的起点严格贴合上一段的终点，实现无缝衔接的无限长镜头。

### 策略 4：全多模态狂暴策略 (Full Multi-modal Strategy)
- **适用场景**：终极爆款制造、极度复杂的创意缝合。
- **输入组合**：`@image (固定主角脸) + @video (爬虫抓取的搞笑动作作骨架) + @audio (特定BGM) + 文本指令`
- **优势**：充分压榨多模态模型的 12 输入位上限，将他人动作、自设主角和爆款音乐强行融合。

## 4. 技术栈选型总结

- **调度与编排**：Python 3.10+
- **LLM/Agent 框架**：LangChain / LlamaIndex (处理模块 0 和模块 1 的多步推理)
- **爬虫技术**：`requests` + `BeautifulSoup4` (轻量级) / `Playwright` (需要绕过反爬的动态页面)
- **图像生成 API**：Midjourney API (通过第三方) 或 Stable Diffusion API (SDXL)
- **音视频联合生成 API**：**ByteDance Seedance 2.0 API** (或兼容聚合平台如 VO3 AI)
- **视频后期合成**：`MoviePy` / `ffmpeg-python`
- **数据交互格式**：全流程结构化 JSON

## 5. 抽象代码架构示例 (Python)

```python
class AssetStrategy(Enum):
    STORY_MODE = "STORY_MODE"
    REMIX_MODE = "REMIX_MODE"
    CONTINUOUS_MODE = "CONTINUOUS_MODE"

class AssetBuilder:
    def __init__(self, strategy: AssetStrategy):
        self.strategy = strategy

    def build_payload(self, scene_data: dict, previous_video=None, crawled_assets=None):
        payload = {
            "prompt": scene_data["action_text"],
            "audio_prompt": scene_data["voiceover"],
            "references": []
        }

        if self.strategy == AssetStrategy.STORY_MODE:
            payload["references"].append({"type": "image", "url": scene_data["generated_image_url"]})

        elif self.strategy == AssetStrategy.REMIX_MODE:
            payload["references"].append({"type": "video", "url": crawled_assets["hot_topic_video_url"]})
            payload["prompt"] = f"Maintain action but change style. {scene_data['action_text']}"

        elif self.strategy == AssetStrategy.CONTINUOUS_MODE:
            if previous_video:
                payload["references"].append({"type": "video", "url": previous_video, "role": "first_frame"})

        return payload
```

## 6. 后续开发计划
1. 初始化项目标准目录结构。
2. 开发模块 0：编写爬虫脚本并接入 LLM，完成“热点获取 -> 创意输出”的测试。
3. 构建 `AssetBuilder` 策略工厂核心类。
4. 接入相关图像与视频生成 API，跑通首个测试用例。