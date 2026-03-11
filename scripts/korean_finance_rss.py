#!/usr/bin/env python3
"""
Korean Financial News RSS Scanner (Standard Library Only)
Categories: AI/Tech, Real Estate, Crypto, Global Market, Korea Market
"""

import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import hashlib
import json
import re
from datetime import datetime, timedelta
import os
import ssl

# Memory paths
MEMORY_DIR = "/Users/geon/.openclaw/workspace/memory"
NEWS_LOG = f"{MEMORY_DIR}/news_log.json"
CANDIDATES_FILE = f"{MEMORY_DIR}/news_candidates.json"

# Korean Financial News RSS Feeds
RSS_FEEDS = {
    # Tier 1: Primary Financial News
    "연합인포맥스": "https://www.yna.co.kr/rss/economy.xml",
    "연합뉴스경제": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "매일경제": "https://www.mk.co.kr/rss/301/",
    
    # Tier 2: Financial Media
    "머니투데이": "https://news.mt.co.kr/rss/rss.jsp?type=market",
    "아시아경제": "https://www.asiae.co.kr/rss/allnews.xml",
    "이데일리": "https://www.edaily.co.kr/rss/allnews.xml",
    "서울경제": "https://www.sedaily.com/rss/",
    
    # Tier 3: Tech & Industry
    "전자신문": "https://www.etnews.com/rss/",
    "아이뉴스24": "https://www.inews24.com/rss/",
}

# Keywords by category
CATEGORIES = {
    "AI/테크": ["AI", "인공지능", "ChatGPT", "클로드", "빅데이터", "반도체", "삼성전자", "SK하이닉스", "엔비디아"],
    "부동산": ["부동산", "아파트", "재건축", "재개발", "분양", "청약", "임대", "PF"],
    "암호화폐": ["비트코인", "이더리움", "가상화폐", "암호화폐", "코인", "블록체인", "ETF"],
    "글로벌마켓": ["나스닥", "S&P500", "다우", "연준", "금리", "달러", "환율", "미국"],
    "한국마켓": ["코스피", "코스닥", "KOSPI", "KOSDAQ", "삼성", "현대차", "네이버", "카카오"],
}

