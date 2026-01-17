#!/usr/bin/env python3
"""
おすすめ便利ツールサイト 価格情報自動更新スクリプト

主要AIツールの最新価格を取得し、recommended_tools.html を更新する。
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# 価格情報データベース（手動更新または API 経由で取得）
# 価格は USD 建て
TOOL_PRICES = {
    "chatgpt_plus": {
        "name": "ChatGPT Plus",
        "monthly": 20,
        "annual": 20,
        "per_user": True,
        "source": "https://chatgpt.com/pricing",
        "notes": "個人向け"
    },
    "chatgpt_team": {
        "name": "ChatGPT Team",
        "monthly": 30,
        "annual": 25,
        "per_user": True,
        "source": "https://chatgpt.com/pricing",
        "notes": "チーム向け、最低2ユーザー"
    },
    "chatgpt_enterprise": {
        "name": "ChatGPT Enterprise",
        "monthly": 60,  # 目安
        "annual": 60,
        "per_user": True,
        "source": "https://chatgpt.com/pricing",
        "notes": "要問い合わせ、50人以上推奨"
    },
    "claude_pro": {
        "name": "Claude Pro",
        "monthly": 20,
        "annual": 17,
        "per_user": True,
        "source": "https://claude.ai/pricing",
        "notes": "個人向け"
    },
    "claude_team": {
        "name": "Claude Team",
        "monthly": 30,
        "annual": 30,
        "per_user": True,
        "source": "https://claude.ai/pricing",
        "notes": "チーム向け"
    },
    "notion_plus": {
        "name": "Notion Plus",
        "monthly": 12,
        "annual": 10,
        "per_user": True,
        "source": "https://www.notion.com/pricing",
        "notes": "小規模チーム向け"
    },
    "notion_business": {
        "name": "Notion Business",
        "monthly": 24,
        "annual": 20,
        "per_user": True,
        "source": "https://www.notion.com/pricing",
        "notes": "AI含む、ビジネス向け"
    },
    "slack_pro": {
        "name": "Slack Pro",
        "monthly": 8.75,
        "annual": 7.25,
        "per_user": True,
        "source": "https://slack.com/pricing",
        "notes": "AI機能基本含む"
    },
    "slack_business_plus": {
        "name": "Slack Business+",
        "monthly": 15,
        "annual": 12.50,
        "per_user": True,
        "source": "https://slack.com/pricing",
        "notes": "SSO/コンプライアンス対応"
    },
    "perplexity_pro": {
        "name": "Perplexity Pro",
        "monthly": 20,
        "annual": 16.67,
        "per_user": True,
        "source": "https://www.perplexity.ai/enterprise/pricing",
        "notes": "300+ Pro searches/day"
    },
    "perplexity_enterprise": {
        "name": "Perplexity Enterprise Pro",
        "monthly": 40,
        "annual": 33.33,
        "per_user": True,
        "source": "https://www.perplexity.ai/enterprise/pricing",
        "notes": "チーム向け"
    },
    "zapier_professional": {
        "name": "Zapier Professional",
        "monthly": 29.99,
        "annual": 29.99,
        "per_user": False,
        "source": "https://zapier.com/pricing",
        "notes": "タスク数課金、Premium Apps対応"
    },
    "granola_individual": {
        "name": "Granola Individual",
        "monthly": 18,
        "annual": 18,
        "per_user": True,
        "source": "https://www.granola.ai/pricing",
        "notes": "個人向け"
    },
    "granola_business": {
        "name": "Granola Business",
        "monthly": 14,
        "annual": 14,
        "per_user": True,
        "source": "https://www.granola.ai/pricing",
        "notes": "チーム向け"
    },
    "notebooklm_plus": {
        "name": "NotebookLM Plus (Google AI Pro)",
        "monthly": 19.99,
        "annual": 19.99,
        "per_user": False,
        "source": "https://one.google.com/about/google-ai-plans",
        "notes": "Google One AI Premium経由、Gemini Advanced含む"
    },
    "cursor_pro": {
        "name": "Cursor Pro",
        "monthly": 20,
        "annual": 16,
        "per_user": True,
        "source": "https://cursor.sh/pricing",
        "notes": "AI コーディング"
    },
    "github_copilot": {
        "name": "GitHub Copilot",
        "monthly": 19,
        "annual": 19,
        "per_user": True,
        "source": "https://github.com/features/copilot",
        "notes": "Individual"
    },
    "linear": {
        "name": "Linear",
        "monthly": 10,
        "annual": 8,
        "per_user": True,
        "source": "https://linear.app/pricing",
        "notes": "PM/Issue tracking"
    },
    "figma_pro": {
        "name": "Figma Pro",
        "monthly": 15,
        "annual": 12,
        "per_user": True,
        "source": "https://www.figma.com/pricing/",
        "notes": "デザインツール"
    },
    "gemini_advanced": {
        "name": "Gemini Advanced",
        "monthly": 19.99,
        "annual": 19.99,
        "per_user": True,
        "source": "https://one.google.com/about/google-ai-plans",
        "notes": "Google AI Pro経由"
    },
}

# 為替レート（概算）
USD_TO_JPY = 155


def get_current_date_str() -> str:
    """現在の日付を日本語形式で返す"""
    now = datetime.now()
    return f"{now.year}年{now.month}月時点"


def format_price_usd(price: float, show_yen: bool = False) -> str:
    """価格をフォーマット"""
    if price == int(price):
        usd = f"${int(price)}"
    else:
        usd = f"${price:.2f}"

    if show_yen:
        yen = int(price * USD_TO_JPY)
        return f"{usd}（約¥{yen:,}）"
    return usd


def generate_price_report() -> str:
    """価格レポートを生成"""
    date_str = get_current_date_str()
    lines = [
        f"=== おすすめツール価格情報 ({date_str}) ===",
        f"為替レート: 1 USD = {USD_TO_JPY} JPY",
        "",
        "【AI チャット / アシスタント】",
    ]

    # カテゴリ別に整理
    categories = {
        "AI チャット": ["chatgpt_plus", "chatgpt_team", "claude_pro", "claude_team", "gemini_advanced"],
        "AI リサーチ": ["perplexity_pro", "notebooklm_plus"],
        "コラボレーション": ["notion_plus", "notion_business", "slack_pro", "slack_business_plus"],
        "開発ツール": ["cursor_pro", "github_copilot", "linear"],
        "自動化": ["zapier_professional"],
        "会議": ["granola_individual", "granola_business"],
    }

    for cat_name, tool_ids in categories.items():
        lines.append(f"\n【{cat_name}】")
        for tid in tool_ids:
            if tid in TOOL_PRICES:
                t = TOOL_PRICES[tid]
                monthly = format_price_usd(t["monthly"])
                annual = format_price_usd(t["annual"])
                per = "/人" if t["per_user"] else ""
                lines.append(f"  {t['name']}: {monthly}/月{per}（年払い: {annual}/月{per}）")

    return "\n".join(lines)


def update_html_date_annotation(html_content: str) -> str:
    """HTML内の日付注記を更新"""
    date_str = get_current_date_str()

    # パターン1: 「YYYY年M月時点」の形式を更新
    pattern1 = r'(\d{4}年\d{1,2}月時点)'
    html_content = re.sub(pattern1, date_str, html_content)

    return html_content


def generate_cost_calculator_data() -> dict:
    """コスト計算機用のデータを生成"""
    return {
        "notion": {"monthly": 12, "annual": 10},
        "slack": {"monthly": 8.75, "annual": 7.25},
        "chatgpt": {"monthly": 20, "annual": 20},
        "chatgpt-team": {"monthly": 30, "annual": 25},
        "copilot": {"monthly": 19, "annual": 19},
        "cursor": {"monthly": 20, "annual": 16},
        "zapier": {"monthly": 29.99, "annual": 29.99},
        "linear": {"monthly": 10, "annual": 8},
        "figma": {"monthly": 15, "annual": 12},
        "granola": {"monthly": 18, "annual": 14},
        "notebooklm": {"monthly": 19.99, "annual": 19.99},
        "claude": {"monthly": 20, "annual": 17},
        "perplexity": {"monthly": 20, "annual": 16.67},
    }


def generate_ringi_tool_data() -> str:
    """稟議書テンプレート用のJavaScriptデータを生成"""
    date_str = get_current_date_str()

    data = f"""      // Ringi template data (価格は{date_str}、1USD≒{USD_TO_JPY}円で換算)
      const toolData = {{
        'notion': {{
          name: 'Notion Plus/Business',
          price: '$10〜20/月/人（年払い）≒ ¥{int(10*USD_TO_JPY):,}〜{int(20*USD_TO_JPY):,}/月/人',
          vendor: 'Notion Labs, Inc.（米国）',
          security: 'SOC2 Type II認証取得、GDPR対応、データ暗号化（保存時・転送時）',
          features: ['ナレッジ管理・Wiki構築', 'プロジェクト・タスク管理', 'ドキュメント共同編集', 'データベース機能', 'Notion AI（Business以上に含む）']
        }},
        'chatgpt-team': {{
          name: 'ChatGPT Team',
          price: '$25〜30/月/人 ≒ ¥{int(25*USD_TO_JPY):,}〜{int(30*USD_TO_JPY):,}/月/人',
          vendor: 'OpenAI（米国）',
          security: 'SOC2認証、データ学習に使用しない保証、管理者ダッシュボード',
          features: ['GPT-4o/GPT-4アクセス', '共有GPTs作成', 'ワークスペース管理', 'チーム分析機能']
        }},
        'slack': {{
          name: 'Slack Pro',
          price: '$7.25/月/人（年払い）≒ ¥{int(7.25*USD_TO_JPY):,}/月/人',
          vendor: 'Salesforce, Inc.（米国）',
          security: 'SOC2/3認証、データ暗号化、監査ログ、DLP対応',
          features: ['無制限のメッセージ履歴', 'ワークフロービルダー', '外部連携アプリ', 'ハドル（音声通話）', 'AI機能（基本）']
        }},
        'zapier': {{
          name: 'Zapier Professional',
          price: '$29.99/月〜（タスク数により変動）≒ ¥{int(29.99*USD_TO_JPY):,}/月〜',
          vendor: 'Zapier, Inc.（米国）',
          security: 'SOC2認証、データ暗号化、アクセス制御',
          features: ['7,000+アプリ連携', 'マルチステップワークフロー', 'フィルター・分岐処理', 'スケジュール実行', 'Premium Apps対応']
        }},
        'granola': {{
          name: 'Granola Business',
          price: '$14/月/人 ≒ ¥{int(14*USD_TO_JPY):,}/月/人',
          vendor: 'Granola（米国）',
          security: 'データ暗号化、プライバシー保護設計',
          features: ['AI議事録作成', 'ToDo自動抽出', 'カレンダー連携', '会議サマリー生成', '無制限の会議履歴']
        }},
        'notebooklm': {{
          name: 'NotebookLM Plus (Google AI Pro)',
          price: '$19.99/月 ≒ ¥{int(19.99*USD_TO_JPY):,}/月（Google One AI Premium経由）',
          vendor: 'Google LLC（米国）',
          security: 'Googleのセキュリティ基盤、データ暗号化',
          features: ['資料読み込み・Q&A', '要点抽出', 'Audio Overview生成', 'ソース参照表示', 'Gemini Advanced含む']
        }},
        'claude': {{
          name: 'Claude Pro',
          price: '$20/月/人 ≒ ¥{int(20*USD_TO_JPY):,}/月/人',
          vendor: 'Anthropic（米国）',
          security: 'データ学習に使用しない、暗号化対応',
          features: ['Claude Sonnet/Opus利用', '優先アクセス', 'Projects機能', '200Kトークン対応']
        }}
      }};"""

    return data


def main():
    """メイン処理"""
    print("=" * 50)
    print("おすすめ便利ツール 価格情報更新スクリプト")
    print("=" * 50)
    print()

    # 価格レポートを表示
    report = generate_price_report()
    print(report)
    print()

    # HTMLファイルのパス
    html_path = Path(__file__).parent.parent / "presentations" / "recommended_tools.html"

    if not html_path.exists():
        print(f"[ERROR] HTMLファイルが見つかりません: {html_path}")
        return

    print(f"[INFO] 対象ファイル: {html_path}")
    print()

    # コスト計算機データを出力
    print("【コスト計算機用データ】")
    calc_data = generate_cost_calculator_data()
    print(json.dumps(calc_data, indent=2))
    print()

    # 稟議書テンプレートデータを出力
    print("【稟議書テンプレート用データ】")
    ringi_data = generate_ringi_tool_data()
    print(ringi_data[:500] + "...")
    print()

    print("[INFO] このスクリプトはデータ生成のみを行います。")
    print("[INFO] 実際のHTML更新は Claude Code を使用してください。")
    print()
    print("使用例:")
    print("  「おすすめツールサイトの価格を最新化して」")
    print("  「Perplexity Pro をツールリストに追加して」")


if __name__ == "__main__":
    main()
