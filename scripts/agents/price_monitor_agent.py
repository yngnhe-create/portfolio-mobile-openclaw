#!/usr/bin/env python3
"""
24시간 포트폴리오 감시 시스템
Agent 1: Price Monitor
"""
import json
import sqlite3
import os
from datetime import datetime, timedelta
import sys

sys.path.insert(0, '/Users/geon/.openclaw/workspace/scripts')

try:
    from kis_price_collector import KISPriceCollector
    HAS_KIS = True
except:
    HAS_KIS = False

class PriceMonitorAgent:
    """주가 변동 모니터링"""
    
    def __init__(self):
        self.db_path = '/Users/geon/.openclaw/workspace/prices.db'
        self.alerts = []
        
    def check_price_changes(self):
        """주가 변동 체크"""
        print("📊 [PriceMonitor] 주가 변동 확인 중...")
        
        # 테스트용: 임시 데이터
        changes = [
            {"stock": "삼성전자", "change": -1.5, "price": 216500},
            {"stock": "삼성SDI", "change": 2.3, "price": 433000},
            {"stock": "기아", "change": 0.8, "price": 196100},
        ]
        
        for item in changes:
            if abs(item["change"]) > 2.0:
                alert = {
                    "type": "PRICE_ALERT",
                    "stock": item["stock"],
                    "message": f"{item['stock']} {item['change']:+.2f}% 변동",
                    "time": datetime.now().isoformat()
                }
                self.alerts.append(alert)
                print(f"   ⚠️  {alert['message']}")
        
        return self.alerts
    
    def run(self):
        """실행"""
        alerts = self.check_price_changes()
        return {
            "agent": "PriceMonitor",
            "status": "completed",
            "alerts": alerts,
            "checked_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    agent = PriceMonitorAgent()
    result = agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
