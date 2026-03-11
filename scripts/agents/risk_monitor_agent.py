#!/usr/bin/env python3
"""
24시간 포트폴리오 감시 시스템
Agent 2: Risk Monitor
"""
import json
from datetime import datetime

class RiskMonitorAgent:
    """리스크 점수 모니터링"""
    
    def __init__(self):
        self.risk_threshold = 70
        self.alerts = []
        
    def calculate_risk_score(self):
        """리스크 점수 계산"""
        print("🎯 [RiskMonitor] 리스크 점수 계산 중...")
        
        # 현재 리스크 지표
        risks = {
            "집중도": 72,
            "변동성": 65,
            "유동성": 45,
            "환율": 78,
            "섹터": 58
        }
        
        # 총점 계산 (가중 평균)
        total_score = sum(risks.values()) / len(risks)
        
        print(f"   현재 리스크 점수: {total_score:.0f}/100")
        
        if total_score > self.risk_threshold:
            alert = {
                "type": "RISK_ALERT",
                "level": "HIGH",
                "score": total_score,
                "message": f"리스크 점수 {total_score:.0f}점! 주의 필요",
                "details": risks,
                "time": datetime.now().isoformat()
            }
            self.alerts.append(alert)
            print(f"   ⚠️  {alert['message']}")
        
        return {
            "score": total_score,
            "risks": risks,
            "alerts": self.alerts
        }
    
    def run(self):
        """실행"""
        result = self.calculate_risk_score()
        return {
            "agent": "RiskMonitor",
            "status": "completed",
            "score": result["score"],
            "alerts": result["alerts"],
            "checked_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    agent = RiskMonitorAgent()
    result = agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
