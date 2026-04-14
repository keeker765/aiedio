"""Edge-TTS provider — free Microsoft TTS, no API key required.

Uses the `edge-tts` Python package which accesses Microsoft Edge's online TTS service.
Supports 400+ voices across 100+ languages.
"""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from core_engine.src.providers.base import TTSProvider

# Voice presets per language
_VOICE_MAP = {
    "zh": "zh-CN-XiaoxiaoNeural",
    "en": "en-US-AriaNeural",
    "ja": "ja-JP-NanamiNeural",
}


class EdgeTTSProvider(TTSProvider):
    """Free TTS via Microsoft Edge online service."""

    def __init__(self, output_dir: str | Path = "core_engine/output/assets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self,
        text: str,
        voice: str = "default",
        lang: str = "zh",
    ) -> Path:
        try:
            import edge_tts
        except ImportError:
            return self._placeholder(text, lang)

        if voice == "default":
            voice = _VOICE_MAP.get(lang, _VOICE_MAP["en"])

        ts = int(time.time())
        out_path = self.output_dir / f"tts_{lang}_{ts}.mp3"

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(out_path))

        asyncio.run(_generate())
        print(f"  [EdgeTTS] Saved: {out_path.name} ({voice})")
        return out_path

    def _placeholder(self, text: str, lang: str) -> Path:
        ts = int(time.time())
        path = self.output_dir / f"tts_placeholder_{ts}.txt"
        path.write_text(
            f"[Placeholder TTS]\nLang: {lang}\nText: {text[:200]}\n"
            f"\nInstall edge-tts: pip install edge-tts\n",
            encoding="utf-8",
        )
        print(f"  [EdgeTTS] edge-tts not installed — wrote placeholder: {path.name}")
        return path
