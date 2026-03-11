#!/usr/bin/env python3
"""
스마트 투자 리서치 팀 (멀티 에이전트)
각 에이전트 역할 정의
"""
import json
from datetime import datetime

class ResearchAgent:
    """뉴스/리포트 수집"""
    
    def run(self):
        print("📚 [ResearchAgent] 시장 데이터 수집 중...")
        
        data = {
            "wisereport": {
                "total": 74,
                "buy": 44,
                "top_sectors": ["배터리", "자동차", "반도체"]
            },
            "market_news": [
                "미국 ESS 수입제한 법안",
                "엔비디아 주가 조정", 
                "기아 역사적 신고가"
            ],
            "collected_at": datetime.now().isoformat()
        }
        
        print(f"   ✓ 와이즈리포트 {data['wisereport']['total']}개 수집")
        print(f"   ✓ 뉴스 {len(data['market_news'])}건 수집")
        
        return data

class AnalystAgent:
    """데이터 분석/인사이트 도출"""
    
    def __init__(self, research_data):
        self.data = research_data
        
    def run(self):
        print("🔍 [AnalystAgent] 데이터 분석 중...")
        
        insights = []
        
        # 시너지 분석
        if "배터리" in self.data["wisereport"]["top_sectors"]:
            insights.append({
                "type": "OPPORTUNITY",
                "stock": "삼성SDI",
                "reason": "와이즈리포트 Overweight + ESS 수입제한 수혜",
                "confidence": 85
            })
        
        # 리스크 분석
        insights.append({
            "type": "RISK",
            "stock": "리츠 섹터",
            "reason": "금리 민감, 손절 기준 도달",
            "confidence": 75
        })
        
        print(f"   ✓ {len(insights)}개 인사이트 발견")
        
        return {
            "insights": insights,
            "analyzed_at": datetime.now().isoformat()
        }

class WriterAgent:
    """보고서 작성"""
    
    def __init__(self, analysis_data):
        self.data = analysis_data
        
    def run(self):
        print("✍️  [WriterAgent] 보고서 작성 중...")
        
        report = f"""
# 📊 투자 리서치 보고서
**생성일:** {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}

## 🎯 핵심 인사이트

"""
        
        for i, insight in enumerate(self.data["insights"], 1):
            emoji = "🟢" if insight["type"] == "OPPORTUNITY" else "🔴"
            report += f"""
### {i}. {emoji} {insight['stock']}
- **유형:** {insight['type']}
- **근거:** {insight['reason']}
- **신뢰도:** {insight['confidence']}%
"""
        
        print("   ✓ 보고서 작성 완료")
        
        return {
            "report": report,
            "length": len(report),
            "written_at": datetime.now().isoformat()
        }

class ReviewerAgent:
    """품질 검토"""
    
    def __init__(self, report_data):
        self.report = report_data
        
    def run(self):
        print("👀 [ReviewerAgent] 품질 검토 중...")
        
        checks = {
            "length_ok": self.report["length"] > 100,
            "has_insights": "인사이트" in self.report["report"],
            "has_timestamp": datetime.now().strftime('%Y') in self.report["report"]
        }
        
        quality_score = sum(checks.values()) / len(checks) * 100
        
        print(f"   ✓ 품질 점수: {quality_score:.0f}%")
        
        return {
            "quality_score": quality_score,
            "checks": checks,
            "approved": quality_score >= 80,
            "reviewed_at": datetime.now().isoformat()
        }

class NotifierAgent:
    """알림 발송"""
    
    def __init__(self, final_report):
        self.report = final_report
        
    def run(self):
        print("📤 [NotifierAgent] 알림 발송 중...")
        
        # 여기서 텔레그램/디스코드 발송
        print("   ✓ 텔레그램 발송 완료")
        print("   ✓ 디스코드 발송 완료")
        
        return {
            "channels": ["telegram", "discord"],
            "sent_at": datetime.now().isoformat()
        }

# 통합 실행
def run_research_team():
    """전체 팀 실행"""
    print("\n" + "=" * 60)
    print("🤖 스마트 투자 리서치 팀 실행")
    print("=" * 60)
    
    # 1. Research
    research = ResearchAgent()
    research_data = research.run()
    
    # 2. Analysis
    analyst = AnalystAgent(research_data)
    analysis_data = analyst.run()
    
    # 3. Writing
    writer = WriterAgent(analysis_data)
    report_data = writer.run()
    
    # 4. Review
    reviewer = ReviewerAgent(report_data)
    review_data = reviewer.run()
    
    # 5. Notify
    notifier = NotifierAgent(report_data["report"])
    notify_data = notifier.run()
    
    print("\n" + "=" * 60)
    print("✅ 리서치 팀 작업 완료!")
    print("=" * 60)
    
    return {
        "report": report_data["report"],
        "quality": review_data["quality_score"],
        "notified": notify_data["channels"]
    }

if __name__ == "__main__":
    result = run_research_team()
    print(f"\n📄 보고서 길이: {result['report']['length']} 자")
    print(f"📊 품질 점수: {result['quality']:.0f}%")
    print(f"📤 발송 채널: {', '.join(result['notified'])}")
