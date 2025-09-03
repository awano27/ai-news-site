#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# 9/1スライドを読み込み（正しく表示されているファイル）
with open('presentations/day_slides/day_slide_2025_09_01.html', 'r', encoding='utf-8') as f:
    template = f.read()

# 9/1の内容を9/2用に変更
content = template

# タイトルと日付を変更
content = content.replace('2025年09月01日', '2025年09月02日')
content = content.replace('🏥 AIヘルスケア革命「RX」', '📱 MiniCPM-V 4.5')
content = content.replace('AIヘルスケア革命「RX」', 'MiniCPM-V 4.5 モバイルAI革命')
content = content.replace('総合スコア: 81/100', '総合スコア: 89/100')

# 最初のh1タグを変更
content = content.replace('<h1>🏥 RXプラットフォーム</h1>', '<h1>📱 MiniCPM-V 4.5</h1>')

# h2タグのサブタイトルを変更
content = content.replace('医療のデジタルツイン実現へ', 'GPT-4oレベルのモバイルAI革命')

# 9/2として保存
with open('presentations/day_slides/day_slide_2025_09_02.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 9/2スライドを9/1テンプレートから作成しました')
print('タイトルが正しく表示されるか確認してください:')