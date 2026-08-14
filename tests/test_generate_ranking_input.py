from scripts.generate_ranking_input import (
    apply_quality_gate,
    is_ai_relevant_item,
    is_denied_title,
    title_has_ai_signal,
)


def _item(title, *, blurb="", stars=4, category="tech", raw_category=None):
    return {
        "title": title,
        "blurb": blurb,
        "stars": stars,
        "category": category,
        "raw_category": raw_category if raw_category is not None else category,
        "source": {"name": "test"},
    }


def test_taalas_triple_collapses():
    items = [
        _item(
            "AMD、Taalas買収によりシリコンへのモデル刻み込みで推論性能向上を目指す",
            blurb="AMDがTaalasを買収",
            stars=4,
            category="hardware",
        ),
        _item(
            "AMD、Taalas買収によりシリコンにモデルを刻み込み、推論性能向上を目指す",
            blurb="AMDがシリコンへのモデル刻み込み技術を持つTaalasを買収し、AI推論のパフォーマンス向上を図る。",
            stars=4,
            category="hardware",
        ),
        _item(
            "AMD、AIモデルの基盤を半導体に組み込むTaalas買収へ",
            blurb="AMDがAI推論特化チップ開発企業Taalasを買収。AIモデルの構造を半導体に直接組み込み、高速化を目指す。",
            stars=4,
            category="hardware",
        ),
    ]
    kept, dropped = apply_quality_gate(items)
    assert len(kept) == 1
    assert "Taalas" in kept[0]["title"]
    assert sum(1 for d in dropped if d.get("dropped_as") == "duplicate") == 2


def test_kumamoto_dropped_even_when_mislabeled_ai_model():
    item = _item(
        "熊本県で最大震度7の地震発生、M7．1と推定",
        blurb="熊本県宇城市を震源とするM7．1の地震が発生。宇城市・氷川町で震度7観測。",
        stars=5,
        category="tech",
        raw_category="AI Model",
    )
    assert is_denied_title(item["title"])
    assert not is_ai_relevant_item(item)
    kept, dropped = apply_quality_gate([item])
    assert kept == []
    assert dropped[0]["dropped_as"] == "denylist"


def test_writing_by_hand_dropped_brain_ai_substring():
    title = "Writing by hand is good for your brain"
    assert "ai" in title.lower()  # brain contains ai — must not count
    assert not title_has_ai_signal(title)
    item = _item(
        title,
        blurb="手書きが脳に与える認知的メリット。AIツール普及で手書き機会が激減する現代に逆張り。",
        stars=4,
        category="ai technology",
        raw_category="AI Technology",
    )
    assert not is_ai_relevant_item(item)
    kept, _ = apply_quality_gate([item])
    assert kept == []


def test_retailers_like_false_positive_dropped():
    title = "Local retailers report strong weekend sales"
    assert "ai" in title.lower()  # retailers contains ai — must not count
    assert not title_has_ai_signal(title)
    item = _item(title, blurb="Store traffic rose after a holiday campaign.", stars=3, category="biz")
    assert not is_ai_relevant_item(item)
    kept, dropped = apply_quality_gate([item])
    assert kept == []
    assert dropped[0]["dropped_as"] == "not_ai"


def test_grok_bot_kept():
    item = _item(
        "Grok Bot：専用クラウドPCを持つ常時稼働AI同僚——チャットから「チーム」へ",
        blurb="xAIがEarly beta公開。Botごとに持続するクラウドPCを持ち、仕事を完遂する常時稼働AI同僚。",
        stars=5,
        category="tech",
    )
    assert title_has_ai_signal(item["title"])
    assert is_ai_relevant_item(item)
    kept, dropped = apply_quality_gate([item])
    assert len(kept) == 1
    assert "Grok Bot" in kept[0]["title"]
    assert dropped == []


def test_kioxia_earnings_dropped_even_with_ai_demand_token():
    title = 'キオクシア、大幅増益 - AI需要拡大が牽引'
    assert title_has_ai_signal(title)  # AI token would otherwise keep it
    assert is_denied_title(title)
    assert is_denied_title("Kioxia posts record profit as AI demand surges")
    item = _item(
        title,
        blurb='キオクシアの業績が前年比4倍超で記録的大幅増益に。AIサーバ需要急増が主要因。',
        stars=5,
        category="biz",
        raw_category="Business",
    )
    assert not is_ai_relevant_item(item)
    kept, dropped = apply_quality_gate([item])
    assert kept == []
    assert dropped[0]["dropped_as"] == "denylist"