def load_seen_urls():
    """Load previously seen article URLs"""
    if os.path.exists(NEWS_LOG):
        try:
            with open(NEWS_LOG, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen_urls(urls):
    """Save seen URLs"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(NEWS_LOG, 'w') as f:
        json.dump(list(urls), f)

def fetch_rss(url, timeout=10):
    """Fetch RSS feed"""
    try:
        # Create SSL context that doesn't verify certificates (for some Korean sites)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def parse_rss(xml_content, source):
    """Parse RSS XML"""
    articles = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Find all item elements (RSS 2.0) or entry elements (Atom)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:10]:  # Top 10
            try:
                # Extract title
                title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text if title_elem is not None else ""
                
                # Extract link
                link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
                if link_elem is not None:
                    url = link_elem.text or link_elem.get('href', '')
                else:
                    url = ""
                
                # Extract description/summary
                desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                summary = desc_elem.text if desc_elem is not None else ""
                
                # Extract pubDate
                date_elem = item.find('pubDate') or item.find('{http://www.w3.org/2005/Atom}published')
                pub_date = date_elem.text if date_elem is not None else ""
                
                articles.append({
                    'title': title or "",
                    'url': url or "",
                    'summary': summary or "",
                    'pub_date': pub_date or "",
                    'source': source
                })
            except:
                continue
                
    except Exception as e:
        pass
    
    return articles

def categorize_article(title, summary):
    """Categorize article based on keywords"""
    text = f"{title} {summary}".lower()
    scores = {}
    
    for category, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "기타"

def score_article(title, source, category):
    """Score article quality"""
    score = 0
    
    # Source tier scoring
    tier1 = ["연합인포맥스", "연합뉴스경제", "한국경제", "매일경제"]
    tier2 = ["머니투데이", "아시아경제", "이데일리", "서울경제"]
    
    if source in tier1:
        score += 30
    elif source in tier2:
        score += 20
    else:
        score += 10
    
    # Category bonus
    if category in ["한국마켓", "글로벌마켓"]:
        score += 15
    elif category in ["AI/테크"]:
        score += 12
    elif category in ["암호화폐", "부동산"]:
        score += 8
    
    # Title quality
    if any(x in title for x in ["급등", "급락", "폭등", "폭락", "신고가", "신저가", "상한가", "하한가"]):
        score += 10
    
    return score

def scan_rss_feeds():
    """Scan all RSS feeds"""
    seen_urls = load_seen_urls()
    all_articles = []
    
    print("📡 Scanning RSS feeds...")
    print()
    
    for source, url in RSS_FEEDS.items():
        try:
            print(f"  [{source}]...", end=" ", flush=True)
            xml_content = fetch_rss(url)
            
            if xml_content is None:
                print("❌ Failed to fetch")
                continue
            
            articles = parse_rss(xml_content, source)
            new_count = 0
            
            for art in articles:
                url = art['url']
                if not url or url in seen_urls:
                    continue
                
                title = art['title']
                summary = art['summary']
                
                category = categorize_article(title, summary)
                score = score_article(title, source, category)
                
                article = {
                    'title': title,
                    'source': source,
                    'url': url,
                    'category': category,
                    'score': score,
                    'published': datetime.now().isoformat(),
                    'summary': summary[:200] if summary else ""
                }
                
                all_articles.append(article)
                seen_urls.add(url)
                new_count += 1
            
            print(f"✅ {new_count} new")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    save_seen_urls(seen_urls)
    return all_articles

def format_output(articles, top_n=10):
    """Format output for Telegram"""
    # Sort by score
    articles.sort(key=lambda x: x['score'], reverse=True)
    top_articles = articles[:top_n]
    
    # Group by category
    by_category = {}
    for art in top_articles:
        cat = art['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(art)
    
    # Format output
    output = []
    output.append("📊 <b>오늘의 투자 뉴스</b>")
    output.append(f"📅 {datetime.now().strftime('%Y.%m.%d %H:%M')}")
    output.append("")
    
    for category in ["한국마켓", "글로벌마켓", "AI/테크", "암호화폐", "부동산", "기타"]:
        if category not in by_category:
            continue
        
        articles_in_cat = by_category[category]
        emoji = {
            "한국마켓": "🇰🇷",
            "글로벌마켓": "🌍",
            "AI/테크": "🤖",
            "암호화폐": "₿",
            "부동산": "🏢",
            "기타": "📰"
        }.get(category, "📰")
        
        output.append(f"{emoji} <b>{category}</b>")
        for art in articles_in_cat[:3]:  # Top 3 per category
            # Escape HTML entities for Telegram
            title = art['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            output.append(f"• <a href='{art['url']}'>{title}</a>")
            output.append(f"  └ {art['source']} | Score: {art['score']}")
        output.append("")
    
    return "\n".join(output)

def main():
    print("=" * 60)
    print("📰 Korean Financial News Scanner")
    print("=" * 60)
    print()
    
    # Scan feeds
    articles = scan_rss_feeds()
    
    if not articles:
        print("\n⚠️  No new articles found")
        # Still output something for Telegram
        output = f"📊 <b>오늘의 투자 뉴스</b>\n📅 {datetime.now().strftime('%Y.%m.%d %H:%M')}\n\n⚠️ 새로운 기사가 없습니다."
    else:
        print(f"\n📊 Total new articles: {len(articles)}")
        
        # Format output
        output = format_output(articles)
    
    # Save candidates
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(CANDIDATES_FILE, 'w') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    # Print output
    print("\n" + "=" * 60)
    print("📤 Telegram Output:")
    print("=" * 60)
    print(output)
    print("=" * 60)
    
    # Save formatted output for Telegram
    output_file = f"{MEMORY_DIR}/news_output_telegram.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Also print the file path for OpenClaw to use
    print(f"\n📎 File path: {output_file}")

if __name__ == "__main__":
    main()