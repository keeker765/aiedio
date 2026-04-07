# Aiedio — Sprint 任务分配文档

> 基于 MVP_CN.md 范围 + 用户新需求 + 当前代码实现状态整理
> 团队5人，按 CODEOWNERS 边界分配

---

## 产品核心流程（两条路径）

```
路径 A（热点自动）:
  爬虫自动抓取热点榜单
      ↓ hot_trends.json
  前端展示热点列表，用户选择一个 topic
      ↓ 用户确认
  后端触发：爬虫针对 topic 搜索相关知识（知乎/GitHub）
      ↓ topic_knowledge.json
  LLM 融合 topic + knowledge → 故事背景 + 分镜脚本
      ↓ storyboard.json
  前端展示故事背景 + 分镜预览（等用户确认）
      ↓ 用户点击"生成视频"
  Kling V3 Video API × N幕 → MP4
      ↓ 字幕合成
  前端实时展示进度 (WebSocket) → 视频播放

路径 B（自定义话题）:
  用户直接输入话题（如"后室恐怖故事"）
  → 同路径 A 的"爬虫搜索相关知识"开始
```

---

## 关键术语说明

| 术语 | 含义 |
|------|------|
| **分镜 / Storyboard** | **同一个东西**。分镜 = Storyboard = 每个视频场景的描述 JSON |
| **故事背景** | 爬虫搜集的 topic 相关知识（知乎问答、GitHub 项目简介），用于丰富故事 |
| **场景 (Scene)** | Storyboard 中的一个单元，对应一段视频（10s） |
| **Pipeline** | 整条自动化流水线：爬虫 → 分镜 → 视频 → 合成 |

---

## 接口契约（Interface Contract）

> 各团队必须遵守，是跨模块并行开发的基础。

### 爬虫 → 后端

**文件格式** `crawler/src/hot_trends.json`
```json
[
  {"platform": "zhihu|github", "title": "话题标题", "hot_value": "热度值"}
]
```

**新增：话题知识搜索** `crawler/src/topic_knowledge.json`
```json
{
  "topic": "后室恐怖故事",
  "sources": [
    {"platform": "zhihu", "title": "知乎问答标题", "summary": "内容摘要（≤200字）", "url": "https://..."},
    {"platform": "github", "title": "仓库名", "summary": "README 摘要（≤200字）", "url": "https://..."}
  ]
}
```

### 后端 → 前端 REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/trends` | 返回热点列表 |
| POST | `/api/knowledge` | `{topic}` → 触发爬虫 → 返回故事背景知识 |
| POST | `/api/storyboard` | `{topic, knowledge[]}` → 返回分镜 JSON |
| POST | `/api/video/start` | `{storyboard}` → 返回 `task_id` |
| GET | `/api/video/status/{task_id}` | 返回进度 `{status, progress, scene}` |
| GET | `/api/video/download/{task_id}` | 下载最终 MP4 |

### 后端 → 前端 WebSocket

```
ws://localhost:8000/ws/video/{task_id}

推送消息格式:
{"event": "scene_start", "scene": 1, "total": 4}
{"event": "scene_done",  "scene": 1, "total": 4, "preview_url": "..."}
{"event": "complete",    "video_url": "/api/video/download/xxx"}
{"event": "error",       "message": "..."}
```

---

## 任务清单

### 👤 @keeker765 — Core Engine（核心引擎）

> 目录：`core_engine/`

**已完成** ✅：
- 4阶段 Pipeline（ScriptGenerator/AssetGenerator/VideoComposer/PostProcessor）
- Kling V3 视频生成（`kling-v3-video-generation`，multi_shot 支持）
- DashScope wan2.7 T2V/I2V 提供者
- 场景连贯系统（末帧→Kling I2I→首帧）
- 分镜独立测试 CLI

**待完成** 🔲：

#### E1 — 接受知识上下文生成分镜
> **背景**：爬虫搜集的话题相关知识（知乎问答/GitHub）应注入 LLM 的 prompt，使故事背景更丰富

- 修改 `ScriptGenerator.execute()` 增加 `knowledge: list[dict]` 参数
- 修改 `_build_wan_prompt()` 将知识摘要拼入 prompt（格式：`Background knowledge: ...`）
- 增加 `story_background: str` 字段到 `StoryboardSchema`（LLM 输出的故事背景摘要，用于前端展示）

