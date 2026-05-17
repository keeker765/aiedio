from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import datetime
import hashlib
import os
import time
import uuid
import asyncio
import json
import logging

# ---- DEBUG ----
print(f"[AIEDIO DEBUG] main.py loaded from: {__file__}", flush=True)
# ---- END DEBUG ----

# --- Logging setup (dedicated file, bypass uvicorn's root logger) ---
_log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server.log").replace("\\", "/")
_log_handler = logging.FileHandler(_log_path, mode="a", encoding="utf-8")
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
log = logging.getLogger("aiedio")
log.setLevel(logging.INFO)
log.addHandler(_log_handler)
log.propagate = False  # don't send to uvicorn's root logger

# --- Disk cache (persistent across restarts) ---
_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

def _cache_key(topic: str, prefix: str = "knowledge") -> str:
    h = hashlib.md5(topic.encode("utf-8")).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{prefix}_{h}.json")

def _cache_get(key: str) -> dict | None:
    if os.path.exists(key):
        try:
            with open(key, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def _cache_set(key: str, data: dict):
    try:
        with open(key, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning("Cache write failed: %s", e)

# --- Defensive imports: degrade gracefully if modules not ready ---
try:
    from core_engine.src.generate_video import run_pipeline
except ImportError:
    run_pipeline = None
    print("[WARN] core_engine.run_pipeline not available")

try:
    from crawler.src.crawler import fetch_all_trends
except ImportError:
    fetch_all_trends = lambda: {"trends": [], "errors": []}
    print("[WARN] crawler.fetch_all_trends not available")

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

log.info("Aiedio backend started")

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
    knowledge: list = []
    analyses: list = []
    refresh: bool = False
    version: str = ""  # specific storyboard cache version to load
    scene_count: int = 0  # 0=auto, 1-4=number of scenes to generate

class VideoRequest(BaseModel):
    storyboard: dict
    video_provider: str = "openrouter"  # "openrouter" | "dashscope" | "fal" | "placeholder"
    video_model: str = ""               # model override (e.g. "happyhorse-1.0-t2v" for openrouter)

# 存储异步任务状态的全局字典
video_tasks = {}

# --- 简单缓存（避免每次刷新都等爬虫） ---
_cache: dict[str, tuple[float, any]] = {}  # key -> (expiry, data)
_CACHE_TTL = 300  # 5 分钟


def _get_cached_or_refresh(key: str, func: callable, ttl: int = _CACHE_TTL):
    """Return cached value or call func, cache result, return."""
    now = time.time()
    cached = _cache.get(key)
    if cached and cached[0] > now:
        return cached[1]
    data = func()
    _cache[key] = (now + ttl, data)
    return data

# --- YouTube 搜索 API ---
@app.get("/api/youtube/search")
def search_youtube(q: str = "", max_results: int = 8):
    """搜索 YouTube 视频，返回可选列表"""
    try:
        from crawler.src.youtube_spider import fetch_youtube_memes
        # Use search-based approach
        import requests
        api_key = os.getenv("YOUTUBE_API_KEY", "")
        if not api_key or not q:
            return {"results": []}
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "q": q, "type": "video", "maxResults": max_results, "key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId", "")
            snippet = item.get("snippet", {})
            results.append({
                "platform": "youtube",
                "title": snippet.get("title", "")[:120],
                "summary": snippet.get("description", "")[:150],
                "url": f"https://www.youtube.com/watch?v={vid}" if vid else "",
                "hot_value": "",
            })
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}


# --- YouTube 视频分析 API（异步） ---
@app.get("/api/youtube/analyze")
def analyze_youtube_video(url: str = ""):
    """异步分析单个 YouTube 视频的字幕内容"""
    if "watch?v=" not in url:
        return {"error": "Invalid YouTube URL"}
    try:
        from crawler.src.video_analyzer import analyze_video
        vid = url.split("watch?v=")[-1].split("&")[0]
        if not vid:
            return {"error": "Invalid video ID"}
        analysis = analyze_video(vid)
        return {"title": "", "url": url, "content": analysis or ""}
    except Exception as e:
        return {"error": str(e)}


