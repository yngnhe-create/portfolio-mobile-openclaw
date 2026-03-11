#!/usr/bin/env python3
"""
뉴스 리포트 Telegram 발송
"""

import json
import os
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse

def send_telegram_news():
    """뉴스 요약 Telegram 발송"""
    
    # 설정
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "1478491246")  # 네 chat_id
    
    if not bot_token:
        print("⚠️ TELEGRAM_BOT_TOKEN not set")
        return False
    
    # 오늘 리포트 파일 읽기
    today = datetime.now().strftime("%Y-%m-%d")
    report_file = Path(f"~/workspace/news_rss/news_summary_{today}.json").expanduser()
    
    if not report_file.exists():
        print(f"⚠️ Report not found: {report_file}")
        return False
    
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 메시지 구성
    message = f"""📰 **경제 뉴스 모닝 브리핑** ({today})

📊 **수집 현황**
• 총 {data['total_collected']}개 기사
• 핵심 기사 {len(data.get('high_score_articles', []))}개

🔥 **주요 뉴스 Top 5**
"""
    
    top_articles = data.get('top_articles', [])[:5]
    for i, article in enumerate(top_articles, 1):
        keywords = ', '.join(article.get('keywords', [])[:3])
        message += f"""
{i}. **{article['title'][:50]}...**
   └ {article['feed']} | {keywords}
"""
    
    # 키워드 분석
    all_keywords = []
    for article in top_articles:
        all_keywords.extend(article.get('keywords', []))
    
    keyword_counts = {}
    for k in all_keywords:
        keyword_counts[k] = keyword_counts.get(k, 0) + 1
    
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    message += f"""
📈 **오늘의 핵심 키워드**
"""
    for keyword, count in top_keywords:
        message += f"• #{keyword} ({count}회)\n"
    
    message += f"""
📁 **상세 리포트**
{Path('~/workspace/news_rss').expanduser()}/news_report_{today}.md

⏰ {datetime.now().strftime('%H:%M')} 업데이트
"""
    
    # Telegram API 호출
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('ok'):
                print("✅ Telegram 발송 완료")
                return True
            else:
                print(f"⚠️ Telegram error: {result}")
                return False
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False

if __name__ == "__main__":
    send_telegram_news()
