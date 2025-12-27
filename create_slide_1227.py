import os
import re

def create_slide_1227():
    template_path = "base_template.html"
    output_path = "presentations/day_slides/day_slide_2025_12_27.html"
    
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_html_content = f.read()

    # Content for 12/27 - LearnLM: The Ultimate Tutor
    today_str = "2025-12-26" # PDF says 12/26 but user wants 12/27 slide
    date_slash = "2025/12/27"
    title = "LearnLM: すべての学習者に『最高の家庭教師』を — Google AIによる教育革命"
    short_title = "LearnLM: The Ultimate Tutor"
    
    # CSS Variables for "Google Education" theme
    css_vars = """
    :root {
      --primary: #4285f4;  /* Google Blue */
      --accent: #34a853;   /* Google Green */
      --bg-light: #f8f9fa;
      --bg-dark: #202124;
      --text: #3c4043;
      --text-light: #70757a;
      --border: #dadce0;
      --highlight: #fbbc04; /* Google Yellow */
      --danger: #ea4335;    /* Google Red */
    }
    """

    intro_box = f"""
    <div style="background: linear-gradient(135deg, var(--primary), #1a73e8); color: white; padding: 24px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 4px 20px rgba(66, 133, 244, 0.3);">
        <p style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px;">「これは、学習の未来を巡る物語の始まりだ。」</p>
        <p style="font-size: 1.1rem; opacity: 0.95; margin: 0; line-height: 1.6;">
            Geminiをベースに、教育に特化したAIモデルファミリー「LearnLM」が登場。単に答えを教えるのではなく、生徒の思考を引き出し、励まし、内省を促す「教育者の魂」を宿したAIが、個別の学習体験を劇的に変えます。
        </p>
    </div>
    """

    highlight_box = f"""
    <div class="highlight-box" style="border-left: 5px solid var(--accent);">
      <strong>秘訣：教育的指示追従 (Pedagogical Instruction Following):</strong> Googleが開発したこの技術により、AIはソクラテスメソッド（対話による気づき）を忠実に実行し、学習者の自律的な成長をサポートします。
    </div>
    """

    feature_grid = """
    <div class="feature-grid">
      <div class="feature-item">
        <span class="feature-icon">🔍</span>
        <div class="feature-title">思考の引き出し</div>
        <div class="feature-desc">答えを教えず、ヒントや質問を通じて「気づき」を促します。</div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">✨</span>
        <div class="feature-title">励ましと寄り添い</div>
        <div class="feature-desc">自信を失いかけている時も、適切なフィードバックで学習を継続。</div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">🧠</span>
        <div class="feature-title">内省の促進</div>
        <div class="feature-desc">自分の考えを振り返らせることで、より深い理解と定着を実現。</div>
      </div>
    </div>
    """

    # Assemble Main Content (15 pages)
    main_content = f"""
    <main>
      <div class="top-image-container">
        <img src="../../input/day/1227.jpg" alt="LearnLM Visual" onerror="this.src='https://placehold.co/1200x600?text=1227+LearnLM+The+Ultimate+Tutor'">
      </div>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🎓</span>
          <h2>{short_title}</h2>
        </div>
        {intro_box}
        <h3>Google AIによる教育革命の実証</h3>
        {highlight_box}
        {feature_grid}
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔗</span>
          <h2>ソース資料</h2>
        </div>
        <div class="highlight-box">
          <p>このスライドの内容は、以下のGoogle公式特設サイトに基づいています：</p>
          <a href="https://learnyourway.withgoogle.com/" target="_blank" rel="noopener noreferrer" style="font-size: 1.2rem; display: block; margin-top: 10px;">
            Learn Your Way with Google: The Future of Teaching & Learning
          </a>
        </div>
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <h2>スライド資料 (全15ページ)</h2>
        </div>
        <div class="slides-container">
          {"".join([f'<img src="../../input/day/1227_slides/slide_{i:03d}.jpg" alt="Slide {i}" class="slide-img">' for i in range(1, 16)])}
        </div>
      </section>
    </main>
    """

    # Replacement logic with robust pattern matching for current template
    new_html = template_html_content
    
    # 1. Title/Meta
    new_html = new_html.replace("{{FULL_TITLE}}", title)
    
    # 2. Header Content
    new_html = new_html.replace("{{BREAKING_BADGE_TEXT}}", "DEEP DIVE")
    new_html = new_html.replace("{{H1_TITLE}}", short_title)
    new_html = new_html.replace("{{SUBTITLE}}", "LearnLM: 教育を加速するAIの魂")
    new_html = new_html.replace("{{DATE}}", date_slash)
    
    # 3. CSS variables block (handle multiline with whitespace)
    css_pattern = r'\{\s*\{\s*CSS_VARS_BLOCK\s*\}\s*\}'
    new_html = re.sub(css_pattern, css_vars, new_html, flags=re.MULTILINE | re.DOTALL)
    
    # 4. Main Content block
    content_pattern = r'\{\s*\{\s*MAIN_CONTENT_HTML\s*\}\s*\}'
    new_html = re.sub(content_pattern, main_content, new_html, flags=re.MULTILINE | re.DOTALL)
    import datetime
    new_html += f"\n<!-- Generated on: {datetime.datetime.now()} -->"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_slide_1227()
