"""Legacy AI Engine — simple LLM wrapper for basic text generation.

Kept for backward compatibility. New code should use the pipeline stages instead.
"""
from core_engine.src.utils.llm_client import call_llm


class AI_Engine:
    """Core AI engine that interfaces with LLM APIs for text/video script generation."""

    @staticmethod
    def generate(prompt: str) -> str:
        """Accept a user prompt and return AI-generated text."""
        return call_llm(prompt, lang="en")
