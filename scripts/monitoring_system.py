#!/usr/bin/env python3
"""
스마트 투자 리서치 팀 (멀티 에이전트)
Master Orchestrator
"""
import json
import subprocess
from datetime import datetime
import os

class ResearchTeamOrchestrator:
    """리서치 팀 오케스트레이터"""
    
    def __init__(self):
        self.agents_dir = "/Users/geon/.openclaw/workspace/scripts/agents"
        self.results = {}
        
    def run_agent(self, agent_name):
        """개별 에이전트 실행"""
        print(f"\n🚀 [{agent_name}] 에이전트 실행 중...")
        
        script_path = f"{self.agents_dir}/{agent_name}.py"
        
        try:
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e), "agent": agent_name}
    
    def run_parallel(self, agent_names):
        """병렬 실행"""
        print("=" * 60)
        print("🤖 멀티 에이전트 병렬 실행")
        print("=" * 60)
        
        # 순차 실행 (실제로는 concurrent.futures로 병렬 가능)
        for name in agent_names:
            self.results[name] = self.run_agent(name)
        
        return self.results
    
    def aggregate_results(self):
        """결과 통합"""
        print("\n" + "=" * 60)
        print("📊 결과 통합 중...")
        print("=" * 60)
        
        all_alerts = []
        for agent, result in self.results.items():
            if "alerts" in result:
                all_alerts.extend(result["alerts"])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.results),
            "total_alerts": len(all_alerts),
            "alerts": all_alerts,
            "details": self.results
        }
    
    def generate_report(self, data):
        """최종 보고서 생성"""
        print("\n" + "=" * 60)
        print("📝 최종 보고서 생성")
        print("=" * 60)
        
        report = f"""
📊 **투자 모니터링 보고서**
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}

**감지된 알림 ({data['total_alerts']}개):**

"""
        
        for alert in data['alerts']:
            emoji = "⚠️" if alert.get('level') == 'HIGH' else "📌"
            report += f"{emoji} {alert.get('message', alert.get('title', '알림'))}\n"
        
        if not data['alerts']:
            report += "✅ 특이사항 없음\n"
        
        report += f"""
**실행된 에이전트:**
"""
        for agent in data['details'].keys():
            report += f"• {agent}\n"
        
        return report
    
    def send_notification(self, report):
        """알림 발송"""
        print("\n📤 텔레그램 알림 발송 중...")
        
        try:
            subprocess.run([
                "openclaw", "message", "send",
                "--channel", "telegram",
                "--channelId", "1478491246",
                "--message", report
            ], capture_output=True)
            print("✅ 발송 완료!")
        except Exception as e:
            print(f"❌ 발송 실패: {e}")
    
    def run(self):
        """전체 실행"""
        print("\n" + "=" * 60)
        print("🚀 24시간 감시 시스템 시작")
        print("=" * 60)
        
        # 3개 에이전트 병렬 실행
        agents = [
            "price_monitor_agent",
            "risk_monitor_agent", 
            "news_monitor_agent"
        ]
        
        self.run_parallel(agents)
        
        # 결과 통합
        data = self.aggregate_results()
        
        # 보고서 생성
        report = self.generate_report(data)
        
        # 알림 발송
        if data['total_alerts'] > 0:
            self.send_notification(report)
        
        # 결과 저장
        output_path = "/tmp/monitoring_report.json"
        with open(output_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과 저장: {output_path}")
        print("=" * 60)
        print("✅ 시스템 실행 완료!")
        print("=" * 60)

if __name__ == "__main__":
    orchestrator = ResearchTeamOrchestrator()
    orchestrator.run()
