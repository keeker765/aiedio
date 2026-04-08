# Core Engine Pipeline Framework Design Report

## 1. 项目现状分析

### 当前 core_engine 结构
```
core_engine/
├── src/
│   ├── asset_builder.py    ← AI_Engine.generate() (ZhipuAI GLM-4-Flash)
│   └── story_prompt.py     ← GitHub趋势 → AI分镜脚本生成
├── output/                 ← 生成的 storyboards.json / .md
├── tests/
└── requirements.txt        ← moviepy, langchain, openai, requests, zhipuai
```

### 已完成
- ✅ GitHub趋势抓取 → LLM分镜脚本生成 (story_prompt.py)
- ✅ ZhipuAI GLM-4-Flash 文本生成接口 (asset_builder.py)
- ✅ JSON/Markdown 分镜输出格式

### 缺失环节 (Pipeline Gap)
- ❌ 图像/视觉素材生成 (Image Generation)
- ❌ 语音/旁白合成 (TTS - Text-to-Speech)
- ❌ 背景音乐生成/匹配 (Music/Audio)
- ❌ 视频合成与剪辑 (Video Composition via MoviePy)
- ❌ 后期处理: 字幕、转场、特效 (Post-production)
- ❌ Pipeline 编排器 (Orchestrator)

---

## 2. 行业调研与参考框架

### 2.1 主流开源 AI 视频生成项目

| 项目 | Stars | 架构特点 | 启发 |
|------|-------|----------|------|
| **OpenMontage** | 216⭐ | Agent-first, 11条pipeline, 49工具, YAML编排 | 阶段化pipeline + 技能系统 |
| **AgentCut** | 32⭐ | 6个专业Agent协作 (导演/编剧/摄影/剪辑/音效/审核) | Multi-Agent分工模式 |
| **AI-Story-To-Movie** | — | 剧本→分镜→配音→剪辑的线性pipeline | 端到端自动化流程 |
| **StoryCraft** | 3⭐ | 意图理解→故事线构建→叙事编排→视频生成 | 叙事驱动的生成逻辑 |
| **ComfyUI Workflows** | 407⭐ | 节点式工作流, 支持Wan2.6/LTX/Hunyuan等模型 | 可视化节点编排 |

### 2.2 业界最佳实践总结

**通用 Pipeline 模式** (来源: Vibbit, Wideo, Predis.ai 等):
```
趋势发现 → 脚本生成 → 分镜规划 → 素材生成 → 视频合成 → 后期处理 → 导出
```

**关键设计原则**:
1. **阶段解耦**: 每个阶段独立可替换 (Strategy Pattern)
2. **中间状态持久化**: 每阶段输出JSON checkpoint, 支持断点续跑
3. **Provider抽象**: 图像/语音/视频生成器可插拔 (适配不同API)
4. **预算控制**: 每步操作前估算成本
5. **人工审核点**: 关键创意决策处暂停等待确认

---

## 3. 目标 Pipeline 架构设计

### 3.1 总体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AIEDIO CORE ENGINE PIPELINE v2                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ Stage 1  │──▶│ Stage 2  │──▶│ Stage 3  │──▶│ Stage 4  │        │
│  │ SCRIPT   │   │ ASSET    │   │ COMPOSE  │   │ POST     │        │
│  │ 脚本生成  │   │ 素材生成  │   │ 视频合成  │   │ 后期处理  │        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│       │              │              │              │                │
│       ▼              ▼              ▼              ▼                │
│  [storyboard]   [images/     [raw_video]    [final_video]          │
│  [.json]         audio/]                                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              PipelineRunner (编排器)                      │       │
│  │  - 加载配置 → 执行阶段 → 状态管理 → 错误恢复             │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              Providers (可插拔服务层)                      │       │
│  │  ImageProvider │ TTSProvider │ MusicProvider │ LLMProvider│       │
│  └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 四阶段 Pipeline 详细设计

