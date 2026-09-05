from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_coding_guide_integrity.py"
GUIDE = ROOT / "presentations" / "ai_coding_agents_guide.html"


class CodingGuideIntegrityTest(unittest.TestCase):
    def test_checked_guide_has_no_known_errors(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(GUIDE)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_known_regression_fails_but_warning_only_claim_passes(self) -> None:
        bad = self._fixture("Claude Codeはサンドボックスなし")
        bad_result = self._run(bad)
        self.assertEqual(bad_result.returncode, 1)
        self.assertIn("ERROR:", bad_result.stdout)

        warning_only = self._fixture("完全自動")
        warning_result = self._run(warning_only)
        self.assertEqual(warning_result.returncode, 0, warning_result.stdout)
        self.assertIn("WARNING:", warning_result.stdout)

    def _fixture(self, body: str) -> Path:
        self._tmp = Path(self._testMethodName + ".html")
        self._tmp.write_text(
            "<html><body>"
            "Bash とその子プロセス macOS・Linux・WSL2 ネイティブ Windows は未対応 "
            "作業ディレクトリ allowUnsandboxedCommands サンドボックス外 Copilot CLI Cloud Agent "
            "https://code.claude.com/docs/en/sandboxing "
            "https://code.claude.com/docs/en/hooks "
            "https://docs.github.com/en/copilot/concepts/agents/hooks "
            "https://docs.github.com/en/copilot/reference/hooks-reference "
            f"{body}</body></html>",
            encoding="utf-8",
        )
        self.addCleanup(self._tmp.unlink, missing_ok=True)
        return self._tmp

    def _run(self, fixture: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(fixture)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
