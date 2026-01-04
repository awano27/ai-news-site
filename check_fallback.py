with open(r"C:\develop\ai-news-site\src\generators\day_news_slide_generator.py", "rb") as f:
    content = f.read()
    # Find all occurrences of "return \"AI"
    import re
    matches = [m.start() for m in re.finditer(b"return \\\"AI", content)]
    for i, idx in enumerate(matches):
        print(f"Occurrence {i} at {idx}")
        snippet = content[idx:idx+100]
        print(f"Snippet {i}:", snippet)
        print(f"Hex {i}:", snippet.hex())