#### Stage 1: ScriptGenerator (脚本与分镜生成)
- **输入**: 热点话题 (来自crawler) 或用户自定义主题
- **处理**: LLM生成结构化分镜脚本
- **输出**: `StoryboardSchema` (JSON)
- **现有基础**: story_prompt.py (需重构为类)
```python
class ScriptGenerator(BaseStage):
    """趋势话题 → 结构化分镜脚本"""
    def execute(self, context: PipelineContext) -> StoryboardSchema
```

**输出 Schema (增强版)**:
```json
{
  "title": "视频标题",
  "description": "简介",
  "target_duration": 60,
  "scenes": [
    {
      "scene_id": 1,
      "duration": 8,
      "visual_prompt": "用于图像生成的详细描述",
      "narration": "旁白文字",
      "text_overlay": "画面文字",
      "style": "cinematic / anime / minimalist",
      "transition": "fade / cut / slide",
      "camera_motion": "zoom_in / pan_left / static"
    }
  ],
  "global_style": {
    "aspect_ratio": "16:9",
    "color_palette": ["#1a1a2e", "#16213e", "#0f3460"],
    "font": "Noto Sans SC",
    "mood": "futuristic"
  }
}
```

#### Stage 2: AssetGenerator (多模态素材生成)
- **输入**: `StoryboardSchema`
- **处理**: 并行生成每个scene的图像、语音、音乐
- **输出**: 素材文件路径映射
```python
class AssetGenerator(BaseStage):
    """分镜脚本 → 图像 + 语音 + 音乐素材"""
    
    image_provider: ImageProvider      # ZhipuAI CogView / DALL-E / FLUX
    tts_provider: TTSProvider          # ZhipuAI TTS / Edge-TTS (免费)
    music_provider: MusicProvider      # Suno / 本地音乐库
    
    def execute(self, context: PipelineContext) -> AssetManifest
```

**Provider 接口设计**:
```python
class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, style: str, 
                 size: tuple = (1920, 1080)) -> Path

class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, voice: str = "default",
                   lang: str = "zh") -> Path

class MusicProvider(ABC):
    @abstractmethod
    def generate(self, mood: str, duration: float) -> Path
```

**推荐 Provider 实现** (成本优先):

| 能力 | 免费方案 | 付费方案 |
|------|---------|---------|
| 图像生成 | ZhipuAI CogView (已有key) | DALL-E 3 / FLUX |
| 语音合成 | Edge-TTS (完全免费) | ZhipuAI TTS / ElevenLabs |
| 背景音乐 | 本地免版权音乐库 | Suno API |

#### Stage 3: VideoComposer (视频合成)
- **输入**: `StoryboardSchema` + `AssetManifest`
- **处理**: 使用MoviePy将素材按分镜组合成视频
- **输出**: 原始视频文件
```python
class VideoComposer(BaseStage):
    """素材 + 分镜 → 视频剪辑"""
    
    def execute(self, context: PipelineContext) -> Path:
        # 1. 为每个scene创建图像clip (带Ken Burns效果)
        # 2. 叠加旁白音频 (对齐时间轴)
        # 3. 添加转场效果 (fade/dissolve)
        # 4. 混入背景音乐 (自动调节音量)
        # 5. 拼接所有scene → 导出视频
```

**MoviePy 合成策略**:
```python
# 伪代码 - 核心合成逻辑
for scene in storyboard.scenes:
    img_clip = ImageClip(scene.image_path).set_duration(scene.duration)
    img_clip = apply_camera_motion(img_clip, scene.camera_motion)  # Ken Burns
    
    narration = AudioFileClip(scene.audio_path)
    img_clip = img_clip.set_audio(narration)
    
    clips.append(img_clip)

video = concatenate_videoclips(clips, method="compose")
video = video.set_audio(CompositeAudioClip([video.audio, bgm]))
video.write_videofile(output_path, fps=24, codec="libx264")
```