```python
# 新的 StoryboardSchema 字段示例
class StoryboardSchema(BaseModel):
    title: str
    story_background: str = ""  # ← 新增：故事背景描述，前端展示用
    scenes: list[SceneSchema]
```

#### E2 — Pipeline 可被后端调用
> **背景**：后端需要 import core_engine 并调用 pipeline，而不只是 CLI

- 在 `generate_video.py` 中提取 `run_pipeline(topic, knowledge, project_id)` 函数
- 返回 `PipelineResult`（包含 `storyboard`, `final_path`, `error`）
- 后端只需：`from core_engine.src.generate_video import run_pipeline`

---

### 👤 @HuYuxuan — Crawler（爬虫）

> 目录：`crawler/`

**已完成** ✅：
- GitHub 热点爬虫 `github_spider.py`
- 知乎爬虫（基础版）
- `hot_trends.json` 输出格式

**待完成** 🔲：

#### C1 — 完善知乎热搜爬虫
> 当前知乎爬虫返回数据不稳定，需要加强

- 确保 `fetch_zhihu_hot()` 返回稳定的5条热点
- 格式：`[{"platform": "zhihu", "title": "...", "hot_value": "..."}]`

#### C2 — 话题知识搜索 API（核心新功能）
> **这是新需求**：给定用户输入的 topic，在知乎/GitHub 搜索相关内容

新建文件 `crawler/src/topic_search.py`：

```python
def search_topic_knowledge(topic: str, max_results: int = 5) -> dict:
    """
    搜索 topic 相关知识，返回格式：
    {
        "topic": topic,
        "sources": [
            {"platform": "zhihu", "title": "...", "summary": "...", "url": "..."},
            ...
        ]
    }
    """
```

- 知乎：用 `https://www.zhihu.com/search?q={topic}` 搜索，提取前5个问答标题+简介
- GitHub：用 `https://api.github.com/search/repositories?q={topic}` 搜索，提取前3个仓库名+description
- 输出写入 `crawler/src/topic_knowledge.json`

#### C3 — 暴露统一接口
新建/更新 `crawler/src/__init__.py`，暴露：
```python
from .zhihu_spider import fetch_zhihu_hot
from .github_spider import fetch_github_hot
from .topic_search import search_topic_knowledge
```

---

### 👤 @LuYi — Backend（后端）

> 目录：`backend/`

**已完成** ✅：
- FastAPI 基础服务器
- `/ui` 端点提供前端页面

**待完成** 🔲：

#### B1 — 热点 API
```python
@app.get("/api/trends")
def get_trends() -> list[dict]:
    # 调用爬虫，返回 hot_trends.json 内容
    from crawler.src.zhihu_spider import fetch_zhihu_hot
    from crawler.src.github_spider import fetch_github_hot
    ...
```

#### B2 — 话题知识 API
```python
@app.post("/api/knowledge")
def get_knowledge(body: KnowledgeRequest) -> dict:
    # body.topic: str
    from crawler.src.topic_search import search_topic_knowledge
    return search_topic_knowledge(body.topic)
```

#### B3 — 分镜生成 API
```python
@app.post("/api/storyboard")
def generate_storyboard(body: StoryboardRequest) -> dict:
    # body: {topic: str, knowledge: list[dict]}
    from core_engine.src.generate_video import run_pipeline
    # 只跑 ScriptGenerator，不跑视频生成
    ...
```

#### B4 — 视频生成（异步任务）
```python
@app.post("/api/video/start")
def start_video(body: VideoRequest) -> dict:
    # 在后台线程启动 pipeline，返回 task_id
    task_id = str(uuid.uuid4())
    Thread(target=run_pipeline_async, args=(task_id, body.storyboard)).start()
    return {"task_id": task_id}

@app.get("/api/video/status/{task_id}")
def get_status(task_id: str) -> dict: ...

@app.websocket("/ws/video/{task_id}")
async def video_ws(websocket, task_id: str): ...
```

#### B5 — 视频下载
```python
@app.get("/api/video/download/{task_id}")
def download_video(task_id: str) -> FileResponse: ...
```

---

### 👤 @LiuShuaizhen + @LiXinying — Client（前端）

> 目录：`client/`

