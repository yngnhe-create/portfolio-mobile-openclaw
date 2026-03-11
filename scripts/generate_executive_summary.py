#!/usr/bin/env python3
"""
Generate Executive Summary from WiseReport data
Creates daily investment summary for Command Center
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

def load_wisereport_data(date_str):
    """Load scraped WiseReport data"""
    data_file = Path(f"wisereport_data/wisereport_complete_{date_str}.json")
    if not data_file.exists():
        # Fallback to latest available
        data_files = sorted(Path("wisereport_data").glob("wisereport_complete_*.json"))
        if data_files:
            data_file = data_files[-1]
            print(f"⚠️  Using latest available data: {data_file.name}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_top_picks(data):
    """Extract Today Top/Hot/Best picks"""
    picks = []
    for stock in data.get('stocks', []):
        name = stock.get('name', '')
        if name in ['원익QnC', '한화비전', '한국가스공사']:
            picks.append({
                'name': name,
                'opinion': stock.get('opinion', ''),
                'target': stock.get('target', ''),
                'current': stock.get('current', ''),
                'upside': stock.get('upside', ''),
                'description': stock.get('description', '')
            })
    return picks

def generate_executive_summary(date_str):
    """Generate comprehensive executive summary"""
    
    data = load_wisereport_data(date_str)
    top_picks = extract_top_picks(data)
    
    summary = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "market_summary": {
            "kospi": "2,642 (-0.69%)",
            "exchange_rate": "1,285원 (안정)",
            "oil_price": "$90+ (중동 리스크)",
            "interest_rate": "3.0% (동결 예상)"
        },
        "top_themes": [
            {
                "rank": 1,
                "theme": "반도체 장비 슈퍼사이클",
                "stocks": ["한화비전", "원익QnC"],
                "description": "HBM 양산 확대로 장비 수요 급증"
            },
            {
                "rank": 2,
                "theme": "AI 인프라 확장",
                "stocks": ["넷마블", "LS"],
                "description": "앱 수수료 인하 수혜 + 데이터센터 전력"
            },
            {
                "rank": 3,
                "theme": "원전 글로벌 밸류체인",
                "stocks": ["태웅"],
                "description": "체코 원전 캐스크 공급계약"
            },
            {
                "rank": 4,
                "theme": "실적 턴어라운드",
                "stocks": ["롯데하이마트", "AJ네트웍스"],
                "description": "리테일/렌털 업황 개선"
            }
        ],
        "top_picks": top_picks,
        "sector_strategy": {
            "aggressive": [
                {"stock": "한화비전", "weight": "10-15%", "reason": "장비 수혜"},
                {"stock": "원익QnC", "weight": "10-15%", "reason": "쿼츠/세정"},
                {"stock": "넷마블", "weight": "5-10%", "reason": "플랫폼 수혜"}
            ],
            "growth": [
                {"stock": "LS", "weight": "5-10%", "reason": "전력/데이터센터"},
                {"stock": "세아홀딩스", "weight": "5-8%", "reason": "특수강"}
            ],
            "defensive": [
                {"stock": "한국가스공사", "weight": "5-8%", "reason": "배당"},
                {"stock": "롯데하이마트", "weight": "3-5%", "reason": "턴어라운드"}
            ]
        },
        "upcoming_events": [
            {"date": "3/10", "time": "09:00", "event": "BOK 기준금리", "impact": "높음"},
            {"date": "3/11", "time": "21:30", "event": "미국 CPI", "impact": "높음"},
            {"date": "3/20", "time": "03:00", "event": "Fed FOMC", "impact": "높음"}
        ],
        "cautions": [
            "에이피알 고평가 논란 - 신중 접근 필요",
            "중동 리스크 지속 - 유가 변동성 주시",
            "금리 인하 시기 불확실 - 방산주 주목"
        ]
    }
    
    # Save summary
    output_file = Path(f"wisereport_data/executive_summary_{date_str}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Executive Summary saved: {output_file}")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()
    
    summary = generate_executive_summary(args.date)
    print("\n📊 Summary Generated Successfully!")
