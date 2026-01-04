import os
import re

MOJIBAKE_MAP = {
    "繧､繝ｳ繝・Μ繧ｸ繧ｧ繝ｳ繧ｹ": "インテリジェンス",
    "繝ｬ繝昴・繝・": "レポート",
    "諡｡蠑ｵ": "拡張",
    "繝・・繧ｿ繧ｹ繧ｭ繝ｼ繝槫ｯｾ蠢・": "データスキーマ対応",
    "繧ｨ繧ｰ繧ｼ繧ｯ繝・ぅ繝悶し繝槭Μ繝ｼ": "エグゼクティブサマリー",
    "蛻・梵險倅ｺ区焚": "分析記事数",
    "ｳ蝮・お繝薙ョ繝ｳ繧ｹ繧ｹ繧ｳ繧｢": "平均エビデンススコア",
    "髱ｩ譁ｰ逧・ｨ倅ｺ区ｯ皮紫": "革新的記事比率",
    "螳溯｣・庄閭ｽ諤ｧ": "実装可能性",
    "蛻・梵日譎・": "分析日時",
    "螟壼ｱ､讀懆ｨｼ貂医∩": "多層検証済み",
    "蜩∬ｳｪ繝√Ε繝ｼ繝・": "品質チャート",
    "繝壹Ν繧ｽ繝雁挨繧､繝ｳ繝代け繝・": "ペルソナ別インパクト",
    "繝ｪ繧ｹ繧ｯ蛻・梵": "リスク分析",
    "繧､繝諾・繝ｼ繧ｷ繝ｧ繝ｳ豢槫ｯ・": "イノベーション洞察",
    "謚€陦・": "技術",
    "蜩∬ｳｪ": "品質",
    "蛻・梵": "分析",
    "讀懆ｨｼ": "検証",
    "繧､繝ｳ繝代け繝・": "インパクト",
    "隧穂ｾ｡": "評価",
    "螳溯｣・": "実装",
    "謗ｨ螂ｨ": "推奨",
    "繝代け繝・": "パクト",
    "繧､繝諾": "イノ",
    "繝ｼ繧ｷ繝ｧ繝ｳ": "ベーション",
    "豢槫ｯ・": "洞察",
    "繧ｨ繝薙ョ繝ｳ繧ｹ": "エビデンス",
    "繝壹Ν繧ｽ繝・": "ペルソナ",
    "繧ｷ繧ｹ繝・Β": "システム",
    "繧ｽ繝ｼ繧ｹ": "ソース",
    "繝峨Γ繧､繝ｳ": "ドメイン",
    "繝輔Ξ繝ｼ繝繝ｯ繝ｼ繧ｯ": "フレームワーク",
    "繝代う繝ｭ繝・ヨ": "パイロット",
    "繝励Ο繧ｸ繧ｧ繧ｯ繝・": "プロジェクト",
    "繝吶Φ繝√・繝ｼ繧ｯ": "ベンチマーク",
    "繝悶Ξ繝ｼ繧ｯ繧ｹ繝ｫ繝ｼ": "ブレークスルー",
    "蟶ょｴ": "市場",
    "諠・ｱ": "情報",
    "騾咏ｶ・": "継続",
    "菫｡鬆ｼ": "信頼",
    "迚ｹ蛹・": "特化",
    "諠・ｱ": "情報",
    "逾ｭ": "祭",
    "荳也阜": "世界",
    "蜈ｬ髢・": "公開",
    "螳溽畑": "実用",
    "荳願・": "機能",
    "笨・": "✅",
    "笘・": "🚀",
    "ｧ": "🧠",
    "剝": "🔍",
    "則": "👥",
    "噫": "🚀",
    "溌": "🔬",
    "嶋": "📈",
    "庁": "💡",
    "肌": "🔧",
    "直": "💼",
    "套": "📅",
    "投": "💡",
}

def fix_file(path):
    print(f"Fixing {path}...")
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 1. Map replacement
        for k, v in MOJIBAKE_MAP.items():
            content = content.replace(k, v)
        
        # 2. Known single character fixes
        content = content.replace('蟷ｴ', '年').replace('譛・', '月').replace('譌･', '日')
        content = content.replace('隧ｳ邏ｰ', '詳細')
        content = content.replace('縺吶', 'す')
        content = content.replace('縺・', 'い')
        content = content.replace('繧｢', 'ア')
        content = content.replace('繧､', 'イ')
        content = content.replace('繧ｦ', 'ウ')
        content = content.replace('繧ｨ', 'エ')
        content = content.replace('繧ｪ', 'オ')
        content = content.replace('繧ｬ', 'ガ')
        content = content.replace('繧ｮ', 'ギ')
        content = content.replace('繧ｰ', 'グ')
        content = content.replace('繧ｲ', 'ゲ')
        content = content.replace('繧ｴ', 'ゴ')
        content = content.replace('繧ｹ', 'ス')
        content = content.replace('繧ｾ', 'ゼ')
        content = content.replace('繧ｿ', 'タ')
        content = content.replace('繝・', 'テ')
        content = content.replace('繝ｨ', 'ヨ')
        content = content.replace('繝翫', 'ナ')
        content = content.replace('繝九', 'ニ')
        content = content.replace('繝・', 'テ')
        content = content.replace('繝', 'ム')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Done.")
    except Exception as e:
        print(f"Error: {e}")

TARGET_DIRS = [
    r"C:\develop\ai-news-site\presentations",
    r"C:\develop\ai-news-site\public-pages\news"
]

for d in TARGET_DIRS:
    for filename in os.listdir(d):
        if filename.endswith(".html") or filename.endswith(".js"):
            fix_file(os.path.join(d, filename))
