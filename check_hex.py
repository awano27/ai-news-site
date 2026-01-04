with open(r"C:\develop\ai-news-site\src\generators\day_news_slide_generator.py", "rb") as f:
    content = f.read()
    # Find the approximate area
    start = content.find(b"def _extract_summary")
    if start != -1:
        end = content.find(b"def _extract_key_points", start)
        print(content[start:end].decode('utf-8', errors='replace'))
        print("Hex:", content[start:end].hex())
