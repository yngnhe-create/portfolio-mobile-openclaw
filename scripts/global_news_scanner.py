#!/usr/bin/env python3
"""
Integrated Global + Korean Financial News Scanner
Sources: Reddit, TechCrunch, OpenAI, RSS feeds (Korean + International)
Categories: AI/Tech, Real Estate, Crypto, Global Market, Korea Market
"""

import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import json
import re
import ssl
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os

# Memory paths
MEMORY_DIR = "/Users/geon/.openclaw/workspace/memory"
NEWS_LOG = f"{MEMORY_DIR}/news_log.json"
CANDIDATES_FILE = f"{MEMORY_DIR}/news_candidates.json"

# ===== RSS FEEDS =====

# Korean Financial News
KOREAN_FEEDS = {
    "연합인포맥스": "https://www.yna.co.kr/rss/economy.xml",
    "연합뉴스경제": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "매일경제": "https://www.mk.co.kr/rss/301/",
    "머니투데이": "https://news.mt.co.kr/rss/rss.jsp?type=market",
    "아시아경제": "https://www.asiae.co.kr/rss/allnews.xml",
    "이데일리": "https://www.edaily.co.kr/rss/allnews.xml",
    "서울경제": "https://www.sedaily.com/rss/",
    "전자신문": "https://www.etnews.com/rss/",
    "아이뉴스24": "https://www.inews24.com/rss/",
}

# International Tech & AI
TECH_FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "THE DECODER": "https://the-decoder.com/feed/",
    "Simon Willison": "https://simonwillison.net/atom/everything/",
    "Ben's Bites": "https://www.bensbites.com/feed",
}

# Global Financial News
GLOBAL_FEEDS = {
    "Reuters Tech": "https://www.reuters.com/technology/rss",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "CNBC Finance": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "Financial Times": "https://www.ft.com/?format=rss",
    "WSJ Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "MarketWatch": "https://www.marketwatch.com/rss/topstories",
}

# ===== REDDIT SUBREDDITS =====
REDDIT_SUBS = {
    "machinelearning": 30,
    "artificial": 25,
    "singularity": 20,
    "LocalLLaMA": 30,
    "OpenAI": 25,
    "ChatGPT": 30,
    "ClaudeAI": 20,
    "technology": 40,
    "Futurology": 35,
    "investing": 30,
    "wallstreetbets": 50,
    "cryptocurrency": 35,
    "Bitcoin": 30,
}

