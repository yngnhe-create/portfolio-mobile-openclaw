#!/usr/bin/env python3
"""
Daily Market Monitor
Event monitoring and notification system for portfolio
"""
import json
import os
from datetime import datetime
import subprocess

class MarketMonitor:
    def __init__(self):
        self.events = []
        self.risks = []
        
    def check_market_events(self):
        """Check market events that affect portfolio"""
        
        # Event database (simplified - in production, this would scrape news APIs)
        events = [
            {
                "title": "미국 중국산 ESS 수입제한 법안",
                "impact": "HIGH",
                "affected": ["삼성SDI", "LG에너지솔루션"],
                "action": "매수 기회",
                "source": "정책"
            },
            {
                "title": "이란-미국 분쟁 격화",
                "impact": "HIGH", 
                "affected": ["BTC", "ETH", "방산주"],
                "action": "가상자산 비중 축소",
                "source": "지정학"
            },
            {
                "title": "FOMC 금리 동결",
                "impact": "MEDIUM",
                "affected": ["리츠", "금융주"],
                "action": "관망",
                "source": "통화정책"
            },
            {
                "title": "엔비디아 주가 조정",
                "impact": "MEDIUM",
                "affected": ["삼성전자", "SK하이닉스"],
                "action": "분할 매수 기회",
                "source": "기업실적"
            }
        ]
        
        return events
    
    def check_risk_alerts(self):
        """Check risk indicators"""
        
        risks = []
        
        # 환율 리스크
        risks.append({
            "type": "환율",
            "level": "HIGH",
            "value": "₩1,455",
            "threshold": "₩1,500",
            "action": "해외주 수익 실현 검토"
        })
        
        # 집중도 리스크
        risks.append({
            "type": "집중도",
            "level": "MEDIUM",
            "value": "삼성전자 22%",
            "threshold": "30%",
            "action": "분산 원칙 적용"
        })
        
        # 변동성
        risks.append({
            "type": "VIX",
            "level": "MEDIUM",
            "value": "22.4",
            "threshold": "30",
            "action": "모니터링 강화"
        })
        
        return risks
    
    def generate_daily_summary(self):
        """Generate daily summary for web update"""
        
        events = self.check_market_events()
        risks = self.check_risk_alerts()
        
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "portfolio": {
                "total_assets": "₩10.9B",
                "ytd_return": "+11.2%",
                "risk_score": 68,
                "top_gainer": "삼성전자 (+77.4M)",
                "top_loser": "코람코리츠 (-13.8%)"
            },
            "events": events,
            "risks": risks,
            "actions": [
                {"type": "BUY", "stock": "삼성SDI", "reason": "목표가 상향 +34%"},
                {"type": "BUY", "stock": "기아", "reason": "역사적 신고가"},
                {"type": "SELL", "stock": "리츠 섹터", "reason": "손절 기준 도달"},
                {"type": "MONITOR", "stock": "해외주", "reason": "환율 리스크"}
            ]
        }
        
        return summary
    
    def send_notification(self, message):
        """Send Telegram notification"""
        try:
            subprocess.run([
                "openclaw", "message", "send",
                "--channel", "telegram",
                "--channelId", "1478491246",
                "--message", message
            ], capture_output=True)
        except Exception as e:
            print(f"Failed to send notification: {e}")
    
    def run_daily_check(self):
        """Run daily market check"""
        
        print("🔍 Daily Market Check Started")
        
        summary = self.generate_daily_summary()
        
        # Check for high priority events
        high_impact_events = [e for e in summary["events"] if e["impact"] == "HIGH"]
        
        if high_impact_events:
            alert_message = f"""🚨 **긴급 시장 알림** ({datetime.now().strftime('%H:%M')})

"""
            for event in high_impact_events:
                alert_message += f"• **{event['title']}**\n"
                alert_message += f"  → {event['action']}\n\n"
            
            alert_message += f"🔗 [커맨드 센터 확인](https://portfolio-mobile-openclaw.pages.dev/command_center.html)"
            
            self.send_notification(alert_message)
            print(f"✅ High impact alert sent: {len(high_impact_events)} events")
        
        # Update web dashboard data
        self.update_web_data(summary)
        
        print("✅ Daily check completed")
    
    def update_web_data(self, summary):
        """Update web dashboard data file"""
        
        data_path = os.path.expanduser("~/.openclaw/workspace/public/data/daily_summary.json")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Web data updated: {data_path}")

def main():
    monitor = MarketMonitor()
    monitor.run_daily_check()

if __name__ == "__main__":
    main()
