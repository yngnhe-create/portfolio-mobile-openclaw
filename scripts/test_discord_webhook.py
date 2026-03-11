#!/usr/bin/env python3
"""
Discord Webhook Test Script
"""
import requests
import json
from datetime import datetime

def test_discord_webhook(webhook_url):
    """Test Discord webhook"""
    
    print("🧪 Testing Discord Webhook...")
    print(f"URL: {webhook_url[:50]}...")
    
    # Rich embed message
    embed = {
        "title": "📊 Content Factory 테스트",
        "description": "Discord 연동 테스트 중입니다!",
        "color": 3447003,  # Blue
        "fields": [
            {
                "name": "⏰ 시간",
                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "inline": True
            },
            {
                "name": "🤖 상태",
                "value": "테스트 성공!",
                "inline": True
            },
            {
                "name": "📈 샘플 데이터",
                "value": "• 총 자산: ₩11.4억\n• YTD: +11.2%\n• 리스크: 중간 (68점)",
                "inline": False
            }
        ],
        "footer": {
            "text": "Content Factory by OpenClaw"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    payload = {
        "content": "@here 테스트 메시지입니다! 🎉",
        "username": "Content Factory",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            print("✅ Discord webhook test successful!")
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
        test_discord_webhook(webhook_url)
    else:
        print("Usage: python3 test_discord_webhook.py <WEBHOOK_URL>")
        print("\nPlease provide your Discord webhook URL")