**已完成** ✅：
- 基础 HTML 页面（`index.html`）

**待完成** 🔲（按复杂度分工）：

> **@LiXinying**（UI/UX，负责样式和静态组件）：

#### F1 — 设计稿 & 组件样式
- 整体页面布局（深色系，参考 Netflix/Kling.ai）
- 热点卡片组件样式
- 故事背景展示组件样式（卡片 + 来源标注）
- 分镜预览组件（4格网格，每格有场景描述）
- 生成进度条样式

> **@LiuShuaizhen**（交互工程师，负责 API 调用和状态管理）：

#### F2 — 话题选择页面
```javascript
// 1. 页面加载时调用 GET /api/trends
// 2. 渲染热点列表供用户点击
// 3. 或提供文本框让用户输入自定义话题
// 4. 用户点击 → 调用 POST /api/knowledge → 显示故事背景
```

#### F3 — 故事背景 + 分镜预览页
```javascript
// 1. 展示爬虫返回的 knowledge.sources（来源卡片）
// 2. 调用 POST /api/storyboard → 显示4个分镜场景描述
// 3. 用户可编辑分镜描述（可选）
// 4. 点击"生成视频"按钮 → 调用 POST /api/video/start
```

#### F4 — 视频生成状态页
```javascript
// 1. 建立 WebSocket 连接 ws://localhost:8000/ws/video/{task_id}
// 2. 实时更新进度（当前幕次 / 总幕次）
// 3. 每幕完成时显示视频预览（preview_url）
// 4. 全部完成时显示最终视频播放器 + 下载按钮
```

---

## 并行开发顺序

```
Week 1（并行）:
  @HuYuxuan:  完成 C1 知乎爬虫 + C2 话题知识搜索 API
  @LuYi:      完成 B1 热点API + B2 知识API 骨架
  @keeker765: 完成 E1 知识上下文注入分镜
  @LiXinying: 完成 F1 设计稿 + 组件样式

Week 2（集成）:
  @LuYi:      完成 B3 分镜API + B4 视频异步API + B5 下载
  @keeker765: 完成 E2 run_pipeline() 可调用函数
  @LiuShuaizhen: 完成 F2 话题选择页 + F3 分镜预览页

Week 3（端到端）:
  全体:       端到端联调（爬虫→后端→核心引擎→前端）
  @LiuShuaizhen: 完成 F4 WebSocket 进度页
  全体:       修 Bug + 优化
```

---

## 依赖关系图

```
C1 知乎热搜 ──┐
C2 话题搜索 ──┼──▶ B1/B2 后端API ──▶ F2 话题选择页
              │         │
              │         ▼
E1 知识注入 ──┼──▶ B3 分镜API ────▶ F3 分镜预览页
              │         │
              │         ▼
E2 run_pipeline ────▶ B4 视频API ──▶ F4 WebSocket进度页
                         │                    │
                         ▼                    ▼
                    B5 下载API ──────▶ 视频播放器
```

---

## 当前可运行的独立测试命令

```bash
# 分镜独立测试（@keeker765 / 任何人都可以运行）
python -m core_engine.src.stages.script_generator --topic "后室恐怖故事" --lang zh

# Kling V3 视频生成（需要 DASHSCOPE_API_KEY）
python -m core_engine.tests.test_backrooms_kling_v3

# 完整 Pipeline（需要 DASHSCOPE_API_KEY + OPENROUTER_API_KEY）
python -m core_engine.src.generate_video --topic "后室恐怖故事" --lang zh

# 后端启动
python -m uvicorn backend.src.main:app --reload
```

---

## 注意事项

1. **所有命令必须从项目根目录运行**（`aiedio/`），不能 `cd` 进子目录
2. **API Key 不能硬编码**，必须用环境变量：
   - `DASHSCOPE_API_KEY` — 视频/图片生成
   - `OPENROUTER_API_KEY` — LLM 分镜生成
3. **跨模块调用约定**：
   - 爬虫结果只写入 `crawler/src/*.json`，不直接导入其他模块
   - 后端通过 `from crawler.src.xxx import ...` 调用爬虫
   - 后端通过 `from core_engine.src.generate_video import run_pipeline` 调用核心引擎
4. **生成的视频文件**（MP4/PNG）不提交到 Git（已加入 `.gitignore`）
