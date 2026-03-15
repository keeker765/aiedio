import os
import zhipuai

# ============================================================
# 🧠 Wu Ke's AI Engine — AssetBuilder / WuKe_AI_Engine
# backend 调用方式（直接导入）：
#   from core_engine.src.asset_builder import WuKe_AI_Engine
#   result = WuKe_AI_Engine.generate("你好")
# ============================================================

# API Key 从环境变量读取，不要把真实 Key 硬编码进代码里！
# 使用前在终端执行：$env:ZHIPU_API_KEY = "你的真实key"
_API_KEY = os.getenv("ZHIPU_API_KEY", "")


class WuKe_AI_Engine:
    """
    AI 核心引擎，负责对接智谱 GLM 大模型 API，生成文本/视频脚本。
    目前实现：文本生成（GLM-4-Flash 免费版）
    """

    @staticmethod
    def generate(prompt: str) -> str:
        """
        接受一段用户 prompt，返回 AI 生成的文本结果（字符串）。

        参数:
            prompt (str): 前端/后端传入的用户指令

        返回:
            str: AI 生成的文本
        """
        if not _API_KEY:
            # API Key 未配置时，返回一段占位回复，不让整个服务崩溃
            return f"[占位回复] AI引擎待激活。收到指令: '{prompt}'"

        client = zhipuai.ZhipuAI(api_key=_API_KEY)
        response = client.chat.completions.create(
            model="glm-4-flash",   # 免费额度版本
            messages=[
                {"role": "system", "content": "你是一个帮助生成视频脚本和内容创意的 AI 助手。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
