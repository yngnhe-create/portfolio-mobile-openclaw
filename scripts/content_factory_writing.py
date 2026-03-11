#!/usr/bin/env python3
"""
Content Factory - Writing Agent
Creates investment reports based on research data
"""
import json
from datetime import datetime

def load_research():
    """Load research data from Research Agent"""
    try:
        with open('/tmp/research_output.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def generate_report():
    """Generate investment report"""
    data = load_research()
    
    if not data:
        print("❌ Research 데이터가 없습니다. Research Agent를 먼저 실행하세요.")
        return
    
    report = f"""
# 📊 투자 일일 리포트
## {data['date']}

---

## 💼 포트폴리오 요약

**총 자산**: {data['portfolio']['total_value']}  
**총 손익**: {data['portfolio']['total_pnl']}  

### 🏆 TOP 수익 종목
"""
    
    for i, stock in enumerate(data['portfolio']['top_gainers'], 1):
        report += f"""
{i}. **{stock['name']}**  
   - 수익률: {stock['pnl']}
   - 손익액: {stock['amount']}
"""
    
    report += f"""

### ⚠️ 주의 필요 종목
"""
    for alert in data['portfolio']['risk_alerts']:
        report += f"""
• **{alert['name']}**: {alert['loss']} ({alert['action']})
"""
    
    report += f"""

---

## 📈 와이즈리포트 인사이트

• **전체 리포트**: {data['wisereport']['total_reports']}개
• **BUY 권장**: {data['wisereport']['buy_recommendations']}개  
• **추천 섹터**: {', '.join(data['wisereport']['top_sectors'])}

### ⭐ Today Best
**{data['wisereport']['today_best']}**

---

## 🎯 오늘의 투자 전략

### BUY 관점
• 반도체/AI: HBM 수혜주 지속 (삼성전자, SK하이닉스)
• 배터리: 미국 ESS 수입제한 수혜 (삼성SDI, LG화학)
• 자동차: 로봇산업 진출 기대 (기아, 현대차)

### 리스크 관리
• 가상자산: 중동 리스크로 변동성 확대, 비중 축소 고려
• 리츠: 금리 민감, 단기 약세 가능

---

## 📰 핫 뉴스 요약

"""
    
    for event in data['events']:
        report += f"{event}\n"
    
    report += f"""

---

*이 리포트는 Content Factory에 의해 자동 생성되었습니다.*  
*생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    return report

def save_report():
    """Save report to file"""
    report = generate_report()
    
    filename = f"/tmp/investment_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n💾 리포트 저장 완료: {filename}")
    
    # Save summary for next agent
    summary = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "report_file": filename,
        "key_points": [
            "반도체/AI: HBM 수혜주",
            "배터리: ESS 수입제한 수혜", 
            "자동차: 로봇산업 진출"
        ]
    }
    
    with open('/tmp/writing_output.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False)
    
    return filename

if __name__ == "__main__":
    print("✍️ Writing Agent: 투자 리포트 작성 중...")
    save_report()
    print("\n✅ Writing 완료! Visualization Agent가 차트를 생성합니다.")
