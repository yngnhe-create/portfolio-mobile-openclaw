#!/usr/bin/env python3
"""
Content Factory - Research Agent
Daily market research and data collection
"""
import subprocess
from datetime import datetime
import json

def research_market():
    """Collect daily market data"""
    
    # 1. Portfolio status
    portfolio_summary = {
        "total_value": "₩11.4억",
        "total_pnl": "+₩127M",
        "top_gainers": [
            {"name": "TIGER 코스피고배당", "pnl": "+80.8%", "amount": "+₩2.46M"},
            {"name": "삼성전자", "pnl": "+222%", "amount": "+₩77.4M"},
            {"name": "현대차3우B", "pnl": "+280%", "amount": "+₩23.5M"},
        ],
        "risk_alerts": [
            {"name": "파마리서치", "loss": "-12.9%", "action": "모니터링"},
            {"name": "코람코리츠", "loss": "-13.8%", "action": "모니터링"},
        ]
    }
    
    # 2. WiseReport highlights
    wisereport_data = {
        "total_reports": 74,
        "buy_recommendations": 44,
        "target_changes": 27,
        "top_sectors": ["반도체/AI", "배터리", "자동차/로봇"],
        "today_best": "디앤씨미디어 (매수, 목표가 17,000)"
    }
    
    # 3. Market events
    market_events = [
        "📰 이란-미국 분쟁: 중동 리스크 확산, 유가/방산주 주목",
        "📰 AI 거품론: 엔비디아 -4%, 기술주 밸류에이션 부담", 
        "📰 FOMC: 3월 금리 동결 확률 96%, 금리 인하 시점 하반기 전망",
        "📰 미국 ESS 수입제한: 삼성SDI·LG화학 수혜 기대"
    ]
    
    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "portfolio": portfolio_summary,
        "wisereport": wisereport_data,
        "events": market_events
    }

def post_to_discord():
    """Post research results (simulated - would post to Discord)"""
    data = research_market()
    
    message = f"""📊 **오늘의 시장 리서치** ({data['date']})

💼 **포트폴리오 현황**
• 총 자산: {data['portfolio']['total_value']}
• 총 손익: {data['portfolio']['total_pnl']}

🚀 **TOP 수익 종목**
"""
    
    for stock in data['portfolio']['top_gainers']:
        message += f"• {stock['name']}: {stock['pnl']} ({stock['amount']})\n"
    
    message += f"""
⚠️ **리스크 알림**
"""
    for alert in data['portfolio']['risk_alerts']:
        message += f"• {alert['name']}: {alert['loss']} - {alert['action']}\n"
    
    message += f"""
📈 **와이즈리포트**
• 전체: {data['wisereport']['total_reports']}개 리포트
• BUY: {data['wisereport']['buy_recommendations']}개
• Today Best: {data['wisereport']['today_best']}

🔥 **핫 이슈**
"""
    for event in data['events'][:3]:
        message += f"{event}\n"
    
    # In real implementation, this would post to Discord
    print(message)
    
    # Save for Writing Agent
    with open('/tmp/research_output.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return message

if __name__ == "__main__":
    print("🔍 Research Agent: 시장 데이터 수집 중...")
    result = post_to_discord()
    print("\n✅ Research 완료! Writing Agent가 이어서 작업합니다.")
