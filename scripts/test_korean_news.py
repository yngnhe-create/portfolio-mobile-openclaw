#!/usr/bin/env python3
# Quick Korean News Test

import xml.etree.ElementTree as ET
import urllib.request
import ssl

def fetch_url(url):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            return r.read().decode('utf-8', errors='ignore')
    except:
        return None

def parse_rss(xml):
    try:
        root = ET.fromstring(xml)
        items = root.findall('.//item')
        articles = []
        for item in items[:5]:
            title = item.find('title')
            link = item.find('link')
            if title is not None and title.text:
                articles.append({
                    'title': title.text.replace('<![CDATA[', '').replace(']]>', ''),
                    'url': link.text if link is not None else ''
                })
        return articles
    except:
        return []

# Test Korean RSS
feeds = {
    "연합뉴스": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "매일경제": "https://www.mk.co.kr/rss/301/",
}

print("📰 한국 경제 뉴스 테스트\n")

for source, url in feeds.items():
    print(f"[{source}]")
    xml = fetch_url(url)
    if xml:
        articles = parse_rss(xml)
        for i, art in enumerate(articles[:3], 1):
            print(f"  {i}. {art['title'][:40]}...")
    else:
        print("  ❌ 실패")
    print()

print("✅ 테스트 완료")
