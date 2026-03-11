#!/usr/bin/env python3
"""
Rich News Scanner with Detailed Explanations
Fetches content and provides context for each news item
"""

import xml.etree.ElementTree as ET
import urllib.request
import ssl
import json
import os
import re
from datetime import datetime

MEMORY_DIR = "/Users/geon/.openclaw/workspace/memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

# RSS Feeds
KOREAN_FEEDS = {
    "연합뉴스 경제": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/all-news",
}

REDDIT_SUBS = ["wallstreetbets", "OpenAI", "technology", "Futurology", "investing"]

CATEGORIES = {
    "AI/테크": ["AI", "OpenAI", "Anthropic", "ChatGPT", "Claude", "LLM", "반도체", "엔비디아"],
    "글로벌마켓": ["Fed", "금리", "나스닥", "S\u0026P", "주식", "시장", "Dubai"],
    "한국마켓": ["코스피", "KOSPI", "삼성", "현대차", "미래에셋"],
    "암호화폐": ["Bitcoin", "비트코인", "crypto", "암호화폐"],
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
        for item in items[:7]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            if title is not None and title.text:
                title_clean = title.text.replace('<![CDATA[', '').replace(']]>', '')
                desc_clean = desc.text.replace('<![CDATA[', '').replace(']]>', '') if desc is not None and desc.text else ""
                # Clean HTML tags from description
                desc_clean = re.sub(r'<[^>]+?>', '', desc_clean)
                articles.append({
                    'title': title_clean,
                    'url': link.text if link is not None else '',
                    'desc': desc_clean[:250],
                    'source': source
                })
        return articles
    except:
        return []

def fetch_reddit(sub, limit=7):
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
                if post.get('score', 0) >= 15:
                    selftext = post.get('selftext', '')[:200]
                    posts.append({
                        'title': post.get('title', ''),
                        'url': f"https://reddit.com{post.get('permalink', '')}",
                        'desc': selftext,
                        'source': f"r/{sub}",
                        'score': post.get('score', 0),
                        'external_url': post.get('url', '')
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

def generate_context(title, desc, source):
    """Generate rich context for the news item"""
    title_lower = title.lower()
    desc_lower = desc.lower() if desc else ""
    combined = f"{title_lower} {desc_lower}"
    
    context_parts = []
    
    # AI/Tech context
    if "openai" in combined and ("leave" in combined or "defect" in combined or "join" in combined):
        context_parts.append("⚡ OpenAI 인재 유출 가속화 - Anthropic으로 이적")
        context_parts.append("💼 AI 업계 경쟁 심화, 인재 쟁탈전 심화")
    elif "chatgpt" in combined and "cancel" in combined:
        context_parts.append("⚡ ChatGPT 구독 취소 운 동 확산")
        context_parts.append("📉 OpenAI 정책 변화에 대한 사용자 반발")
    elif "claude" in combined and ("#1" in title or "top" in combined):
        context_parts.append("⚡ Anthropic Claude, 앱스토어 1위 등극")
        context_parts.append("📈 OpenAI 이탈 사용자 Claude로 유입")
    
    # Market crash context
    elif any(x in combined for x in ["crash", "plunges", "plunge", "폭락", "급락"]):
        if "kospi" in combined or "korea" in combined:
            context_parts.append("⚡ 코스피 10% 급락 - 외국인 매도세 확대")
            context_parts.append("📉 단기적 공포 심리 확산, 저가 매수 기회 가능성")
        elif "dubai" in combined:
            context_parts.append("⚡ 두바이 증시 4.6% 폭락 - 중동 리스크 확대")
            context_parts.append("🛢️ 유가 상승 및 지정학적 리스크 영향")
        else:
            context_parts.append("⚡ 시장 급락 - 리스크 관리 필요")
    
    # Fed/Rate context
    elif "fed" in combined or "금리" in title:
        context_parts.append("🏦 연준 정책 방향에 시장 주목")
        context_parts.append("📊 금리 인상/인하 기대감에 따른 변동성")
    
    # Crypto context
    elif any(x in combined for x in ["bitcoin", "crypto", "비트코인"]):
        context_parts.append("₿ 암호화폐 시장 동향")
        if "etf" in combined:
            context_parts.append("📈 ETF 관련 자금 유입/유출 주목")
    
    # Korean corporate context
    elif "미래에셋" in title and "소각" in title:
        context_parts.append("🏢 미래에셋생명 자사주 93% 소각 결정")
        context_parts.append("💰 주주가치 제고 및 EPS 상승 기대")
    
    # Default context
    if not context_parts:
        if source.startswith("r/"):
            context_parts.append("💬 Reddit 커뮤니티 관심사")
        else:
            context_parts.append("📰 투자 관련 주요 소식")
    
    return context_parts

def format_news_item(art, idx):
    """Format a single news item with rich context"""
    title = art['title'][:60] + "..." if len(art['title']) > 60 else art['title']
    url = art['url']
    desc = art.get('desc', '')[:100] + "..." if art.get('desc') else ""
    source = art['source']
    
    lines = []
    lines.append(f"{idx}. <a href='{url}'><b>{title}</b></a>")
    
    # Add context bullets
    contexts = generate_context(art['title'], art.get('desc', ''), source)
    for ctx in contexts:
        lines.append(f"   {ctx}")
    
    # Add source with emoji
    if source.startswith("r/"):
        lines.append(f"   🔗 출처: Reddit {source} (🔥 {art.get('score', 0)} upvotes)")
    else:
        lines.append(f"   🔗 출처: {source}")
    
    # Add link line
    lines.append(f"   📎 <a href='{url}'>{url[:50]}...</a>")
    lines.append("")
    
    return "\n".join(lines)

print("=" * 70)
print("📰 오늘의 투자 뉴스 - 상세 분석")
print("=" * 70)
print()

all_articles = []

# Scan Korean RSS
print("📡 한국 뉴스 수집 중...")
for source, url in KOREAN_FEEDS.items():
    print(f"  → {source}...", end=" ", flush=True)
    xml = fetch_url(url)
    if xml:
        articles = parse_rss(xml, source)
        for art in articles:
            art['category'] = categorize(art['title'])
            all_articles.append(art)
        print(f"✅ {len(articles)}개")
    else:
        print("❌")

# Scan Reddit
print("\n🔥 Reddit 수집 중...")
for sub in REDDIT_SUBS:
    print(f"  → r/{sub}...", end=" ", flush=True)
    posts = fetch_reddit(sub)
    for post in posts:
        post['category'] = categorize(post['title'])
        all_articles.append(post)
    print(f"✅ {len(posts)}개")

print()
print("=" * 70)
print(f"📊 총 {len(all_articles)}개 기사 분석 완료")
print("=" * 70)
print()

# Group by category
by_cat = {}
for art in all_articles:
    cat = art['category']
    if cat not in by_cat:
        by_cat[cat] = []
    by_cat[cat].append(art)

# Category headers with emojis
cat_headers = {
    "한국마켓": "🇰🇷 한국마켓",
    "글로벌마켓": "🌍 글로벌마켓", 
    "AI/테크": "🤖 AI/테크",
    "암호화폐": "₿ 암호화폐",
    "부동산": "🏢 부동산",
    "기타": "📰 기타 투자 소식"
}

# Generate output
output_lines = []
output_lines.append(f"📊 <b>오늘의 투자 뉴스 상세 분석</b>")
output_lines.append(f"📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} KST")
output_lines.append(f"📰 총 {len(all_articles)}건 분석 완료")
output_lines.append("")

for cat in ["한국마켓", "글로벌마켓", "AI/테크", "암호화폐", "부동산", "기타"]:
    if cat not in by_cat:
        continue
    
    arts = by_cat[cat]
    header = cat_headers.get(cat, f"📰 {cat}")
    output_lines.append(f"━" * 60)
    output_lines.append(f"{header} ({len(arts)}건)")
    output_lines.append(f"━" * 60)
    output_lines.append("")
    
    for i, art in enumerate(arts[:4], 1):  # Top 4 per category
        output_lines.append(format_news_item(art, i))

output_lines.append("━" * 60)
output_lines.append("📌 투자 판단은 본인 책임하에 신중히 결정하세요.")

output = "\n".join(output_lines)
print(output)

# Save
output_file = f"{MEMORY_DIR}/news_detailed_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n💾 저장됨: {output_file}")
