"""Semantic validation for generated daily-report publication artifacts."""

from __future__ import annotations

import json
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


class _ReportDateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.report_dates: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "meta":
            return
        values = {name.lower(): value for name, value in attrs if value is not None}
        if values.get("name", "").lower() == "report:date":
            self.report_dates.append(values.get("content", ""))


def _load_json(path: Path, relative_path: str, errors: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"invalid JSON artifact {relative_path}: {error}")
        return None


def _expect_date(
    data: Any, field: str, expected: str, relative_path: str, errors: list[str]
) -> None:
    if not isinstance(data, dict) or data.get(field) != expected:
        errors.append(
            f"artifact date mismatch for {relative_path}: expected {field}={expected}"
        )


def _expect_report_membership(
    data: Any,
    report_date: date,
    relative_path: str,
    errors: list[str],
) -> None:
    expected_date = report_date.isoformat()
    expected_file = f"auto_daily_report_{report_date:%Y_%m_%d}.html"
    if not isinstance(data, dict):
        errors.append(f"artifact must be a JSON object: {relative_path}")
        return
    if data.get("generated") != expected_date:
        errors.append(
            f"artifact date mismatch for {relative_path}: expected generated={expected_date}"
        )
    reports = data.get("reports")
    if not isinstance(reports, list) or not any(
        isinstance(item, dict)
        and item.get("date") == expected_date
        and item.get("file") == expected_file
        for item in reports
    ):
        errors.append(
            f"artifact is missing current report membership: {relative_path}"
        )


def validate_output_artifact(
    project_root: Path, relative_path: str, report_date: date
) -> list[str]:
    """Return semantic errors for one required daily-report artifact.

    Freshness and hashes establish provenance. These checks establish that the
    newly written bytes are a usable artifact for the requested report date.
    """

    errors: list[str] = []
    path = project_root / relative_path
    if not path.is_file():
        return [f"missing required artifact: {relative_path}"]
    try:
        if path.stat().st_size <= 0 or not path.read_bytes().strip():
            return [f"empty required artifact: {relative_path}"]
    except OSError as error:
        return [f"could not read required artifact {relative_path}: {error}"]

    expected_date = report_date.isoformat()
    if path.suffix.lower() == ".html":
        try:
            parser = _ReportDateParser()
            parser.feed(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as error:
            return [f"could not read HTML artifact {relative_path}: {error}"]
        if parser.report_dates != [expected_date]:
            errors.append(
                f"HTML report date mismatch for {relative_path}: expected {expected_date}"
            )
        return errors

    if path.suffix.lower() != ".json":
        if relative_path == f"input/day/{report_date:%m%d}.txt":
            try:
                first_line = path.read_text(encoding="utf-8").splitlines()[0]
            except (OSError, UnicodeError, IndexError) as error:
                return [f"could not read report text {relative_path}: {error}"]
            localized_date = report_date.strftime("%Y年%m月%d日")
            if localized_date not in first_line:
                errors.append(
                    f"report text date mismatch for {relative_path}: expected {localized_date}"
                )
        return errors

    data = _load_json(path, relative_path, errors)
    if data is None:
        return errors

    dated_objects = {
        "presentations/auto_daily_report.json",
        "public-pages/api/auto_daily_report/latest.json",
        "daily-news/data.json",
        f"public-pages/news/{expected_date}.json",
    }
    if relative_path in dated_objects:
        _expect_date(data, "date", expected_date, relative_path, errors)

    if relative_path == f"public-pages/news/{expected_date}.json":
        if not isinstance(data, dict) or not isinstance(data.get("items"), list) or not data["items"]:
            errors.append(f"archive JSON has no current report items: {relative_path}")
    elif relative_path == "public-pages/news/archive_index.json":
        if not isinstance(data, list) or not any(
            isinstance(item, dict)
            and item.get("date") == expected_date
            and item.get("file") == f"{expected_date}.json"
            for item in data
        ):
            errors.append(
                f"archive index is missing current report membership: {relative_path}"
            )
    elif relative_path in {
        "presentations/daily_reports/index.json",
        "presentations/daily_reports/searchable.json",
    }:
        _expect_report_membership(data, report_date, relative_path, errors)
    elif relative_path == "public-pages/news/version.json":
        if not isinstance(data, dict) or not isinstance(data.get("updated"), str):
            errors.append(f"archive version artifact is invalid: {relative_path}")

    return errors


def validate_output_artifacts(
    project_root: Path, relative_paths: Iterable[str], report_date: date
) -> list[str]:
    errors: list[str] = []
    for relative_path in relative_paths:
        errors.extend(validate_output_artifact(project_root, relative_path, report_date))
    return errors