# --- B1: 热点 API（缓存 5 分钟） ---
@app.get("/api/trends")
def get_trends():
    """获取各平台热点列表，含平台状态（缓存 5 分钟）"""
    return _get_cached_or_refresh("trends", fetch_all_trends, ttl=300)

# --- Debug: check cache ---
@app.get("/api/debug/cache")
def debug_cache():
    """Check cache state"""
    return {
        "__file__": __file__,
        "_CACHE_DIR": _CACHE_DIR,
        "cache_exists": os.path.isdir(_CACHE_DIR),
        "cache_files": os.listdir(_CACHE_DIR) if os.path.isdir(_CACHE_DIR) else [],
        "log_path": _log_path,
        "log_exists": os.path.exists(_log_path),
    }

# --- B2: 话题知识 API（同步返回视频分析） ---
@app.post("/api/knowledge")
def get_knowledge(body: KnowledgeRequest):
    """根据话题搜索背景知识，并行分析最多 4 个 YouTube 视频的字幕（磁盘缓存）"""
    topic = body.topic
    ck = _cache_key(topic, "knowledge")
    cached = _cache_get(ck)
    if cached:
        log.info("Knowledge cache hit: %s", topic[:60])
        return cached

    log.info("Knowledge API start: topic=%s", topic[:80])
    t0 = time.time()
    result = search_topic_knowledge(topic)
    log.info("Topic search done: %d sources in %.1fs", len(result.get("sources") or []), time.time() - t0)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from crawler.src.video_analyzer import analyze_video

    youtube_videos = []
    for src in (result.get("sources") or []):
        if src.get("platform") == "youtube" and "watch?v=" in src.get("url", ""):
            if len(youtube_videos) >= 4:
                break
            vid = src["url"].split("watch?v=")[-1].split("&")[0]
            youtube_videos.append((src, vid))

    analyses = [None] * len(youtube_videos)
    t1 = time.time()

    with ThreadPoolExecutor(max_workers=4) as pool:
        fut_map = {}
        for i, (src, vid) in enumerate(youtube_videos):
            fut = pool.submit(analyze_video, vid)
            fut_map[fut] = (i, src)
            log.info("  Video analysis started [%d/%d]: %s", i + 1, len(youtube_videos), src.get('title', '')[:50])

        for fut in as_completed(fut_map):
            i, src = fut_map[fut]
            try:
                raw = (fut.result() or "")
                conflict = ""
                drama = ""
                content = raw[:1000]
                lines = raw.split("\n")
                rest_lines = []
                for line in lines:
                    if line.startswith("Conflict:"):
                        conflict = line[9:].strip()
                    elif line.startswith("Drama:"):
                        drama = line[6:].strip()
                    else:
                        rest_lines.append(line)
                if conflict or drama:
                    content = "\n".join(rest_lines).strip()[:1000]
                else:
                    content = raw[:1000]
                if content.startswith("Title:") and "Description:" in content:
                    content = ""
                if raw:
                    analyses[i] = {
                        "title": src["title"],
                        "url": src["url"],
                        "summary": src.get("summary", "")[:200],
                        "conflict": conflict,
                        "drama": drama,
                        "content": content,
                    }
                log.info("  Video analysis done [%d/%d]: %s (%.1fs)", i + 1, len(youtube_videos), src.get('title', '')[:40], time.time() - t1)
            except Exception as e:
                log.error("Video analysis failed [%d/%d]: %s -> %s", i + 1, len(youtube_videos), src.get('title', '')[:40], e)

    result["analyses"] = [a for a in analyses if a]
    elapsed = time.time() - t0
    log.info("Knowledge API done: %d analyses in %.1fs", len(result["analyses"]), elapsed)
    _cache_set(ck, result)
    return result

