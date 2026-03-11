# 🤖 Discord Webhook 연동 가이드

## 1. Discord Webhook 생성

### 방법:
1. Discord 서버 → 채널 설정 → 연동 → 웹후크
2. "새 웹후크" 클릭
3. 이름: "Content Factory"
4. 채널 선택: #리서치, #리포트, #차트 등
5. "웹후크 URL 복사"

## 2. Python에서 Webhook 전송

```python
import requests
import json
from datetime import datetime

def send_to_discord(webhook_url, content, embeds=None):
    """Send message to Discord via webhook"""
    
    payload = {
        "content": content,
        "username": "Content Factory",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
        "embeds": embeds or []
    }
    
    response = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 204:
        print("✅ Discord message sent")
    else:
        print(f"❌ Error: {response.status_code}")
    
    return response.status_code == 204

# 사용 예시
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"

# 간단한 메시지
send_to_discord(
    WEBHOOK_URL,
    "📊 오늘의 포트폴리오 리포트가 생성되었습니다!"
)

# Rich Embed 메시지
embed = {
    "title": "📊 투자 일일 리포트",
    "description": "2026년 3월 2일 분석 결과",
    "color": 3447003,  # Blue
    "fields": [
        {
            "name": "💼 총 자산",
            "value": "₩11.4억",
            "inline": True
        },
        {
            "name": "📈 YTD 수익률",
            "value": "+11.2%",
            "inline": True
        },
        {
            "name": "🎯 TOP 수익 종목",
            "value": "1. 삼성전자 (+77.4M)\n2. 현대차3우B (+23.5M)\n3. 삼성전자우 (+21.2M)",
            "inline": False
        }
    ],
    "footer": {
        "text": "Content Factory 자동 생성"
    },
    "timestamp": datetime.now().isoformat()
}

send_to_discord(
    WEBHOOK_URL,
    "",
    embeds=[embed]
)
```

## 3. Content Factory에 통합

```python
# content_factory_master.py 수정

def send_to_discord():
    """Send report to Discord"""
    
    # Webhook URLs (각 채널별)
    WEBHOOK_RESEARCH = "https://discord.com/api/webhooks/XXX/YYY"  # #리서치
    WEBHOOK_REPORT = "https://discord.com/api/webhooks/XXX/YYY"    # #리포트
    WEBHOOK_CHART = "https://discord.com/api/webhooks/XXX/YYY"     # #차트
    
    # 1. 리서치 채널에 요약 전송
    research_embed = {
        "title": "🔍 오늘의 시장 리서치",
        "color": 3066993,  # Green
        "fields": [
            {"name": "📈 전체 리포트", "value": "74개", "inline": True},
            {"name": "💚 BUY 권장", "value": "44개", "inline": True},
            {"name": "🎯 목표가 변경", "value": "27개", "inline": True},
        ]
    }
    send_to_discord(WEBHOOK_RESEARCH, "", embeds=[research_embed])
    
    # 2. 리포트 채널에 상세 리포트 전송
    with open('/tmp/investment_report_YYYYMMDD.md', 'r') as f:
        report_content = f.read()
    
    # Discord는 2000자 제한이 있으므로 분할
    chunks = [report_content[i:i+1900] for i in range(0, len(report_content), 1900)]
    for i, chunk in enumerate(chunks):
        send_to_discord(
            WEBHOOK_REPORT,
            f"📄 리포트 (Part {i+1}/{len(chunks)})\n```markdown\n{chunk}\n```"
        )
    
    # 3. 차트 채널에 대시보드 링크 전송
    chart_embed = {
        "title": "📊 포트폴리오 대시보드",
        "description": "실시간 차트 및 분석",
        "color": 15158332,  # Orange
        "fields": [
            {
                "name": "🔗 대시보드 링크",
                "value": "[포트폴리오 보기](https://portfolio-mobile-openclaw.pages.dev)"
            },
            {
                "name": "🔗 와이즈리포트",
                "value": "[리포트 보기](https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html)"
            }
        ]
    }
    send_to_discord(WEBHOOK_CHART, "", embeds=[chart_embed])
```

## 4. 파일 첨부 (차트 이미지 등)

```python
def send_file_to_discord(webhook_url, file_path, message=""):
    """Send file to Discord"""
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        payload = {'content': message}
        
        response = requests.post(
            webhook_url,
            data=payload,
            files=files
        )
    
    return response.status_code == 200

# 차트 이미지 전송
send_file_to_discord(
    WEBHOOK_CHART,
    '/tmp/portfolio_chart.png',
    "📈 오늘의 포트폴리오 분포"
)
```

## 장점/단점

✅ **장점:**
- 설정 매우 간단 (5분 완료)
- 서버/봇 호스팅 불필요
- 물론 물질적 비용 없음

❌ **단점:**
- 단방향 통신만 가능 (Discord → Bot 불가)
- Webhook URL이 노출되면 보안 위험
- 복잡한 상호작용 불가

## 보안 주의사항

```python
# ❌ 안좋은 방법: 코드에 직접 URL
WEBHOOK_URL = "https://discord.com/api/webhooks/123456/abcdef..."

# ✅ 좋은 방법: 환경변수 사용
import os
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# 또는 설정 파일
import json
with open('config.json') as f:
    config = json.load(f)
    WEBHOOK_URL = config['discord_webhook_url']
```
