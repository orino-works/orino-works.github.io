#!/usr/bin/env python3
"""Check the actual Hugo output using only Python's standard library."""
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.headings = []
        self.meta = {}
        self.canonical = []
        self.title = ''
        self.in_title = False
        self.lang = None
        self.has_main = False
        self.scripts = 0
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag in ('a', 'link') and a.get('href'):
            self.links.append(a['href'])
        if tag in ('img', 'script') and a.get('src'):
            self.links.append(a['src'])
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href', ''))
        if tag == 'meta':
            self.meta[a.get('name') or a.get('property')] = a.get('content', '')
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'main':
            self.has_main = True
        if re.fullmatch(r'h[1-6]', tag):
            self.headings.append(int(tag[1]))
        if tag == 'title':
            self.in_title = True
        self.scripts += tag == 'script'
        self.forms += tag == 'form'

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'public').resolve()
    origin = 'https://orino-works.github.io'
    errors = []
    pages = {}
    forbidden = re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,}|Japan-Bio-Tools|investment-os|gtag\(|googletagmanager\.com|google-analytics\.com|document\.cookie|localStorage', re.I)
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.name.startswith('.') or path.suffix in ('.md', '.toml', '.yml', '.yaml', '.py'):
            errors.append(f'Unexpected published source: {path.relative_to(root)}')
        content = path.read_text(encoding='utf-8')
        if forbidden.search(content) or re.search(r'\bG-[A-Z0-9]{6,}\b', content):
            errors.append(f'Potential secret, private project, or unapproved tracking: {path.relative_to(root)}')
        if path.suffix == '.html':
            p = Page()
            p.feed(content)
            pages[path] = p
            if p.lang != 'ja' or not p.has_main or p.headings.count(1) != 1:
                errors.append(f'Language/main/h1: {path.relative_to(root)}')
            if not p.title.strip() or not p.meta.get('description') or not p.meta.get('viewport'):
                errors.append(f'Title/description/viewport: {path.relative_to(root)}')
            if len(p.canonical) != 1 or not p.canonical[0].startswith(origin + '/'):
                errors.append(f'Canonical: {path.relative_to(root)}')
            for key in ('og:title', 'og:description', 'og:url', 'og:type', 'og:site_name'):
                if not p.meta.get(key):
                    errors.append(f'Missing {key}: {path.relative_to(root)}')
            if len(p.ids) != len(set(p.ids)):
                errors.append(f'Duplicate ids: {path.relative_to(root)}')
            if p.scripts or p.forms:
                errors.append(f'Unexpected script/form: {path.relative_to(root)}')
            if any(b > a + 1 for a, b in zip(p.headings, p.headings[1:])):
                errors.append(f'Skipped heading level: {path.relative_to(root)}')

    checked_links = 0
    for path, p in pages.items():
        for link in p.links:
            u = urlsplit(link)
            if u.scheme and u.scheme not in ('https', 'mailto'):
                errors.append(f'Unexpected URL scheme: {link}')
            if u.netloc and u.netloc != 'orino-works.github.io':
                continue
            if u.scheme == 'mailto':
                continue
            target = root / unquote(u.path).lstrip('/') if u.path.startswith('/') else path.parent / unquote(u.path)
            if not u.path:
                target = path
            if target.is_dir():
                target /= 'index.html'
            target = target.resolve()
            if not target.is_relative_to(root) or not target.exists():
                errors.append(f'Broken internal link in {path.relative_to(root)}: {link}')
            elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
                errors.append(f'Broken anchor in {path.relative_to(root)}: {link}')
            checked_links += 1

    required = ['index.html', '記事/index.html', '記事/chatgpt-営業活用/index.html', '記事/生成ai-仕事の準備/index.html', '運営者情報/index.html', 'お問い合わせ/index.html', 'プライバシー/index.html', '広告掲載方針/index.html', '404.html', 'sitemap.xml', 'robots.txt']
    for name in required:
        if not (root / name).exists():
            errors.append(f'Missing page: {name}')
    sitemap = root / 'sitemap.xml'
    if sitemap.exists():
        for loc in ET.parse(sitemap).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            u = urlsplit(loc.text or '')
            if u.netloc != 'orino-works.github.io' or not (root / unquote(u.path).lstrip('/') / 'index.html').exists():
                errors.append(f'Invalid sitemap location: {loc.text}')
    if (root / 'robots.txt').exists() and 'https://orino-works.github.io/sitemap.xml' not in (root / 'robots.txt').read_text():
        errors.append('Missing sitemap in robots.txt')
    if errors:
        for error in errors:
            print('FAIL:', error)
        raise SystemExit(1)
    print(f'PASS: {len(pages)} HTML pages, {checked_links} internal links, SEO metadata, headings, sitemap, robots, source/secret/tracking checks')
    print('LIMIT: automated scans do not prove the absence of every secret; review the source diff before merging.')
    print('LIMIT: responsive CSS is implemented; visual mobile/browser QA is a separate check.')
    print('CONTACT: no contact channel is configured; operator approval is required before configuration.')


if __name__ == '__main__':
    main()
