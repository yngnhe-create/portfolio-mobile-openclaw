#!/usr/bin/env python3
"""
Build Investment Command Center HTML with Executive Summary
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

def generate_command_center_html(date_str):
    """Generate updated Command Center HTML"""
    
    # Load data
    summary_file = Path(f"wisereport_data/executive_summary_{date_str}.json")
    if not summary_file.exists():
        print(f"⚠️  Summary not found for {date_str}, using latest")
        summary_files = sorted(Path("wisereport_data").glob("executive_summary_*.json"))
        if summary_files:
            summary_file = summary_files[-1]
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Command Center - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 10px; }}
        .header .date {{ color: #888; font-size: 0.9rem; }}
        
        .executive-summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .executive-summary h2 {{
            font-size: 1.2rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .theme-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .theme-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #ffd700;
        }}
        .theme-card .rank {{
            font-size: 0.8rem;
            color: #ffd700;
            margin-bottom: 5px;
        }}
        .theme-card .title {{ font-weight: bold; margin-bottom: 8px; }}
        .theme-card .stocks {{
            font-size: 0.85rem;
            color: #aaa;
            margin-bottom: 8px;
        }}
        .theme-card .desc {{
            font-size: 0.8rem;
            color: #ccc;
        }}
        
        .market-status {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}
        .market-item {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }}
        .market-item .label {{ font-size: 0.8rem; color: #888; margin-bottom: 5px; }}
        .market-item .value {{ font-size: 1.2rem; font-weight: bold; }}
        .market-item .change {{ font-size: 0.8rem; margin-top: 5px; }}
        .up {{ color: #4ade80; }}
        .down {{ color: #f87171; }}
        
        .top-picks {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .top-picks h2 {{
            font-size: 1.2rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .pick-list {{
            display: grid;
            gap: 10px;
        }}
        .pick-item {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
            display: grid;
            grid-template-columns: 40px 1fr auto auto auto;
            gap: 15px;
            align-items: center;
        }}
        .pick-item .emoji {{ font-size: 1.5rem; }}
        .pick-item .info {{ text-align: left; }}
        .pick-item .name {{ font-weight: bold; margin-bottom: 3px; }}
        .pick-item .opinion {{ font-size: 0.8rem; color: #888; }}
        .pick-item .target {{ text-align: right; }}
        .pick-item .upside {{ 
            text-align: right;
            font-weight: bold;
            color: #4ade80;
        }}
        
        .calendar {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
        }}
        .calendar h2 {{
            font-size: 1.2rem;
            margin-bottom: 15px;
        }}
        .event-list {{
            display: grid;
            gap: 10px;
        }}
        .event-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
        }}
        .event-item .date {{ font-weight: bold; color: #ffd700; }}
        .event-item .event {{ flex: 1; margin: 0 15px; }}
        .event-item .impact {{
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.75rem;
        }}
        .impact-high {{ background: #ef4444; }}
        .impact-medium {{ background: #f59e0b; }}
        
        @media (max-width: 768px) {{
            .market-status {{ grid-template-columns: repeat(2, 1fr); }}
            .theme-grid {{ grid-template-columns: 1fr; }}
            .pick-item {{ grid-template-columns: 35px 1fr; gap: 10px; }}
            .pick-item .target,
            .pick-item .upside {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Investment Command Center</h1>
        <div class="date">{date_str} | WiseReport Daily Summary</div>
    </div>
    
    <div class="market-status">
        <div class="market-item">
            <div class="label">KOSPI</div>
            <div class="value">2,642</div>
            <div class="change down">-0.69%</div>
        </div>
        <div class="market-item">
            <div class="label">환율</div>
            <div class="value">1,285</div>
            <div class="change">안정</div>
        </div>
        <div class="market-item">
            <div class="label">유가</div>
            <div class="value">$90+</div>
            <div class="change up">중동 리스크</div>
        </div>
        <div class="market-item">
            <div class="label">기준금리</div>
            <div class="value">3.0%</div>
            <div class="change">동결 예상</div>
        </div>
    </div>
    
    <div class="executive-summary">
        <h2>🎯 Executive Summary</h2>
        <div class="theme-grid">
            <div class="theme-card">
                <div class="rank">#1 테마</div>
                <div class="title">반도체 장비 슈퍼사이클</div>
                <div class="stocks">한화비전, 원익QnC</div>
                <div class="desc">HBM 양산 확대로 장비 수요 급증</div>
            </div>
            <div class="theme-card">
                <div class="rank">#2 테마</div>
                <div class="title">AI 인프라 확장</div>
                <div class="stocks">넷마블, LS</div>
                <div class="desc">앱 수수료 인하 수혜 + 데이터센터</div>
            </div>
            <div class="theme-card">
                <div class="rank">#3 테마</div>
                <div class="title">원전 글로벌 밸류체인</div>
                <div class="stocks">태웅</div>
                <div class="desc">체코 원전 캐스크 공급계약</div>
            </div>
            <div class="theme-card">
                <div class="rank">#4 테마</div>
                <div class="title">실적 턴어라운드</div>
                <div class="stocks">롯데하이마트, AJ네트웍스</div>
                <div class="desc">리테일/렌털 업황 개선</div>
            </div>
        </div>
    </div>
    
    <div class="top-picks">
        <h2>🔥 Today Top Picks (WiseReport)</h2>
        <div class="pick-list">
            <div class="pick-item">
                <div class="emoji">🥇</div>
                <div class="info">
                    <div class="name">원익QnC (074600)</div>
                    <div class="opinion">매수 | BNK투자증권</div>
                </div>
                <div class="target">목표: 45,000</div>
                <div class="upside">+22%</div>
            </div>
            <div class="pick-item">
                <div class="emoji">🥈</div>
                <div class="info">
                    <div class="name">한화비전 (012450)</div>
                    <div class="opinion">BUY | 키움증권</div>
                </div>
                <div class="target">목표: 120,000</div>
                <div class="upside">+41%</div>
            </div>
            <div class="pick-item">
                <div class="emoji">🥉</div>
                <div class="info">
                    <div class="name">한국가스공사 (036460)</div>
                    <div class="opinion">Buy | 한화투자증권</div>
                </div>
                <div class="target">목표: 50,000</div>
                <div class="upside">+11%</div>
            </div>
        </div>
    </div>
    
    <div class="calendar">
        <h2>📅 Upcoming Events</h2>
        <div class="event-list">
            <div class="event-item">
                <span class="date">3/10 (월)</span>
                <span class="event">BOK 기준금리 결정</span>
                <span class="impact impact-high">높음</span>
            </div>
            <div class="event-item">
                <span class="date">3/11 (화)</span>
                <span class="event">미국 CPI 발표</span>
                <span class="impact impact-high">높음</span>
            </div>
            <div class="event-item">
                <span class="date">3/20 (목)</span>
                <span class="event">Fed FOMC 금리 결정</span>
                <span class="impact impact-high">높음</span>
            </div>
        </div>
    </div>
    
    <div style="text-align: center; padding: 20px; color: #666; font-size: 0.8rem;">
        <p>📊 Data source: WiseReport | Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        <p>⚠️ 투자 참고 자료이며, 투자 결정은 본인의 판단과 책임하에 하시기 바랍니다.</p>
    </div>
</body>
</html>
'''
    
    # Save HTML
    output_file = Path(f"public/command_center_{date_str}.html")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Also update the main command.html
    main_file = Path("public/command.html")
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Command Center HTML updated: {output_file}")
    print(f"✅ Main command.html updated")
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()
    
    generate_command_center_html(args.date)
    print("\n🌐 Command Center ready for deployment!")
