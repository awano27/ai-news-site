"""Pin Date.now() for node scripts spawned by a test.

scripts/build-homepage-latest.js fails closed when the report is more than
14 days older than the real clock, so a fixture dated in October 2026 stops
producing sections two weeks after it was written. Tests that keep dated
fixtures preload a fixed clock through NODE_OPTIONS instead of changing the
production clock; the value also reaches node processes that a Python script
under test spawns itself.
"""
from pathlib import Path


def fixed_node_clock(tmp_path: Path, instant: str) -> str:
    clock = tmp_path / 'fixed-clock.cjs'
    clock.write_text(
        "const RealDate = Date; global.Date = class extends RealDate {"
        f"constructor(...args) {{ super(...(args.length ? args : ['{instant}'])); }}"
        f"static now() {{ return RealDate.parse('{instant}'); }}}};",
        encoding='utf-8',
    )
    # NODE_OPTIONS treats a backslash inside quotes as an escape, so the path must stay POSIX-style.
    return f'--require "{clock.as_posix()}"'
