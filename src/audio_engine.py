"""Dual-output audio engine – plays to headphones AND a virtual cable simultaneously."""
from __future__ import annotations

import threading
import numpy as np

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False

try:
    import soundfile as sf
    HAS_SF = True
except ImportError:
    HAS_SF = False

try:
    import miniaudio
    HAS_MINIAUDIO = True
except ImportError:
    HAS_MINIAUDIO = False


CHUNK_FRAMES = 1024


def load_audio(path: str) -> tuple[np.ndarray, int]:
    """Return (float32 array shape [N, C], samplerate).
    Tries soundfile first, falls back to miniaudio for MP3."""
    if HAS_SF:
        try:
            data, sr = sf.read(path, dtype="float32", always_2d=True)
            return data, sr
        except Exception:
            pass

    if HAS_MINIAUDIO:
        try:
            decoded = miniaudio.decode_file(
                path,
                output_format=miniaudio.SampleFormat.FLOAT32,
                nchannels=2,
            )
            samples = np.frombuffer(decoded.samples, dtype=np.float32)
            data = samples.reshape(-1, decoded.nchannels)
            return data, decoded.sample_rate
        except Exception:
            pass

    raise RuntimeError(
        f"No se pudo cargar '{path}'.\n"
        "Formatos soportados: WAV, FLAC, OGG, MP3 (con miniaudio instalado)."
    )


def _adapt_channels(data: np.ndarray, target: int) -> np.ndarray:
    """Mix or duplicate channels to match target channel count."""
    current = data.shape[1]
    if current == target:
        return data
    if current == 1 and target == 2:
        return np.hstack([data, data])
    if current == 2 and target == 1:
        return np.mean(data, axis=1, keepdims=True)
    # General case: pad with silence or truncate
    if current < target:
        pad = np.zeros((data.shape[0], target - current), dtype=data.dtype)
        return np.hstack([data, pad])
    return data[:, :target]


class PlaybackHandle:
    """Returned by AudioEngine.play() – call .stop() to cancel playback."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self.frames_played: int = 0   # written each chunk by audio thread (GIL-safe)
        self.total_frames: int = 0    # set once before playback loop
        self._samplerate: int = 44100 # set by _worker before loop

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def stopped(self) -> bool:
        return self._stop_event.is_set()

    @property
    def progress(self) -> float:
        if self.total_frames <= 0:
            return 0.0
        return min(1.0, self.frames_played / self.total_frames)

    @property
    def elapsed_sec(self) -> float:
        return self.frames_played / self._samplerate if self._samplerate > 0 else 0.0

    @property
    def total_sec(self) -> float:
        return self.total_frames / self._samplerate if self._samplerate > 0 else 0.0


class AudioEngine:
    def __init__(self) -> None:
        self._volume: float = 1.0
        self._handles: list[PlaybackHandle] = []
        self._lock = threading.Lock()

    # ── Public API ──────────────────────────────────────────────────────────

    def set_volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, float(value)))

    def play(
        self,
        audio_data: np.ndarray,
        samplerate: int,
        monitor_device: int | None = None,
        mic_device: int | None = None,
        on_finished: "callable | None" = None,
    ) -> PlaybackHandle:
        """Start playback in a daemon thread, returns a handle to stop it."""
        if not HAS_SD:
            raise RuntimeError("sounddevice no está instalado.")

        handle = PlaybackHandle()
        with self._lock:
            self._handles.append(handle)

        t = threading.Thread(
            target=self._worker,
            args=(audio_data, samplerate, monitor_device, mic_device, handle, on_finished),
            daemon=True,
            name="BotonEra-playback",
        )
        t.start()
        return handle

    def stop_all(self) -> None:
        with self._lock:
            for h in self._handles:
                h.stop()
            self._handles.clear()

    # ── Internal ────────────────────────────────────────────────────────────

    def _worker(
        self,
        raw_data: np.ndarray,
        samplerate: int,
        monitor_device: int | None,
        mic_device: int | None,
        handle: PlaybackHandle,
        on_finished: "callable | None",
    ) -> None:
        data = (raw_data * self._volume).astype(np.float32)
        streams: list = []

        try:
            # Build list of (device_idx_or_None, stream)
            targets = []
            if monitor_device is not None:
                targets.append(monitor_device)
            else:
                targets.append(None)  # default output for monitor

            if mic_device is not None and mic_device != monitor_device:
                targets.append(mic_device)

            for dev in targets:
                try:
                    info = sd.query_devices(dev) if dev is not None else sd.query_devices(sd.default.device[1])
                    ch = min(2, int(info["max_output_channels"]))
                    ch = max(ch, 1)
                    chunk = _adapt_channels(data, ch)
                    stream = sd.OutputStream(
                        device=dev,
                        samplerate=samplerate,
                        channels=ch,
                        dtype="float32",
                        blocksize=CHUNK_FRAMES,
                    )
                    stream.start()
                    streams.append((stream, chunk))
                except Exception:
                    pass

            if not streams:
                return

            total = max(s[1].shape[0] for s in streams)
            handle.total_frames = total
            handle._samplerate = samplerate
            for i in range(0, total, CHUNK_FRAMES):
                if handle.stopped:
                    break
                handle.frames_played = i
                for stream, chunk in streams:
                    frame = chunk[i: i + CHUNK_FRAMES]
                    if len(frame) == 0:
                        continue
                    try:
                        stream.write(frame)
                    except Exception:
                        pass

        finally:
            for stream, _ in streams:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass
            with self._lock:
                try:
                    self._handles.remove(handle)
                except ValueError:
                    pass
            if on_finished and not handle.stopped:
                on_finished()
