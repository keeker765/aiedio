<<<<<<< HEAD

from fastapi import FastAPI

=======
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
>>>>>>> 47cfbe14154ccb8403958389d3e2888ee9b32411
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

# Demo video files from previously generated Kling V3 Backrooms content
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEMO_VIDEOS = {
    "scene_clips": [
        os.path.join(_PROJECT_ROOT, "core_engine", "output", "videos", "backrooms_kling", "kling_v3_video_1775474758.mp4"),
        os.path.join(_PROJECT_ROOT, "core_engine", "output", "videos", "backrooms_kling", "kling_v3_video_1775474988.mp4"),
    ],
    "final": os.path.join(_PROJECT_ROOT, "core_engine", "output", "videos", "backrooms_kling", "backrooms_act1_act2_preview.mp4"),
}

async def run_video_pipeline_async(task_id: str, storyboard: dict):
    """异步 Pipeline 运行并更新状态（事件格式与前端 WebSocket 对齐）

    当前使用 demo 模式：播放已生成的后室 Kling V3 视频。
    """
    demo_clips = [p for p in _DEMO_VIDEOS["scene_clips"] if os.path.exists(p)]
    total_scenes = len(demo_clips) if demo_clips else len(storyboard.get("scenes", [])) or 1

    video_tasks[task_id] = {
        "status": "processing",
        "events": [],
        "progress": 0,
        "scene": 0,
        "total": total_scenes,
    }

    for i in range(1, total_scenes + 1):
        video_tasks[task_id]["events"].append(
            {"event": "scene_start", "scene": i, "total": total_scenes}
        )
        video_tasks[task_id]["scene"] = i

        await asyncio.sleep(3)

        preview_url = f"/api/video/clip/{task_id}/{i}" if i <= len(demo_clips) else ""
        video_tasks[task_id]["progress"] = int((i / total_scenes) * 100)
        video_tasks[task_id]["events"].append(
            {"event": "scene_done", "scene": i, "total": total_scenes, "preview_url": preview_url}
        )
        print(f"Task {task_id}: Scene {i}/{total_scenes} done")

    # Store demo video path for download
    final_path = _DEMO_VIDEOS["final"]
    video_tasks[task_id]["final_path"] = final_path if os.path.exists(final_path) else None
    video_tasks[task_id]["demo_clips"] = demo_clips
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

# --- B5: 视频下载 & 片段预览 ---
@app.get("/api/video/clip/{task_id}/{scene_idx}")
def serve_clip(task_id: str, scene_idx: int):
    """返回单幕视频片段预览"""
    task = video_tasks.get(task_id)
    if task and "demo_clips" in task:
        clips = task["demo_clips"]
        idx = scene_idx - 1
        if 0 <= idx < len(clips) and os.path.exists(clips[idx]):
            return FileResponse(clips[idx], media_type="video/mp4")
    return {"message": "Clip not available"}

@app.get("/api/video/download/{task_id}")
def download_video(task_id: str):
    """下载最终合成视频"""
    task = video_tasks.get(task_id)
    if task and task.get("final_path") and os.path.exists(task["final_path"]):
        return FileResponse(task["final_path"], media_type="video/mp4", filename=f"aiedio_{task_id[:8]}.mp4")
    return {"message": "Video not ready yet"}

# --- 基础页面路由 ---
@app.get("/showcase")
def serve_showcase():
    """MVP 项目进展展示页面"""
    showcase = os.path.join(_CLIENT_DIR, "showcase.html")
    if os.path.exists(showcase):
        return FileResponse(showcase)
    return {"message": "Showcase page not found"}

