from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import datetime
import os
import uuid
import asyncio
import json

# 📍 导入组长定义的模块
from core_engine.src.generate_video import run_pipeline
from crawler.src.zhihu_spider import fetch_zhihu_hot
from crawler.src.github_spider import fetch_github_hot
from crawler.src.topic_search import search_topic_knowledge

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
    # 仅运行脚本生成部分
    result = run_pipeline(body.topic, body.knowledge, project_id=str(uuid.uuid4()))
    return result["storyboard"]

# --- B4: 视频生成（异步逻辑） ---
async def run_video_pipeline_async(task_id: str, storyboard: dict):
    """模拟异步 Pipeline 运行并更新状态"""
    video_tasks[task_id] = {"status": "processing", "progress": 0, "scene": 0}
    
    total_scenes = len(storyboard.get("scenes", []))
    for i in range(1, total_scenes + 1):
        # 模拟每幕生成时间
        await asyncio.sleep(5) 
        video_tasks[task_id]["progress"] = int((i / total_scenes) * 100)
        video_tasks[task_id]["scene"] = i
        # 这里未来会调用真实的渲染逻辑
        print(f"Task {task_id}: Scene {i} done")

    video_tasks[task_id]["status"] = "complete"
    video_tasks[task_id]["download_url"] = f"/api/video/download/{task_id}"

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
    """WebSocket 实时推送进度"""
    await websocket.accept()
    try:
        while True:
            task = video_tasks.get(task_id)
            if task:
                await websocket.send_json(task)
                if task["status"] == "complete":
                    break
            await asyncio.sleep(1) # 每秒推送一次
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
    return FileResponse(os.path.join(_CLIENT_DIR, "index.html"))

@app.get("/")
def health_check():
    return {"status": "online", "time": datetime.datetime.now()}