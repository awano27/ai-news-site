from src.auto_collect import report_dashboard as rd


def _item(title, source="GIGAZINE", summary=""):
    return {"title": title, "tldr": "", "summary": summary, "source": source}


def test_title_decides_theme_before_incidental_summary_words():
    item = _item("新エージェント基盤を公開", summary="攻撃耐性も評価した")
    assert rd.classify_theme(item) == "agents"


def test_arxiv_without_specific_topic_is_research():
    assert rd.classify_theme(_item("Efficient contrastive decoding", source="arXiv (cs.CL)")) == "research"
    assert rd.classify_theme(_item("ロボット把持のベンチマーク", source="arXiv (cs.RO)")) == "robotics"


def test_dashboard_flags_theme_far_above_recent_average():
    headlines = [_item("パスワード流出"), _item("脆弱性を修正"), _item("詐欺グループ摘発"), _item("新モデル発表")]
    themes = [rd.classify_theme(h) for h in headlines]
    history = [{"date": f"2026-10-0{d}", "counts": {"models": 3}} for d in range(1, 8)]

    dash = rd.build_dashboard("2026-10-08", headlines, themes, {}, tools_count=0, history=history)

    assert dash["lead"] == "security"
    assert dash["rising"] == ["security"]
    assert "セキュリティ・不正」3件（直近7日平均 0件）" in rd.brief_sentence(dash)
    html = rd.render_dashboard(dash)
    assert 'href="#sig-01"' in html and 'data-theme="security"' in html