#### Stage 4: PostProcessor (后期处理)
- **输入**: 原始视频文件
- **处理**: 字幕烧录、色彩校正、水印
- **输出**: 最终成品视频
```python
class PostProcessor(BaseStage):
    """原始视频 → 成品视频 (字幕/特效/水印)"""
    
    def execute(self, context: PipelineContext) -> Path:
        # 1. 生成SRT字幕文件 (从narration文本)
        # 2. 烧录字幕到视频
        # 3. 添加片头/片尾
        # 4. 添加水印/Logo
        # 5. 多格式导出 (16:9 横屏, 9:16 竖屏)
```

### 3.3 Pipeline 编排器

```python
class PipelineRunner:
    """Pipeline 编排与执行引擎"""
    
    stages: list[BaseStage]
    context: PipelineContext  # 跨阶段共享状态
    
    def run(self, input_data: dict) -> PipelineResult:
        """顺序执行所有阶段, 支持断点续跑"""
        for stage in self.stages:
            checkpoint = self.load_checkpoint(stage.name)
            if checkpoint:
                self.context.restore(checkpoint)
                continue
            
            result = stage.execute(self.context)
            self.save_checkpoint(stage.name, result)
        
        return self.context.final_result

class PipelineContext:
    """跨阶段共享的上下文对象"""
    project_dir: Path           # 项目输出目录
    storyboard: StoryboardSchema
    assets: AssetManifest       # 素材文件路径
    video_path: Path            # 合成后视频路径
    final_path: Path            # 最终成品路径
    metadata: dict              # 运行时元数据
```

### 3.4 目录结构规划

```
core_engine/
├── src/
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── runner.py           # PipelineRunner 编排器
│   │   ├── context.py          # PipelineContext 上下文
│   │   └── base.py             # BaseStage 抽象基类
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── script_generator.py # Stage 1: 脚本生成 (重构自 story_prompt.py)
│   │   ├── asset_generator.py  # Stage 2: 素材生成
│   │   ├── video_composer.py   # Stage 3: 视频合成 (MoviePy)
│   │   └── post_processor.py   # Stage 4: 后期处理
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py             # Provider 抽象接口
│   │   ├── image/
│   │   │   ├── zhipu_cogview.py    # ZhipuAI CogView 图像生成
│   │   │   └── placeholder.py      # 占位符 (无API时降级)
│   │   ├── tts/
│   │   │   ├── edge_tts.py         # Edge-TTS (免费)
│   │   │   └── zhipu_tts.py        # ZhipuAI TTS
│   │   └── music/
│   │       └── local_library.py    # 本地免版权音乐
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py           # Pydantic 数据模型
│   ├── asset_builder.py        # (保留) AI_Engine 兼容层
│   └── story_prompt.py         # (保留) CLI 入口, 内部委托给 stages
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_script_generator.py
│   └── test_video_composer.py
├── output/                     # 生成产物
│   ├── storyboards/
│   ├── assets/
│   └── videos/
├── resources/                  # 静态资源
│   ├── music/                  # 免版权背景音乐
│   ├── fonts/                  # 字幕字体
│   └── templates/              # 片头/片尾模板
└── requirements.txt            # 更新依赖
```

---

## 4. 数据流 (完整 Pipeline)

