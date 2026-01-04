#!/usr/bin/env python3
"""
Fix tool-card category classes in recommended_tools.html

This script adds appropriate category classes to tool-card divs based on:
- Tool title/subtitle/description content
- Presence of Product Hunt links
- Known tool categorizations
"""

import re
from pathlib import Path

def categorize_tool(tool_html, tool_id, title):
    """Determine categories for a tool based on its content"""
    categories = []

    # Check for Product Hunt link
    has_ph_link = 'producthunt.com' in tool_html.lower()

    # Category keywords mapping
    meeting_keywords = ['会議', 'ミーティング', 'meeting', '議事録', 'カレンダー', 'calendar', '文字起こし', 'transcript', 'granola', 'notion meetings']
    docs_keywords = ['ドキュメント', 'document', 'wiki', 'ナレッジ', 'knowledge', 'notion', 'markdown', 'エディタ', 'editor', '資料']
    pm_keywords = ['プロジェクト管理', 'project management', 'タスク', 'task', 'チケット', 'ticket', 'イシュー', 'issue', 'linear', 'asana', 'jira']
    automation_keywords = ['自動化', 'automation', 'ワークフロー', 'workflow', 'zapier', 'n8n', 'make', '連携', 'integration']
    ai_keywords = ['ai', 'chatgpt', 'claude', 'gpt', 'llm', '生成', 'generation', 'prompt']
    dev_keywords = ['開発', 'development', 'デプロイ', 'deploy', 'api', 'github', 'code', 'vercel', 'supabase', 'cursor', 'copilot', 'sentry', 'postman']

    text_lower = tool_html.lower()
    title_lower = title.lower()

    # Check each category
    if any(kw in text_lower or kw in title_lower for kw in meeting_keywords):
        categories.append('meeting')

    if any(kw in text_lower or kw in title_lower for kw in docs_keywords):
        categories.append('docs')

    if any(kw in text_lower or kw in title_lower for kw in pm_keywords):
        categories.append('pm')

    if any(kw in text_lower or kw in title_lower for kw in automation_keywords):
        categories.append('automation')

    if any(kw in text_lower or kw in title_lower for kw in ai_keywords):
        categories.append('ai')

    if any(kw in text_lower or kw in title_lower for kw in dev_keywords):
        categories.append('dev')

    # Add 'ph' category if has Product Hunt link
    if has_ph_link:
        categories.append('ph')

    # If no categories matched, mark as 'other'
    if not categories:
        categories.append('other')

    return categories


def fix_tool_categories():
    """Add category classes to all tool-card elements"""

    html_path = Path(r'c:\develop\ai-news-site\presentations\recommended_tools.html')

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match tool-card opening tags with optional id
    # Match: <div class="tool-card"> or <div class="tool-card" id="tool-notion">
    tool_card_pattern = r'<div class="tool-card"(\s+id="[^"]*")?>'

    # Find all tool cards and their content
    results = []

    # Split by tool-card to process each
    parts = re.split(tool_card_pattern, content)

    # First part is before any tool-card
    new_content = parts[0]

    # Process in groups of 3: (prefix_content, id_attr, tool_content)
    # Actually the split creates: [before_first, id_or_None, after_first, id_or_None, after_second, ...]

    # Let's use finditer instead for better control
    new_content = content

    # Find all tool-card divs with their full content
    # Match both: <div class="tool-card"> and <div class="tool-card" data-tags="...">
    tool_pattern = r'(<div class="tool-card"(?:\s+[^>]*)?)(>)(.*?)(?=<div class="tool-card"|<!-- Tool Grid End -->)'

    matches = list(re.finditer(tool_pattern, content, re.DOTALL))

    print(f"Found {len(matches)} tool cards to process")

    # Process in reverse to preserve positions
    replacements = []

    for i, match in enumerate(matches):
        opening_tag_pre = match.group(1)  # <div class="tool-card" or <div class="tool-card" id="..."
        closing_bracket = match.group(2)  # >
        tool_content = match.group(3)

        # Extract title
        title_match = re.search(r'<h3>([^<]+)', tool_content)
        title = title_match.group(1) if title_match else f"Tool {i+1}"

        # Extract id if present
        id_match = re.search(r'id="([^"]*)"', opening_tag_pre)
        tool_id = id_match.group(1) if id_match else None

        # Determine categories
        categories = categorize_tool(tool_content, tool_id, title)

        # Build new class attribute
        category_classes = ' '.join(categories)
        new_class = f'tool-card {category_classes}'

        # Replace the class attribute in opening tag
        # Handle both simple and complex opening tags
        if 'class="tool-card"' in opening_tag_pre:
            new_opening_tag = opening_tag_pre.replace('class="tool-card"', f'class="{new_class}"')
        else:
            # Shouldn't happen after our fix, but just in case
            new_opening_tag = opening_tag_pre

        replacements.append({
            'start': match.start(1),
            'end': match.end(2),
            'old': opening_tag_pre + closing_bracket,
            'new': new_opening_tag + closing_bracket,
            'title': title,
            'categories': categories
        })

        print(f"{i+1}. {title[:50]}: {', '.join(categories)}")

    # Apply replacements in reverse order
    for repl in reversed(replacements):
        new_content = new_content[:repl['start']] + repl['new'] + new_content[repl['end']:]

    # Write back
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n[OK] Successfully updated {len(replacements)} tool cards")
    print(f"[OK] File saved: {html_path}")


if __name__ == '__main__':
    fix_tool_categories()
