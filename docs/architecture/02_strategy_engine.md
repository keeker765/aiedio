# AI Video Generation Pipeline - Strategy Engine

## 1. 核心设计：素材组装策略引擎 (Asset Strategy Engine)
为打破“只能用 AI 生成图片作为参考”的局限，系统抽象出了一层策略工厂（Strategy Pattern）。

### 策略 1：纯原创/风格一致性策略 (Original & Consistent Strategy)
- **适用场景**：虚构故事、科幻短片、绘本动画等从零开始的内容。
- **输入组合**：【Midjourney 关键帧图片】 + 动效提示词 + 台词文本
- **优势**：保证人物长相和整体画风绝对一致。

### 策略 2：热点二创/缝合策略 (Trend Remix Strategy)
- **适用场景**：社会热点解读、新闻二次创作、搞笑鬼畜。
- **输入组合**：【爬虫热搜原视频/截图】 + 二创剧本台词 + 风格化重绘指令
- **优势**：利用 Video-to-Video 能力，进行动作延续或快速风格转换（如赛博朋克风）。

### 策略 3：时间轴顺延长镜头策略 (Timeline Extension Strategy)
- **适用场景**：需要突破单次 15 秒限制，生成极度连贯的长镜头动作。
- **输入组合**：【上一段刚才生成的视频最后一帧/最后3秒】 + 下一步动作 + 延续台词
- **优势**：终点贴起点，实现无缝衔接的长镜头。

### 策略 4：全多模态狂暴策略 (Full Multi-modal Strategy)
- **适用场景**：极度复杂的创意缝合或爆款模版生成。
- **输入组合**：@image (主角脸) + @video (爬来的大流量动作骨架) + @audio (神曲BGM) + 文本指令
- **优势**：极致压榨多模态输入的极限能力，一键拼装爆款因子。

## 2. 技术栈选型
- **调度编排**：Python 3.10+
- **LLM 框架**：LangChain / LlamaIndex (执行多步推理与提词组装)
- **爬虫技术**：
equests + BeautifulSoup4 (轻量) / Playwright (强反爬动态池)
- **图像生成**：Midjourney API / Stable Diffusion (SDXL)
- **联合视频生成**：Video Gen API (或相兼容的大模型接口)
- **渲染组合**：MoviePy / ffmpeg-python
