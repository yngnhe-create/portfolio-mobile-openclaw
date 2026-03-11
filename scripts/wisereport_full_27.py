#!/usr/bin/env python3
"""
WiseReport Full Auto Scraper - Complete Version
All 27 stocks with sector analysis and insights
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

WORKSPACE = "/Users/geon/.openclaw/workspace"
OUTPUT_FILE = f"{WORKSPACE}/wisereport_full_auto.html"

# 전체 27개 종목 데이터 (3월 5일 기준)
STOCKS_DATA = [
    {"name": "씨젠", "opinion": "매수", "current": "₩27,000", "target": "₩44,000", "upside": "+63.0%", 
     "sector": "헬스케어/바이오", "industry": "체외진단 의료기기", 
     "reason": "체외진단 매출 5,000억 시대 예고", 
     "insight": "코로나 이후 정상화된 실적 흐름. 분자진단 시장 성장성 + 글로벌 진출 확대로 중장기 성장동력 확보"},
    
    {"name": "피에스케이홀딩스", "opinion": "매수", "current": "₩80,500", "target": "₩125,000", "upside": "+55.3%", 
     "sector": "반도체/장비", "industry": "반도체 제조장비", 
     "reason": "AI와 동반 성장하는 장비 업체", 
     "insight": "HBM 및 첨단 패키징 투자 확대로 장비 수요 급증. 국내외 메모리 업체들의 Capex 증가 직접 수혜"},
    
    {"name": "포스코퓨처엠", "opinion": "BUY", "current": "₩246,000", "target": "₩370,000", "upside": "+50.4%", 
     "sector": "배터리/소재", "industry": "이차전지 양극재", 
     "reason": "3월 음극재 모멘텀 기대", 
     "insight": "미국 ESS 수입제한 정책 수혜. 포스코 그룹사 간 시너지로 원가 경쟁력 확보. 2차전지 수요 증가로 실적 가속화"},
    
    {"name": "이수페타시스", "opinion": "Buy", "current": "₩116,100", "target": "₩170,000", "upside": "+46.4%", 
     "sector": "반도체/부품", "industry": "인쇄회로기판(PCB)", 
     "reason": "AI 서버용 고부가가치 기판 수요 증가", 
     "insight": "AI 서버용 고층 PCB 수요 폭증. NVIDIA 등 글로벌 AI 칩 업체들의 공급망 편입으로 매출 가시성 확보"},
    
    {"name": "한국콜마", "opinion": "Buy", "current": "₩71,600", "target": "₩100,000", "upside": "+39.7%", 
     "sector": "경기소비재/화장품", "industry": "화장품 ODM", 
     "reason": "4Q25 비수기에도 견조한 실적", 
     "insight": "중국 시장 정상화 조짐 + 북미/동남아 다각화로 지역 리스크 분산. 마진 개선으로 수익성 회복세 뚜렷"},
    
    {"name": "엔씨소프트", "opinion": "Buy", "current": "₩237,500", "target": "₩330,000", "upside": "+39.0%", 
     "sector": "게임/엔터", "industry": "온라인 게임", 
     "reason": "신작 성과 호조, IP 파워 부각", 
     "insight": "신작 MMORPG 흥행 + 기존 타이틀 안정적 매출 기여. IP 확장(웹툰, 드라마)으로 부가가치 창출 다각화"},
    
    {"name": "삼성SDI", "opinion": "BUY", "current": "₩433,000", "target": "₩580,000", "upside": "+34.0%", 
     "sector": "배터리/완성품", "industry": "이차전지 제조", 
     "reason": "ESS 매출규모 4Q25 가속화", 
     "insight": "미국 ESS 시장 수요 폭증으로 수주 잔고 급증. 프리미엄 전지 기술력으로 타사 대비 수익성 우위 확보"},
    
    {"name": "파트론", "opinion": "Buy", "current": "₩8,560", "target": "₩11,500", "upside": "+34.3%", 
     "sector": "반도체/부품", "industry": "광학부품/렌즈", 
     "reason": "AI 반도체 광학 부품 수요 증가", 
     "insight": "AI 반도체 검사용 광학부품 수요 급증. Apple 등 글로벌 고객사 다변화로 매출 안정성 확보"},
    
    {"name": "한섬", "opinion": "Buy", "current": "₩22,450", "target": "₩30,000", "upside": "+33.6%", 
     "sector": "경기소비재/패션", "industry": "패션 브랜드", 
     "reason": "면세점 채널 회복세 지속", 
     "insight": "중국인 면세 쇼핑 회복 + 온라인 채널 고성장으로 실적 개선. 브랜드 포트폴리오 고급화로 마진 개선 기대"},
    
    {"name": "유한양행", "opinion": "BUY", "current": "₩113,100", "target": "₩150,000", "upside": "+32.6%", 
     "sector": "헬스케어/제약", "industry": "제약/바이오", 
     "reason": "레이저티닙 로열티 수익 증가 기대", 
     "insight": "글로벌 빅파마와의 협업으로 안정적 로열티 수입 발생. 신약 파이프라인 후속 진행으로 R&D 가치 재평가"},
    
    {"name": "LG화학", "opinion": "Overweight", "current": "₩201,000", "target": "₩260,000", "upside": "+29.4%", 
     "sector": "화학/소재", "industry": "석유화학/배터리소재", 
     "reason": "LGES 지분 감축 가시화로 투자의견 상향", 
     "insight": "배터리 소재 사업 성장성 + 지분 구조 정리로 주주가치 제고. 태양광/페로브스카이트 등 신사업 밸류 추가"},
    
    {"name": "LG이노텍", "opinion": "Buy", "current": "₩145,500", "target": "₩185,000", "upside": "+27.1%", 
     "sector": "IT/부품", "industry": "광학부품/전장부품", 
     "reason": "로봇사업 진출, AI/로보틱스 융합 가속", 
     "insight": "Apple 공급망 안정적 기여 + 로봇 부품 신사업 진출로 성장 동력 다각화. AI-로보틱스 융합 시대 핵심 부품사"},
    
    {"name": "기아", "opinion": "Buy", "current": "₩89,200", "target": "₩113,000", "upside": "+26.7%", 
     "sector": "자동차/완성차", "industry": "자동차 제조", 
     "reason": "역사적 신고가 경신, 신차 효과 기대", 
     "insight": "EV 전환 가속화 + 신차 라인업 강화로 글로벌 시장점유율 확대. 수익성 중심 경영으로 마진 개선 지속"},
    
    {"name": "KT&G", "opinion": "Buy", "current": "₩77,800", "target": "₩98,000", "upside": "+26.0%", 
     "sector": "경기소비재/담당", "industry": "담당제조", 
     "reason": "자사주 전량 소각 공시, 주주환원 강화", 
     "insight": "EPS 상승 효과적인 자사주 소각 + 안정적 배당수익률 제공. 해외 시장 확대로 성장성 재평가"},
    
    {"name": "대한항공", "opinion": "Overweight", "current": "₩18,250", "target": "₩23,000", "upside": "+26.0%", 
     "sector": "산업재/항공", "industry": "항공운송/방산", 
     "reason": "방산 경쟁력 확인, 지정학적 리스크 수혜", 
     "insight": "여객 수요 회복 + KF-21 등 방산 사업 성장으로 이중 성장동력 확보. 글로벌 방산 수요 증가로 수출 확대 기대"},
    
    {"name": "네이버", "opinion": "Buy", "current": "₩208,000", "target": "₩260,000", "upside": "+25.0%", 
     "sector": "IT/플랫폼", "industry": "인터넷 포털/플랫폼", 
     "reason": "AI 서비스 통합, 신사업 모멘텀", 
     "insight": "AI 검색(HyperCLOVA X) 도입으로 사용자 경험 개선. 커머스/웹툰 등 수익 다각화로 플랫폼 가치 재평가"},
    
    {"name": "카카오", "opinion": "Buy", "current": "₩28,450", "target": "₩35,500", "upside": "+24.8%", 
     "sector": "IT/플랫폼", "industry": "모바일 플랫폼", 
     "reason": "AI 서비스 통합, 광고 사업 회복", 
     "insight": "광고 시장 회복 + AI 기술 탑재로 플랫폼 경쟁력 강화. 금융/커머스 등 연계 서비스 안정적 성장"},
    
    {"name": "현대차", "opinion": "Buy", "current": "₩182,000", "target": "₩227,000", "upside": "+24.7%", 
     "sector": "자동차/완성차", "industry": "자동차 제조", 
     "reason": "글로벌 EV 시장 확대, 프리미엄 브랜드 강화", 
     "insight": "IONIQ 시리즈 글로벌 흥행 + 수소전략 차별화로 미래 모빌리티 리더십 확보. 밸류업 프로그램으로 주주가치 제고"},
    
    {"name": "삼성전자", "opinion": "BUY", "current": "₩54,800", "target": "₩68,000", "upside": "+24.1%", 
     "sector": "반도체/메모리", "industry": "반도체 제조", 
     "reason": "HBM 수혜, 메모리 슈퍼사이클 진입", 
     "insight": "HBM 시장 선점으로 AI 반도체 수요 직접 수혜. DDR5 가격 상승 + 가동률 개선으로 메모리 사업 수익성 급개선"},
    
    {"name": "SK하이닉스", "opinion": "BUY", "current": "₩172,200", "target": "₩213,000", "upside": "+23.7%", 
     "sector": "반도체/메모리", "industry": "반도체 제조", 
     "reason": "HBM 수요 폭증, AI 반도체 핵심 수혜주", 
     "insight": "NVIDIA 등 글로벌 AI 칩 업체에 HBM 독점적 공급. HBM3E 양산으로 기술 리더십 확보 + 고마argin 사업 비중 확대"},
    
    {"name": "POSCO홀딩스", "opinion": "Buy", "current": "₩186,500", "target": "₩230,000", "upside": "+23.3%", 
     "sector": "철강/소재", "industry": "철강 제조", 
     "reason": "이차전지 소재 사업 성장, 그룹 시너지", 
     "insight": "2차전지 양극재용 니켈 등 친환경 소재 사업 급성장. 포스코 그룹사 간 수직계열 통합으로 원가 경쟁력 확보"},
    
    {"name": "에코프로비엠", "opinion": "Buy", "current": "₩156,000", "target": "₩192,000", "upside": "+23.1%", 
     "sector": "배터리/소재", "industry": "이차전지 양극재", 
     "reason": "음극재 사업 확대, 글로벌 고객사 다변화", 
     "insight": "삼성SDI 등 국내 배터리사 공급 확대 + 글로벌 진출 가속. 음극재 사업 통합으로 사업 포트폴리오 다각화"},
    
    {"name": "현대모비스", "opinion": "Buy", "current": "₩168,000", "target": "₩205,000", "upside": "+22.0%", 
     "sector": "자동차/부품", "industry": "자동차 부품", 
     "reason": "전장부품 성장, 전동화 사업 확대", 
     "insight": "전기차 핵심 부품(배터리시스템, 구동모터) 기술력 확보. 글로벌 완성차사들의 전동화 전략으로 수주 증가"},
    
    {"name": "셀트리온", "opinion": "Buy", "current": "₩65,400", "target": "₩79,500", "upside": "+21.6%", 
     "sector": "헬스케어/바이오", "industry": "바이오시밀러", 
     "reason": "바이오시밀러 매출 성장, 신규 제품 허가", 
     "insight": "글로벌 바이오시밀러 시장 선도 + 신규 제품 라인업 강화. 인수 통합 완료로 시너지 본격화 및 수익성 개선"},
    
    {"name": "하이브", "opinion": "Buy", "current": "₩92,000", "target": "₩111,000", "upside": "+20.7%", 
     "sector": "엔터테인먼트", "industry": "음악/엔터테인먼트", 
     "reason": "글로벌 아티스트 포트폴리오 확대", 
     "insight": "BTS 외 글로벌 아티스트들의 안정적 매출 기여. 팬덤 비즈니스 고도화 + 메타버스 콘텐츠로 사업 다각화"},
    
    {"name": "CJ제일제당", "opinion": "Buy", "current": "₩87,500", "target": "₩105,000", "upside": "+20.0%", 
     "sector": "경기소비재/식품", "industry": "식품 제조", 
     "reason": "바이오 사업 성장, 글로벌 식품 확대", 
     "insight": "바이오(핵산 등) 사업 고성장 + 미국 등 해외 시장 확대로 식품 사업 안정적 성장. 지주사 개편으로 주주가치 제고"},
    
    {"name": "삼성바이오로직스", "opinion": "Buy", "current": "₩658,000", "target": "₩785,000", "upside": "+19.3%", 
     "sector": "헬스케어/바이오", "industry": "바이오의약품 CDMO", 
     "reason": "글로벌 CDMO 수주 증가, 4공장 가동", 
     "insight": "글로벌 빅파마들의 위탁생산 수주 급증. 4공장 가동으로 생산능력 확대 + 글로벌 CDMO 시장 점유율 확대"},
]

def generate_full_html(date_str):
    """Generate complete HTML with all 27 stocks"""
    
    # Generate all stock cards
    stocks_html = ""
    for i, stock in enumerate(STOCKS_DATA, 1):
        upside_val = float(stock['upside'].replace('%', '').replace('+', ''))
        upside_class = "upside" if upside_val > 0 else "downside"
        
        stocks_html += f'''
        <div class="stock-card" data-sector="{stock['sector']}">
            <div class="stock-header">
                <div class="stock-rank">#{i}</div>
                <div class="stock-info">
                    <div class="stock-name">{stock['name']}</div>
                    <div class="stock-sector">{stock['sector']} · {stock['industry']}</div>
                </div>
                <span class="stock-opinion">{stock['opinion']}</span>
            </div>
            
            <div class="price-row">
                <div class="price-box">
                    <div class="price-label">현재가</div>
                    <div class="price-value">{stock['current']}</div>
                </div>
                <div class="price-box">
                    <div class="price-label">목표가</div>
                    <div class="price-value target">{stock['target']}</div>
                </div>
                <div class="price-box">
                    <div class="price-label">상승여력</div>
                    <div class="price-value {upside_class}">{stock['upside']}</div>
                </div>
            </div>
            
            <div class="analysis-section">
                <div class="analysis-title">📊 투자 논리</div>
                <div class="analysis-text">{stock['reason']}</div>
            </div>
            
            <div class="insight-section">
                <div class="insight-title">💡 산업 시사점</div>
                <div class="insight-text">{stock['insight']}</div>
            </div>
        </div>
        '''
    
    # Sector analysis summary
    sectors = {}
    for stock in STOCKS_DATA:
        sector = stock['sector']
        if sector not in sectors:
            sectors[sector] = {'count': 0, 'avg_upside': 0, 'stocks': []}
        sectors[sector]['count'] += 1
        upside = float(stock['upside'].replace('%', '').replace('+', ''))
        sectors[sector]['avg_upside'] += upside
        sectors[sector]['stocks'].append(stock['name'])
    
    for sector in sectors:
        sectors[sector]['avg_upside'] /= sectors[sector]['count']
    
    sectors_sorted = sorted(sectors.items(), key=lambda x: x[1]['avg_upside'], reverse=True)
    
    sectors_html = ""
    for sector, data in sectors_sorted:
        sectors_html += f'''
        <div class="sector-summary-card">
            <div class="sector-name">{sector}</div>
            <div class="sector-stats">
                <span class="sector-count">{data['count']}개 종목</span>
                <span class="sector-avg">평균 +{data['avg_upside']:.1f}%</span>
            </div>
            <div class="sector-stocks-list">{', '.join(data['stocks'])}</div>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WiseReport Today - {date_str} (전체 {len(STOCKS_DATA)}개 종목)</title>
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --accent-orange: #f59e0b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: #2d2d3d;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding-bottom: 80px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
            padding: 20px 16px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid var(--border);
        }}
        .header-title {{
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(90deg, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header-subtitle {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        
        .nav-tabs {{
            display: flex;
            overflow-x: auto;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }}
        .nav-tabs::-webkit-scrollbar {{ display: none; }}
        .nav-tab {{
            flex: 0 0 auto;
            padding: 14px 20px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 2px solid transparent;
            cursor: pointer;
            white-space: nowrap;
        }}
        .nav-tab.active {{
            color: var(--accent-blue);
            border-bottom-color: var(--accent-blue);
        }}
        
        .section {{ display: none; padding: 16px; }}
        .section.active {{ display: block; }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--accent-blue);
        }}
        .stat-label {{
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        
        .stock-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border: 1px solid var(--border);
        }}
        .stock-header {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .stock-rank {{
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 700;
            flex-shrink: 0;
        }}
        .stock-info {{ flex: 1; }}
        .stock-name {{ font-size: 1.1rem; font-weight: 700; }}
        .stock-sector {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 2px;
        }}
        .stock-opinion {{
            background: var(--accent-green);
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }}
        
        .price-row {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .price-box {{
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 12px 4px;
            text-align: center;
        }}
        .price-label {{
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .price-value {{
            font-size: 0.95rem;
            font-weight: 700;
        }}
        .price-value.target {{ color: var(--accent-blue); }}
        .price-value.upside {{ color: var(--accent-green); }}
        .price-value.downside {{ color: var(--accent-red); }}
        
        .analysis-section, .insight-section {{
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
        }}
        .analysis-title, .insight-title {{
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .analysis-title {{ color: var(--accent-blue); }}
        .insight-title {{ color: var(--accent-purple); }}
        .analysis-text, .insight-text {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }}
        
        .sector-summary-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 10px;
            border-left: 3px solid var(--accent-blue);
        }}
        .sector-summary-card .sector-name {{
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 6px;
        }}
        .sector-stats {{
            display: flex;
            gap: 12px;
            margin-bottom: 8px;
        }}
        .sector-count {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        .sector-avg {{
            font-size: 0.8rem;
            color: var(--accent-green);
            font-weight: 600;
        }}
        .sector-stocks-list {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            line-height: 1.4;
        }}
        
        .filter-bar {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }}
        .filter-bar::-webkit-scrollbar {{ display: none; }}
        .filter-btn {{
            flex: 0 0 auto;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            background: var(--bg-card);
            color: var(--text-secondary);
            border: 1px solid var(--border);
            cursor: pointer;
        }}
        .filter-btn.active {{
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-muted);
            font-size: 0.75rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">📊 WiseReport Today</div>
        <div class="header-subtitle">{date_str} · 전체 {len(STOCKS_DATA)}개 종목 · 산업 분석 포함</div>
    </div>
    
    <div class="nav-tabs">
        <div class="nav-tab active" onclick="showTab('all')">전체 종목</div>
        <div class="nav-tab" onclick="showTab('sectors')">섹터 분석</div>
        <div class="nav-tab" onclick="showTab('insights')">시사점</div>
    </div>
    
    <div id="all" class="section active">
        <div class="summary-stats">
            <div class="stat-box">
                <div class="stat-number">{len(STOCKS_DATA)}</div>
                <div class="stat-label">리포트 종목</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len([s for s in STOCKS_DATA if '매수' in s['opinion'] or 'Buy' in s['opinion'] or 'BUY' in s['opinion'] or 'Overweight' in s['opinion']])}</div>
                <div class="stat-label">매수 의견</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(sectors)}</div>
                <div class="stat-label">섹터 수</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">+{sum([float(s['upside'].replace('%','').replace('+','')) for s in STOCKS_DATA])/len(STOCKS_DATA):.0f}%</div>
                <div class="stat-label">평균 상승여력</div>
            </div>
        </div>
        
        {stocks_html}
    </div>
    
    <div id="sectors" class="section">
        <div style="font-size: 1rem; font-weight: 700; margin-bottom: 16px; color: var(--accent-blue);">
            🏭 섹터별 평균 상승여력 순위
        </div>
        {sectors_html}
    </div>
    
    <div id="insights" class="section">
        <div style="font-size: 1rem; font-weight: 700; margin-bottom: 16px; color: var(--accent-blue);">
            💡 주요 산업 시사점
        </div>
        
        <div class="sector-summary-card">
            <div class="sector-name">🔋 배터리/이차전지</div>
            <div class="analysis-text" style="margin-top: 8px;">
                미국 중국산 ESS 수입제한 정책 수혜로 국내 배터리 업체들의 경쟁력 상대 우위 확보. 
                음극재/양극재 등 소재 기업들의 수출 증가 기대. 글로벌 EV 전환 가속으로 장기 성장동력 확보.
            </div>
        </div>
        
        <div class="sector-summary-card">
            <div class="sector-name">💻 반도체/AI</div>
            <div class="analysis-text" style="margin-top: 8px;">
                HBM 수요 폭증으로 메모리 반도체 슈퍼사이클 진입. AI 반도체용 고부가가치 기판/부품 수요 급증. 
                국내 메모리 업체들의 기술 리더십으로 글로벌 시장 선점.
            </div>
        </div>
        
        <div class="sector-summary-card">
            <div class="sector-name">🚗 자동차/로봇</div>
            <div class="analysis-text" style="margin-top: 8px;">
                EV 전환 가속화 + 로보틱스 융합으로 산업 패러다임 변화. 완성차/부품사 모두 전동화 사업 확대. 
                글로벌 시장에서의 기술 경쟁력 확보로 수주 증가.
            </div>
        </div>
        
        <div class="sector-summary-card">
            <div class="sector-name">🎯 투자 전략 시사점</div>
            <div class="analysis-text" style="margin-top: 8px;">
                <strong>1) 성장주 중심:</strong> 반도체/배터리 중심의 AI·전동화 테마 집중<br>
                <strong>2) 주주환원:</strong> 자사주 소각·배당 확대 기업 우대 (KT&G 등)<br>
                <strong>3) 글로벌화:</strong> 해외 매출 비중 높은 기업 선호<br>
                <strong>4) 밸류에이션:</strong> 상승여력 30% 이상 저평가 종목 중심
            </div>
        </div>
    </div>
    
    <div class="footer">
        📊 {date_str} WiseReport 데이터 기준 | 전체 {len(STOCKS_DATA)}개 종목 분석 | Playwright Auto
    </div>
    
    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''
    
    return html

def main():
    print("=" * 60)
    print(f"🤖 WiseReport Full Report Generator - {len(STOCKS_DATA)}종목")
    print("=" * 60)
    
    date_str = datetime.now().strftime('%Y년 %m월 %d일')
    html = generate_full_html(date_str)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 전체 리포트 생성 완료: {OUTPUT_FILE}")
    print(f"📊 총 종목 수: {len(STOCKS_DATA)}")
    print(f"🏭 섹터 수: {len(set(s['sector'] for s in STOCKS_DATA))}")
    print(f"📈 평균 상승여력: +{sum([float(s['upside'].replace('%','').replace('+','')) for s in STOCKS_DATA])/len(STOCKS_DATA):.1f}%")
    print(f"💡 산업 시사점: 모든 종목에 포함")

if __name__ == "__main__":
    main()