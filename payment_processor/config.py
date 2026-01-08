import os


def is_live_mode_enabled() -> bool:
    """Return True when repository-wide live mode activation is enabled.

    This env var acts as a safety switch to avoid accidental live money operations.
    Set `ENABLE_LIVE_MODE=1` or `ENABLE_LIVE_MODE=true` to enable.
    """
    return os.environ.get("ENABLE_LIVE_MODE", "0").lower() in ("1", "true", "yes")
