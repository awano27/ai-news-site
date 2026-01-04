with open(r"C:\develop\ai-news-site\src\generators\day_news_slide_generator.py", "rb") as f:
    content = f.read()
    print("Length:", len(content))
    # Look for the fallback summary part
    idx = content.find(b"return \"AI")
    if idx != -1:
        print("Found AI at", idx)
        # Print next 50 bytes
        snippet = content[idx:idx+50]
        print("Snippet:", snippet)
        print("Hex:", snippet.hex())
