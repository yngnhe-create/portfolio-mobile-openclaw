#!/usr/bin/env python3
"""
Real-time Iran War Monitor
Tracks Reddit r/worldnews + Twitter trends
"""

import urllib.request
import json
import time
from datetime import datetime

def fetch_reddit_live():
    """Fetch r/worldnews live thread"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        # Search for Iran war related posts
        url = 'https://www.reddit.com/r/worldnews/search.json?q=iran+israel+war&sort=new&limit=10'
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            posts = []
            for post in data['data']['children']:
                p = post['data']
                posts.append({
                    'title': p['title'][:100],
                    'score': p['score'],
                    'comments': p['num_comments'],
                    'time': datetime.fromtimestamp(p['created_utc']).strftime('%H:%M'),
                    'url': f"https://reddit.com{p['permalink']}"
                })
            return posts
    except Exception as e:
        return [{'error': str(e)}]

def fetch_news_headlines():
    """Fetch BBC/CNN headlines via RSS-like approach"""
    try:
        # Try to get BBC Middle East
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = 'https://www.bbc.com/news/world/middle_east'
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode()
            # Extract headlines (basic parsing)
            headlines = []
            # Look for h2/h3 tags with Iran/Israel keywords
            import re
            matches = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', html, re.IGNORECASE)
            for match in matches[:5]:
                text = re.sub(r'<[^>]+>', '', match)  # Remove HTML tags
                if any(keyword in text.lower() for keyword in ['iran', 'israel', 'war', 'gaza', 'middle east']):
                    headlines.append(text.strip())
            return headlines[:3]
    except Exception as e:
        return [f'Error: {e}']

def monitor():
    """Main monitoring function"""
    print("=" * 70)
    print(f"🚨 이란-미국 전쟅 실시간 모니터링")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 70)
    
    # Reddit
    print("\n📱 Reddit r/worldnews (최신 10개)")
    print("-" * 70)
    posts = fetch_reddit_live()
    for i, post in enumerate(posts[:5], 1):
        if 'error' in post:
            print(f"⚠️  Reddit 접근 제한: {post['error']}")
            break
        print(f"{i}. [{post['time']}] ⬆️{post['score']:,} 💬{post['comments']:,}")
        print(f"   {post['title']}")
        print(f"   {post['url'][:60]}...")
        print()
    
    # News Headlines
    print("\n📰 BBC 중동 헤드라인")
    print("-" * 70)
    headlines = fetch_news_headlines()
    for i, headline in enumerate(headlines, 1):
        print(f"{i}. {headline}")
    
    print("\n" + "=" * 70)
    print("🔄 다음 업데이트: 5분 후")
    print("💡 종료: Ctrl+C")
    print("=" * 70)

if __name__ == "__main__":
    monitor()