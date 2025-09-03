@echo off
cd /d "C:\Users\yoshitaka\ai-news-site"

echo Creating clean 9/2 slide with Python...

python -c "
import codecs

html_content = '''<!DOCTYPE html>
<html lang=\"ja\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, user-scalable=yes\">
    <title>2025年09月02日 - 📱 MiniCPM-V 4.5 モバイルAI革命</title>
    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.css\">
    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/theme/white.css\">
    <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\" rel=\"stylesheet\">
    <style>
        html, body {
            height: 100%%;
            overflow-y: auto !important;
            overflow-x: hidden;
        }
        
        .reveal {
            position: relative !important;
            height: auto !important;
            min-height: 100vh;
            overflow: visible !important;
            font-family: ''Inter'', system-ui, sans-serif;
        }
        
        .reveal .slides {
            position: relative !important;
            width: 100%% !important;
            height: auto !important;
            padding: 20px !important;
            text-align: center !important;
            overflow: visible !important;
            transform: none !important;
        }
        
        .reveal .slides section {
            position: relative !important;
            width: 100%% !important;
            max-width: 1200px !important;
            height: auto !important;
            margin: 0 auto 30px auto !important;
            padding: 20px !important;
            display: block !important;
            overflow: visible !important;
            transform: none !important;
            opacity: 1 !important;
            visibility: visible !important;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
            text-align: left;
        }
        
        .reveal .controls,
        .reveal .progress,
        .reveal .playback,
        .reveal .slide-number {
            display: none !important;
        }

        .reveal a {
            pointer-events: auto !important;
            cursor: pointer !important;
        }
        
        .reveal a[target=\"_blank\"] {
            pointer-events: auto !important;
            cursor: pointer !important;
            z-index: 9999 !important;
            position: relative !important;
        }

        :root {
            --primary-color: #2d3748;
            --accent-color: #3182ce;
            --mobile-color: #9f7aea;
            --innovation-color: #805ad5;
        }

        body {
            font-family: ''Inter'', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%);
            color: var(--primary-color);
            line-height: 1.6;
        }

        .title-slide {
            text-align: center !important;
            background: linear-gradient(135deg, #9f7aea 0%%, #805ad5 100%%) !important;
            color: white !important;
        }

        h1 {
            font-size: 2.8em !important;
            font-weight: 700 !important;
            margin-bottom: 0.3em !important;
        }

        h2 {
            font-size: 2em !important;
            font-weight: 600 !important;
            color: var(--primary-color) !important;
            margin-bottom: 0.5em !important;
            padding-bottom: 0.3em;
            border-bottom: 3px solid var(--mobile-color);
        }

        .impact-badge {
            display: inline-block;
            background: linear-gradient(135deg, var(--mobile-color), #b794f6);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            margin: 5px;
        }

        .feature-box {
            background: linear-gradient(to bottom right, #faf5ff, #f3e8ff);
            border: 2px solid var(--mobile-color);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .stat-item {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: 700;
            color: var(--mobile-color);
            display: block;
            margin-bottom: 5px;
        }

        .stat-label {
            color: var(--primary-color);
            font-size: 0.9em;
            font-weight: 500;
        }

        ul li {
            margin-bottom: 10px;
            line-height: 1.6;
        }

        strong {
            color: var(--primary-color);
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class=\"reveal\">
        <div class=\"slides\">
            <section class=\"title-slide\">
                <h1>📱 MiniCPM-V 4.5</h1>
                <h2 style=\"color: white !important; border: none;\">GPT-4oレベルのモバイルAI革命</h2>
                <div style=\"margin: 30px 0;\">
                    <span class=\"impact-badge\">8Bパラメータ</span>
                    <span class=\"impact-badge\">30言語対応</span>
                    <span class=\"impact-badge\">オープンソース</span>
                    <span class=\"impact-badge\">モバイル最適化</span>
                </div>
                <p style=\"font-size: 1.2em; margin-top: 30px; opacity: 0.95;\">
                    2025年9月2日 | 総合スコア: 89/100
                </p>
            </section>

            <section>
                <h2>🚀 革新的モバイルAIの実現</h2>
                
                <div class=\"feature-box\">
                    <h3>⭐ 画期的な特徴</h3>
                    <ul>
                        <li><strong>モバイル最適化:</strong> 8BパラメータでGPT-4oレベルの性能をiPhone/iPadで実現</li>
                        <li><strong>マルチモーダル:</strong> 画像・ビデオ・OCR・ドキュメント解析を統合処理</li>
                        <li><strong>ビデオ理解:</strong> 96倍圧縮技術で長時間・高FPSビデオの効率的解析</li>
                        <li><strong>オフライン動作:</strong> プライバシー保護とアクセシビリティ向上</li>
                        <li><strong>OCR性能:</strong> GPT-4o-latestを上回る手書き認識・PDF解析</li>
                    </ul>
                </div>

                <div class=\"stats-grid\">
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">20,868</span>
                        <span class=\"stat-label\">GitHub Stars</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">77.0</span>
                        <span class=\"stat-label\">OpenCompassスコア</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">16-18</span>
                        <span class=\"stat-label\">トークン/s (iPad M4)</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">96倍</span>
                        <span class=\"stat-label\">ビデオ圧縮率</span>
                    </div>
                </div>
            </section>

            <section>
                <h2>💻 技術詳細と実装手順</h2>
                
                <div class=\"feature-box\">
                    <h3>🔧 システム仕様</h3>
                    <ul>
                        <li><strong>アーキテクチャ:</strong> 8Bパラメータ、制御可能なハイブリッド思考</li>
                        <li><strong>ビデオ処理:</strong> 96倍トークン圧縮、28G GPUメモリで推論時間0.26h</li>
                        <li><strong>OCR性能:</strong> GPT-4o-latestを上回る手書き認識・PDF解析</li>
                        <li><strong>多言語対応:</strong> 30以上の言語でマルチモーダル処理</li>
                        <li><strong>デバイス要件:</strong> Python 3.8+, PyTorch 2.0+, GPU推奨</li>
                    </ul>
                </div>

                <h3>⚡ 5分で始める実装手順</h3>
                <pre style=\"background: #1e293b; color: #94a3b8; padding: 15px; border-radius: 8px;\">
git clone https://github.com/OpenBMB/MiniCPM-V.git
cd MiniCPM-V
pip install -r requirements.txt

from transformers import AutoModel, AutoTokenizer
from PIL import Image

model = AutoModel.from_pretrained(''openbmb/MiniCPM-V-4_5'', trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(''openbmb/MiniCPM-V-4_5'', trust_remote_code=True)

image = Image.open(''example.jpg'').convert(''RGB'')
msgs = [{''role'': ''user'', ''content'': ''画像を詳しく説明して''}]
res, context, _ = model.chat(image=image, msgs=msgs, tokenizer=tokenizer)
print(res)
                </pre>
            </section>

            <section>
                <h2>🎯 ビジネス活用とワークフロー</h2>
                
                <div class=\"feature-box\">
                    <h3>💼 即実装可能なユースケース</h3>
                    <div style=\"display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;\">
                        <div style=\"background: white; padding: 15px; border-radius: 8px; border-left: 4px solid var(--mobile-color);\">
                            <strong>📄 ドキュメント管理</strong><br>
                            • 手書きメモ→デジタル化<br>
                            • PDF解析→CRM統合<br>
                            • 議事録自動生成<br>
                            • <em>KPI: 入力時間50%%短縮</em>
                        </div>
                        <div style=\"background: white; padding: 15px; border-radius: 8px; border-left: 4px solid var(--innovation-color);\">
                            <strong>🎥 カスタマーサポート</strong><br>
                            • ビデオ問い合わせ解析<br>
                            • リアルタイム要約生成<br>
                            • トラブルシューティング自動化<br>
                            • <em>KPI: 対応時間30%%削減</em>
                        </div>
                    </div>
                </div>
            </section>

            <section>
                <h2>📊 総合評価とリソース</h2>
                
                <div class=\"stats-grid\">
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">90/100</span>
                        <span class=\"stat-label\">技術実装性</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">80/100</span>
                        <span class=\"stat-label\">ビジネス価値</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">95/100</span>
                        <span class=\"stat-label\">技術革新性</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-number\">89/100</span>
                        <span class=\"stat-label\">総合スコア</span>
                    </div>
                </div>

                <div style=\"background: white; padding: 20px; border-radius: 12px; margin-top: 30px; text-align: center;\">
                    <h3>🔗 公式リソース</h3>
                    <div style=\"display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center;\">
                        <a href=\"https://x.com/akshay_pachaar/status/1962132670126981459\" target=\"_blank\" style=\"display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; cursor: pointer;\">📱 X投稿</a>
                        <a href=\"https://github.com/OpenBMB/MiniCPM-V\" target=\"_blank\" style=\"display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; cursor: pointer;\">💻 GitHub</a>
                        <a href=\"https://huggingface.co/openbmb/MiniCPM-V-4_5\" target=\"_blank\" style=\"display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; cursor: pointer;\">🤗 Hugging Face</a>
                        <a href=\"https://github.com/OpenBMB/MiniCPM-V/blob/main/README.md\" target=\"_blank\" style=\"display: inline-block; background: var(--accent-color); color: white; padding: 0.6rem 1.2rem; border-radius: 25px; text-decoration: none; cursor: pointer;\">📖 ドキュメント</a>
                    </div>
                </div>
            </section>
        </div>
    </div>

    <script src=\"https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.js\"></script>
    <script>
        Reveal.initialize({
            embedded: true,
            width: ''100%%'',
            height: ''100%%'',
            margin: 0,
            minScale: 1,
            maxScale: 1,
            hash: false,
            controls: false,
            progress: false,
            center: false,
            transition: ''none''
        });
    </script>
</body>
</html>'''

with codecs.open(r'presentations\day_slides\day_slide_2025_09_02.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Successfully created clean 9/2 slide')
"

if %errorlevel% equ 0 (
    echo.
    echo Committing and pushing...
    git add presentations/day_slides/day_slide_2025_09_02.html
    git commit -m "fix(9/2): complete rebuild with clean UTF-8 encoding"
    git push origin main
    
    echo.
    echo SUCCESS: Clean 9/2 slide deployed!
    echo URL: https://awano27.github.io/ai-news-site/presentations/day_slides/day_slide_2025_09_02.html
) else (
    echo Failed to create file
)

pause