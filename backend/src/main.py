from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import datetime
import os
import uuid
import asyncio
import json

# --- Defensive imports: degrade gracefully if modules not ready ---
try:
    from core_engine.src.generate_video import run_pipeline
except ImportError:
    run_pipeline = None
    print("[WARN] core_engine.run_pipeline not available")

try:
    from crawler.src.zhihu_spider import fetch_zhihu_hot
except ImportError:
    fetch_zhihu_hot = lambda: []
    print("[WARN] crawler.zhihu_spider not available")

try:
    from crawler.src.github_spider import fetch_github_hot
except ImportError:
    fetch_github_hot = lambda: []
    print("[WARN] crawler.github_spider not available")

try:
    from crawler.src.topic_search import search_topic_knowledge
except ImportError:
    search_topic_knowledge = lambda topic, **kw: {"topic": topic, "sources": []}
    print("[WARN] crawler.topic_search not available")

_CLIENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "client")

app = FastAPI(
    title="Aiedio Backend Hub",
    description="Backend hub responsible for connecting crawler, frontend, and AI engine.",
    version="1.1.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件：serve client/ 目录下的 CSS/JS
if os.path.isdir(_CLIENT_DIR):
    app.mount("/static", StaticFiles(directory=_CLIENT_DIR), name="static")

# --- 数据模型 ---
class KnowledgeRequest(BaseModel):
    topic: str

class StoryboardRequest(BaseModel):
    topic: str
    knowledge: list

class VideoRequest(BaseModel):
    storyboard: dict

# 存储异步任务状态的全局字典
video_tasks = {}

# --- B1: 热点 API ---
@app.get("/api/trends")
def get_trends():
    """获取知乎和GitHub热点列表"""
    zhihu = fetch_zhihu_hot()
    github = fetch_github_hot()
    return zhihu + github

# --- B2: 话题知识 API ---
@app.post("/api/knowledge")
def get_knowledge(body: KnowledgeRequest):
    """根据话题搜索背景知识"""
    return search_topic_knowledge(body.topic)

# --- B3: 分镜生成 API ---
@app.post("/api/storyboard")
def generate_storyboard(body: StoryboardRequest):
    """调用 AI 引擎生成分镜脚本 (Storyboard)"""
    if run_pipeline is None:
        return {
            "title": body.topic,
            "description": f"Storyboard for: {body.topic}",
            "scenes": [
                {"scene_id": i + 1, "visual_prompt": f"Scene {i + 1} for {body.topic}", "narration": "", "duration": 10}
                for i in range(4)
            ],
        }
    result = run_pipeline(body.topic, body.knowledge, storyboard_only=True)
    return result.get("storyboard", {})

# --- B4: 视频生成（异步逻辑） ---
async def run_video_pipeline_async(task_id: str, storyboard: dict):
    """异步 Pipeline 运行并更新状态（事件格式与前端 WebSocket 对齐）"""
    total_scenes = len(storyboard.get("scenes", []))
    if total_scenes == 0:
        total_scenes = 1

    video_tasks[task_id] = {
        "status": "processing",
        "events": [],
        "progress": 0,
        "scene": 0,
        "total": total_scenes,
    }

    for i in range(1, total_scenes + 1):
        # 推送 scene_start 事件
        video_tasks[task_id]["events"].append(
            {"event": "scene_start", "scene": i, "total": total_scenes}
        )
        video_tasks[task_id]["scene"] = i

        # TODO: 替换为真实的视频生成调用
        await asyncio.sleep(5)

        video_tasks[task_id]["progress"] = int((i / total_scenes) * 100)
        video_tasks[task_id]["events"].append(
            {"event": "scene_done", "scene": i, "total": total_scenes, "preview_url": ""}
        )
        print(f"Task {task_id}: Scene {i}/{total_scenes} done")

    video_tasks[task_id]["status"] = "complete"
    video_tasks[task_id]["events"].append(
        {"event": "complete", "video_url": f"/api/video/download/{task_id}"}
    )

@app.post("/api/video/start")
async def start_video(body: VideoRequest, background_tasks: BackgroundTasks):
    """启动异步视频生成任务"""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_video_pipeline_async, task_id, body.storyboard)
    return {"task_id": task_id}

@app.get("/api/video/status/{task_id}")
def get_status(task_id: str):
    """查询任务进度"""
    return video_tasks.get(task_id, {"status": "not_found"})

@app.websocket("/ws/video/{task_id}")
async def video_ws(websocket: WebSocket, task_id: str):
    """WebSocket 实时推送进度（事件格式与前端 script.js 对齐）"""
    await websocket.accept()
    last_event_idx = 0
    try:
        while True:
            task = video_tasks.get(task_id)
            if task:
                events = task.get("events", [])
                # 只推送新事件
                while last_event_idx < len(events):
                    await websocket.send_json(events[last_event_idx])
                    last_event_idx += 1
                if task["status"] == "complete" and last_event_idx >= len(events):
                    break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"Client disconnected from task {task_id}")

# --- B5: 视频下载 ---
@app.get("/api/video/download/{task_id}")
def download_video(task_id: str):
    # 这里应返回真实的 MP4 文件路径
    # return FileResponse(path="path/to/video.mp4", filename=f"{task_id}.mp4")
    return {"message": "Download link would be here."}

# --- 基础页面路由 ---
@app.get("/ui")
def serve_frontend():
    """Serve the new product UI (index_new.html)"""
    new_html = os.path.join(_CLIENT_DIR, "index_new.html")
    if os.path.exists(new_html):
        return FileResponse(new_html)
    return FileResponse(os.path.join(_CLIENT_DIR, "index.html"))

@app.get("/style.css")
def serve_css():
    return FileResponse(os.path.join(_CLIENT_DIR, "style.css"), media_type="text/css")

@app.get("/script.js")
def serve_js():
    return FileResponse(os.path.join(_CLIENT_DIR, "script.js"), media_type="application/javascript")

@app.get("/")
def health_check():
    return {"status": "online", "time": datetime.datetime.now()}