@app.get("/api/showcase/videos")
def list_showcase_videos():
    """列出所有已生成的视频、图片和分镜数据供展示页使用"""
    output_dir = os.path.join(_PROJECT_ROOT, "core_engine", "output")
    result = {"projects": []}

    projects_meta = [
        {
            "id": "backrooms_kling",
            "title": "🏚️ Backrooms Horror — Kling V3",
            "desc": "Horror short film generated with Kling V3 model. Pipeline: AI first-frame → I2V animation.",
            "model": "Kling V3",
            "video_dir": "videos/backrooms_kling",
            "asset_dir": "assets",
            "storyboard": "storyboards/storyboard_1775561440.json",
            "final": "backrooms_act1_act2_preview.mp4",
            "clips": ["kling_v3_video_1775474758.mp4", "kling_v3_video_1775474988.mp4"],
            "images": ["kling_v3_1775466427.png"],
        },
        {
            "id": "backrooms_continuity",
            "title": "🔗 Backrooms Continuity — wan2.7 I2V",
            "desc": "4-scene continuity experiment: last frame of scene N → first frame of scene N+1, ensuring visual coherence.",
            "model": "wan2.7 (DashScope I2V)",
            "video_dir": "videos/backrooms_continuity",
            "asset_dir": "assets/backrooms_continuity",
            "storyboard": "storyboards/storyboard_1775561440.json",
            "final": "backrooms_continuity_final.mp4",
            "clips": ["dashscope_i2v_1775467158.mp4", "dashscope_i2v_1775469275.mp4", "dashscope_i2v_1775470681.mp4", "scene2_recovered.mp4"],
            "images": ["kling_v3_1775466556.png", "kling_v3_1775467196.png", "kling_v3_1775468703.png", "kling_v3_1775469350.png"],
        },
        {
            "id": "backrooms_v2",
            "title": "🎬 Backrooms V2 Final — Mixed Composition",
            "desc": "4 scenes + BGM mixing + post-production. MoviePy multi-track concatenation.",
            "model": "wan2.7 + MoviePy",
            "video_dir": "videos/backrooms_final_v2",
            "asset_dir": None,
            "storyboard": "storyboards/storyboard_1775561440.json",
            "final": "backrooms_v2_final.mp4",
            "clips": ["mixed_scene1.mp4", "mixed_scene2.mp4", "mixed_scene3.mp4", "mixed_scene4.mp4"],
            "images": [],
        },
        {
            "id": "backrooms_v3",
            "title": "✨ Backrooms V3 — Final Delivery",
            "desc": "Final delivery version. Fully automated end-to-end pipeline generation.",
            "model": "Pipeline V3",
            "video_dir": "videos/backrooms_v3",
            "asset_dir": None,
            "storyboard": "storyboards/storyboard_1775561440.json",
            "final": "backrooms_v3_final.mp4",
            "clips": [],
            "images": [],
        },
    ]

    for pm in projects_meta:
        proj = {"id": pm["id"], "title": pm["title"], "desc": pm["desc"], "model": pm["model"]}

        # Final video
        fpath = os.path.join(output_dir, pm["video_dir"], pm["final"])
        if os.path.exists(fpath):
            proj["final_video"] = f"/api/showcase/file/{pm['video_dir']}/{pm['final']}"
            proj["final_size_mb"] = round(os.path.getsize(fpath) / 1024 / 1024, 1)
        else:
            proj["final_video"] = None

        # Clips
        proj["clips"] = []
        for c in pm.get("clips", []):
            cp = os.path.join(output_dir, pm["video_dir"], c)
            if os.path.exists(cp):
                proj["clips"].append({
                    "name": c,
                    "url": f"/api/showcase/file/{pm['video_dir']}/{c}",
                    "size_mb": round(os.path.getsize(cp) / 1024 / 1024, 1),
                })

        # Images
        proj["images"] = []
        if pm.get("asset_dir"):
            for img in pm.get("images", []):
                ip = os.path.join(output_dir, pm["asset_dir"], img)
                if os.path.exists(ip):
                    proj["images"].append({
                        "name": img,
                        "url": f"/api/showcase/file/{pm['asset_dir']}/{img}",
                    })

        # Storyboard
        sp = os.path.join(output_dir, pm.get("storyboard", ""))
        if os.path.exists(sp):
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    proj["storyboard"] = json.load(f)
            except Exception:
                proj["storyboard"] = None
        else:
            proj["storyboard"] = None

        result["projects"].append(proj)

    return result

@app.get("/api/showcase/file/{path:path}")
def serve_showcase_file(path: str):
    """服务 core_engine/output/ 下的静态文件"""
    full = os.path.join(_PROJECT_ROOT, "core_engine", "output", path)
    if not os.path.exists(full):
        return {"error": "not found"}
    ext = os.path.splitext(full)[1].lower()
    mime = {"mp4": "video/mp4", "png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "application/octet-stream")
    return FileResponse(full, media_type=mime)

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