```
[用户输入/热点话题]
        │
        ▼
┌─ Stage 1: ScriptGenerator ──────────────────────────┐
│  热点话题 → LLM (OpenRouter/ZhipuAI)                │
│  → StoryboardSchema (scenes[], global_style)        │
│  → 保存 output/storyboards/project_xxx.json         │
└─────────────────────────────────────────────────────┘
        │ StoryboardSchema
        ▼
┌─ Stage 2: AssetGenerator ───────────────────────────┐
│  For each scene (可并行):                            │
│    visual_prompt → ImageProvider → scene_01.png     │
│    narration     → TTSProvider  → scene_01.mp3     │
│  Global:                                            │
│    mood → MusicProvider → bgm.mp3                   │
│  → AssetManifest (文件路径映射)                       │
│  → 保存 output/assets/project_xxx/                   │
└─────────────────────────────────────────────────────┘
        │ AssetManifest
        ▼
┌─ Stage 3: VideoComposer ────────────────────────────┐
│  For each scene:                                    │
│    image + audio → ImageClip + AudioClip            │
│    + Ken Burns / zoom / pan 动效                    │
│    + transition (fade/dissolve)                     │
│  Concat all scenes + BGM mixing                    │
│  → raw_video.mp4                                   │
│  → 保存 output/videos/project_xxx_raw.mp4           │
└─────────────────────────────────────────────────────┘
        │ raw video
        ▼
┌─ Stage 4: PostProcessor ────────────────────────────┐
│  + 字幕烧录 (SRT → hardcode)                        │
│  + 片头/片尾                                        │
│  + 水印/Logo                                       │
│  + 多格式导出 (横屏16:9 / 竖屏9:16)                 │
│  → final_video.mp4                                 │
│  → 保存 output/videos/project_xxx_final.mp4         │
└─────────────────────────────────────────────────────┘
```

---

## 5. 技术选型建议

### 5.1 新增依赖

| 包 | 用途 | 成本 |
|----|------|------|
| `edge-tts` | 微软免费TTS (多语言/多角色) | 免费 |
| `pydantic>=2.0` | 数据模型验证 | 免费 |
| `Pillow` | 图像处理/文字叠加 | 免费 |
| `aiohttp` | 异步HTTP (并行素材生成) | 免费 |

### 5.2 现有依赖保留
- `moviepy` → 视频合成核心
- `zhipuai` → LLM + CogView图像生成 (同一个API Key!)
- `langchain` → 未来Agent编排
- `requests` → 同步API调用

### 5.3 AI模型策略

| 阶段 | 模型 | 备注 |
|------|------|------|
| 脚本生成 | OpenRouter (免费) / ZhipuAI GLM-4 | 保持现有方案 |
| 图像生成 | ZhipuAI CogView-3 | **已有ZHIPU_API_KEY, 零额外成本** |
| 语音合成 | Edge-TTS | **完全免费, 无需API Key** |
| 背景音乐 | 本地免版权库 | 后续可接入Suno |

---

## 6. 实施路线图

### Phase 1: 基础框架搭建
- 定义 BaseStage / PipelineContext / PipelineRunner
- 定义 Pydantic schemas (StoryboardSchema, AssetManifest)
- 重构 story_prompt.py → ScriptGenerator stage

### Phase 2: 素材生成层
- 实现 ImageProvider (ZhipuAI CogView + Placeholder)
- 实现 TTSProvider (Edge-TTS)
- 实现 AssetGenerator stage

### Phase 3: 视频合成
- 实现 VideoComposer (MoviePy)
- Ken Burns 效果 / 转场 / 音频混合
- 实现 PostProcessor (字幕烧录)

### Phase 4: 集成与优化
- PipelineRunner 断点续跑
- 与 backend API 集成
- 测试用例

---

## 7. 与同类项目的差异化

| 特性 | Aiedio (目标) | OpenMontage | AgentCut |
|------|-------------|-------------|----------|
| 定位 | 热点驱动的自动视频 | 通用视频制作 | Multi-Agent视频 |
| 输入源 | 爬虫热点自动触发 | 用户Prompt | 用户Prompt |
| 技术路线 | Python Pipeline | Agent+YAML | Multi-Agent |
| 成本 | 极低 (免费API优先) | 中等 ($0.15-$3) | 高 |
| 复杂度 | 中等 (4阶段) | 高 (11 pipelines) | 高 (6 agents) |
| 差异化 | **趋势驱动 + 零成本优先** | 功能全面 | 协作质量高 |

---

