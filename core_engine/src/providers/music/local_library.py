"""Local music library provider — serves royalty-free background music."""
from __future__ import annotations

import os
import random
from pathlib import Path

from core_engine.src.providers.base import MusicProvider

_ROOT = Path(__file__).resolve().parents[3]  # core_engine/
_MUSIC_DIR = _ROOT / "resources" / "music"


class LocalMusicProvider(MusicProvider):
    """Pick a track from the local royalty-free music library."""

    def __init__(self, music_dir: str | Path | None = None):
        self.music_dir = Path(music_dir) if music_dir else _MUSIC_DIR
        self.music_dir.mkdir(parents=True, exist_ok=True)

    def get_track(
        self,
        mood: str = "neutral",
        duration: float = 30.0,
    ) -> Path:
        tracks = list(self.music_dir.glob("*.mp3")) + list(self.music_dir.glob("*.wav"))

        if not tracks:
            return self._placeholder(mood, duration)

        # Simple mood-based matching by filename keyword
        mood_lower = mood.lower()
        matched = [t for t in tracks if mood_lower in t.stem.lower()]
        chosen = random.choice(matched) if matched else random.choice(tracks)

        print(f"  [Music] Selected: {chosen.name} (mood={mood})")
        return chosen

    def _placeholder(self, mood: str, duration: float) -> Path:
        path = self.music_dir / "placeholder_bgm.txt"
        path.write_text(
            f"[Placeholder BGM]\nMood: {mood}\nDuration: {duration}s\n"
            f"\nAdd .mp3 files to core_engine/resources/music/ to enable BGM.\n",
            encoding="utf-8",
        )
        print(f"  [Music] No tracks found — wrote placeholder")
        return path
