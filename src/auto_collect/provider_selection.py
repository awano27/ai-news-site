"""Choose the morning override LLM provider without printing secrets.

NVIDIA is used only when the key looks like an nvapi key and
NVIDIA_PRODUCTION_USE_CONFIRMED is exactly 'true'. The Python health check
still requires that same flag; this selector keeps the Windows runner from
picking nvidia and then failing the health check.
"""
from __future__ import annotations

import os


def select_daily_provider(api_key: str | None, confirmed: str | None) -> tuple[str, str | None]:
    has_key = (api_key or "").lower().startswith("nvapi-")
    if has_key and confirmed == "true":
        return "nvidia", None
    if has_key:
        return "ollama", "NVIDIA key found but NVIDIA_PRODUCTION_USE_CONFIRMED is not 'true'; using ollama."
    return "ollama", None


def main() -> int:
    name, note = select_daily_provider(
        os.environ.get("NVIDIA_API_KEY"),
        os.environ.get("NVIDIA_PRODUCTION_USE_CONFIRMED"),
    )
    print(f"provider={name}")
    if note:
        print(f"note={note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
