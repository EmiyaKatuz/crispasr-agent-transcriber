from __future__ import annotations

import math
import wave
from pathlib import Path


def write_tone_wav(path: Path, *, seconds: float = 0.25, sample_rate: int = 16000) -> Path:
    frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(frames):
            sample = int(12000 * math.sin(2 * math.pi * 440 * (i / sample_rate)))
            wav.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))
    return path
