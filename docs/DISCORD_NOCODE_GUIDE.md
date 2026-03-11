# ⚡ Zapier/Make Discord 연동 (노코드)

## 개요
코딩 없이 워크플로우 자동화 도구로 Discord 연동

## Zapier 사용법

### 1. Zap 생성
```
Trigger: Schedule (Cron) - 매일 8시
Action: Discord - Send Channel Message
```

### 2. Content Factory와 연결
```
Trigger: Webhook (from Content Factory)
Action: Discord - Send Message
```

### 3. Python에서 Zapier 호출
```python
import requests

def trigger_zapier():
    """Trigger Zapier webhook"""
    
    ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/XXX/YYY/"
    
    payload = {
        "date": datetime.now().isoformat(),
        "total_assets": "₩11.4억",
        "ytd_return": "+11.2%",
        "top_gainer": "삼성전자 (+77.4M)",
        "report_url": "https://portfolio-mobile-openclaw.pages.dev"
    }
    
    requests.post(ZAPIER_WEBHOOK, json=payload)
```

## Make (Integromat) 사용법

시나리오:
1. HTTP Webhook (Content Factory → Make)
2. Discord → Send Message
3. Filter (조걶 ��� 알림)

## 장점/단점

✅ **장점:**
- 코딩 불필요
- 시각적 워크플로우
- 100+ 앱 연동

❌ **단점:**
- 월 100회 물료, 초과시 유료
- 커스터마이징 제한적
