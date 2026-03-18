import os
import zhipuai

# ============================================================
# Wu Ke's AI Engine — AssetBuilder / WuKe_AI_Engine
# Usage from backend (direct import):
#   from core_engine.src.asset_builder import AI_Engine
#   result = AI_Engine.generate("hello")
# ============================================================

# API Key is read from environment variable. Never hardcode real keys!
# Before running, execute in terminal: $env:ZHIPU_API_KEY = "your_real_key"
_API_KEY = os.getenv("ZHIPU_API_KEY", "")


class AI_Engine:
    """Core AI engine that interfaces with ZhipuAI GLM API for text/video script generation."""

    @staticmethod
    def generate(prompt: str) -> str:
        """Accept a user prompt and return AI-generated text."""
        if not _API_KEY:
            return f"[Placeholder] AI engine not activated. Received: '{prompt}'"

        client = zhipuai.ZhipuAI(api_key=_API_KEY)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "You are an AI assistant that helps generate video scripts and creative content."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
