from wiki_query import WikiQuery


def test_default_wiki_root_is_in_repo():
    wq = WikiQuery()
    assert wq.entities_dir.exists(), "wiki/entities must exist in-repo"


def test_search_entities_returns_scored_results():
    wq = WikiQuery()
    results = wq.search_entities("descriptor")
    assert isinstance(results, list)
    assert all("match_score" in r and "title" in r for r in results)
    # sorted descending by score
    scores = [r["match_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_title_is_real_not_frontmatter_delimiter():
    """Regression: title was being read as the YAML '---' delimiter."""
    wq = WikiQuery()
    results = wq.search_entities("bBootLunEn")
    assert results, "bBootLunEn should match the attributes entity"
    top = results[0]
    assert top["title"] not in ("---", ""), f"bad title: {top['title']!r}"


def test_search_surfaces_real_spec_content_for_bbootlunen():
    """Regression: definition was always empty (looked for missing 'Definition' heading)."""
    wq = WikiQuery()
    results = wq.search_entities("bBootLunEn")
    top = results[0]
    blob = (top.get("definition", "") + " " + " ".join(top.get("matched_lines", []))).lower()
    # the real spec values for bBootLunEn must surface
    assert "boot lu" in blob or "bbootlunen" in blob, f"no spec content surfaced: {blob[:120]!r}"
