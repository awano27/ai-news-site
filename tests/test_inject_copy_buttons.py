from scripts.inject_copy_buttons import build_block, has_target


def test_has_target_code_and_cmd():
    assert has_target('<p>run <code>uv add nooa</code></p>')
    assert has_target('<span class="cmd">npx foo</span>')
    assert not has_target("<p>no commands here</p><pre>plain</pre>")


def test_block_is_self_contained_and_stable():
    a, b = build_block(), build_block()
    assert a == b
    assert "<!-- copy-btn:start -->" in a
    assert "<!-- copy-btn:end -->" in a
    assert "slide-nav" not in a
    assert "</script>" in a
    assert a.count("<script>") == 1
