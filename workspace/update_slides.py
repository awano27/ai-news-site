#!/usr/bin/env python3
"""Update HTML with slide images"""

html_file = "D:/ai-news-site-main/presentations/day_slides/day_slide_2026_01_06.html"

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the placeholder with slide images
old_content = '''        <div class="slides-container">
          <p style="text-align: center; color: var(--text-light); font-size: 1.1rem; padding: 40px;">
            ※ スライド画像は準備中です。<br>
            PPTXファイルは <a href="../../output/0106_slides.pptx" download>こちら</a> からダウンロードできます。
          </p>
        </div>'''

new_content = '''        <div class="slides-container">
          <img src="../../input/day/0106_slides/slide_001.jpg" alt="Slide 1" class="slide-img"><img src="../../input/day/0106_slides/slide_002.jpg" alt="Slide 2" class="slide-img"><img src="../../input/day/0106_slides/slide_003.jpg" alt="Slide 3" class="slide-img"><img src="../../input/day/0106_slides/slide_004.jpg" alt="Slide 4" class="slide-img"><img src="../../input/day/0106_slides/slide_005.jpg" alt="Slide 5" class="slide-img">
        </div>'''

content = content.replace(old_content, new_content)

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {html_file} with slide images")
