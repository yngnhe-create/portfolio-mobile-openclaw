#!/usr/bin/env python3
"""
WiseReport 대시보드 v3 - 상세 분석 버전
2026-03-03 현행화
"""

import json
from datetime import datetime
from pathlib import Path

def load_wisereport_data():
    """와이즈리포트 데이터 로드"""
    data_file = Path("wisereport_data.json")
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_yellow_summary():
    """Yellow.kr 요약 로드"""
    yellow_file = Path("~/workspace/yellow_monitor/daily_summary.json").expanduser()
    if yellow_file.exists():
        with open(yellow_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generate_detailed_stock_card(stock):
    """상세 종목 카드 생성"""
    upside = stock.get('upside', '')
    upside_class = 'high' if '+' in upside and float(upside.replace('%', '').replace('+', '')) > 30 else 'medium' if '+' in upside else 'low'
    
    return f"""
    <div class="stock-card">
      <div class="stock-header">
        <h4>{stock['name']}</h4>
        <span class="opinion-badge {stock['opinion'].lower().replace(' ', '-')}">{stock['opinion']}</span>
      </div>
      <div class="stock-metrics">
        <div class="metric">
          <span class="label">목표가</span>
          <span class="value target">{stock['target']}</span>
        </div>
        <div class="metric">
          <span class="label">현재가</span>
          <span class="value current">{stock['current']}</span>
        </div>
        <div class="metric">
          <span class="label">상승여력</span>
          <span class="value upside {upside_class}">{upside}</span>
        </div>
      </div>
      <div class="stock-desc">
        <p>{stock['desc']}</p>
      </div>
      <div class="stock-action">
        <span class="recommendation">💡 추천: {"적극 매수" if upside_class == 'high' else "매수" if '+' in upside else "관망"}</span>
      </div>
    </div>
    """

def generate_sector_card(sector):
    """상세 섹터 카드 생성"""
    weight_class = {
        'Overweight': 'overweight',
        'Positive': 'positive',
        'Neutral': 'neutral',
        'Underweight': 'underweight'
    }.get(sector['weight'], 'neutral')
    
    # 섹터별 상세 분석 내용 추가
    detailed_analysis = {
        "반도체/AI": {
            "drivers": ["HBM3E 수요 폭증", "AI 서버 투자 확대", "CoWoS 패키징 수혜"],
            "risks": ["중국 증설 경쟁", "가격 조정 가능성"],
            "timeline": "2026-2027년 수혜 지속",
            "key_stocks": "SK하이닉스, 삼성전자, 피에스케이홀딩스"
        },
        "배터리/이차전지": {
            "drivers": ["미국 ESS 수입제한", "리튬 가격 반등", "음극재 모멘텀"],
            "risks": ["중국 과잉공급", "원자재 가격 변동성"],
            "timeline": "2분기부터 실적 개선 가시화",
            "key_stocks": "삼성SDI, 포스코퓨처엠, LG에너지솔루션"
        },
        "자동차/로봇": {
            "drivers": ["기아 역사적 신고가", "로봇사업 진출", "AI 융합 가속"],
            "risks": ["미국 관세 정책", "환율 리스크"],
            "timeline": "1분기 판매 호조 지속",
            "key_stocks": "기아, LG이노텍, 현대차"
        },
        "화학/소재": {
            "drivers": ["지분 가치 재평가", "태양광 수요 회복"],
            "risks": ["중국 경기 둔화", "원자재 비용 상승"],
            "timeline": "2026년 하반기부터 본격 회복",
            "key_stocks": "LG화학, 한화솔루션"
        }
    }.get(sector['name'], {})
    
    return f"""
    <div class="sector-card {weight_class}">
      <div class="sector-header">
        <h4>{sector['name']}</h4>
        <span class="weight-badge {weight_class}">{sector['weight']}</span>
      </div>
      <p class="sector-desc">{sector['desc']}</p>
      {generate_sector_detail(detailed_analysis) if detailed_analysis else ''}
    </div>
    """

def generate_sector_detail(analysis):
    """섹터 상세 분석 HTML"""
    if not analysis:
        return ""
    
    drivers_html = "".join([f"<li>✓ {d}</li>" for d in analysis.get('drivers', [])])
    risks_html = "".join([f"<li>⚠ {r}</li>" for r in analysis.get('risks', [])])
    
    return f"""
    <div class="sector-detail">
      <div class="detail-row">
        <span class="detail-label">📈 성장동력:</span>
        <ul class="detail-list">{drivers_html}</ul>
      </div>
      <div class="detail-row">
        <span class="detail-label">⚡ 리스크:</span>
        <ul class="detail-list">{risks_html}</ul>
      </div>
      <div class="detail-row">
        <span class="detail-label">📅 타임라인:</span>
        <span class="detail-value">{analysis.get('timeline', '미정')}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">🎯 핵심종목:</span>
        <span class="detail-value">{analysis.get('key_stocks', '-')}</span>
      </div>
    </div>
    """

def generate_html():
    """HTML 페이지 생성"""
    data = load_wisereport_data()
    yellow_data = load_yellow_summary()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 종목 카드 생성
    stock_cards = ""
    for stock in data.get('target_stocks', []):
        stock_cards += generate_detailed_stock_card(stock)
    
    # 섹터 카드 생성
    sector_cards = ""
    for sector in data.get('sectors', []):
        sector_cards += generate_sector_card(sector)
    
    # Yellow.kr 알림
    yellow_section = ""
    if yellow_data and yellow_data.get('new_count', 0) > 0:
        yellow_posts = ""
        for post in yellow_data.get('posts', [])[:3]:
            keywords = ', '.join(post.get('keywords', []))
            yellow_posts += f"<li><a href='{post['url']}' target='_blank'>{post['title']}</a> <span class='keywords'>{keywords}</span></li>"
        
        yellow_section = f"""
        <div class="yellow-section">
          <h3>🌐 Yellow.kr 외부 분석 ({yellow_data['date']})</h3>
          <ul class="yellow-posts">{yellow_posts}</ul>
          <p class="yellow-note">매일 오전 9시 자동 업데이트</p>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>와이즈리포트 분석 대시보드 v3</title>
  <style>
    :root {{
      --primary: #1a73e8;
      --success: #34a853;
      --warning: #fbbc04;
      --danger: #ea4335;
      --overweight: #1e8e3e;
      --positive: #34a853;
      --neutral: #fbbc04;
      --underweight: #ea4335;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      overflow: hidden;
    }}
    .header {{
      background: linear-gradient(90deg, #1a73e8, #4285f4);
      color: white;
      padding: 30px;
      text-align: center;
    }}
    .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
    .header .date {{ opacity: 0.9; font-size: 14px; }}
    
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      padding: 30px;
      background: #f8f9fa;
    }}
    .stat-item {{
      text-align: center;
      padding: 20px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    .stat-value {{
      font-size: 32px;
      font-weight: bold;
      color: var(--primary);
    }}
    .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
    
    .content {{ padding: 30px; }}
    .section {{ margin-bottom: 40px; }}
    .section h2 {{
      font-size: 22px;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 3px solid var(--primary);
      display: inline-block;
    }}
    
    .stocks-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }}
    .stock-card {{
      background: white;
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      border-left: 4px solid var(--primary);
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .stock-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }}
    .stock-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
    }}
    .stock-header h4 {{ font-size: 18px; }}
    .opinion-badge {{
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      text-transform: uppercase;
    }}
    .opinion-badge.buy, .opinion-badge.매수 {{ background: #e6f4ea; color: #1e8e3e; }}
    .opinion-badge.buy-상향 {{ background: #e8f0fe; color: var(--primary); }}
    
    .stock-metrics {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 15px;
    }}
    .metric {{
      text-align: center;
      padding: 10px;
      background: #f8f9fa;
      border-radius: 8px;
    }}
    .metric .label {{ font-size: 11px; color: #888; display: block; }}
    .metric .value {{ font-size: 14px; font-weight: bold; }}
    .metric .value.target {{ color: var(--primary); }}
    .metric .value.current {{ color: #666; }}
    .metric .value.upside {{ color: var(--success); }}
    .metric .value.upside.high {{ color: #1e8e3e; font-size: 16px; }}
    
    .stock-desc {{ font-size: 13px; color: #555; line-height: 1.6; margin-bottom: 15px; }}
    .stock-action {{
      padding-top: 10px;
      border-top: 1px solid #eee;
    }}
    .recommendation {{
      font-size: 13px;
      color: var(--primary);
      font-weight: 500;
    }}
    
    .sectors-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 20px;
    }}
    .sector-card {{
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      border-top: 4px solid var(--neutral);
    }}
    .sector-card.overweight {{ border-top-color: var(--overweight); }}
    .sector-card.positive {{ border-top-color: var(--positive); }}
    .sector-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}
    .weight-badge {{
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
    }}
    .weight-badge.overweight {{ background: #e6f4ea; color: #1e8e3e; }}
    .weight-badge.positive {{ background: #e6f4ea; color: #34a853; }}
    
    .sector-detail {{
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid #eee;
    }}
    .detail-row {{
      margin-bottom: 10px;
      font-size: 13px;
    }}
    .detail-label {{
      font-weight: 600;
      color: #333;
      display: inline-block;
      width: 100px;
    }}
    .detail-value {{ color: #555; }}
    .detail-list {{
      list-style: none;
      display: inline;
    }}
    .detail-list li {{
      display: inline-block;
      margin-right: 15px;
      color: #555;
    }}
    
    .yellow-section {{
      background: linear-gradient(135deg, #fef3e2, #fff9e6);
      border-radius: 16px;
      padding: 24px;
      margin-top: 30px;
    }}
    .yellow-section h3 {{ margin-bottom: 15px; color: #f57c00; }}
    .yellow-posts {{ list-style: none; }}
    .yellow-posts li {{ margin-bottom: 10px; }}
    .yellow-posts a {{ color: var(--primary); text-decoration: none; }}
    .yellow-posts a:hover {{ text-decoration: underline; }}
    .keywords {{
      font-size: 12px;
      color: #888;
      margin-left: 10px;
    }}
    .yellow-note {{
      font-size: 12px;
      color: #999;
      margin-top: 15px;
      text-align: right;
    }}
    
    .footer {{
      text-align: center;
      padding: 20px;
      background: #f8f9fa;
      color: #888;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📊 와이즈리포트 분석 대시보드 v3</h1>
      <p class="date">기준일: {today} | 매일 08:30 자동 업데이트</p>
    </div>
    
    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-value">{data.get('total_reports', 0)}</div>
        <div class="stat-label">전체 리포트</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{data.get('buy_count', 0)}</div>
        <div class="stat-label">BUY 권장</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{data.get('target_changes', 0)}</div>
        <div class="stat-label">목표가 변경</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{data.get('today_best', {}).get('name', '-')}</div>
        <div class="stat-label">Today Best</div>
      </div>
    </div>
    
    <div class="content">
      <div class="section">
        <h2>🎯 목표가 변경 종목 (상세 분석)</h2>
        <div class="stocks-grid">
          {stock_cards}
        </div>
      </div>
      
      <div class="section">
        <h2>📈 섹터별 투자 의견 (상세 전망)</h2>
        <div class="sectors-grid">
          {sector_cards}
        </div>
      </div>
      
      {yellow_section}
    </div>
    
    <div class="footer">
      <p>Generated by OpenClaw | Data from WiseReport & Yellow.kr</p>
    </div>
  </div>
</body>
</html>
"""
    
    return html

def main():
    """메인 실행"""
    print("🏗️ 와이즈리포트 대시보드 v3 생성 중...")
    
    html = generate_html()
    
    # 파일 저장
    output_file = Path("wisereport_dashboard_v3.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 생성 완료: {output_file.absolute()}")
    
    # Cloudflare Pages 배포 (선택)
    deploy_dir = Path("~/workspace/portfolio-mobile-openclaw").expanduser()
    if deploy_dir.exists():
        deploy_file = deploy_dir / "wisereport_summary.html"
        with open(deploy_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ 배포 파일 업데이트: {deploy_file}")

if __name__ == "__main__":
    main()
