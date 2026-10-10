"""Offline regressions for the curated catalog's visible tool counts.

Runs the page's real filtering JavaScript against a minimal DOM adapter.
No network calls or package installation are needed (Python + Node.js).
"""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "presentations/recommended_tools/index.html"


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.card = None
        self.in_name = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "tool-card" in attrs.get("class", "").split():
            self.card = {
                "name": "",
                "text": "",
                "tags": attrs.get("data-tags", ""),
                "roles": attrs.get("data-roles", ""),
            }
            self.cards.append(self.card)
        elif tag == "h3" and self.card is not None:
            self.in_name = True

    def handle_endtag(self, tag):
        if tag == "article":
            self.card = None
        elif tag == "h3":
            self.in_name = False

    def handle_data(self, data):
        if self.card is not None:
            self.card["text"] += data
            if self.in_name:
                self.card["name"] += data


class ToolCatalogIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = CATALOG.read_text(encoding="utf-8")
        parser = CatalogParser()
        parser.feed(cls.html)
        cls.cards = parser.cards
        cls.script = next(
            script for script in re.findall(r"<script>(.*?)</script>", cls.html, re.S)
            if "function applyFilters()" in script
        )

    def run_filter(self, query="", purpose="all", role="all"):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is required to execute the catalog JavaScript")
        # Only the browser boundary is adapted. The entire unmodified page
        # script runs, including recent tags, event handlers and applyFilters.
        adapter = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
function element() {
  return {textContent: '', style: {}, handlers: {},
    addEventListener(event, callback) { this.handlers[event] = callback; }};
}
const ids = Object.fromEntries(['searchInput', 'purposeRow', 'roleRow',
  'resultMeta', 'emptyState'].map(id => [id, element()]));
ids.searchInput.value = input.query;
const cards = input.cards.map(card => ({
  textContent: card.text, dataset: {tags: card.tags, roles: card.roles}, style: {},
  querySelector(selector) { return selector === 'h3' ? {textContent: card.name} : null; }
}));
const document = {
  getElementById(id) { return ids[id]; },
  querySelectorAll(selector) { return selector === '.tool-card' ? cards : []; }
};
vm.runInNewContext(input.script, {document});
function select(id, key, value) {
  ids[id].handlers.click({target: {closest() {return {dataset: {[key]: value}};}}});
}
select('purposeRow', 'filter', input.purpose);
select('roleRow', 'role', input.role);
process.stdout.write(JSON.stringify({
  summary: ids.resultMeta.textContent,
  emptyDisplay: ids.emptyState.style.display,
  visible: cards.filter(card => card.style.display !== 'none').length
}));
"""
        result = subprocess.run(
            [node, "-e", adapter],
            input=json.dumps({"script": self.script, "cards": self.cards,
                              "query": query, "purpose": purpose, "role": role}),
            text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)

    def test_badge_matches_distinct_catalog_names(self):
        badge = re.search(r'class="hero-badge">(\d+)ツール</span>', self.html)
        self.assertIsNotNone(badge)
        names = {card["name"].strip() for card in self.cards}
        self.assertTrue(names)
        self.assertEqual(int(badge.group(1)), len(names))

    def test_all_tools_counts_featured_repeats_once(self):
        result = self.run_filter()
        unique = len({card["name"].strip() for card in self.cards})
        self.assertEqual(result["visible"], len(self.cards))
        self.assertEqual(result["summary"], f"表示ツール: {unique}件（{len(self.cards)}カード）")
        self.assertEqual(result["emptyDisplay"], "none")

    def test_search_counts_repeated_tool_once(self):
        result = self.run_filter(query="orca")
        matching = [card for card in self.cards if "orca" in card["text"].lower()]
        unique = len({card["name"].strip() for card in matching})
        self.assertGreater(len(matching), unique)
        self.assertEqual(result["summary"], f"表示ツール: {unique}件（{len(matching)}カード）")

    def test_purpose_and_role_filters_keep_real_card_visibility(self):
        result = self.run_filter(purpose="meeting", role="biz")
        matching = [card for card in self.cards if "meeting" in card["tags"].split(",")]
        unique = len({card["name"].strip() for card in matching})
        self.assertEqual(result["visible"], len(matching))
        self.assertEqual(result["summary"], f"表示ツール: {unique}件（{len(matching)}カード）")

    def test_unmatched_search_shows_zero_and_empty_state(self):
        result = self.run_filter(query="not-a-real-tool-catalog-fixture-2026")
        self.assertEqual(result["summary"], "表示ツール: 0件（0カード）")
        self.assertEqual(result["visible"], 0)
        self.assertEqual(result["emptyDisplay"], "block")


if __name__ == "__main__":
    unittest.main()
