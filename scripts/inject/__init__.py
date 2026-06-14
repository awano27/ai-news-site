# inject package — shared Injector framework for inject_*.py scripts
from inject._framework import (
    ROOT,
    Injector,
    insert_after_body_anchor,
    insert_before_head_close,
    iter_targets,
    strip_marker_block,
)

__all__ = [
    "ROOT",
    "Injector",
    "insert_after_body_anchor",
    "insert_before_head_close",
    "iter_targets",
    "strip_marker_block",
]