## 8. Wan 2.6 模型深度分析 — 适配 Aiedio Pipeline

### 8.1 模型概述

**Wan 2.6** 是阿里巴巴通义万相团队推出的 AI 视频生成模型系列，支持从文本、图像、参考视频生成高质量视频。开源 (Apache 2.0)，拥有 15,000+ GitHub Stars。

### 8.2 三种生成模式

| 模式 | 缩写 | 说明 | 适合 Aiedio 场景 |
|------|------|------|-----------------|
| **Text-to-Video** | T2V | 纯文本描述 → 视频 | ✅ **主模式** — 分镜脚本直接生成 |
| **Image-to-Video** | I2V | 静态图片 + 文本 → 视频 | ✅ **增强模式** — 先用CogView生成图像, 再I2V动态化 |
| **Reference-to-Video** | R2V | 参考视频 + 文本 → 新视频 | ⚠️ 可选 — 角色一致性场景 |

### 8.3 输入能力详细分析

#### 📥 Text-to-Video (T2V) 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 视频描述 (最大800字符) |
| `duration` | string | ❌ | `"5"` / `"10"` / `"15"` 秒 |
| `resolution` | string | ❌ | `"720p"` / `"1080p"` (不支持480p) |
| `aspect_ratio` | string | ❌ | `"16:9"` / `"9:16"` / `"1:1"` / `"4:3"` / `"3:4"` |
| `audio_url` | string | ❌ | 背景音频URL (WAV/MP3, 3-30秒, ≤15MB) |
| `enable_prompt_expansion` | bool | ❌ | 用LLM自动丰富简短prompt |
| `seed` | int | ❌ | 随机种子 (可复现结果) |
| `enable_safety_checker` | bool | ❌ | 安全检查 (默认true) |

**🔑 关键特性 — Multi-Shot (多镜头)**:
- T2V **默认开启** multi-shot
- 使用时间标记语法实现多镜头分割:
```
Overall scene description.
Shot 1 [0-3s] First scene details, camera movement, lighting.
Shot 2 [3-6s] Second scene details, transition elements.
Shot 3 [6-10s] Final scene details, resolution.
```
- 模型自动理解镜头切割, 维持角色/场景一致性

#### 📥 Image-to-Video (I2V) 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 运动/动作描述 (最大800字符) |
| `image_url` | string | ✅ | 首帧图片URL |
| `duration` | string | ❌ | `"5"` / `"10"` / `"15"` 秒 |
| `resolution` | string | ❌ | `"480p"` / `"720p"` / `"1080p"` |
| `audio_url` | string | ❌ | 背景音频URL |
| `multi_shot` | bool | ❌ | 默认 `false` |

**图片要求**: JPEG/PNG/BMP/WEBP, 360-2000px, ≤25MB

#### 📥 Reference-to-Video (R2V) 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 描述 + @Video1/@Video2/@Video3 标记 |
| `video_urls` | list[str] | ✅ | 1-3个参考视频URL |
| `duration` | string | ❌ | `"5"` / `"10"` (不支持15秒) |
| `resolution` | string | ❌ | `"720p"` / `"1080p"` |

### 8.4 输出能力详细分析

#### 📤 视频输出

| 属性 | 值 |
|------|-----|
| **格式** | MP4 |
| **分辨率** | 最高 1080p (1920×1080) |
| **帧率** | 24fps |
| **时长** | 5 / 10 / 15 秒 |
| **宽高比** | 16:9, 9:16, 1:1, 4:3, 3:4 |

#### 📤 音频输出

| 属性 | 说明 |
|------|------|
| **内置音频** | ✅ 支持 — 模型可生成与视频同步的原生音频 |
| **口型同步** | ✅ 支持 — 角色对话时嘴唇动作与语音对齐 |
| **背景音频** | ✅ 支持输入音频混合 — 如果输入了 `audio_url`, 会与视频同步 |
| **音频超出时长** | 自动截断 |
| **音频短于时长** | 剩余部分静音 |