# ===== KEYWORDS BY CATEGORY =====
CATEGORIES = {
    "AI/테크": [
        "AI", "artificial intelligence", "machine learning", "deep learning",
        "ChatGPT", "GPT", "Claude", "Gemini", "LLM", "large language model",
        "OpenAI", "Anthropic", "Google AI", "Meta AI",
        "반도체", "semiconductor", "NVIDIA", "엔비디아", "GPU",
        "삼성전자", "SK하이닉스", "Samsung", "SK Hynix",
        "빅데이터", "big data", "cloud", "클우드"
    ],
    "부동산": [
        "부동산", "real estate", "아파트", "apartment",
        "재건축", "재개발", "분양", "청약",
        "임대", "rent", "PF", "project financing",
        "property", "housing", "mortgage", "REITs"
    ],
    "암호화폐": [
        "비트코인", "Bitcoin", "이더리움", "Ethereum",
        "가상화폐", "cryptocurrency", "crypto",
        "블록체인", "blockchain", "DeFi", "NFT",
        "코인", "coin", "altcoin", "stablecoin",
        "ETF", "spot ETF", "halving"
    ],
    "글로벌마켓": [
        "나스닥", "Nasdaq", "S\u0026P500", "Dow", "다우",
        "연준", "Fed", "금리", "interest rate",
        "달러", "USD", "환율", "exchange rate",
        "미국", "US market", "Europe", "China",
        "inflation", "CPI", "GDP", "recession"
    ],
    "한국마켓": [
        "코스피", "KOSPI", "코스닥", "KOSDAQ",
        "삼성", "Samsung", "현대차", "Hyundai", "네이버", "Naver", "카카오", "Kakao",
        "LG", "SK", "기아", "Kia",
        "한국", "Korea", "서울", "Seoul",
        "기관", "외국인", "매수", "매도"
    ],
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

def fetch_url(url, timeout=10):
    """Fetch URL content"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='ignore')
    except:
        return None

def parse_rss(xml_content, source):
    """Parse RSS XML"""
    articles = []
    
    try:
        root = ET.fromstring(xml_content)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:15]:
            try:
                title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text if title_elem is not None else ""
                
                link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
                if link_elem is not None:
                    url = link_elem.text or link_elem.get('href', '')
                else:
                    url = ""
                
                desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                summary = desc_elem.text if desc_elem is not None else ""
                
                articles.append({
                    'title': title or "",
                    'url': url or "",
                    'summary': summary or "",
                    'source': source
                })
            except:
                continue
    except:
        pass
    
    return articles

def fetch_reddit(subreddit, min_score=30):
    """Fetch Reddit posts from subreddit"""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (NewsBot/1.0)'}
        req = urllib.request.Request(url, headers=headers)
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            posts = []
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                score = post.get('score', 0)
                
                if score >= min_score:
                    posts.append({
                        'title': post.get('title', ''),
                        'url': f"https://reddit.com{post.get('permalink', '')}",
                        'summary': post.get('selftext', '')[:200],
                        'source': f"r/{subreddit}",
                        'score': score
                    })
            return posts
    except:
        return []

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

def score_article(title, source, category, is_reddit=False, reddit_score=0):
    """Score article quality"""
    score = 0
    
    # Source tier scoring
    tier1_kr = ["연합인포맥스", "연합뉴스경제", "한국경제", "매일경제"]
    tier2_kr = ["머니투데이", "아시아경제", "이데일리", "서울경제"]
    tier1_intl = ["Reuters", "Bloomberg", "OpenAI Blog", "TechCrunch AI"]
    tier2_intl = ["The Verge", "MIT Tech Review", "Ars Technica", "Hugging Face"]
    
    if source in tier1_kr or source in tier1_intl:
        score += 30
    elif source in tier2_kr or source in tier2_intl:
        score += 20
    elif "reddit" in source.lower() or source.startswith("r/"):
        score += 10 + (reddit_score // 10)  # Bonus for high Reddit score
    else:
        score += 15
    
    # Category bonus
    if category in ["한국마켓", "글로벌마켓"]:
        score += 15
    elif category in ["AI/테크"]:
        score += 12
    elif category in ["암호화폐", "부동산"]:
        score += 8
    
    # Title quality signals
    boost_keywords = ["급등", "급락", "폭등", "폭락", "신고가", "신저가", 
                      "breakthrough", "launch", "announces", "partnership",
                      "acquisition", "IPO", "earnings", "beats", "surge", "plunge"]
    if any(x.lower() in title.lower() for x in boost_keywords):
        score += 10
    
    return score

def scan_all_sources():
    """Scan all news sources"""
    seen_urls = load_seen_urls()
    all_articles = []
    
    print("=" * 60)
    print("📰 Scanning Korean Financial News...")
    print("=" * 60)
    
    # Scan Korean RSS
    for source, url in KOREAN_FEEDS.items():
        try:
            print(f"  [{source}]...", end=" ", flush=True)
            xml = fetch_url(url)
            if xml:
                articles = parse_rss(xml, source)
                new = 0
                for art in articles:
                    if art['url'] and art['url'] not in seen_urls:
                        cat = categorize_article(art['title'], art['summary'])
                        score = score_article(art['title'], source, cat)
                        all_articles.append({
                            **art, 'category': cat, 'score': score,
                            'published': datetime.now().isoformat()
                        })
                        seen_urls.add(art['url'])
                        new += 1
                print(f"✅ {new} new")
            else:
                print("❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("🌍 Scanning International Tech News...")
    print("=" * 60)
    
    # Scan International RSS
    for source, url in TECH_FEEDS.items():
        try:
            print(f"  [{source}]...", end=" ", flush=True)
            xml = fetch_url(url)
            if xml:
                articles = parse_rss(xml, source)
                new = 0
                for art in articles:
                    if art['url'] and art['url'] not in seen_urls:
                        cat = categorize_article(art['title'], art['summary'])
                        score = score_article(art['title'], source, cat)
                        all_articles.append({
                            **art, 'category': cat, 'score': score,
                            'published': datetime.now().isoformat()
                        })
                        seen_urls.add(art['url'])
                        new += 1
                print(f"✅ {new} new")
            else:
                print("❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("💹 Scanning Global Financial News...")
    print("=" * 60)
    
    # Scan Global RSS
    for source, url in GLOBAL_FEEDS.items():
        try:
            print(f"  [{source}]...", end=" ", flush=True)
            xml = fetch_url(url)
            if xml:
                articles = parse_rss(xml, source)
                new = 0
                for art in articles:
                    if art['url'] and art['url'] not in seen_urls:
                        cat = categorize_article(art['title'], art['summary'])
                        score = score_article(art['title'], source, cat)
                        all_articles.append({
                            **art, 'category': cat, 'score': score,
                            'published': datetime.now().isoformat()
                        })
                        seen_urls.add(art['url'])
                        new += 1
                print(f"✅ {new} new")
            else:
                print("❌ Failed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("🔥 Scanning Reddit...")
    print("=" * 60)
    
    # Scan Reddit
    for subreddit, min_score in REDDIT_SUBS.items():
        try:
            print(f"  [r/{subreddit}]...", end=" ", flush=True)
            posts = fetch_reddit(subreddit, min_score)
            new = 0
            for post in posts:
                if post['url'] and post['url'] not in seen_urls:
                    cat = categorize_article(post['title'], post['summary'])
                    score = score_article(post['title'], f"r/{subreddit}", cat, 
                                        is_reddit=True, reddit_score=post.get('score', 0))
                    all_articles.append({
                        **post, 'category': cat, 'score': score,
                        'published': datetime.now().isoformat()
                    })
                    seen_urls.add(post['url'])
                    new += 1
            print(f"✅ {new} new")
        except Exception as e:
            print(f"❌ Error")
    
    save_seen_urls(seen_urls)
    return all_articles

def format_output(articles, top_n=15):
    """Format output for Telegram"""
    articles.sort(key=lambda x: x['score'], reverse=True)
    top_articles = articles[:top_n]
    
    by_category = {}
    for art in top_articles:
        cat = art['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(art)
    
    output = []
    output.append("📊 <b>오늘의 투자 뉴스</b>")
    output.append(f"📅 {datetime.now().strftime('%Y.%m.%d %H:%M')}")
    output.append(f"📰 Total Sources: {len(KOREAN_FEEDS) + len(TECH_FEEDS) + len(GLOBAL_FEEDS)} RSS + {len(REDDIT_SUBS)} Reddit")
    output.append("")
    
    category_order = ["AI/테크", "글로벌마켓", "한국마켓", "암호화폐", "부동산", "기타"]
    emoji_map = {
        "AI/테크": "🤖", "글로벌마켓": "🌍", "한국마켓": "🇰🇷",
        "암호화폐": "₿", "부동산": "🏢", "기타": "📰"
    }
    
    for category in category_order:
        if category not in by_category:
            continue
        
        articles_in_cat = by_category[category]
        emoji = emoji_map.get(category, "📰")
        
        output.append(f"{emoji} <b>{category}</b>")
        for art in articles_in_cat[:3]:
            title = art['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            output.append(f"• <a href='{art['url']}'>{title}</a>")
            src = art['source']
            if src.startswith('r/'):
                output.append(f"  └ 🔥 Reddit {src} | Score: {art['score']}")
            else:
                output.append(f"  └ {src} | Score: {art['score']}")
        output.append("")
    
    return "\n".join(output)

def main():
    print("=" * 70)
    print("🚀 Global + Korean Financial News Scanner")
    print("=" * 70)
    print()
    
    articles = scan_all_sources()
    
    print()
    print("=" * 70)
    print(f"📊 Summary: {len(articles)} new articles found")
    print("=" * 70)
    
    if not articles:
        output = f"📊 <b>오늘의 투자 뉴스</b>\n📅 {datetime.now().strftime('%Y.%m.%d %H:%M')}\n\n⚠️ 새로운 기사가 없습니다."
    else:
        output = format_output(articles)
    
    # Save
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(CANDIDATES_FILE, 'w') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    output_file = f"{MEMORY_DIR}/news_output_telegram.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    # Print
    print()
    print("📤 Telegram Output:")
    print("-" * 70)
    print(output)
    print("-" * 70)
    print(f"\n💾 Saved: {output_file}")

if __name__ == "__main__":
    main()