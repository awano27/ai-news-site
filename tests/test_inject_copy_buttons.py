from scripts.inject_copy_buttons import build_block, has_target, is_cmd


def test_has_target_code_and_cmd():
    assert has_target('<p>run <code>uv add nooa</code></p>')
    assert has_target('<span class="cmd">npx foo</span>')
    assert not has_target("<p>no commands here</p><pre>plain</pre>")


def test_is_cmd_prefix_or_long_oneliner_but_not_url():
    assert is_cmd("npx @truefoundry/trueforge")
    assert is_cmd("uv add nooa")
    assert is_cmd("claude")
    assert not is_cmd("nooa")
    assert not is_cmd("...")
    assert not is_cmd("grok.com/imagine")
    assert not is_cmd("https://example.com/install.sh")
    assert not is_cmd("コマンド例ですよ")


def test_block_is_self_contained_and_stable():
    a, b = build_block(), build_block()
    assert a == b
    assert "<!-- copy-btn:start -->" in a
    assert "<!-- copy-btn:end -->" in a
    assert "slide-nav" not in a
    assert "</script>" in a
    assert a.count("<script>") == 1
