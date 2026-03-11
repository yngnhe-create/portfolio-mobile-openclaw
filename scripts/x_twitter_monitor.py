#!/usr/bin/env python3
"""
X/Twitter Monitor via Nitter (Free, No API Key)
Tracks Iran War related tweets in real-time
"""

import urllib.request
import json
import re
from datetime import datetime
from xml.etree import ElementTree as ET

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.it", 
    "https://nitter.cz",
    "https://nitter.privacydev.net"
]

SEARCH_QUERIES = [
    "Iran War",
    "Israel Iran", 
    "Middle East conflict",
    "Hormuz Strait",
    "Iran attack"
]

def fetch_nitter_rss(instance, query):
    """Fetch RSS feed from Nitter"""
    try:
        # URL encode query
        encoded_query = query.replace(' ', '%20')
        url = f"{instance}/search/rss?f=tweets&q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/rss+xml, application/xml'
        }
        
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
                
                if title is not None and link is not None:
                    items.append({
                        'title': title.text[:150] if title.text else '',
                        'link': link.text,
                        'time': pub_date.text if pub_date is not None else 'Unknown',
                        'source': instance
                    })
            
            return items[:5]  # Return top 5
            
    except Exception as e:
        return []

def monitor_x_twitter():
    """Main monitoring function"""
    print("=" * 70)
    print(f"🐦 X/Twitter 실시간 모니터링 (Nitter RSS)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 70)
    
    all_tweets = []
    
    for query in SEARCH_QUERIES:
        print(f"\n🔍 검색: '{query}'")
        print("-" * 70)
        
        for instance in NITTER_INSTANCES:
            tweets = fetch_nitter_rss(instance, query)
            
            if tweets:
                print(f"✅ {instance.split('//')[1]}: {len(tweets)}개 찾음")
                for tweet in tweets[:2]:  # Show top 2 per instance
                    print(f"   • {tweet['title'][:80]}...")
                    print(f"     {tweet['link'][:50]}...")
                    all_tweets.append(tweet)
                break  # Found working instance
            else:
                print(f"   {instance.split('//')[1]}: 실패")
    
    # Summary
    print("\n" + "=" * 70)
    print(f"📊 총 수집: {len(all_tweets)}개 트윗")
    print("💡 Nitter는 5~15분 지연될 수 있음")
    print("=" * 70)
    
    return all_tweets

if __name__ == "__main__":
    monitor_x_twitter()