#### 📤 字幕输出

| 属性 | 说明 |
|------|------|
| **内置字幕** | ❌ **不支持** — Wan 2.6 不生成字幕/SRT文件 |
| **处理方案** | 需要在 PostProcessor 阶段自行烧录字幕 (FFmpeg / MoviePy) |

#### 📤 其他输出

| 属性 | 说明 |
|------|------|
| `video.url` | 生成视频的下载URL |
| `actual_prompt` | 如果开启了 prompt expansion, 返回扩展后的prompt |
| `seed` | 实际使用的随机种子 (用于复现) |

### 8.5 ⚠️ 重要限制

| 限制 | 说明 |
|------|------|
| 最大时长 | 单次生成最多 **15秒** (需拼接多段才能做长视频) |
| 无字幕输出 | 字幕需要外部处理 |
| 无独立音轨输出 | 音频嵌入视频中, 无法单独获取 |
| 生成时间 | 2-8分钟/次 (取决于分辨率和时长) |
| 文本渲染 | 视频中的文字/UI/标签可能模糊失真 |
| 物理模拟 | 液体/布料等复杂物理效果不稳定 |
| 品牌素材 | 无法直接使用品牌Logo/产品图 (需用I2V或R2V) |

### 8.6 API 平台对比 (Wan 2.6 调用方式)

| 平台 | Python SDK | 特点 | 定价 |
|------|-----------|------|------|
| **fal.ai** | `fal-client` | 亚秒冷启动, 自动扩展 | 按使用量计费 |
| **Replicate** | `replicate` | 简单易用, 社区活跃 | 按GPU秒计费 |
| **AIML API** | `requests` | REST API, 简单集成 | 按调用计费 |
| **本地部署** | `diffusers` | 免费但需GPU (≥24GB VRAM) | 免费 (需硬件) |

### 8.7 适配 Aiedio Pipeline 方案

```
┌─────────────────────────────────────────────────────────────────────┐
│             AIEDIO PIPELINE — 适配 Wan 2.6 的两条路径                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  路径A: T2V 直出 (简单快速)                                         │
│  ┌──────────┐   ┌──────────────────┐   ┌──────────┐               │
│  │ Stage 1  │──▶│ Stage 2: Wan T2V │──▶│ Stage 3  │               │
│  │ 脚本生成  │   │ prompt→视频(含音) │   │ 后期处理  │               │
│  └──────────┘   └──────────────────┘   └──────────┘               │
│  分镜prompt → Wan 2.6 T2V → 带音频的MP4 → 加字幕/拼接              │
│                                                                     │
│  路径B: I2V 增强 (质量优先)                                         │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────┐   ┌─────────┐ │
│  │ Stage 1  │──▶│ Stage 2  │──▶│ Stage 3: Wan I2V│──▶│ Stage 4 │ │
│  │ 脚本生成  │   │ 图片+TTS │   │ 图片→动态视频    │   │ 后期处理 │ │
│  └──────────┘   └──────────┘   └─────────────────┘   └─────────┘ │
│  分镜 → CogView图片+EdgeTTS → Wan I2V动态化 → 加字幕/拼接/配音     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**路径A (推荐起步)**: 直接把 StoryboardSchema 中每个 scene 的 `visual_prompt` 送入 Wan T2V，得到带原生音频的视频片段。然后在后期阶段拼接、加字幕。

**路径B (质量提升)**: 先用 CogView 生成精确控制的首帧图像，再用 Wan I2V 将静态图动态化。TTS 旁白作为 `audio_url` 传入，实现音画同步。

### 8.8 Wan 2.6 Provider 接口设计

```python
class WanVideoProvider(ABC):
    """Wan 2.6 视频生成 Provider 抽象"""
    
    @abstractmethod
    def text_to_video(
        self,
        prompt: str,
        duration: Literal["5", "10", "15"] = "10",
        resolution: Literal["720p", "1080p"] = "1080p",
        aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9",
        audio_url: str | None = None,
        seed: int | None = None,
    ) -> Path:
        """T2V: 文本 → 视频"""
        ...
    
    @abstractmethod
    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["480p", "720p", "1080p"] = "1080p",
        audio_url: str | None = None,
    ) -> Path:
        """I2V: 图片 + 文本 → 视频"""
        ...