# --- B3: 分镜生成 API ---
@app.post("/api/storyboard")
def generate_storyboard(body: StoryboardRequest):
    """调用 AI 引擎生成分镜脚本 (Storyboard，磁盘缓存)"""
    # If specific version requested, serve directly from cache
    if body.version:
        vck = os.path.join(_CACHE_DIR, f"storyboard_{body.version}.json")
        cached = _cache_get(vck)
        if cached:
            log.info("Storyboard version loaded: %s (%s)", body.topic[:60], body.version)
            return cached
        log.warning("Requested version not found: %s", body.version)

    # Cache key = topic + hash of analyses + scene_count (different counts = different results)
    analyses_hash = hashlib.md5(str(body.analyses).encode("utf-8")).hexdigest()[:12]
    ck = _cache_key(f"{body.topic}_{analyses_hash}_sc{body.scene_count}", "storyboard")
    if not body.refresh:
        cached = _cache_get(ck)
        if cached:
            log.info("Storyboard cache hit: %s (sc=%s)", body.topic[:60], body.scene_count)
            return cached

    log.info("Storyboard API start: %s (sc=%s)", body.topic[:60], body.scene_count)
    sb = None
    pipeline_error = None

    if run_pipeline is not None:
        result = run_pipeline(body.topic, body.knowledge, storyboard_only=True, analyses=body.analyses, scene_count=body.scene_count)
        sb = result.get("storyboard")
        pipeline_error = result.get("error")

    if not sb:
        log.warning(
            "Storyboard generation failed — using placeholder scenes. topic=%r error=%s",
            body.topic[:60], pipeline_error or "run_pipeline unavailable or returned None",
        )
        sb = {
            "title": body.topic,
            "description": f"Storyboard for: {body.topic}",
            "scenes": [
                {"scene_id": i + 1, "visual_prompt": f"Scene {i + 1} for {body.topic}", "narration": "", "duration": 10}
                for i in range(4)
            ],
        }

    # Replace LLM story_background with real video analysis from captions
    try:
        from crawler.src.video_analyzer import analyze_video
        for src in (body.knowledge or []):
            if src.get("platform") == "youtube" and "watch?v=" in src.get("url", ""):
                vid = src["url"].split("watch?v=")[-1].split("&")[0]
                if vid:
                    analysis = analyze_video(vid)
                    if analysis:
                        sb["story_background"] = "🎬 Video Content Breakdown\n" + analysis
                    break
    except Exception:
        pass

    _cache_set(ck, sb)
    return sb

# --- B4: 视频生成（异步逻辑） ---

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEMO_VIDEOS = {
    "scene_clips": [
        os.path.join(_PROJECT_ROOT, "core_engine", "output", "videos", "backrooms_kling", "kling_v3_video_1775474758.mp4"),
        os.path.join(_PROJECT_ROOT, "core_engine", "output", "videos", "backrooms_kling", "kling_v3_video_1775474988.mp4"),
    ],
    "final": os.path.join(_PROJECT_ROOT, "core_engine", "output", "videos", "backrooms_kling", "backrooms_act1_act2_preview.mp4"),
}

