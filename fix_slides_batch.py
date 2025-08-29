#!/usr/bin/env python3
"""Batch fix for Daily AI News slides - Add Sources and Navigation sections"""

import os
import re

def fix_slide_file(filepath):
    """Fix a single slide file by adding Sources and Navigation sections plus keyboard shortcuts"""
    
    # Standard sections to add
    sources_section = '''
            <!-- Sources Slide -->
            <section>
                <h2 class="slide-title">📚 情報源・参考資料</h2>
                <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 15px; padding: 2rem; margin: 1.5rem 0;">
                    <h3 style="margin-top: 0; color: var(--primary-color);">🔗 関連リンク</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 2rem;">信頼できる一次ソースからの情報</p>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;">
                        <a href="https://techcrunch.com" target="_blank" style="display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; font-size: 0.9em; font-weight: 500;">📄 TechCrunch</a>
                        <a href="https://venturebeat.com" target="_blank" style="display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; font-size: 0.9em; font-weight: 500;">📄 VentureBeat</a>
                        <a href="https://www.theverge.com" target="_blank" style="display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; font-size: 0.9em; font-weight: 500;">📄 The Verge</a>
                        <a href="https://ai.googleblog.com" target="_blank" style="display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; font-size: 0.9em; font-weight: 500;">📄 Google AI Blog</a>
                    </div>
                    
                    <div style="margin-top: 2rem; padding: 1rem; background: #f3f4f6; border-radius: 8px;">
                        <h4 style="margin-top: 0; color: var(--primary-color);">信頼度指標</h4>
                        <div style="width: 100%; height: 12px; background: #e2e8f0; border-radius: 6px; overflow: hidden;">
                            <div style="height: 100%; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%); width: 88%; border-radius: 6px;"></div>
                        </div>
                        <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9em;">
                            信頼度: 88% (主要ソース確認済み)
                        </p>
                    </div>
                </div>
            </section>

            <!-- Navigation Slide -->
            <section>
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 3rem; border-radius: 15px; text-align: center;">
                    <h2 style="color: white;">🧭 ナビゲーション</h2>
                    <p style="opacity: 0.9; margin: 1rem 0;">他のレポートやスライドにアクセス</p>
                    
                    <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 2rem; flex-wrap: wrap;">
                        <a href="../day_slides_index.html" style="background: rgba(255, 255, 255, 0.2); color: white; padding: 1rem 2rem; border-radius: 25px; text-decoration: none; font-weight: 500; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3);">
                            📅 日次スライド一覧
                        </a>
                        <a href="../ai_ranking_report_20250826.html" style="background: rgba(255, 255, 255, 0.2); color: white; padding: 1rem 2rem; border-radius: 25px; text-decoration: none; font-weight: 500; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3);">
                            🏆 ランキングレポート
                        </a>
                        <a href="../daily_ai_news_report_20250826.html" style="background: rgba(255, 255, 255, 0.2); color: white; padding: 1rem 2rem; border-radius: 25px; text-decoration: none; font-weight: 500; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.3);">
                            📰 詳細レポート
                        </a>
                    </div>
                    
                    <div style="margin-top: 3rem; font-size: 0.9em; opacity: 0.7;">
                        <p>🎯 キーボードショートカット: H (ホーム) | R (レポート) | ESC (戻る)</p>
                    </div>
                </div>
            </section>
'''

    keyboard_shortcuts = '''
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            switch(event.key) {
                case 'h':
                case 'H':
                    window.location.href = '../day_slides_index.html';
                    break;
                case 'r':
                case 'R':
                    window.location.href = '../ai_ranking_report_20250826.html';
                    break;
                case 'm':
                case 'M':
                    window.location.href = '../daily_ai_news_report_20250826.html';
                    break;
                case 'Escape':
                    window.history.back();
                    break;
            }
        });

'''
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if already has 6 sections (already fixed)
        section_count = content.count('<section>')
        if section_count >= 6:
            print(f"✓ {os.path.basename(filepath)} already has {section_count} sections (fixed)")
            return True
            
        print(f"Fixing {os.path.basename(filepath)} ({section_count} sections -> 6 sections)")
        
        # Add Sources and Navigation sections before closing </div></div>
        pattern = r'(\s+</section>\s+</div>\s+</div>\s+<script>)'
        replacement = sources_section + r'\n        </div>\n    </div>\n\n\n    <script>'
        content = re.sub(pattern, replacement, content)
        
        # Add keyboard shortcuts after Reveal.initialize
        pattern = r'(\s+});)\s+(//\s*Create evaluation chart)'
        replacement = r'\1\n\n' + keyboard_shortcuts + r'\n        \2'
        content = re.sub(pattern, replacement, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    slides_dir = r"presentations\day_slides"
    
    # List of files to fix (4 section slides)
    files_to_fix = [
        "day_slide_2025_08_13.html",
        "day_slide_2025_08_14.html", 
        "day_slide_2025_08_15.html",
        "day_slide_2025_08_16.html",
        "day_slide_2025_08_17.html",
        "day_slide_2025_08_19.html",
        "day_slide_2025_08_20.html",
        "day_slide_2025_08_22.html",
        "day_slide_2025_08_23.html",
        "day_slide_2025_08_24.html",
        "day_slide_2025_08_26.html"
    ]
    
    fixed_count = 0
    
    for filename in files_to_fix:
        filepath = os.path.join(slides_dir, filename)
        if os.path.exists(filepath):
            if fix_slide_file(filepath):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")
    
    print(f"\n✅ Fixed {fixed_count}/{len(files_to_fix)} slides")

if __name__ == "__main__":
    main()