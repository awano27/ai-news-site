#!/usr/bin/env python3
"""Compare the generated TOP metadata and resource cards with the public page."""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import re
import time
import urllib.request

IDS = {'heroTwist', 'heroWhy', 'todaySlideDate', 'sitrepUpdate', 'sitrepDesk',
       'sitrepAction', 'footerUpdated', 'heroUpdatedAt', 'dailyNewsDate', 'dailyReportDate'}

class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.values, self.links, self.targets, self.depth, self.active = {}, {}, {}, 0, []
        self.resource, self.resource_depth = None, 0
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in {'img', 'meta', 'link', 'br', 'input', 'hr'}:
            self.depth += 1
        key = attrs.get('id')
        if key in {'sitrepLink', 'todaySlideCard', 'dailyReportLink'}:
            self.targets[key] = attrs.get('href', '')
        if key in IDS:
            self.values[key] = ''
            self.active.append((key, self.depth))
        if tag == 'a' and 'res-card' in attrs.get('class', '').split():
            self.resource = attrs.get('href', '')
            self.resource_depth = self.depth
            self.links[self.resource] = {'text': '', 'alt': ''}
        if self.resource and tag == 'img':
            self.links[self.resource]['alt'] = attrs.get('alt', '')
    def handle_data(self, data):
        for key, _ in self.active:
            self.values[key] += data
        if self.resource:
            self.links[self.resource]['text'] += data
    def handle_endtag(self, tag):
        if tag in {'img', 'meta', 'link', 'br', 'input', 'hr'}:
            return
        self.active = [(key, level) for key, level in self.active if level != self.depth]
        if self.resource and self.resource_depth == self.depth:
            self.resource = None
        self.depth -= 1
    def snapshot(self):
        clean = lambda value: re.sub(r'\s+', ' ', value).strip()
        return {'targets': self.targets, 'values': {k: clean(v) for k, v in self.values.items()},
                'resources': {k: {key: clean(v) for key, v in data.items()} for k, data in self.links.items()}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--base-url')
    parser.add_argument('--attempts', type=int, default=6)
    args = parser.parse_args()
    expected_text = (args.root / 'index.html').read_text(encoding='utf-8')
    if "foot.textContent = 'UPDATED ' + entries[0].date" in expected_text:
        raise SystemExit('FAIL: archive metadata still overwrites TOP date')
    expected = Metadata(expected_text).snapshot()
    assert IDS <= expected['values'].keys(), 'Missing required homepage metadata'
    if not args.base_url:
        print('PASS: TOP metadata fields and resource cards are present')
        return
    for attempt in range(args.attempts):
        try:
            request = urllib.request.Request(args.base_url.rstrip('/') + '/?homepage-sync=' + str(time.time_ns()),
                                           headers={'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(request, timeout=30) as response:
                text = response.read().decode('utf-8')
            assert Metadata(text).snapshot() == expected, 'Published TOP metadata differs from generated source'
            assert "foot.textContent = 'UPDATED ' + entries[0].date" not in text
            print('PASS: published TOP metadata, links and resource descriptions match generated source')
            return
        except (OSError, AssertionError) as error:
            if attempt + 1 == args.attempts:
                raise SystemExit('FAIL: ' + str(error))
            time.sleep(10)

if __name__ == '__main__':
    main()
