from __future__ import annotations

import json
import re
import unittest
from html import unescape
from pathlib import Path

from src.auto_collect.claim_evidence import normalized_text, validate_bundle
from scripts.render_claim_evidence import visible_text


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "presentations" / "ai_coding_agents_guide.html"
ABOUT = ROOT / "about.html"

GUIDE_IDS = {
    "G-SBX-01", "G-SBX-02", "G-HOOK-01", "G-HOOK-02",
    "G-PRICE-01", "G-PRICE-02", "G-PRICE-03", "G-PRICE-04",
    "G-PERF-01", "G-PERF-02", "G-PERF-03", "G-PERF-04",
    "G-USE-01", "G-USE-02", "G-USE-03", "G-USE-04", "G-USE-05",
    "G-USE-06", "G-USE-07", "G-USE-08", "G-USE-09", "G-USE-10",
}
ABOUT_IDS = {
    "G-ABOUT-01", "G-ABOUT-02", "G-ABOUT-03", "G-ABOUT-04",
    "G-ABOUT-05", "G-ABOUT-06",
}


class GuidePolicyEvidenceTest(unittest.TestCase):
    def test_pages_embed_valid_claim_bundles_and_bind_each_statement_once(self) -> None:
        self._assert_page_contract(GUIDE, GUIDE_IDS)
        self._assert_page_contract(ABOUT, ABOUT_IDS)

    def test_guide_replaces_all_star_scores_with_condition_checks(self) -> None:
        html = GUIDE.read_text(encoding="utf-8")
        self.assertNotIn("&#9733;", html)
        self.assertIn("選択前に確認する条件", html)
        self.assertIn("安全性の順位は表示しません", html)
        for claim_id in sorted(item for item in GUIDE_IDS if item.startswith("G-USE-")):
            self.assertIn(f'data-claim-id="{claim_id}"', html)

    def test_guide_places_each_evidence_block_with_its_bound_body(self) -> None:
        html = GUIDE.read_text(encoding="utf-8")
        for claim_id in (
            "G-PERF-01", "G-PERF-02", "G-PERF-03", "G-PERF-04",
            "G-PRICE-01", "G-PRICE-02", "G-PRICE-03", "G-PRICE-04",
            "G-SBX-01", "G-HOOK-01", "G-HOOK-02",
        ):
            self.assertRegex(
                html,
                rf'<td><span data-claim-id="{claim_id}">.*?</span><div data-evidence-for="{claim_id}">',
                claim_id,
            )
        self.assertRegex(
            html,
            r'<span data-claim-id="G-SBX-02">.*?</span><div data-evidence-for="G-SBX-02">',
        )
        for claim_id in sorted(item for item in GUIDE_IDS if item.startswith("G-USE-")):
            self.assertRegex(
                html,
                rf'<tr data-claim-id="{claim_id}">.*?</tr>\s*<tr><td colspan="3"><div data-evidence-for="{claim_id}">',
                claim_id,
            )

    def test_about_separates_policy_from_unrecorded_operational_guarantees(self) -> None:
        html = ABOUT.read_text(encoding="utf-8")
        self.assertNotIn("100%</div><div class=\"lbl\">一次ソース引用率", html)
        self.assertNotIn("公開前に運営者（人間）が全件レビュー", html)
        self.assertIn("方針", html)
        self.assertIn("記録", html)
        self.assertIn("記録がないことは、未実施の証明ではありません", html)

    def test_about_explains_evidence_labels_statuses_and_dates_in_visible_text(self) -> None:
        text = visible_text(ABOUT.read_text(encoding="utf-8"))
        self.assertIn("情報区分であり、信頼度や真偽の保証ではありません", text)
        for label in (
            "公式仕様・公式発表", "ベンダー公称値", "第三者の測定", "報道",
            "運営者による実測", "編集者の見解・推奨", "資料との照合済み",
            "一部のみ裏付けあり", "未確認・根拠未登録", "資料間に不一致あり",
        ):
            self.assertIn(label, text)
        for meaning in (
            "公式の性能公称は第三者実測ではありません", "Cognition の自社ベンチマーク",
            "AIによる資料照合は人によるレビューではありません", "HTTP 200、ビルド、リンク確認で確認日を自動代入しません",
            "本文または条件が変われば、再照合が必要です", "全サイトへの適用済みを意味しません",
            "本文全文を保存せず", "何を支えるか（support）",
        ):
            self.assertIn(meaning, text)

    def _assert_page_contract(self, path: Path, expected_ids: set[str]) -> None:
        html = path.read_text(encoding="utf-8")
        self.assertIn('/assets/claim-evidence.css', html)
        match = re.search(
            r'<script type="application/json" id="claim-evidence-data">\s*(.*?)\s*</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match, path.name)
        bundle = json.loads(match.group(1))
        self.assertEqual(validate_bundle(bundle), [], path.name)
        claims = bundle["claims"]
        self.assertEqual({claim["id"] for claim in claims}, expected_ids)
        for claim in claims:
            claim_id = claim["id"]
            self.assertEqual(html.count(f'data-claim-id="{claim_id}"'), 1, claim_id)
            self.assertEqual(html.count(f'data-evidence-for="{claim_id}"'), 1, claim_id)
            statement = normalized_text(unescape(claim["statement"]))
            self.assertIn(statement, normalized_text(unescape(html)), claim_id)


if __name__ == "__main__":
    unittest.main()
