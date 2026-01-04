def test_fix():
    # "繧､繝ｳ繝・Μ繧ｸ繧ｧ繝ｳ繧ｹ" is "インテリジェンス" (UTF-8) read as SJIS
    mojibake = "繧､繝ｳ繝・Μ繧ｸ繧ｧ繝ｳ繧ｹ"
    try:
        # Encode back to SJIS bytes
        bytes_sjis = mojibake.encode('shift-jis')
        # Decode correctly as UTF-8
        fixed = bytes_sjis.decode('utf-8')
        print(f"Original: {mojibake}")
        print(f"Fixed:    {fixed}")
    except Exception as e:
        print(f"Error: {e}")

test_fix()
