#!/usr/bin/env python3
"""Static guardrails for the AI coding-agent comparison guide.

This check catches only known regressions in claims that were corrected on
2026-09-05. It does not verify vendor features, pricing, or performance.
Those claims still require a human review against the linked primary source.
"""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from pathlib import Path


DEFAULT_GUIDE = Path("presentations/ai_coding_agents_guide.html")

REQUIRED_SOURCES = {
    "Claude Code sandbox": "https://code.claude.com/docs/en/sandboxing",
    "Claude Code hooks": "https://code.claude.com/docs/en/hooks",
    "GitHub Copilot hooks": "https://docs.github.com/en/copilot/concepts/agents/hooks",
    "GitHub Copilot hooks reference": "https://docs.github.com/en/copilot/reference/hooks-reference",
}

KNOWN_REGRESSIONS = {
    "Claude Codeはサンドボックスなし": "Claude Code の Bash sandbox を『なし』と断定している",
    "なし（ユーザー承認制で安全性を確保）": "承認フローをサンドボックスの代替としている",
    "唯一の自動介入システム": "Hooks を唯一の仕組みと断定している",
    "Codex/Copilot/Antigravityにはこのレベルの行動制御機構が存在しない": "他製品の行動制御を不存在と断定している",
    "プロダクション環境の安全性で最も優位": "比較可能な評価根拠なしに安全性の順位を断定している",
    "他を凌駕": "同一評価条件なしに性能の順位を断定している",
    "最も優れている": "評価条件なしに製品の順位を断定している",
    "最も優位": "評価条件なしに製品の順位を断定している",
    "唯一無二": "他製品との比較根拠なしに独自性を断定している",
    "他3ツールには": "他製品の機能を一括で断定している",
}

HUMAN_REVIEW_PATTERNS = {
    "完全自動": "適用環境、承認、失敗時の扱いを人が確認する",
    "最適解": "評価条件と対象読者を人が確認する",
    "完全アクセス": "対象のファイル、ネットワーク、実行環境を人が確認する",
}


def visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", html, flags=re.I | re.S)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", without_scripts))).strip()


def check_html(html: str) -> tuple[list[str], list[str]]:
    text = visible_text(html)
    errors: list[str] = []
    warnings: list[str] = []

    for label, url in REQUIRED_SOURCES.items():
        if url not in html:
            errors.append(f"{label} の直接一次資料リンクがない: {url}")

    for phrase, reason in KNOWN_REGRESSIONS.items():
        if phrase in text:
            errors.append(reason)

    for phrase in (
        "Bash とその子プロセス",
        "macOS・Linux・WSL2",
        "ネイティブ Windows は未対応",
        "作業ディレクトリ",
        "allowUnsandboxedCommands",
        "サンドボックス外",
        "Copilot CLI",
        "Cloud Agent",
    ):
        if phrase not in text:
            errors.append(f"sandbox/hooks の適用条件が不足している: {phrase}")

    for phrase, advice in HUMAN_REVIEW_PATTERNS.items():
        if phrase in text:
            warnings.append(f"{phrase}: {advice}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_GUIDE)
    args = parser.parse_args()
    try:
        html = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: ガイドを読めません: {exc}")
        return 2

    errors, warnings = check_html(html)
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    if errors:
        return 1
    print("PASS: known comparison-guide regressions are absent; primary-source review remains required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