async def run_video_pipeline_async(task_id: str, storyboard: dict, video_provider: str = "openrouter", video_model: str = ""):
    """异步 Pipeline 运行并更新状态。

    优先调用真实 run_pipeline()，失败时回退到 demo 模式。
    """
    scenes = storyboard.get("scenes", [])
    total_scenes = len(scenes) or 1

    video_tasks[task_id] = {
        "status": "processing",
        "events": [],
        "progress": 0,
        "scene": 0,
        "total": total_scenes,
    }

    # Initialize scene_start events upfront
    for i in range(1, total_scenes + 1):
        video_tasks[task_id]["events"].append(
            {"event": "scene_start", "scene": i, "total": total_scenes}
        )

    def on_scene_done(scene_idx: int, total: int, clip_path: str | None = None):
        """同步回调 — 由 Pipeline 的 on_scene_done 触发"""
        video_tasks[task_id]["events"].append(
            {"event": "scene_done", "scene": scene_idx, "total": total, "preview_url": clip_path or ""}
        )
        video_tasks[task_id]["progress"] = int((scene_idx / total) * 100)
        log.info("  Task %s: Scene %d/%d done (real pipeline)", task_id[:8], scene_idx, total)

    # 尝试真实 Pipeline
    if run_pipeline is not None and scenes:
        try:
            log.info("  Task %s: Starting real pipeline for %s...", task_id[:8], scenes[0].get('visual_prompt', '')[:40])
            result = await asyncio.to_thread(
                run_pipeline,
                topic=storyboard.get("title", "custom"),
                storyboard_dict=storyboard,
                project_id=task_id,
                video_provider=video_provider,
                video_model=video_model,
                on_scene_done=on_scene_done,
            )

            final_path = result.get("final_path")
            if final_path and os.path.exists(final_path):
                video_tasks[task_id]["final_path"] = final_path
                video_tasks[task_id]["status"] = "complete"
                video_tasks[task_id]["events"].append(
                    {"event": "complete", "video_url": f"/api/video/download/{task_id}"}
                )
                log.info("  Task %s: Pipeline complete -> %s", task_id[:8], final_path)
                return
            else:
                log.warning("  Task %s: Real pipeline returned no output, using demo fallback", task_id[:8])
        except Exception as e:
            log.error("  Task %s: Real pipeline failed: %s", task_id[:8], e)

    # 回退到 demo 模式
    log.info("  Task %s: Using demo mode (fallback)", task_id[:8])
    demo_clips = [p for p in _DEMO_VIDEOS["scene_clips"] if os.path.exists(p)]
    demo_total = len(demo_clips) if demo_clips else total_scenes

    for i in range(1, demo_total + 1):
        video_tasks[task_id]["events"].append(
            {"event": "scene_start", "scene": i, "total": demo_total}
        )
        video_tasks[task_id]["scene"] = i
        await asyncio.sleep(3)

        preview_url = f"/api/video/clip/{task_id}/{i}" if i <= len(demo_clips) else ""
        video_tasks[task_id]["progress"] = int((i / demo_total) * 100)
        video_tasks[task_id]["events"].append(
            {"event": "scene_done", "scene": i, "total": demo_total, "preview_url": preview_url}
        )

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
    background_tasks.add_task(run_video_pipeline_async, task_id, body.storyboard, body.video_provider, body.video_model)
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
        log.info("Client disconnected from task %s", task_id[:8])

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

