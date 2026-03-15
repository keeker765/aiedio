from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

import datetime



app = FastAPI(

    title="Aiedio Backend Hub",

    description="This is the backend hub that Lu Yi is in charge of, responsible for connecting the frontend and the AI ​​engine.",

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

    这个函数就是处理前端请求的“中枢”。

    等前端同学 (@Liu/@Li) 的按钮画好了，他们的请求会打到这里。

    """

    # ------------------------------------------------------

    # 1. 对接前端：这个函数的入口就是前端的“投递箱”

    # 前端把数据发过来，item 就是前端塞进来的“纸条”

    # ------------------------------------------------------

    # 1. 后端终端打印日志（方便你看有没有接到请求）

    print(f"🚀 收到前端点击请求: {item.user_input}")

    # ------------------------------------------------------

    # 2. 对接 AI 内核

    # 下周 @Wu Ke 写好 AI 引擎后，你会在这里写一行类似：

    # ai_result = WuKe_AI_Engine.generate(item.user_input)

    # ------------------------------------------------------

    # 2. 模拟处理逻辑

    mock_ai_reply = f"【AI 回复】后端已收到指令：'{item.user_input}'。连接测试成功！"

    

    # 3. 返回给前端的数据（JSON 格式）

    return {

        "success": True,

        "data": {

            "reply": mock_ai_reply,

            "received_at": datetime.datetime.now().strftime("%H:%M:%S")

        }

    }



# ============================================================

# 📍 【对接区域结束】

# ============================================================