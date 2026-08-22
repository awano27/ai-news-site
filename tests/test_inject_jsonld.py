from scripts.inject_jsonld import desired_payload, is_article_block, is_complete


KEEP = {
    "headline": "Ox Alpha",
    "description": "stealth frontier",
    "datePublished": "2026-08-21",
    "dateModified": "2026-08-21",
    "articleSection": "AI Models",
}


def test_desired_keeps_existing_fields_and_adds_missing():
    existing = {"@context": "https://schema.org", "@type": "PresentationDigitalDocument", **KEEP}
    out = desired_payload(
        existing,
        og_image="https://visionhub.jp/x.jpg",
        canonical="https://visionhub.jp/presentations/day_slides/day_slide_2026_08_21.html",
    )
    for key, value in KEEP.items():
        assert out[key] == value
    assert out["@type"] == ["PresentationDigitalDocument", "NewsArticle"]
    assert out["author"]["name"] == "AI Intelligence Hub"
    assert out["publisher"]["url"] == "https://visionhub.jp/"
    assert out["image"] == "https://visionhub.jp/x.jpg"
    assert out["inLanguage"] == "ja"
    assert out["mainEntityOfPage"].endswith("day_slide_2026_08_21.html")


def test_does_not_overwrite_existing_author():
    existing = {
        "@type": "NewsArticle",
        "headline": "H",
        "author": {"@type": "Person", "name": "awano27"},
    }
    out = desired_payload(existing, og_image=None, canonical="https://visionhub.jp/x")
    assert out["author"] == {"@type": "Person", "name": "awano27"}
    assert "PresentationDigitalDocument" in out["@type"]
    assert "NewsArticle" in out["@type"]
    assert "image" not in out


def test_complete_requires_both_types():
    data = desired_payload(
        {"@type": "NewsArticle", "headline": "H"},
        og_image=None,
        canonical="https://visionhub.jp/x",
    )
    assert is_complete(data, None)
    assert is_article_block(data)
    assert not is_complete({"@type": "NewsArticle", "author": {}, "publisher": {}, "mainEntityOfPage": "u", "inLanguage": "ja"}, None)
