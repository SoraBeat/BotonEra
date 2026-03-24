"""Manage the sound library: load, import, persist to config.json."""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from src.audio_engine import load_audio
from src.styles.theme import BUTTON_COLORS, BUTTON_EMOJIS


@dataclass
class SoundEntry:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    path: str = ""
    color: str = "#6C63FF"
    emoji: str = "🔊"
    keybind: str = ""

    # ── runtime only (not serialised) ──────────────────────────────────────
    audio_data: "np.ndarray | None" = field(default=None, compare=False, repr=False)
    samplerate: int = field(default=44100, compare=False, repr=False)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()
                if k not in ("audio_data", "samplerate")}


class SoundManager:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.sounds_dir = base_dir / "sounds"
        self.config_path = base_dir / "config.json"
        self.sounds_dir.mkdir(parents=True, exist_ok=True)

        self.sounds: list[SoundEntry] = []
        self.mic_device_id: int | None = None
        self.monitor_device_id: int | None = None
        self.volume: float = 1.0

        self._load_config()

    # ── Config persistence ──────────────────────────────────────────────────

    def _load_config(self) -> None:
        if not self.config_path.exists():
            return
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            self.mic_device_id = data.get("mic_device_id")
            self.monitor_device_id = data.get("monitor_device_id")
            self.volume = float(data.get("volume", 1.0))
            for s in data.get("sounds", []):
                entry = SoundEntry(
                    id=s.get("id", uuid.uuid4().hex[:12]),
                    name=s.get("name", ""),
                    path=s.get("path", ""),
                    color=s.get("color", "#6C63FF"),
                    emoji=s.get("emoji", "🔊"),
                    keybind=s.get("keybind", ""),
                )
                # Skip entries whose file no longer exists
                if Path(entry.path).exists():
                    self.sounds.append(entry)
        except Exception:
            pass

    def save_config(self) -> None:
        data = {
            "mic_device_id": self.mic_device_id,
            "monitor_device_id": self.monitor_device_id,
            "volume": self.volume,
            "sounds": [s.to_dict() for s in self.sounds],
        }
        self.config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # ── Sound library ───────────────────────────────────────────────────────

    def import_sound(
        self,
        src_path: Path,
        name: str,
        color: str | None = None,
        emoji: str | None = None,
    ) -> SoundEntry:
        """Copy the file into the sounds folder and register it."""
        dest = self.sounds_dir / src_path.name
        if dest.exists():
            dest = self.sounds_dir / f"{uuid.uuid4().hex[:6]}_{src_path.name}"
        shutil.copy2(src_path, dest)

        idx = len(self.sounds)
        entry = SoundEntry(
            name=name or src_path.stem,
            path=str(dest),
            color=color or BUTTON_COLORS[idx % len(BUTTON_COLORS)],
            emoji=emoji or BUTTON_EMOJIS[idx % len(BUTTON_EMOJIS)],
        )
        self.sounds.append(entry)
        self.save_config()
        return entry

    def update_sound(self, sound_id: str, **kwargs) -> None:
        """Update fields of an existing entry and persist."""
        for s in self.sounds:
            if s.id == sound_id:
                for k, v in kwargs.items():
                    if hasattr(s, k):
                        setattr(s, k, v)
                break
        self.save_config()

    def remove_sound(self, sound_id: str) -> None:
        self.sounds = [s for s in self.sounds if s.id != sound_id]
        self.save_config()

    def ensure_audio_loaded(self, entry: SoundEntry) -> None:
        """Decode audio into memory if not already done."""
        if entry.audio_data is None:
            data, sr = load_audio(entry.path)
            entry.audio_data = data
            entry.samplerate = sr
