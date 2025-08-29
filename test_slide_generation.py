#!/usr/bin/env python3
"""
スライド生成機能のテストスクリプト

既存のニュースデータを使用してHTMLスライドを生成し、機能をテストします。
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.generators.slide_generator import SlideGenerator
    print("✅ SlideGenerator クラスのインポート成功")
except ImportError as e:
    print(f"❌ SlideGenerator クラスのインポート失敗: {e}")
    sys.exit(1)


def test_slide_generation():
    """スライド生成機能のテスト"""
    print("\n🧪 スライド生成機能テスト開始\n")
    
    # SlideGeneratorインスタンスの作成
    try:
        generator = SlideGenerator(
            news_dir="news",
            templates_dir="templates", 
            output_dir="presentations"
        )
        print("✅ SlideGenerator インスタンス作成成功")
    except Exception as e:
        print(f"❌ SlideGenerator インスタンス作成失敗: {e}")
        return False
    
    # Jinja2の依存関係確認
    try:
        from jinja2 import Environment
        print("✅ Jinja2 依存関係確認成功")
    except ImportError:
        print("❌ Jinja2がインストールされていません")
        print("💡 pip install Jinja2 を実行してください")
        return False
    
    # 利用可能なニュースデータの確認
    news_dir = Path("news")
    available_dates = []
    
    for file_path in news_dir.glob("*.json"):
        if file_path.stem != "latest" and "-" in file_path.stem:  # 日付形式のファイル
            available_dates.append(file_path.stem)
    
    available_dates.sort()
    print(f"📊 利用可能なニュースデータ: {len(available_dates)} 日分")
    if available_dates:
        print(f"   - 最古: {available_dates[0]}")
        print(f"   - 最新: {available_dates[-1]}")
    else:
        print("❌ ニュースデータが見つかりません")
        return False
    
    # テンプレートファイルの確認
    templates_dir = Path("templates")
    required_templates = ["monthly_report.html", "daily_slide.html", "index.html"]
    missing_templates = []
    
    for template_name in required_templates:
        template_path = templates_dir / template_name
        if template_path.exists():
            print(f"✅ テンプレート確認: {template_name}")
        else:
            print(f"❌ テンプレート不足: {template_name}")
            missing_templates.append(template_name)
    
    if missing_templates:
        print(f"❌ 不足テンプレート: {missing_templates}")
        return False
    
    # 日次スライド生成テスト
    print("\n📅 日次スライド生成テスト")
    test_date = available_dates[-1]  # 最新の日付を使用
    
    try:
        daily_result = generator.generate_daily_slide(test_date)
        if daily_result:
            print(f"✅ 日次スライド生成成功: {daily_result}")
            
            # 生成されたファイルの確認
            if Path(daily_result).exists():
                file_size = Path(daily_result).stat().st_size
                print(f"   📄 ファイルサイズ: {file_size:,} bytes")
            else:
                print("❌ 生成されたファイルが見つかりません")
        else:
            print("❌ 日次スライド生成失敗")
            return False
    except Exception as e:
        print(f"❌ 日次スライド生成でエラー: {e}")
        return False
    
    # 月次スライド生成テスト（最新の日付から年月を取得）
    print("\n📈 月次スライド生成テスト")
    try:
        # "2025-08-26" -> year=2025, month=8
        year, month, day = map(int, test_date.split('-'))
        monthly_result = generator.generate_monthly_slides(year, month)
        
        if monthly_result:
            print(f"✅ 月次スライド生成成功: {monthly_result}")
            
            # 生成されたファイルの確認
            if Path(monthly_result).exists():
                file_size = Path(monthly_result).stat().st_size
                print(f"   📄 ファイルサイズ: {file_size:,} bytes")
            else:
                print("❌ 生成されたファイルが見つかりません")
        else:
            print("❌ 月次スライド生成失敗")
            return False
    except Exception as e:
        print(f"❌ 月次スライド生成でエラー: {e}")
        return False
    
    # インデックスページ更新テスト
    print("\n📝 インデックスページ更新テスト")
    try:
        generator.update_presentation_index()
        
        index_file = Path("presentations") / "index.html"
        if index_file.exists():
            file_size = index_file.stat().st_size
            print(f"✅ インデックスページ更新成功: {index_file}")
            print(f"   📄 ファイルサイズ: {file_size:,} bytes")
        else:
            print("❌ インデックスページが生成されていません")
            return False
    except Exception as e:
        print(f"❌ インデックスページ更新でエラー: {e}")
        return False
    
    # 生成結果の総合確認
    print("\n📋 生成結果の総合確認")
    presentations_dir = Path("presentations")
    
    if presentations_dir.exists():
        generated_files = list(presentations_dir.glob("*.html"))
        print(f"✅ 生成されたファイル数: {len(generated_files)}")
        
        for file_path in sorted(generated_files):
            file_size = file_path.stat().st_size
            print(f"   - {file_path.name}: {file_size:,} bytes")
    else:
        print("❌ presentations ディレクトリが見つかりません")
        return False
    
    print("\n🎉 すべてのテスト完了！")
    print(f"🌐 プレゼンテーションを確認: file://{presentations_dir.absolute()}/index.html")
    
    return True


def main():
    """メイン実行関数"""
    print("🚀 AIニュース スライド生成機能 テストツール")
    print("=" * 50)
    
    # 必要な依存関係の確認
    required_packages = ["jinja2"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 不足している依存関係: {missing_packages}")
        print(f"💡 インストールコマンド: pip install {' '.join(missing_packages)}")
        return
    
    # テスト実行
    success = test_slide_generation()
    
    if success:
        print("\n✅ テスト結果: 成功")
        print("🎯 次のステップ:")
        print("   1. presentations/index.html をブラウザで開く")
        print("   2. 生成されたスライドの内容を確認")
        print("   3. Reveal.js のスライド機能をテスト")
    else:
        print("\n❌ テスト結果: 失敗")
        print("🔧 上記のエラーメッセージを確認して問題を修正してください")


if __name__ == "__main__":
    main()