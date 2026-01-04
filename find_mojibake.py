import os
import re

dir_path = r"C:\develop\ai-news-site\presentations\day_slides"
mojibake_patterns = [
    re.compile(r"縺"),
    re.compile(r"・縲"),
    re.compile(r"縺吶"),
    re.compile(r"縺・"),
    re.compile(r"ŐV"),
]

corrupted_files = []

for filename in os.listdir(dir_path):
    if filename.endswith(".html"):
        file_path = os.path.join(dir_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in mojibake_patterns:
                    if pattern.search(content):
                        corrupted_files.append(filename)
                        break
        except Exception:
            # If it's not even UTF-8, it might be something else, but we're mostly looking for the SJIS-interp-as-UTF8 case
            pass

print(f"Total files in directory: {len([f for f in os.listdir(dir_path) if f.endswith('.html')])}")
print(f"Found {len(corrupted_files)} corrupted files:")
for f in corrupted_files:
    print(f)
