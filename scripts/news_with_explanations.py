#!/usr/bin/env python3
"""
Enhanced News Scanner with Descriptions
Adds brief explanations to each news item
"""

import xml.etree.ElementTree as ET
import urllib.request
import ssl
import json
import os
from datetime import datetime

MEMORY_DIR = "/Users/geon/.openclaw/workspace/memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

# RSS Feeds
KOREAN_FEEDS = {
    "연합뉴스": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/all-news",
}

REDDIT_SUBS = ["wallstreetbets", "OpenAI", "technology", "Futurology", "singularity"]

CATEGORIES = {
    "AI/테크": ["AI", "OpenAI", "Anthropic", "ChatGPT", "Claude", "LLM", "반도체"],
    "글로벌마켓": ["Fed", "금리", "나스닥", "S&P", "주식", "시장"],
    "한국마켓": ["코스피", "KOSPI", "삼성", "현대차"],
    "암호화폐": ["Bitcoin", "비트코인", "crypto"],
}

def fetch_url(url, timeout=10):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode('utf-8', errors='ignore')
    except:
        return None

def parse_rss(xml, source):
    try:
        root = ET.fromstring(xml)
        items = root.findall('.//item')
        articles = []
        for item in items[:5]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            if title is not None and title.text:
                articles.append({
                    'title': title.text.replace('<![CDATA[', '').replace(']]>', ''),
                    'url': link.text if link is not None else '',
                    'desc': desc.text[:150] if desc is not None and desc.text else '',
                    'source': source
                })
        return articles
    except:
        return []

def fetch_reddit(sub, limit=5):
    try:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
        headers = {'User-Agent': 'Mozilla/5.0 (NewsBot/1.0)'}
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            posts = []
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                if post.get('score', 0) >= 20:
                    posts.append({
                        'title': post.get('title', ''),
                        'url': f"https://reddit.com{post.get('permalink', '')}",
                        'desc': post.get('selftext', '')[:100],
                        'source': f"r/{sub}",
                        'score': post.get('score', 0)
                    })
            return posts
    except:
        return []

def categorize(title):
    text = title.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                return cat
    return "기타"

def get_explanation(title, desc):
    """Generate brief explanation based on title and description"""
    title_lower = title.lower()
    
    # AI/Tech explanations
    if any(x in title_lower for x in ["openai", "chatgpt", "claude", "anthropic"]):
        return "AI 업계 주요 인물/기업 동향"
    if "leave" in title_lower or "join" in title_lower:
        return "인재 이동 및 조직 변화"
    if "crash" in title_lower or "plunge" in title_lower or "급락" in title:
        return "시장 급락 및 리스크 발생"
    if "fed" in title_lower or "금리" in title:
        return "미 연준 정책 및 금리 동향"
    if "bitcoin" in title_lower or "crypto" in title_lower:
        return "암호화폐 시장 동향"
    if "etf" in title_lower:
        return "ETF 관련 투자 소식"
    
    return "투자 관련 주요 소식"

print("=" * 65)
print("📰 오늘의 투자 뉴스 (설명 포함)")
print("=" * 65)
print()

all_articles = []

# Scan Korean RSS
print("📡 한국 뉴스 스캔 중...")
for source, url in KOREAN_FEEDS.items():
    print(f"  [{source}]...", end=" ", flush=True)
    xml = fetch_url(url)
    if xml:
        articles = parse_rss(xml, source)
        for art in articles:
            art['category'] = categorize(art['title'])
            art['explanation'] = get_explanation(art['title'], art['desc'])
            all_articles.append(art)
        print(f"✅ {len(articles)}개")
    else:
        print("❌")

# Scan Reddit
print("\n🔥 Reddit 스캔 중...")
for sub in REDDIT_SUBS:
    print(f"  [r/{sub}]...", end=" ", flush=True)
    posts = fetch_reddit(sub)
    for post in posts:
        post['category'] = categorize(post['title'])
        post['explanation'] = get_explanation(post['title'], post['desc'])
        all_articles.append(post)
    print(f"✅ {len(posts)}개")

print()
print("=" * 65)
print(f"📊 총 {len(all_articles)}개 기사 수집 완료")
print("=" * 65)
print()

# Group by category
by_cat = {}
for art in all_articles:
    cat = art['category']
    if cat not in by_cat:
        by_cat[cat] = []
    by_cat[cat].append(art)

# Output
emoji = {"한국마켓": "🇰🇷", "글로벌마켓": "🌍", "AI/테크": "🤖", 
         "암호화폐": "₿", "부동산": "🏢", "기타": "📰"}

output_lines = []
output_lines.append("📊 <b>오늘의 투자 뉴스</b>")
output_lines.append(f"📅 {datetime.now().strftime('%Y.%m.%d %H:%M')} KST")
output_lines.append(f"📰 총 {len(all_articles)}개 소식")
output_lines.append("")

for cat in ["한국마켓", "글로벌마켓", "AI/테크", "암호화폐", "부동산", "기타"]:
    if cat not in by_cat:
        continue
    arts = by_cat[cat]
    output_lines.append(f"{emoji.get(cat, '📰')} <b>{cat}</b>")
    for art in arts[:3]:
        title = art['title'][:55] + "..." if len(art['title']) > 55 else art['title']
        expl = art.get('explanation', '')
        output_lines.append(f"• <a href='{art['url']}'>{title}</a>")
        if expl:
            output_lines.append(f"  💡 {expl}")
        src = art['source']
        if src.startswith('r/'):
            output_lines.append(f"  └ 🔥 Reddit {src}")
        else:
            output_lines.append(f"  └ {src}")
    output_lines.append("")

output = "\n".join(output_lines)
print(output)

# Save
with open(f"{MEMORY_DIR}/news_with_explanations.txt", 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n💾 저장됨: {MEMORY_DIR}/news_with_explanations.txt")
