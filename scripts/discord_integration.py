#!/usr/bin/env python3
"""
Discord Webhook Integration for Content Factory
"""
import requests
import json
from datetime import datetime

# Discord Webhook URLs
WEBHOOK_REPORT = "https://discord.com/api/webhooks/1477912490494001273/rARLAutiXuzcbDyCjVqwC9hZ-O4LiKghHsE2hP8gd-51OvJCUTAlw72Yl2uzMcpRjc2v"
WEBHOOK_RESEARCH = "https://discord.com/api/webhooks/1477912616822378539/ugYpAFGuJZldVIAQ8gRxmDIZF-4gRSzeRQvJei9ghsxRmD42NTaomGu0fCqarcVcu_Ig"
WEBHOOK_CHART = "https://discord.com/api/webhooks/1477912908330434571/EOoxL5XbkJPWVicGCX7WbpVJOnmAG8eMZk77-oudmY4GaibAL_py4rJWr1grmWwzP9GQ"

def send_to_discord(webhook_url, content=None, embeds=None, username="Content Factory"):
    """Send message to Discord via webhook"""
    
    payload = {
        "username": username,
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
    }
    
    if content:
        payload["content"] = content
    
    if embeds:
        payload["embeds"] = embeds
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            print(f"✅ Discord message sent to {webhook_url[:50]}...")
            return True
        else:
            print(f"❌ Discord Error {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Discord Exception: {e}")
        return False

def send_research_data(data):
    """Send research data to #리서치 channel"""
    
    embed = {
        "title": "🔍 오늘의 시장 리서치",
        "description": f"{datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}",
        "color": 3447003,  # Blue
        "fields": [
            {
                "name": "💼 포트폴리오 현황",
                "value": f"총 자산: {data.get('total_assets', '₩10.9억')}\nYTD 수익률: {data.get('ytd', '+11.2%')}",
                "inline": True
            },
            {
                "name": "📊 와이즈리포트",
                "value": f"전체: {data.get('total_reports', 74)}개\nBUY: {data.get('buy_count', 44)}개",
                "inline": True
            },
            {
                "name": "🚨 리스크 알림",
                "value": data.get('risk_alert', '• 파마리서치 -12.9%\n• 코람코리츠 -13.8%'),
                "inline": False
            }
        ],
        "footer": {
            "text": "Content Factory - Research Agent"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return send_to_discord(WEBHOOK_RESEARCH, embeds=[embed])

def send_report(report_content):
    """Send report to #리포트 channel"""
    
    # Send summary first
    summary_embed = {
        "title": "📊 투자 일일 리포트",
        "description": f"{datetime.now().strftime('%Y년 %m월 %d일')}",
        "color": 3066993,  # Green
        "fields": [
            {
                "name": "💰 총 자산",
                "value": "₩10.9억",
                "inline": True
            },
            {
                "name": "📈 YTD 수익률",
                "value": "+11.2%",
                "inline": True
            },
            {
                "name": "🎯 Today Best",
                "value": "디앤씨미디어 (매수, 목표가 17,000)",
                "inline": False
            },
            {
                "name": "🏆 TOP 3 수익 종목",
                "value": "1. 삼성전자 (+77.4M)\n2. 현대차3우B (+23.5M)\n3. 삼성전자우 (+21.2M)",
                "inline": False
            }
        ],
        "footer": {
            "text": "Content Factory - Writing Agent"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    send_to_discord(WEBHOOK_REPORT, embeds=[summary_embed])
    
    # Send links
    links_embed = {
        "title": "🔗 대시보드 링크",
        "color": 15158332,  # Orange
        "fields": [
            {
                "name": "📊 포트폴리오",
                "value": "[대시보드 보기](https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html)"
            },
            {
                "name": "📈 와이즈리포트",
                "value": "[리포트 보기](https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html)"
            },
            {
                "name": "📖 플레이북",
                "value": "[운영 가이드](https://portfolio-mobile-openclaw.pages.dev/portfolio_playbook.html)"
            }
        ]
    }
    
    return send_to_discord(WEBHOOK_REPORT, embeds=[links_embed])

def send_chart_update():
    """Send chart/dashboard update to #차트 channel"""
    
    embed = {
        "title": "📈 대시보드 업데이트 완료",
        "description": "모든 차트 및 데이터가 최신 상태로 업데이트되었습니다.",
        "color": 15158332,  # Orange
        "fields": [
            {
                "name": "📊 포트폴리오 대시보드",
                "value": "[바로가기](https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html)"
            },
            {
                "name": "📈 와이즈리포트 대시보드",
                "value": "[바로가기](https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html)"
            },
            {
                "name": "📖 포트폴리오 플레이북",
                "value": "[바로가기](https://portfolio-mobile-openclaw.pages.dev/portfolio_playbook.html)"
            }
        ],
        "footer": {
            "text": "Content Factory - Visualization Agent"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return send_to_discord(WEBHOOK_CHART, embeds=[embed])

def test_all_webhooks():
    """Test all Discord webhooks"""
    print("🧪 Testing all Discord webhooks...")
    
    # Test research
    print("\n1. Testing #리서치...")
    send_to_discord(
        WEBHOOK_RESEARCH,
        content="🧪 테스트 메시지입니다!",
        embeds=[{
            "title": "🔍 리서치 채널 테스트",
            "description": "Content Factory 연동 테스트 중",
            "color": 3447003
        }]
    )
    
    # Test report
    print("2. Testing #리포트...")
    send_to_discord(
        WEBHOOK_REPORT,
        content="🧪 테스트 메시지입니다!",
        embeds=[{
            "title": "📊 리포트 채널 테스트",
            "description": "Content Factory 연동 테스트 중",
            "color": 3066993
        }]
    )
    
    # Test chart
    print("3. Testing #차트...")
    send_to_discord(
        WEBHOOK_CHART,
        content="🧪 테스트 메시지입니다!",
        embeds=[{
            "title": "📈 차트 채널 테스트",
            "description": "Content Factory 연동 테스트 중",
            "color": 15158332
        }]
    )
    
    print("\n✅ All webhooks tested!")

if __name__ == "__main__":
    # Test all webhooks
    test_all_webhooks()
