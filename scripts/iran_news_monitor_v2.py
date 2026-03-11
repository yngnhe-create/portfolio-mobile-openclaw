#!/usr/bin/env python3
"""
X/Twitter Alternative: Google News RSS + Reddit Combo
Free, stable, no API key needed
"""

import urllib.request
import json
import re
from datetime import datetime
from xml.etree import ElementTree as ET

def fetch_google_news_rss(query):
    """Fetch Google News RSS"""
    try:
        # Google News RSS
        encoded_query = query.replace(' ', '%20')
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            
            # Parse RSS
            root = ET.fromstring(content)
            items = []
            
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                if title is not None:
                    items.append({
                        'title': title.text[:120] if title.text else '',
                        'link': link.text if link is not None else '',
                        'time': pub_date.text if pub_date is not None else '',
                        'source': source.text if source is not None else 'Unknown'
                    })
            
            return items[:10]
            
    except Exception as e:
        print(f"   Error: {e}")
        return []

def fetch_reddit_iran():
    """Fetch Reddit r/worldnews hot"""
    try:
        url = 'https://www.reddit.com/r/worldnews/hot.json?limit=10'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            posts = []
            
            for post in data['data']['children']:
                p = post['data']
                title = p['title'].lower()
                
                # Filter Iran/Israel related
                if any(keyword in title for keyword in ['iran', 'israel', 'gaza', 'middle east', 'war']):
                    posts.append({
                        'title': p['title'][:100],
                        'score': p['score'],
                        'comments': p['num_comments'],
                        'url': f"https://reddit.com{p['permalink']}"
                    })
            
            return posts[:5]
            
    except Exception as e:
        print(f"   Reddit Error: {e}")
        return []

def monitor_news():
    """Main monitoring function"""
    print("=" * 70)
    print(f"🌍 이란 전쟅 실시간 뉴스 모니터링")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 70)
    
    # Google News
    queries = [
        "이란 미국 전쟅",
        "Iran Israel war",
        "Middle East conflict"
    ]
    
    print("\n📰 Google News (최신)")
    print("-" * 70)
    
    all_news = []
    for query in queries:
        news = fetch_google_news_rss(query)
        if news:
            print(f"\n🔍 '{query}': {len(news)}건")
            for i, item in enumerate(news[:3], 1):
                print(f"{i}. [{item['source']}] {item['title']}")
                all_news.append(item)
    
    # Reddit
    print("\n\n📱 Reddit r/worldnews (핫토픽)")
    print("-" * 70)
    
    reddit_posts = fetch_reddit_iran()
    if reddit_posts:
        for i, post in enumerate(reddit_posts, 1):
            print(f"{i}. ⬆️{post['score']:,} 💬{post['comments']:,}")
            print(f"   {post['title']}")
    else:
        print("   데이터 수집 중...")
    
    # Summary
    print("\n" + "=" * 70)
    print(f"📊 총 수집: 뉴스 {len(all_news)}건 + Reddit {len(reddit_posts)}건")
    print("🔄 다음 업데이트: 5분 후")
    print("=" * 70)

if __name__ == "__main__":
    monitor_news()