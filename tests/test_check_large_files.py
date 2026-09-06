"""End-to-end regression tests for scripts/check_large_files.py.

Each test invokes the CLI from a temporary Git repository. Event tests use
local bare remotes so they exercise ref resolution as Actions does.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_large_files.py"
MAX_BYTES = 5 * 1024 * 1024
ZERO_SHA = "0" * 40


class LargeFilesCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "large-files tests")
        self.write("seed.txt", b"seed\n")
        self.git("add", "seed.txt")
        self.git("commit", "-qm", "seed")
        self.seed = self.rev("HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.repo, text=True, capture_output=True, check=check)

    def rev(self, ref: str) -> str:
        return self.git("rev-parse", ref).stdout.strip()

    def write(self, relative: str, data: bytes) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def commit_file(self, relative: str, data: bytes, message: str) -> str:
        self.write(relative, data)
        self.git("add", "--", relative)
        self.git("commit", "-qm", message)
        return self.rev("HEAD")

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )

    def event_file(self, event: dict[str, object]) -> Path:
        path = self.repo / "event.json"
        path.write_text(json.dumps(event), encoding="utf-8")
        return path

    def event_cli(self, event_name: str, event: dict[str, object]) -> subprocess.CompletedProcess[str]:
        return self.cli("--event-path", str(self.event_file(event)), "--event-name", event_name)

    def push_event(
        self,
        before: str,
        after: str,
        default_branch: str = "main",
        ref: str = "refs/heads/feature",
    ) -> dict[str, object]:
        return {
            "before": before,
            "after": after,
            "ref": ref,
            "repository": {"default_branch": default_branch},
        }

    def pr_event(self, base: str, head: str) -> dict[str, object]:
        return {"pull_request": {"base": {"sha": base}, "head": {"sha": head}}}

    def make_bare_remote(self, default_branch: str = "main") -> Path:
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        self.git("branch", "-M", default_branch)
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "-qu", "origin", default_branch)
        return remote

    def fresh_scanner(self, remote: Path) -> Path:
        scanner = Path(self.temp.name) / "scanner"
        scanner.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=scanner, check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=scanner, check=True)
        return scanner

    def cli_in(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )

    def test_no_args_checks_staged_file(self) -> None:
        self.write("space 日本語.txt", b"small")
        self.git("add", "--", "space 日本語.txt")
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No newly added files", result.stdout)

    def test_no_args_rejects_oversized_staged_file(self) -> None:
        self.write("staged-large.bin", b"x" * (MAX_BYTES + 1))
        self.git("add", "staged-large.bin")
        result = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("staged-large.bin", result.stdout)

    def test_range_rejects_only_over_five_mib_and_handles_unicode_spaces(self) -> None:
        before = self.rev("HEAD")
        self.commit_file("space 日本語.txt", b"a" * MAX_BYTES, "at boundary")
        boundary = self.rev("HEAD")
        allowed = self.cli("--range", f"{before}..{boundary}")
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.commit_file("large 日本語.bin", b"b" * (MAX_BYTES + 1), "over boundary")
        rejected = self.cli("--range", f"{boundary}..{self.rev('HEAD')}")
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("large 日本語.bin", rejected.stdout)

    def test_push_event_uses_before_after_for_normal_push(self) -> None:
        before = self.rev("HEAD")
        after = self.commit_file("new.txt", b"small", "new")
        result = self.event_cli("push", self.push_event(before, after))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reason=push-before", result.stdout)

    def test_pull_request_event_uses_base_head(self) -> None:
        base = self.rev("HEAD")
        head = self.commit_file("pr file.txt", b"small", "pr")
        result = self.event_cli("pull_request", self.pr_event(base, head))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reason=pull-request-base", result.stdout)

    def test_zero_before_small_push_fetches_remote_default_and_passes(self) -> None:
        remote = self.make_bare_remote("trunk")
        after = self.commit_file("space 日本語.txt", b"small", "feature")
        self.git("push", "-q", "origin", "HEAD:refs/heads/feature")
        scanner = self.fresh_scanner(remote)
        result = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, after, "trunk"))), "--event-name", "push")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reason=zero-before-merge-base", result.stdout)
        self.assertIn(f"base={self.seed}", result.stdout)
        self.assertIn("target_count=1", result.stdout)

    def test_zero_before_oversized_push_fails_with_proper_size(self) -> None:
        remote = self.make_bare_remote()
        after = self.commit_file("large 日本語.bin", b"x" * (MAX_BYTES + 1), "feature")
        self.git("push", "-q", "origin", "HEAD:refs/heads/feature")
        scanner = self.fresh_scanner(remote)
        result = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, after))), "--event-name", "push")
        self.assertEqual(result.returncode, 1)
        self.assertIn("5.00 MiB", result.stdout)
        self.assertIn("result=fail", result.stdout)

    def test_zero_before_checks_early_large_file_across_multiple_commits(self) -> None:
        remote = self.make_bare_remote()
        self.commit_file("early-large.bin", b"x" * (MAX_BYTES + 1), "early large")
        after = self.commit_file("later.txt", b"small", "later")
        self.git("push", "-q", "origin", "HEAD:refs/heads/feature")
        scanner = self.fresh_scanner(remote)
        result = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, after))), "--event-name", "push")
        self.assertEqual(result.returncode, 1)
        self.assertIn("early-large.bin", result.stdout)

    def test_zero_before_uses_actual_merge_base_after_default_advances(self) -> None:
        remote = self.make_bare_remote()
        feature_base = self.rev("HEAD")
        self.commit_file("default-only.txt", b"default", "default advance")
        advanced_default = self.rev("HEAD")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", "feature", feature_base)
        after = self.commit_file("feature-only.txt", b"feature", "feature")
        self.git("push", "-q", "origin", "feature")
        scanner = self.fresh_scanner(remote)
        result = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, after))), "--event-name", "push")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"base={feature_base}", result.stdout)
        self.assertNotIn(f"base={advanced_default}", result.stdout)
        self.assertIn("target_count=1", result.stdout)

    def test_zero_before_ignores_inherited_unmodified_large_blob(self) -> None:
        self.commit_file("inherited-large.bin", b"x" * (MAX_BYTES + 1), "large on default")
        remote = self.make_bare_remote()
        self.git("checkout", "-q", "-b", "feature")
        after = self.commit_file("feature.txt", b"small", "feature")
        self.git("push", "-q", "origin", "feature")
        scanner = self.fresh_scanner(remote)
        result = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, after))), "--event-name", "push")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("target_count=1", result.stdout)

    def test_zero_before_default_branch_and_unrelated_history_fail_closed(self) -> None:
        remote = self.make_bare_remote()
        scanner = self.fresh_scanner(remote)
        default_event = self.push_event(ZERO_SHA, self.rev("HEAD"), ref="refs/heads/main")
        default_branch = self.cli_in(
            scanner, "--event-path", str(self.event_file(default_event)), "--event-name", "push"
        )
        self.assertNotEqual(default_branch.returncode, 0)
        self.assertIn("default branch", default_branch.stderr)
        tag_event = self.push_event(ZERO_SHA, self.rev("HEAD"), ref="refs/tags/v1")
        tag_push = self.cli_in(scanner, "--event-path", str(self.event_file(tag_event)), "--event-name", "push")
        self.assertNotEqual(tag_push.returncode, 0)
        self.assertIn("valid branch ref", tag_push.stderr)

        unrelated = Path(self.temp.name) / "unrelated"
        unrelated.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=unrelated, check=True)
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=unrelated, check=True)
        subprocess.run(["git", "config", "user.name", "large-files tests"], cwd=unrelated, check=True)
        (unrelated / "unrelated.txt").write_text("unrelated", encoding="utf-8")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=unrelated, check=True)
        subprocess.run(["git", "commit", "-qm", "unrelated"], cwd=unrelated, check=True)
        unrelated_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=unrelated, text=True, capture_output=True, check=True).stdout.strip()
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=unrelated, check=True)
        subprocess.run(["git", "push", "-q", "origin", "HEAD:refs/heads/unrelated"], cwd=unrelated, check=True)
        no_common = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, unrelated_after))), "--event-name", "push")
        self.assertNotEqual(no_common.returncode, 0)
        self.assertIn("no common ancestor", no_common.stderr)

    def test_invalid_missing_and_unfetchable_event_bases_fail_closed(self) -> None:
        after = self.rev("HEAD")
        invalid = self.event_cli("push", self.push_event("not-a-sha", after))
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("invalid push before SHA", invalid.stderr)
        missing = self.event_cli("pull_request", {"pull_request": {"head": {"sha": after}}})
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("missing pull request base", missing.stderr)
        remote = self.make_bare_remote()
        scanner = self.fresh_scanner(remote)
        unknown = "f" * 40
        fetch_failed = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, unknown))), "--event-name", "push")
        self.assertNotEqual(fetch_failed.returncode, 0)
        self.assertIn("cannot resolve push after commit", fetch_failed.stderr)

        known_after = self.rev("HEAD")
        unavailable_before = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(unknown, known_after))), "--event-name", "push")
        self.assertNotEqual(unavailable_before.returncode, 0)
        self.assertIn("cannot resolve push before commit", unavailable_before.stderr)
        unavailable_default = self.cli_in(scanner, "--event-path", str(self.event_file(self.push_event(ZERO_SHA, known_after, "does-not-exist"))), "--event-name", "push")
        self.assertNotEqual(unavailable_default.returncode, 0)
        self.assertIn("cannot fetch repository.default_branch", unavailable_default.stderr)

    def test_invalid_event_json_and_deletion_fail_cleanly(self) -> None:
        path = self.repo / "event.json"
        path.write_text("{", encoding="utf-8")
        malformed = self.cli("--event-path", str(path), "--event-name", "push")
        self.assertNotEqual(malformed.returncode, 0)
        self.assertIn("invalid event JSON", malformed.stderr)
        deletion = self.event_cli("push", self.push_event(self.rev("HEAD"), ZERO_SHA))
        self.assertNotEqual(deletion.returncode, 0)
        self.assertIn("deletion", deletion.stderr)


if __name__ == "__main__":
    unittest.main()
