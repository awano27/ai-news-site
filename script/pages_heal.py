"""Small, deterministic status model for the Pages self-heal workflow.

The workflow performs the network and GitHub CLI operations.  This module only
classifies their observed outcomes so a rejected dispatch can never be reported
as a successful repair.
"""

from __future__ import annotations

import argparse
from enum import Enum


class HealStatus(str, Enum):
    HEALTHY = "healthy"
    DISPATCH_REJECTED = "dispatch_rejected"
    DISPATCH_ACCEPTED = "dispatch_accepted"
    RECOVERED = "recovered"
    RECOVERY_FAILED = "recovery_failed"


def classify_heal(
    initial_failures: int,
    *,
    dispatch_succeeded: bool | None = None,
    recovery_failures: int | None = None,
) -> HealStatus:
    """Classify probe, dispatch, and recovery as separate observable states."""
    if initial_failures < 0 or (recovery_failures is not None and recovery_failures < 0):
        raise ValueError("failure counts must be non-negative")
    if initial_failures == 0:
        return HealStatus.HEALTHY
    if dispatch_succeeded is not True:
        return HealStatus.DISPATCH_REJECTED
    if recovery_failures is None:
        return HealStatus.DISPATCH_ACCEPTED
    if recovery_failures == 0:
        return HealStatus.RECOVERED
    return HealStatus.RECOVERY_FAILED


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a Pages self-heal attempt")
    parser.add_argument("--initial-failures", type=int, required=True)
    parser.add_argument("--dispatch-succeeded", choices=("true", "false", "unknown"), default="unknown")
    parser.add_argument("--recovery-failures", type=int)
    args = parser.parse_args()

    dispatch = {"true": True, "false": False, "unknown": None}[args.dispatch_succeeded]
    status = classify_heal(
        args.initial_failures,
        dispatch_succeeded=dispatch,
        recovery_failures=args.recovery_failures,
    )
    print(status.value)
    return 0 if status in {HealStatus.HEALTHY, HealStatus.RECOVERED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
