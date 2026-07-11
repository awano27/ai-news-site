from pathlib import Path
import re


ARCHIVE = Path(__file__).resolve().parents[1] / "presentations" / "news_archive.html"


def test_archive_feature_cards_describe_only_supported_behavior():
    html = ARCHIVE.read_text(encoding="utf-8")
    grid = re.search(
        r'<div class="features-grid"(?P<attrs>[^>]*)>(?P<body>.*?)</div>\s*\n\s*</div>\s*\n\s*<div class="related">',
        html,
        re.DOTALL,
    )

    assert grid is not None
    assert "hidden" not in grid.group("attrs")

    assert grid.group("body").count('<div class="feature-card">') == 6

    copy = re.sub(r"<[^>]+>", " ", grid.group("body"))
    required_phrases = (
        "キーワード検索",
        "カテゴリ絞り込み",
        "日付範囲指定",
        "条件の組み合わせ",
        "日次ニュースの集約",
        "50件ずつ追加表示",
    )
    for phrase in required_phrases:
        assert phrase in copy

    assert "日次ニュースデータをまとめて確認できます。" in copy

    unsupported_phrases = ("重要度", "リアルタイム", "07:00", "4カテゴリ", "新しい日付順")
    for phrase in unsupported_phrases:
        assert phrase not in copy
