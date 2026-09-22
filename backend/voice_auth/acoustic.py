"""Transparent acoustic anomaly fallback.

This is deliberately not represented as a deepfake model.  It performs actual
signal measurements on WAV data and returns uncertain unless the evidence is
unusually strong.  A future RawTFNet adapter can implement the same interface.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from backend.voice_auth.base import VoiceResult


class AcousticAnomalyAuthenticator:
    model_name = "SCAMTRACE acoustic anomaly fallback v1"

    def analyze(self, audio_path: Path) -> VoiceResult:
        try:
            with wave.open(str(audio_path), "rb") as source:
                sample_width = source.getsampwidth()
                channels = source.getnchannels()
                sample_rate = source.getframerate()
                frames = source.readframes(min(source.getnframes(), sample_rate * 45))
            if sample_width != 2:
                return self._uncertain("WAV must be 16-bit for acoustic fallback.")
            signal = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            if channels > 1:
                signal = signal.reshape(-1, channels).mean(axis=1)
            if len(signal) < max(1024, sample_rate // 2):
                return self._uncertain("Audio is too short for a meaningful acoustic measurement.")
            rms = float(np.sqrt(np.mean(signal * signal)))
            dynamic_range = float(np.percentile(np.abs(signal), 95) - np.percentile(np.abs(signal), 15))
            zero_crossing = float(np.mean(np.abs(np.diff(np.signbit(signal)).astype(np.float32))))
            frame = signal[: min(len(signal), 16384)]
            spectrum = np.abs(np.fft.rfft(frame * np.hanning(len(frame)))) + 1e-10
            spectral_flatness = float(np.exp(np.mean(np.log(spectrum))) / np.mean(spectrum))
            clipping_ratio = float(np.mean(np.abs(signal) > 0.985))
            anomaly = (
                min(28.0, spectral_flatness * 100.0)
                + min(20.0, abs(zero_crossing - 0.09) * 190.0)
                + (18.0 if dynamic_range < 0.06 else 0.0)
                + (16.0 if clipping_ratio > 0.03 else 0.0)
                + (10.0 if rms < 0.008 else 0.0)
            )
            score = round(max(0.0, min(100.0, anomaly)), 1)
            # A heuristic must preserve uncertainty; it cannot reliably identify
            # modern synthetic speech outside a benchmarked anti-spoofing model.
            return {
                "synthetic_score": score,
                "label": "uncertain",
                "confidence": round(min(0.48, 0.20 + score / 200.0), 2),
                "model": self.model_name,
                "available": True,
                "features": {
                    "sample_rate_hz": sample_rate,
                    "rms": round(rms, 5),
                    "dynamic_range": round(dynamic_range, 5),
                    "zero_crossing_rate": round(zero_crossing, 5),
                    "spectral_flatness": round(spectral_flatness, 5),
                    "clipping_ratio": round(clipping_ratio, 5),
                },
                "warning": "Acoustic fallback is an anomaly measurement, not a deepfake verdict.",
            }
        except (OSError, wave.Error, ValueError) as exc:
            return self._uncertain(f"Acoustic analysis unavailable: {exc}")

    def _uncertain(self, warning: str) -> VoiceResult:
        return {
            "synthetic_score": 0.0,
            "label": "uncertain",
            "confidence": 0.0,
            "model": self.model_name,
            "available": False,
            "features": {},
            "warning": warning,
        }

