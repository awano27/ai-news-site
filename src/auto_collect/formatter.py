"""Format processed articles into enhanced input/day/MMDD.txt format.

Output structure:
  Section 1: ヘッドライン速報 (top 5 news)
  Section 2: 市場・資金動向 (funding/M&A)
  Section 3: GitHub Trending (trending repos)
  Section 4: HuggingFace注目モデル (trending models)
"""

import logging
from datetime import date
from pathlib import Path
from typing import List, Dict

from .config import MAX_ARTICLES_IN_REPORT

logger = logging.getLogger(__name__)


class DayFileFormatter:
    """Format articles with evidence into enhanced MMDD.txt."""

    def write(self, articles: List[Dict], output_path: Path, target_date: date,
              github_articles: List[Dict] = None,
              benchmark_articles: List[Dict] = None,
              funding_articles: List[Dict] = None):
        """Write multi-section daily report."""
        if not articles and not github_articles:
            logger.warning("[Formatter] No articles to write")
            return

        date_str = target_date.strftime("%Y年%m月%d日")
        top_articles = articles[:MAX_ARTICLES_IN_REPORT]

        lines = []

        # Title
        top_title = top_articles[0]["title"] if top_articles else "本日のAIニュース"
        lines.append(f"{date_str}のAIニュース速報 - {top_title}")
        lines.append("")

        # === Section 1: ヘッドライン速報 ===
        lines.append("=" * 50)
        lines.append(f"📰 ヘッドライン速報（{len(top_articles)}件）")
        lines.append("=" * 50)
        lines.append("")

        for article in top_articles:
            lines.extend(self._format_article(article))

        # === Section 2: 市場・資金動向 ===
        if funding_articles:
            top_funding = [a for a in funding_articles if a.get("score", 0) >= 50][:5]
            if top_funding:
                lines.append("=" * 50)
                lines.append(f"💰 市場・資金動向（{len(top_funding)}件）")
                lines.append("=" * 50)
                lines.append("")

                for article in top_funding:
                    lines.extend(self._format_article(article))

        # === Section 3: GitHub Trending ===
        if github_articles:
            top_github = github_articles[:5]
            if top_github:
                lines.append("=" * 50)
                lines.append(f"🔥 GitHub Trending AI/ML（{len(top_github)}件）")
                lines.append("=" * 50)
                lines.append("")

                for repo in top_github:
                    lines.extend(self._format_github_repo(repo))

        # === Section 4: HuggingFace注目モデル ===
        if benchmark_articles:
            top_models = benchmark_articles[:5]
            if top_models:
                lines.append("=" * 50)
                lines.append(f"🤗 HuggingFace注目モデル（{len(top_models)}件）")
                lines.append("=" * 50)
                lines.append("")

                for model in top_models:
                    lines.extend(self._format_model(model))

        # Write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"[Formatter] Wrote report to {output_path}")

    def _format_article(self, article: Dict) -> List[str]:
        """Format a single article with evidence."""
        lines = []
        title = article["title"]
        score = article.get("score", 0)
        category = article.get("category", "")
        tldr = article.get("tldr", "")
        summary = article.get("summary", "")
        points = article.get("points", [])
        url = article.get("url", "")
        source = article.get("source", "")
        hn_score = article.get("hn_score")
        evidence = article.get("evidence", {})

        lines.append(f"■ {title}（{category} / スコア: {score}）")

        if source:
            lines.append(f"  ソース: {source}")

        if tldr:
            lines.append(f"  🎯 TL;DR: {tldr}")

        if summary:
            lines.append(f"  {summary}")

        for point in points[:5]:
            p = point if point.startswith("・") else f"・{point}"
            lines.append(f"  {p}")

        # Evidence layer
        metrics = [m for m in evidence.get("metrics", []) if m]
        if metrics:
            lines.append(f"  📊 数値: {' / '.join(metrics)}")

        competitors = [c for c in evidence.get("competitors", []) if c]
        if competitors:
            lines.append(f"  🔄 競合: {', '.join(competitors)}")

        impact = evidence.get("impact_ja", "")
        if impact:
            lines.append(f"  🇯🇵 影響: {impact}")

        actionable = evidence.get("actionable", "")
        if actionable:
            lines.append(f"  ⚡ 今すぐ: {actionable}")

        evidence_label = evidence.get("evidence_label", "")
        if evidence_label:
            lines.append(f"  🏷️ Label: {evidence_label}")

        if hn_score:
            lines.append(f"  HN Score: {hn_score}")

        if url:
            lines.append(f"  URL: {url}")

        lines.append("")
        return lines

    def _format_github_repo(self, repo: Dict) -> List[str]:
        """Format a GitHub trending repo."""
        lines = []
        title = repo["title"]
        summary = repo.get("summary", "")
        url = repo.get("url", "")
        evidence = repo.get("evidence", {})

        metrics = [m for m in evidence.get("metrics", []) if m]
        metrics_str = " / ".join(metrics) if metrics else ""
        license_str = evidence.get("license", "")

        lines.append(f"■ {title}")
        if summary:
            lines.append(f"  {summary}")
        if metrics_str:
            lines.append(f"  📊 {metrics_str}")
        if license_str:
            lines.append(f"  📄 License: {license_str}")

        actionable = evidence.get("actionable", "")
        if actionable:
            lines.append(f"  ⚡ {actionable}")

        topics = evidence.get("topics", [])
        if topics:
            lines.append(f"  🏷️ {', '.join(topics)}")

        if url:
            lines.append(f"  URL: {url}")

        lines.append("")
        return lines

    def _format_model(self, model: Dict) -> List[str]:
        """Format a HuggingFace trending model."""
        lines = []
        title = model["title"]
        url = model.get("url", "")
        evidence = model.get("evidence", {})

        metrics = [m for m in evidence.get("metrics", []) if m]
        metrics_str = " / ".join(metrics) if metrics else ""

        lines.append(f"■ {title}")
        if metrics_str:
            lines.append(f"  📊 {metrics_str}")

        impact = evidence.get("impact_ja", "")
        if impact:
            lines.append(f"  {impact}")

        actionable = evidence.get("actionable", "")
        if actionable:
            lines.append(f"  ⚡ {actionable}")

        if url:
            lines.append(f"  URL: {url}")

        lines.append("")
        return lines
