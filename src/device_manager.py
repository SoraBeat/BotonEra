"""Query available audio output devices via sounddevice."""
from __future__ import annotations

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False


def get_output_devices() -> list[dict]:
    """Return list of output-capable devices as {id, name}."""
    if not HAS_SD:
        return []
    devices = sd.query_devices()
    result = []
    for i, d in enumerate(devices):
        if int(d.get("max_output_channels", 0)) > 0:
            result.append({"id": i, "name": d["name"]})
    return result


def get_default_output_id() -> int | None:
    """Return the default system output device id, or None."""
    if not HAS_SD:
        return None
    try:
        default = sd.default.device[1]
        if default is None or default < 0:
            return None
        return int(default)
    except Exception:
        return None