# --- 缓存列表 ---
@app.get("/api/cache/topics")
def list_cached_topics():
    """返回已缓存的 topics 列表（供前端选择）"""
    topics = []
    seen = set()
    for fname in os.listdir(_CACHE_DIR):
        if fname.startswith("knowledge_") and fname.endswith(".json"):
            try:
                with open(os.path.join(_CACHE_DIR, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    t = data.get("topic", "")
                if t and t not in seen:
                    seen.add(t)
                    # Find all storyboard versions for this topic
                    sb_versions = []
                    for sf in os.listdir(_CACHE_DIR):
                        if sf.startswith("storyboard_") and sf.endswith(".json"):
                            try:
                                sd = json.load(open(os.path.join(_CACHE_DIR, sf)))
                                if sd.get("title") == t:
                                    scenes = sd.get("scenes", [])
                                    bg = sd.get("story_background", "")[:120]
                                    sb_versions.append({
                                        "scenes": len(scenes),
                                        "preview": bg,
                                        "cache_key": sf.replace("storyboard_", "").replace(".json", ""),
                                    })
                            except Exception:
                                pass
                    topics.append({
                        "topic": t,
                        "sources": len(data.get("sources", [])),
                        "analyses": len(data.get("analyses", [])),
                        "cache_key": fname.replace("knowledge_", "").replace(".json", ""),
                        "versions": sb_versions,
                    })
            except Exception:
                pass
    topics.sort(key=lambda x: x["topic"])
    return {"topics": topics}

# --- 视频模型列表 ---
@app.get("/api/video/models")
def list_video_models():
    """返回可用的视频生成模型列表（供前端下拉选择）"""
    return {"models": [
        {"id": "openrouter", "name": "Kling Video O1 (OpenRouter)", "provider": "openrouter"},
        {"id": "dashscope",  "name": "Wan 2.7 T2V (阿里百炼)",     "provider": "dashscope"},
        {"id": "happyhorse", "name": "Happyhorse T2V (阿里百炼)",  "provider": "happyhorse"},
    ]}

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
    """自动扫描 core_engine/output/videos/ 下所有项目，返回展示数据"""
    output_dir = os.path.join(_PROJECT_ROOT, "core_engine", "output")
    videos_dir = os.path.join(output_dir, "videos")
    assets_dir = os.path.join(output_dir, "assets")
    result = {"projects": []}

    if not os.path.isdir(videos_dir):
        return result

    # Scan all subdirectories
    dirs = sorted(os.listdir(videos_dir), key=lambda d: os.path.getmtime(os.path.join(videos_dir, d)), reverse=True)

    for dirname in dirs:
        vdir = os.path.join(videos_dir, dirname)
        if not os.path.isdir(vdir):
            continue

        proj = {"id": dirname, "clips": [], "images": [], "storyboard": None}

        # Read metadata.json if available
        meta_path = os.path.join(vdir, "metadata.json")
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass

        proj["title"] = meta.get("title", dirname)
        proj["desc"] = f"{meta.get('scenes', '?')} scenes, {meta.get('total_duration', '?')}s total"
        proj["model"] = "DashScope I2V" if any("dashscope" in f.lower() for f in os.listdir(vdir)) else "Pipeline"
        # Surface the embedded storyboard so showcase.html can render scenes.
        sb = meta.get("storyboard")
        if isinstance(sb, dict) and sb.get("scenes"):
            proj["storyboard"] = sb

        # Find final video (*_final.mp4 or fallback to final_path from metadata)
        final_video = None
        final_meta = meta.get("final_path")
        if final_meta and os.path.exists(final_meta):
            fname = os.path.basename(final_meta)
            final_video = f"/api/showcase/file/videos/{dirname}/{fname}"
            proj["final_size_mb"] = round(os.path.getsize(final_meta) / 1024 / 1024, 1)
        else:
            for f in os.listdir(vdir):
                if f.endswith("_final.mp4"):
                    final_video = f"/api/showcase/file/videos/{dirname}/{f}"
                    proj["final_size_mb"] = round(os.path.getsize(os.path.join(vdir, f)) / 1024 / 1024, 1)
                    break
        proj["final_video"] = final_video

        # Find all mp4 clips (exclude _final.mp4)
        for f in sorted(os.listdir(vdir)):
            if f.endswith(".mp4") and not f.endswith("_final.mp4"):
                proj["clips"].append({
                    "name": f,
                    "url": f"/api/showcase/file/videos/{dirname}/{f}",
                    "size_mb": round(os.path.getsize(os.path.join(vdir, f)) / 1024 / 1024, 1),
                })

        # Skip projects with no video content at all (only placeholder txt files)
        if not proj["clips"] and not proj["final_video"]:
            continue

        # Find images in corresponding assets directory
        adir = os.path.join(assets_dir, dirname)
        if os.path.isdir(adir):
            for f in sorted(os.listdir(adir)):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    proj["images"].append({
                        "name": f,
                        "url": f"/api/showcase/file/assets/{dirname}/{f}",
                    })

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

@app.get("/storyboard")
def serve_storyboard():
    """Serve the standalone storyboard page"""
    sb = os.path.join(_CLIENT_DIR, "storyboard.html")
    if os.path.exists(sb):
        return FileResponse(sb)
    return {"message": "Storyboard page not found"}

@app.get("/style.css")
def serve_css():
    return FileResponse(os.path.join(_CLIENT_DIR, "style.css"), media_type="text/css")

@app.get("/script.js")
def serve_js():
    return FileResponse(os.path.join(_CLIENT_DIR, "script.js"), media_type="application/javascript")

@app.get("/")
def health_check():
    return {"status": "online", "time": datetime.datetime.now()}