class FalWanProvider(WanVideoProvider):
    """fal.ai 平台的 Wan 2.6 实现"""
    ...

class ReplicateWanProvider(WanVideoProvider):
    """Replicate 平台的 Wan 2.6 实现"""
    ...

class PlaceholderWanProvider(WanVideoProvider):
    """无API Key时的占位实现 (返回测试视频)"""
    ...
```

### 8.9 StoryboardSchema 更新 (适配 Wan 2.6)

```json
{
  "title": "GitHub热点: AI代码助手崛起",
  "target_duration": 45,
  "wan_config": {
    "resolution": "1080p",
    "aspect_ratio": "16:9",
    "mode": "t2v"
  },
  "scenes": [
    {
      "scene_id": 1,
      "duration": 15,
      "wan_prompt": "A futuristic control room with holographic code displays. Shot 1 [0-5s] Camera slowly zooms into glowing screen showing GitHub trending page. Shot 2 [5-10s] A developer's hands type rapidly, code flowing across multiple monitors. Shot 3 [10-15s] Wide shot reveals entire AI-powered development team.",
      "narration": "在GitHub上，一场AI编程革命正在悄然发生...",
      "style": "cinematic sci-fi",
      "audio_mode": "tts_overlay"
    },
    {
      "scene_id": 2,
      "duration": 15,
      "wan_prompt": "Split screen montage of coding productivity. Shot 1 [0-5s] Side by side: manual coding vs AI-assisted coding speed comparison. Shot 2 [5-10s] Charts and graphs showing exponential growth in AI coding tools adoption. Shot 3 [10-15s] Diverse team of developers celebrating a successful deployment.",
      "narration": "AI辅助编程工具的使用量在过去一年中增长了300%...",
      "style": "modern tech documentary",
      "audio_mode": "tts_overlay"
    },
    {
      "scene_id": 3,
      "duration": 15,
      "wan_prompt": "Inspiring finale sequence. Shot 1 [0-5s] Close-up of a student learning to code with an AI tutor on screen. Shot 2 [5-10s] Montage of diverse faces around the world, all coding together. Shot 3 [10-15s] Final shot: a glowing future cityscape symbolizing AI-augmented humanity.",
      "narration": "未来的编程，将是人与AI的协奏曲...",
      "style": "inspirational cinematic",
      "audio_mode": "tts_overlay"
    }
  ]
}
```

### 8.10 总结: Wan 2.6 能力矩阵

```
                    输入支持                    输出支持
            ┌──────────────────┐      ┌──────────────────────┐
  文本 ──── │ ✅ prompt (必填)  │      │ ✅ 视频 MP4          │
            │    最大800字符    │      │    1080p / 24fps     │
            │                  │      │    5-15秒            │
  图片 ──── │ ✅ I2V模式首帧    │      │ ✅ 内嵌音频          │
            │    360-2000px    │      │    原生口型同步       │
            │    ≤25MB         │      │                      │
  音频 ──── │ ✅ 背景音频       │      │ ❌ 无独立音轨输出    │
            │    WAV/MP3       │      │ ❌ 无字幕/SRT输出    │
            │    3-30秒, ≤15MB │      │ ❌ 无独立图片帧输出  │
            │                  │      │                      │
  视频 ──── │ ✅ R2V参考视频    │      │ ✅ 返回 seed         │
            │    1-3个参考      │      │ ✅ 返回扩展后prompt  │
            └──────────────────┘      └──────────────────────┘
```
