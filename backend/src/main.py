from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import httpx

# 📌 AI 引擎服务地址（Wu Ke 的 core_engine 独立启动后监听这个地址）
CORE_ENGINE_URL = "http://localhost:8001/generate"


app = FastAPI(
    title="Aiedio Backend Hub",
    description="This is the backend hub that Lu Yi is in charge of, responsible for connecting the frontend and the AI engine.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Interaction(BaseModel):
    user_input: str
    action_type: str = "click"


@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "The back-end central control is operating normally!"
    }


# ============================================================
# 📍 【前端对接区域 - FRONTEND API ZONE】
# 这下面就是前端同学要调用的接口。
# 前端调用的完整 URL 是：http://localhost:8000/api/test-flow
# ============================================================


@app.post("/api/test-flow")
async def handle_test_flow(item: Interaction):
    """
    这个函数就是处理前端请求的"中枢"。
    等前端同学 (@Liu/@Li) 的按钮画好了，他们的请求会打到这里。
    """

    # ------------------------------------------------------
    # 1. 对接前端：收到请求后打印日志
    # ------------------------------------------------------
    print(f"🚀 收到前端点击请求: {item.user_input}")

    # ------------------------------------------------------
    # 2. 对接 AI 内核（方案B：HTTP 解耦调用 core_engine 服务）
    # Wu Ke 的 core_engine 需要在 http://localhost:8001 独立运行
    # 调用接口：POST /generate  Body: {"prompt": "..."}
    # ------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                CORE_ENGINE_URL,
                json={"prompt": item.user_input}
            )
            response.raise_for_status()
            ai_result = response.json()
            ai_reply_text = ai_result.get("reply", "(AI 引擎返回了空内容)")
    except httpx.ConnectError:
        # core_engine 还没启动时的降级处理，不影响前端联调
        ai_reply_text = f"【暂时降级】core_engine 服务未启动，后端已收到：'{item.user_input}'"
    except Exception as e:
        ai_reply_text = f"【错误】调用 AI 引擎失败：{str(e)}"

    # ------------------------------------------------------
    # 3. 返回给前端的数据（JSON 格式）
    # ------------------------------------------------------
    return {
        "success": True,
        "data": {
            "reply": ai_reply_text,
            "received_at": datetime.datetime.now().strftime("%H:%M:%S")
        }
    }


# ============================================================
# 📍 【对接区域结束】
# ============================================================
