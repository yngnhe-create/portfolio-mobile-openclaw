#!/usr/bin/env python3
# Korean News Only - Fast Scan

import xml.etree.ElementTree as ET
import urllib.request
import ssl
import json
import os
from datetime import datetime

MEMORY_DIR = "/Users/geon/.openclaw/workspace/memory"
KOREAN_FEEDS = {
    "연합뉴스": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/all-news", 
    "머니투데이": "https://news.mt.co.kr/rss/rss.jsp?type=market",
    "아시아경제": "https://www.asiae.co.kr/rss/allnews.xml",
}

CATEGORIES = {
    "AI/테크": ["AI", "인공지능", "반도체", "엔비디아", "삼성전자", "SK하이닉스"],
    "부동산": ["부동산", "아파트", "재건축", "분양", "청약"],
    "암호화폐": ["비트코인", "이더리움", "가상화폐", "코인", "블록체인"],
    "글로벌마켓": ["나스닥", "S&P500", "연준", "금리", "달러", "환율"],
    "한국마켓": ["코스피", "코스닥", "KOSPI", "KOSDAQ", "삼성", "현대차"],
}

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

def categorize(title):
    text = title.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                return cat
    return "기타"

print("=" * 60)
print("📰 한국 경제 뉴스 (빠른 스캔)")
print("=" * 60)
print()

all_articles = []
for source, url in KOREAN_FEEDS.items():
    print(f"[{source}]...", end=" ", flush=True)
    xml = fetch_url(url)
    if xml:
        articles = parse_rss(xml)
        for art in articles:
            art['source'] = source
            art['category'] = categorize(art['title'])
            all_articles.append(art)
        print(f"✅ {len(articles)}개")
    else:
        print("❌ 실패")

print()
print("=" * 60)
print(f"📊 총 {len(all_articles)}개 기사")
print("=" * 60)
print()

# 출력
by_cat = {}
for art in all_articles:
    cat = art['category']
    if cat not in by_cat:
        by_cat[cat] = []
    by_cat[cat].append(art)

emoji = {"한국마켓": "🇰🇷", "글로벌마켓": "🌍", "AI/테크": "🤖", 
         "암호화폐": "₿", "부동산": "🏢", "기타": "📰"}

for cat in ["한국마켓", "글로벌마켓", "AI/테크", "암호화폐", "부동산", "기타"]:
    if cat not in by_cat:
        continue
    arts = by_cat[cat]
    print(f"{emoji.get(cat, '📰')} <b>{cat}</b>")
    for art in arts[:3]:
        print(f"• <a href='{art['url']}'>{art['title'][:50]}...</a>")
        print(f"  └ {art['source']}")
    print()

# 저장
os.makedirs(MEMORY_DIR, exist_ok=True)
with open(f"{MEMORY_DIR}/korean_news_fast.json", 'w') as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)
