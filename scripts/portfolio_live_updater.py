#!/usr/bin/env python3
"""
투자커멘드 포트폴리오 라이브 업데이터
- CSV 읽기 → 현재가 API 조회 → HTML 재생성 → Cloudflare 배포
- 실행 주기: 4시간마다 (cron)
- 가격 소스: 네이버 금융 (한국주식), Yahoo Finance (미국주식), CoinGecko (코인)
"""

import requests
import pandas as pd
import json
import os
import subprocess
import re
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
CSV_PATH = f"{WORKSPACE}/portfolio_full.csv"
OUTPUT_PATH = f"{WORKSPACE}/public/portfolio.html"
LOG_PATH = f"{WORKSPACE}/scripts/portfolio_updater.log"

# ─── 가격 소스 매핑 ────────────────────────────────────────────────

# 한국 주식/ETF 종목코드
KR_CODES = {
    '삼성전자': '005930',
    '삼성전자우': '005935',
    '현대차': '005380',
    '현대차우': '005385',
    '현대차3우B': '005387',
    '파마리서치': '214450',
    'DL이앤씨우': '002210',
    '두산': '000150',
    '네이버': '035420',
    '삼성SDI': '006400',
    'LG에너지솔루션': '373220',
    '엘오티베큠': '307750',
    '현대건설': '000720',
    '세아베스틸지주': '003030',
    '코람코라이프인프라리츠': '357250',
    'SK리츠': '439200',
    '신한서부티엔디리츠': '449950',
    '이지스밸류플러스리츠': '330590',
    'ESR켄달스퀘어리츠': '431980',
    # ETF
    'TIGER 코리아AI전력기기TOP3+': '381180',
    'TIGER 글로벌AI액티브': '466950',
    'TIGER 미국테크TOP10 INDXX': '381170',
    'SOL 미국AI전력인프라': '457580',
    'KODEX 미국30년국채액티브(H)': '304660',
    'KODEX 미국30년국채울트라(H)': '304670',
    'KODEX 미국S&P500헬스케어': '379800',
    'ACE 구글밸류체인액티브': '483340',
    'TIME 글로벌우주테크&방산': '471530',
    'TIGER 테슬라채권혼합Fn': '447770',
    'KODEX TRF3070': '329650',
    'TIGER 글로벌멀티에셋TIF': '441650',
    'TIGER 미국달러단기채권': '329750',
    'TIGER 미국초단기국채': '441660',
    'TIGER 코스피고배당': '211900',
    'TIGER 글로벌AI사이버보안': '441670',
    'HANARO 글로벌금채굴기업': '441730',
    'KODEX 증권': '102970',
}

# 미국 주식 야후 티커
US_TICKERS = {
    'INTC': 'INTC', 'NVDA': 'NVDA', 'AMD': 'AMD',
    'TSLA': 'TSLA', 'AMZN': 'AMZN', 'MSFT': 'MSFT',
    'NLR': 'NLR', 'GRID ETF': 'GRID', 'ARTY': 'ARTY',
    'HSAI': 'HSAI', 'RTX': 'RTX', 'LLY': 'LLY',
    'PLTR': 'PLTR', 'GOOGL': 'GOOGL',
    '샤오미': '1810.HK',
}

# 코인 CoinGecko ID (결과: KRW 가격)
CRYPTO_IDS = {
    'BTC/KRW': 'bitcoin',
    'ETH/KRW': 'ethereum',
    'SOL/KRW': 'solana',
    'LINK/USD': 'chainlink',
}


# ─── 가격 조회 함수들 ─────────────────────────────────────────────

def get_naver_price(code):
    """네이버 금융 API로 현재가 조회"""
    try:
        url = f"https://api.finance.naver.com/service/itemSummary.nhn?itemcode={code}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if r.status_code == 200:
            d = r.json()
            price = int(d.get('now', 0))
            change_rate = float(d.get('changeRate', 0))
            return price, change_rate
    except Exception as e:
        log(f"  ⚠️ 네이버 {code}: {e}")
    return None, None


def get_yahoo_prices(tickers):
    """Yahoo Finance로 미국주식 현재가 일괄 조회"""
    prices = {}
    try:
        symbols = ','.join(set(tickers.values()))
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('quoteResponse', {}).get('result', []):
                sym = item.get('symbol', '')
                prices[sym] = {
                    'price': item.get('regularMarketPrice', 0),
                    'change_pct': item.get('regularMarketChangePercent', 0),
                }
    except Exception as e:
        log(f"  ⚠️ Yahoo Finance: {e}")
    return prices


def get_crypto_prices():
    """CoinGecko로 코인 현재가 조회 (KRW + USD)"""
    try:
        ids = ','.join(set(CRYPTO_IDS.values()))
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=krw,usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log(f"  ⚠️ CoinGecko: {e}")
    return {}


# ─── CSV 읽기 및 처리 ─────────────────────────────────────────────

def load_portfolio():
    """CSV 파일 읽기"""
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8')
        df.columns = ['자산', '분류', '수량', '자산가치', '매수가', '현재가', '손익', '배당월', '투자배당률']
        return df
    except Exception as e:
        log(f"❌ CSV 읽기 실패: {e}")
        return None


def clean_number(val):
    """숫자 문자열 정제"""
    if pd.isna(val) or val == '-':
        return 0
    s = str(val).replace(',', '').replace('₩', '').replace('$', '').replace('+', '').replace('%', '').strip()
    # 괄호 안 내용 제거 (예: "+₩77,433,243 (+221.68%)" → 추출)
    s = re.sub(r'\(.*?\)', '', s).strip()
    try:
        return float(s)
    except:
        return 0


# ─── 산업별 섹터 매핑 ─────────────────────────────────────────────

INDUSTRY_MAP = {
    # 반도체/AI칩
    '삼성전자':      '반도체/AI칩',
    '삼성전자우':     '반도체/AI칩',
    'SK하이닉스':    '반도체/AI칩',
    'NVDA':        '반도체/AI칩',
    'INTC':        '반도체/AI칩',
    'AMD':         '반도체/AI칩',
    # AI 전력/인프라
    'TIGER 코리아AI전력기기TOP3+': 'AI전력/인프라',
    'SOL 미국AI전력인프라':        'AI전력/인프라',
    'GRID ETF':                 'AI전력/인프라',
    # AI/테크 ETF
    'TIGER 글로벌AI액티브':        'AI/테크 ETF',
    'TIGER 미국테크TOP10 INDXX': 'AI/테크 ETF',
    'ACE 구글밸류체인액티브':        'AI/테크 ETF',
    'TIGER 글로벌AI사이버보안':     'AI/테크 ETF',
    'ARTY':                     'AI/테크 ETF',
    # 미국 빅테크
    'GOOGL':  '미국 빅테크',
    'MSFT':   '미국 빅테크',
    'AMZN':   '미국 빅테크',
    'PLTR':   '미국 빅테크',
    # 자동차/모빌리티
    '현대차':    '자동차/모빌리티',
    '현대차우':   '자동차/모빌리티',
    '현대차3우B': '자동차/모빌리티',
    'TSLA':    '자동차/모빌리티',
    '샤오미':    '자동차/모빌리티',
    'HSAI':    '자동차/모빌리티',
    # 이차전지
    'LG에너지솔루션': '이차전지',
    '삼성SDI':       '이차전지',
    # 헬스케어/바이오
    '파마리서치':              '헬스케어',
    'KODEX 미국S&P500헬스케어': '헬스케어',
    'LLY':                   '헬스케어',
    # 원전/에너지
    '두산': '원전/에너지',
    'NLR':  '원전/에너지',
    # 가상자산
    'BTC/KRW':  '가상자산',
    'ETH/KRW':  '가상자산',
    'SOL/KRW':  '가상자산',
    'LINK/USD': '가상자산',
    # 부동산/리츠
    'ESR켄달스퀘어리츠':   '부동산/리츠',
    '코람코라이프인프라리츠': '부동산/리츠',
    'SK리츠':             '부동산/리츠',
    '신한서부티엔디리츠':   '부동산/리츠',
    '이지스밸류플러스리츠': '부동산/리츠',
    # 채권/안전자산
    'KODEX 미국30년국채액티브(H)': '채권/안전자산',
    'KODEX 미국30년국채울트라(H)': '채권/안전자산',
    'TIGER 미국초단기국채':         '채권/안전자산',
    'TIGER 미국달러단기채권':        '채권/안전자산',
    'KODEX TRF3070':              '채권/안전자산',
    'TIGER 글로벌멀티에셋TIF':       '채권/안전자산',
    'TIGER 코스피고배당':            '채권/안전자산',
    'TIGER 테슬라채권혼합Fn':        '채권/안전자산',
    'HANARO 글로벌금채굴기업':       '채권/안전자산',
    # 방산/우주
    'TIME 글로벌우주테크&방산': '방산/우주',
    'RTX':                   '방산/우주',
    # IT서비스/플랫폼
    '네이버': 'IT서비스',
    # 금융/증권
    'KODEX 증권': '금융/증권',
    # 소재/산업재
    '세아베스틸지주':  '소재/산업재',
    '엘오티베큠':     '소재/산업재',
    'DL이앤씨우':    '소재/산업재',
    '현대건설':      '소재/산업재',
}

# 섹터별 색상
INDUSTRY_COLORS = {
    '반도체/AI칩':   '#4834d4',
    'AI전력/인프라': '#ff6b35',
    'AI/테크 ETF':  '#686de0',
    '미국 빅테크':   '#3498db',
    '자동차/모빌리티': '#4ecdc4',
    '이차전지':      '#00b894',
    '헬스케어':      '#a55eea',
    '원전/에너지':   '#fdcb6e',
    '가상자산':      '#f7931a',
    '부동산/리츠':   '#27ae60',
    '채권/안전자산': '#636e72',
    '방산/우주':     '#e17055',
    'IT서비스':      '#74b9ff',
    '금융/증권':     '#ffeaa7',
    '소재/산업재':   '#b2bec3',
    '현금':         '#2d3436',
}


# ─── 포트폴리오 HTML 생성 ─────────────────────────────────────────

def fmt_krw(val):
    """억/만 단위 포맷"""
    if val >= 100_000_000:
        return f"₩{val/100_000_000:.1f}억"
    elif val >= 10_000:
        return f"₩{val/10_000:.0f}만"
    else:
        return f"₩{val:,.0f}"


def pct_color(pct):
    if pct > 0:
        return "color:#ff4757"
    elif pct < 0:
        return "color:#4ecdc4"
    return "color:#8b9dc3"


def generate_stock_item(row, current_price_str, change_pct, is_new=False,
                        total_val_krw=0, profit_krw=0):
    """종목 HTML 아이템 생성 (총 자산액 + 수익금액 포함)"""
    name = str(row['자산'])
    qty = row['수량']
    분류 = str(row['분류'])

    color_map = {
        '첨단 기술': '#4834d4', '가상자산': '#f7931a',
        '경기 소비재': '#4ecdc4', '채권': '#0984e3',
        '부동산': '#27ae60', 'ETF': '#6c5ce7',
        '헬스케어': '#00b894', '금융': '#fdcb6e',
        '현금': '#636e72', 'IT': '#3498db',
    }
    bg = '#636e72'
    for k, v in color_map.items():
        if k in 분류:
            bg = v
            break

    ico_text = name[:2] if len(name) >= 2 else name
    new_badge = '<span class="nbadge">NEW</span>' if is_new else ''
    border = 'border:1px solid #ff4757;border-radius:10px;' if is_new else ''
    chg_style = pct_color(change_pct)

    # 총 자산 표시
    val_str = fmt_krw(total_val_krw) if total_val_krw > 0 else ''
    # 수익 금액 표시
    profit_sign = '+' if profit_krw >= 0 else ''
    profit_color = '#ff4757' if profit_krw > 0 else '#4ecdc4' if profit_krw < 0 else '#8b9dc3'
    profit_str = f'{profit_sign}{fmt_krw(abs(profit_krw))}' if profit_krw != 0 else ''

    return f'''
<div class="stock-item" style="{border}">
  <div class="stock-ico" style="background:{bg};color:#fff">{ico_text}</div>
  <div class="stock-info">
    <div class="stock-nm">{name}{new_badge}</div>
    <div class="stock-det">{qty}주/개 · {분류}</div>
    {f'<div style="font-size:11px;margin-top:3px"><span style="color:var(--sub)">{val_str}</span> <span style="color:{profit_color};font-weight:600">{profit_str}</span></div>' if val_str else ''}
  </div>
  <div class="stock-num">
    <div class="stock-val">{current_price_str}</div>
    <div class="stock-chg" style="{chg_style}">{change_pct:+.1f}%</div>
  </div>
</div>'''


def load_history_js() -> str:
    """히스토리 JSON → JS 배열 문자열 반환"""
    import json as _json
    hist_path = f"{WORKSPACE}/wisereport_data/portfolio_history.json"
    try:
        with open(hist_path, 'r') as f:
            data = _json.load(f)
        return _json.dumps(data, ensure_ascii=False)
    except:
        return '[]'


def generate_html(df, updated_at, total_val, total_cost, total_profit, total_pct, stock_items_html):
    """portfolio.html 전체 생성"""

    history_js = load_history_js()  # 차트 데이터

    # ── 산업별 세부 섹터 집계
    industry_data = {}
    for _, row in df.iterrows():
        name = str(row['자산'])
        분류 = str(row['분류'])
        try:
            val = clean_number(str(row['자산가치']))
        except:
            val = 0
        industry = INDUSTRY_MAP.get(name)
        if not industry:
            if '현금' in 분류:
                industry = '현금'
            elif '부동산' in 분류:
                industry = '부동산/리츠'
            elif '가상자산' in 분류:
                industry = '가상자산'
            elif '채권' in 분류:
                industry = '채권/안전자산'
            elif '헬스케어' in 분류:
                industry = '헬스케어'
            elif '금융' in 분류:
                industry = '금융/증권'
            elif '소재' in 분류 or '산업재' in 분류:
                industry = '소재/산업재'
            else:
                industry = '기타'
        industry_data[industry] = industry_data.get(industry, 0) + val

    # 현금 제외 총액
    industry_total = sum(v for k, v in industry_data.items() if k != '현금') or 1
    # 비중순 정렬
    industry_sorted = sorted(
        [(k, v) for k, v in industry_data.items() if v > 0 and k != '현금'],
        key=lambda x: x[1], reverse=True
    )

    # 산업별 섹터 HTML
    industry_html = ''
    for ind, val in industry_sorted:
        pct = val / industry_total * 100
        col = INDUSTRY_COLORS.get(ind, '#636e72')
        bar_w = min(pct * 2.5, 100)
        industry_html += f'''
<div style="margin-bottom:13px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
    <div style="display:flex;align-items:center;gap:8px">
      <div style="width:10px;height:10px;border-radius:3px;background:{col};flex-shrink:0"></div>
      <span style="font-size:13px;font-weight:600">{ind}</span>
    </div>
    <div style="text-align:right">
      <span style="font-size:13px;font-weight:700">{pct:.1f}%</span>
      <span style="font-size:11px;color:var(--sub);margin-left:6px">{fmt_krw(val)}</span>
    </div>
  </div>
  <div style="height:7px;background:#2d3748;border-radius:4px;overflow:hidden">
    <div style="width:{bar_w:.0f}%;height:100%;background:{col};border-radius:4px;transition:.3s"></div>
  </div>
</div>'''

    # 대분류 섹터 집계
    sector_data = {
        '첨단기술/IT': 0, '가상자산': 0, '경기소비재': 0,
        '채권/리츠': 0, '헬스케어/기타': 0
    }
    # 세부 섹터 집계
    sub_sector_data = {}
    sub_sector_items = {}  # 각 세부섹터의 대표 종목명

    cat_to_main = {
        '첨단 기술': '첨단기술/IT', 'ETF': '첨단기술/IT', 'IT': '첨단기술/IT',
        '가상자산': '가상자산',
        '경기 소비재': '경기소비재', '산업재': '경기소비재', '소재': '경기소비재',
        '유틸리티': '경기소비재',
        '채권': '채권/리츠', '부동산': '채권/리츠',
        '헬스케어': '헬스케어/기타', '금융': '헬스케어/기타', '기타': '헬스케어/기타',
        '현금': '헬스케어/기타',
    }

    for _, row in df.iterrows():
        cat = str(row['분류'])
        name = str(row['자산'])
        try:
            if '₩' in str(row['자산가치']):
                val = clean_number(str(row['자산가치']))
            else:
                val = clean_number(str(row['자산가치'])) * 1400
        except:
            val = 0

        main = '헬스케어/기타'
        for k, v in cat_to_main.items():
            if k in cat:
                main = v
                break
        sector_data[main] += val

        # 세부 섹터
        sub = cat.strip()
        sub_sector_data[sub] = sub_sector_data.get(sub, 0) + val
        if sub not in sub_sector_items:
            sub_sector_items[sub] = []
        sub_sector_items[sub].append(name[:8])

    total_v = sum(sector_data.values()) or 1
    s_pcts = {k: v / total_v * 100 for k, v in sector_data.items()}

    # 세부 섹터 정렬
    sub_sorted = sorted(sub_sector_data.items(), key=lambda x: x[1], reverse=True)
    sub_sector_html = ''
    for sub, val in sub_sorted:
        if val <= 0: continue
        pct = val / total_v * 100
        items_str = ', '.join(sub_sector_items.get(sub, [])[:3])
        bar_w = min(pct * 2, 100)  # 최대 100%로 스케일
        sub_sector_html += f'''
<div style="margin-bottom:12px">
  <div style="display:flex;justify-content:space-between;margin-bottom:5px">
    <span style="font-size:12px;font-weight:600">{sub}</span>
    <span style="font-size:12px;font-weight:700">{pct:.1f}% · {fmt_krw(val)}</span>
  </div>
  <div style="height:6px;background:#2d3748;border-radius:3px;overflow:hidden;margin-bottom:3px">
    <div style="width:{bar_w:.0f}%;height:100%;background:var(--blu);border-radius:3px"></div>
  </div>
  <div style="font-size:10px;color:var(--sub)">{items_str}</div>
</div>'''

    profit_sign = '+' if total_profit >= 0 else ''
    profit_color = '#ff4757' if total_profit >= 0 else '#4ecdc4'

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>투자커멘드 | 포트폴리오</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0e1a;--card:#151b2d;--hdr:#1a1f2e;--brd:#2d3748;--txt:#e0e6ed;--sub:#8b9dc3;--red:#ff4757;--grn:#4ecdc4;--blu:#4834d4;--yel:#f9ca24}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;background:var(--bg);color:var(--txt);font-size:14px;padding-bottom:80px}}
.hdr{{background:var(--hdr);padding:15px;border-bottom:1px solid var(--brd);position:sticky;top:0;z-index:999}}
.hdr-ttl{{font-size:18px;font-weight:800;margin-bottom:4px}}
.upd{{font-size:11px;color:var(--sub)}}
.tabs{{display:flex;gap:8px;margin-top:12px}}
.tab{{flex:1;padding:10px;background:var(--card);border:1px solid var(--brd);border-radius:8px;text-align:center;font-size:13px;font-weight:600;cursor:pointer}}
.tab.on{{background:var(--blu);border-color:var(--blu);color:#fff}}
.tc{{display:none}}.tc.show{{display:block}}
.tcard{{background:linear-gradient(135deg,var(--blu),#686de0);padding:25px 20px;margin:15px;border-radius:16px}}
.tval{{font-size:36px;font-weight:800;margin-bottom:6px}}
.tlbl{{font-size:13px;opacity:.9;margin-bottom:4px}}
.tchg{{font-size:16px;font-weight:700}}
.smgrid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:0 15px 15px}}
.smcard{{background:var(--card);padding:18px 12px;border-radius:12px;text-align:center}}
.smval{{font-size:22px;font-weight:800;margin-bottom:4px}}
.smlbl{{font-size:11px;color:var(--sub)}}
.sec{{background:var(--card);margin:0 15px 15px;padding:18px;border-radius:12px}}
.sec-ttl{{font-size:15px;font-weight:700;margin-bottom:14px}}
.leg{{display:flex;flex-direction:column;gap:10px}}
.leg-row{{display:flex;align-items:center;gap:10px;font-size:13px}}
.leg-dot{{width:12px;height:12px;border-radius:3px;flex-shrink:0}}
.leg-nm{{flex:1}}
.leg-bar{{flex:2;height:8px;background:#2d3748;border-radius:4px;overflow:hidden}}
.leg-fill{{height:100%;border-radius:4px}}
.leg-pct{{font-weight:700;font-size:13px;min-width:35px;text-align:right}}
.leg-amt{{font-size:10px;color:var(--sub);min-width:40px;text-align:right}}
.stock-item{{display:flex;align-items:center;gap:12px;padding:14px;background:var(--hdr);border-radius:10px;margin-bottom:10px}}
.stock-ico{{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;text-align:center}}
.stock-info{{flex:1}}
.stock-nm{{font-size:14px;font-weight:700;margin-bottom:3px}}
.stock-det{{font-size:11px;color:var(--sub)}}
.stock-num{{text-align:right}}
.stock-val{{font-size:15px;font-weight:700}}
.stock-chg{{font-size:12px;font-weight:600;margin-top:2px}}
.nbadge{{background:#ff4757;color:#fff;font-size:9px;padding:2px 5px;border-radius:3px;margin-left:5px;font-weight:700}}
.tog-btn{{display:block;width:100%;padding:12px;background:rgba(72,52,212,.15);border:1px solid var(--blu);border-radius:8px;color:var(--blu);font-size:13px;font-weight:700;cursor:pointer;margin-top:10px;text-align:center}}
.chart-range-btn{{padding:4px 10px;border-radius:12px;background:var(--hdr);border:1px solid var(--brd);color:var(--sub);font-size:11px;font-weight:600;cursor:pointer}}
.chart-range-btn.on{{background:var(--blu);border-color:var(--blu);color:#fff}}
.bnav{{position:fixed;bottom:0;left:0;right:0;background:var(--hdr);border-top:1px solid var(--brd);display:flex;justify-content:space-around;padding:8px 0 20px;z-index:999}}
.bnav a{{display:flex;flex-direction:column;align-items:center;gap:3px;color:var(--sub);text-decoration:none;font-size:10px;padding:5px 10px}}
.bnav a.on{{color:var(--blu)}}.ni{{font-size:22px}}
.mask-btn{{position:fixed;top:12px;right:12px;z-index:9999;background:rgba(72,52,212,.9);color:#fff;border:none;border-radius:20px;padding:6px 14px;font-size:12px;font-weight:700;cursor:pointer;backdrop-filter:blur(4px);box-shadow:0 2px 8px rgba(0,0,0,.4)}}
body.masked .tval,body.masked .tchg,body.masked .smval,body.masked .stock-val,body.masked .stock-chg{{filter:blur(8px);user-select:none;transition:filter .2s}}
</style>
</head>
<body>
<button class="mask-btn" id="maskBtn" onclick="toggleMask()">🙈 마스킹</button>
<div class="hdr">
  <div class="hdr-ttl">📊 포트폴리오</div>
  <div class="upd">⏱ 마지막 업데이트: {updated_at}</div>
  <div class="tabs">
    <div class="tab on" onclick="switchTab('all',this)">전체</div>
    <div class="tab" onclick="switchTab('sector',this)">섹터</div>
    <div class="tab" onclick="switchTab('stocks',this)">종목</div>
    <div class="tab" onclick="switchTab('returns',this)">수익</div>
  </div>
</div>

<!-- 전체 탭 -->
<div class="tc show" id="content-all">
  <div class="tcard">
    <div class="tlbl">총 자산</div>
    <div class="tval">{fmt_krw(total_val)}</div>
    <div class="tchg">{profit_sign}{total_pct:.1f}% ({profit_sign}{fmt_krw(abs(total_profit))})</div>
  </div>
  <div class="smgrid">
    <div class="smcard"><div class="smval">{fmt_krw(total_cost)}</div><div class="smlbl">총 매수금액</div></div>
    <div class="smcard"><div class="smval" style="color:{profit_color}">{profit_sign}{fmt_krw(abs(total_profit))}</div><div class="smlbl">평가손익</div></div>
  </div>
  <!-- 총 자산 변동 차트 -->
  <div class="sec">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div class="sec-ttl" style="margin-bottom:0">📈 총 자산 변동</div>
      <div style="display:flex;gap:6px">
        <button class="chart-range-btn on" onclick="setRange(7,this)">1W</button>
        <button class="chart-range-btn" onclick="setRange(14,this)">2W</button>
        <button class="chart-range-btn" onclick="setRange(30,this)">1M</button>
        <button class="chart-range-btn" onclick="setRange(0,this)">전체</button>
      </div>
    </div>
    <div style="position:relative;height:180px"><canvas id="assetChart"></canvas></div>
    <div style="display:flex;gap:16px;margin-top:10px;font-size:11px">
      <span><span style="display:inline-block;width:10px;height:3px;background:#4834d4;vertical-align:middle;border-radius:2px"></span> 총 자산</span>
      <span><span style="display:inline-block;width:10px;height:3px;background:rgba(139,157,195,.6);vertical-align:middle;border-radius:2px"></span> 매수금액</span>
      <span id="chart-period-label" style="color:var(--sub);margin-left:auto;font-size:10px"></span>
    </div>
  </div>

  <div class="sec">
    <div class="sec-ttl">섹터 비중</div>
    <div class="leg">
      <div class="leg-row"><div class="leg-dot" style="background:#4834d4"></div><span class="leg-nm">첨단기술/IT</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['첨단기술/IT']:.0f}%;background:#4834d4"></div></div><span class="leg-pct">{s_pcts['첨단기술/IT']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#ff4757"></div><span class="leg-nm">가상자산</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['가상자산']:.0f}%;background:#ff4757"></div></div><span class="leg-pct">{s_pcts['가상자산']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#4ecdc4"></div><span class="leg-nm">경기소비재</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['경기소비재']:.0f}%;background:#4ecdc4"></div></div><span class="leg-pct">{s_pcts['경기소비재']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#f9ca24"></div><span class="leg-nm">채권/리츠</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['채권/리츠']:.0f}%;background:#f9ca24"></div></div><span class="leg-pct">{s_pcts['채권/리츠']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#a55eea"></div><span class="leg-nm">헬스케어/기타</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['헬스케어/기타']:.0f}%;background:#a55eea"></div></div><span class="leg-pct">{s_pcts['헬스케어/기타']:.1f}%</span></div>
    </div>
  </div>
  <div class="sec">
    <div class="sec-ttl">보유 종목 <span style="font-size:12px;color:var(--sub)">{len(df)}개</span></div>
    <div id="top-stocks">TOP8_PLACEHOLDER</div>
    <div id="hidden-stocks" style="display:none">HIDDEN_PLACEHOLDER</div>
    <button class="tog-btn" id="toggle-btn" onclick="toggleAllStocks()">전체 종목 보기 ▼</button>
  </div>
</div>

<!-- 섹터 탭 -->
<div class="tc" id="content-sector">
  <div style="padding:15px">
  <div class="sec">
    <div class="sec-ttl">대분류 섹터</div>
    <div class="leg">
      <div class="leg-row"><div class="leg-dot" style="background:#4834d4"></div><span class="leg-nm">첨단기술/IT</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['첨단기술/IT']:.0f}%;background:#4834d4"></div></div><span class="leg-pct">{s_pcts['첨단기술/IT']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#ff4757"></div><span class="leg-nm">가상자산</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['가상자산']:.0f}%;background:#ff4757"></div></div><span class="leg-pct">{s_pcts['가상자산']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#4ecdc4"></div><span class="leg-nm">경기소비재</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['경기소비재']:.0f}%;background:#4ecdc4"></div></div><span class="leg-pct">{s_pcts['경기소비재']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#f9ca24"></div><span class="leg-nm">채권/리츠</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['채권/리츠']:.0f}%;background:#f9ca24"></div></div><span class="leg-pct">{s_pcts['채권/리츠']:.1f}%</span></div>
      <div class="leg-row"><div class="leg-dot" style="background:#a55eea"></div><span class="leg-nm">헬스케어/기타</span><div class="leg-bar"><div class="leg-fill" style="width:{s_pcts['헬스케어/기타']:.0f}%;background:#a55eea"></div></div><span class="leg-pct">{s_pcts['헬스케어/기타']:.1f}%</span></div>
    </div>
  </div>
  <div class="sec">
    <div class="sec-ttl">산업별 세부 섹터</div>
    {industry_html}
  </div>
  </div>
</div>

<!-- 종목 탭 -->
<div class="tc" id="content-stocks">
  <div style="padding:15px">
  <div class="sec">
    <div class="sec-ttl">전체 종목 ({len(df)}개)</div>
    {stock_items_html}
  </div>
  </div>
</div>

<!-- 수익 탭 -->
<div class="tc" id="content-returns">
  <div style="padding:15px">
  <div class="tcard" style="margin:0 0 15px">
    <div class="tlbl">총 수익률</div>
    <div class="tval">{profit_sign}{total_pct:.1f}%</div>
    <div class="tchg">{profit_sign}{fmt_krw(abs(total_profit))} 수익</div>
  </div>
  <div class="smgrid" style="margin:0 0 15px">
    <div class="smcard"><div class="smval">{fmt_krw(total_cost)}</div><div class="smlbl">총 매수금액</div></div>
    <div class="smcard"><div class="smval">{fmt_krw(total_val)}</div><div class="smlbl">현재 평가금액</div></div>
    <div class="smcard"><div class="smval" style="color:{profit_color}">{profit_sign}{fmt_krw(abs(total_profit))}</div><div class="smlbl">평가손익</div></div>
    <div class="smcard"><div class="smval">{len(df)}개</div><div class="smlbl">보유종목</div></div>
  </div>
  </div>
</div>

<nav class="bnav">
  <a href="index.html"><span class="ni">🏠</span>홈</a>
  <a href="portfolio.html" class="on"><span class="ni">📊</span>포트폴리오</a>
  <a href="wisereport.html"><span class="ni">📋</span>리포트</a>
  <a href="playbook.html"><span class="ni">📖</span>플레이북</a>
</nav>

<script>
function switchTab(name, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('on'));
  el.classList.add('on');
  document.querySelectorAll('.tc').forEach(c => c.classList.remove('show'));
  document.getElementById('content-' + name).classList.add('show');
}}
function toggleAllStocks() {{
  const h = document.getElementById('hidden-stocks');
  const b = document.getElementById('toggle-btn');
  if (h.style.display === 'none') {{
    h.style.display = 'block';
    b.textContent = '접기 ▲';
  }} else {{
    h.style.display = 'none';
    b.textContent = '전체 종목 보기 ▼';
  }}
}}
function toggleMask(){{const on=document.body.classList.toggle('masked');document.getElementById('maskBtn').textContent=on?'👁 해제':'🙈 마스킹';localStorage.setItem('mask',on?'1':'0');}}
if(localStorage.getItem('mask')==='1'){{document.body.classList.add('masked');document.getElementById('maskBtn').textContent='👁 해제';}}
</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
const HISTORY = {history_js};
let chartInstance = null;
function fmtAmt(v){{
  if(v>=1e8) return (v/1e8).toFixed(2)+'억';
  return (v/1e4).toFixed(0)+'만';
}}
function buildChart(days){{
  const now = new Date();
  const cutoff = days > 0 ? new Date(now - days*86400000) : new Date(0);
  const filtered = HISTORY.filter(d => new Date(d.date) >= cutoff);
  if(!filtered.length) return;
  const labels = filtered.map(d => {{ const dt=new Date(d.date); return (dt.getMonth()+1)+'/'+(dt.getDate()); }});
  const totals = filtered.map(d => d.total);
  const costs  = filtered.map(d => d.cost);
  const lbl = document.getElementById('chart-period-label');
  if(lbl) lbl.textContent = filtered[0]?.date + ' ~ ' + filtered[filtered.length-1]?.date;
  if(chartInstance) chartInstance.destroy();
  const ctx = document.getElementById('assetChart').getContext('2d');
  const grad = ctx.createLinearGradient(0,0,0,180);
  grad.addColorStop(0,'rgba(72,52,212,0.45)');
  grad.addColorStop(1,'rgba(72,52,212,0.02)');
  chartInstance = new Chart(ctx, {{
    type:'line',
    data:{{
      labels,
      datasets:[
        {{ label:'총 자산', data:totals, borderColor:'#4834d4', backgroundColor:grad,
           borderWidth:2.5, pointRadius:filtered.length>15?2:4, pointBackgroundColor:'#4834d4',
           fill:true, tension:0.4 }},
        {{ label:'매수금액', data:costs, borderColor:'rgba(139,157,195,.6)', backgroundColor:'transparent',
           borderWidth:1.5, borderDash:[5,4], pointRadius:0, fill:false, tension:0 }}
      ]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'#1a1f2e', borderColor:'#2d3748', borderWidth:1,
          titleColor:'#e0e6ed', bodyColor:'#8b9dc3',
          callbacks:{{
            label: ctx => ctx.dataset.label+': ₩'+fmtAmt(ctx.parsed.y),
            afterBody: items => {{
              const d = filtered[items[0].dataIndex];
              if(!d) return [];
              const s = d.profit>=0?'+':'';
              return ['수익: '+s+'₩'+fmtAmt(Math.abs(d.profit))+' ('+s+d.profit_pct.toFixed(1)+'%)'];
            }}
          }}
        }}
      }},
      scales:{{
        x:{{ grid:{{color:'rgba(255,255,255,.04)'}}, ticks:{{color:'#8b9dc3',font:{{size:10}}}} }},
        y:{{ grid:{{color:'rgba(255,255,255,.06)'}}, ticks:{{color:'#8b9dc3',font:{{size:10}},callback:v=>fmtAmt(v)}} }}
      }}
    }}
  }});
}}
function setRange(days, el){{
  document.querySelectorAll('.chart-range-btn').forEach(b=>b.classList.remove('on'));
  el.classList.add('on');
  buildChart(days);
}}
document.addEventListener('DOMContentLoaded', ()=>buildChart(7));
</script>
</body>
</html>'''


# ─── 메인 실행 ────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass


def main():
    log("=" * 60)
    log("🚀 포트폴리오 라이브 업데이터 시작")

    # 1. CSV 읽기
    df = load_portfolio()
    if df is None:
        log("❌ 종료: CSV 읽기 실패")
        return

    log(f"✅ CSV 로드 완료 ({len(df)}개 종목)")

    # 2. 가격 조회
    log("📡 현재가 조회 중...")

    # 미국주식 일괄 조회
    us_prices = get_yahoo_prices(US_TICKERS)
    log(f"  📈 Yahoo Finance: {len(us_prices)}개 티커")

    # 코인 조회
    crypto_prices = get_crypto_prices()
    log(f"  🪙 CoinGecko: {len(crypto_prices)}개 코인")

    # 3. 종목별 현재가 매핑 + HTML 생성
    stock_items = []
    total_val_krw = 0
    total_cost_krw = 0
    crypto_val_krw = 0

    # KRW 환율 근사 (USD→KRW)
    try:
        fx_r = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=5
        ).json()
        usd_krw = fx_r.get('rates', {}).get('KRW', 1400)
    except:
        usd_krw = 1400

    NEW_ASSETS = {'현대차', 'KODEX 증권'}

    for _, row in df.iterrows():
        name = str(row['자산'])
        분류 = str(row['분류'])
        qty = float(row['수량']) if not pd.isna(row['수량']) else 0

        # 현재가 및 변화율 결정
        current_price = None
        change_pct = 0.0
        price_str = str(row['현재가'])

        if name in KR_CODES:
            p, chg = get_naver_price(KR_CODES[name])
            if p:
                current_price = p
                change_pct = chg or 0
                price_str = f"₩{p:,}"
        elif name in US_TICKERS:
            ticker = US_TICKERS[name]
            if ticker in us_prices:
                p = us_prices[ticker]['price']
                current_price = p
                change_pct = us_prices[ticker]['change_pct']
                price_str = f"${p:.2f}"
        elif '1810.HK' in US_TICKERS.get(name, ''):
            ticker = '1810.HK'
            if ticker in us_prices:
                current_price = us_prices[ticker]['price']
                change_pct = us_prices[ticker]['change_pct']
                price_str = f"HK${current_price:.2f}"
        elif name in CRYPTO_IDS:
            cg_id = CRYPTO_IDS[name]
            if cg_id in crypto_prices:
                cd = crypto_prices[cg_id]
                if 'KRW' in name.upper() or '/KRW' in name:
                    current_price = cd.get('krw', 0)
                    price_str = f"₩{current_price:,.0f}"
                else:
                    current_price = cd.get('usd', 0)
                    price_str = f"${current_price:.2f}"
                change_pct = cd.get('krw_24h_change', cd.get('usd_24h_change', 0)) or 0

        # 자산가치 계산
        try:
            raw_val = str(row['자산가치'])
            if '₩' in raw_val:
                val_krw = clean_number(raw_val)
            else:
                val_usd = clean_number(raw_val)
                val_krw = val_usd * usd_krw
        except:
            val_krw = 0

        # 매수가 계산
        try:
            raw_cost = str(row['매수가'])
            if raw_cost in ['-', 'nan', '']:
                cost_krw = 0
            elif '₩' in raw_cost:
                cost_per = clean_number(raw_cost)
                cost_krw = cost_per * qty
            elif raw_cost.startswith('$') or raw_cost.replace(',', '').replace('.', '').lstrip('-').isdigit():
                cost_per = clean_number(raw_cost)
                cost_krw = cost_per * qty * usd_krw
            else:
                cost_per = clean_number(raw_cost)
                cost_krw = cost_per * qty
        except:
            cost_krw = 0

        # 수익금액 계산
        profit_krw = val_krw - cost_krw if cost_krw > 0 else 0

        if 분류 != '현금':
            total_val_krw += val_krw
            if cost_krw > 0:
                total_cost_krw += cost_krw

        # 가상자산 별도 집계
        if '가상자산' in 분류:
            crypto_val_krw += val_krw

        is_new = name in NEW_ASSETS
        item_html = generate_stock_item(
            row, price_str, change_pct, is_new,
            total_val_krw=val_krw, profit_krw=profit_krw
        )
        stock_items.append((val_krw, item_html))

    # 자산가치 내림차순 정렬
    stock_items.sort(key=lambda x: x[0], reverse=True)

    # TOP 8 + 나머지 분리
    top8_html = ''.join(i[1] for i in stock_items[:8])
    rest_html = ''.join(i[1] for i in stock_items[8:])

    # TOP 8을 id="top-stocks"에, 나머지를 id="hidden-stocks"에 넣기
    all_stocks_html = ''.join(i[1] for i in stock_items)

    # 손익 계산
    total_profit = total_val_krw - total_cost_krw
    total_pct = (total_profit / total_cost_krw * 100) if total_cost_krw > 0 else 0

    updated_at = datetime.now().strftime('%Y년 %m월 %d일 %H:%M KST')
    log(f"💰 총 자산: {fmt_krw(total_val_krw)} | 수익률: {total_pct:.1f}%")

    # 3-1. 히스토리 기록
    import json as _json
    hist_path = f"{WORKSPACE}/wisereport_data/portfolio_history.json"
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')
        history = []
        if os.path.exists(hist_path):
            with open(hist_path, 'r') as f:
                history = _json.load(f)
        # 오늘 데이터 업데이트 (이미 있으면 교체, 없으면 추가)
        today_entry = {
            "date": today_str,
            "total": int(total_val_krw),
            "cost": int(total_cost_krw),
            "profit": int(total_val_krw - total_cost_krw),
            "profit_pct": round(total_pct, 2)
        }
        if history and history[-1]['date'] == today_str:
            history[-1] = today_entry
        else:
            history.append(today_entry)
        # 최대 180일 유지
        history = history[-180:]
        with open(hist_path, 'w') as f:
            _json.dump(history, f, ensure_ascii=False)
        log(f"📈 히스토리 기록: {len(history)}일치")
    except Exception as e:
        log(f"⚠️ 히스토리 기록 실패: {e}")

    # 4. HTML 생성 후 플레이스홀더 치환
    html = generate_html(df, updated_at, total_val_krw, total_cost_krw, total_profit, total_pct, all_stocks_html)
    html = html.replace('TOP8_PLACEHOLDER', top8_html)
    html = html.replace('HIDDEN_PLACEHOLDER', rest_html)

    # 5. 파일 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    log(f"✅ HTML 저장 완료: {OUTPUT_PATH}")

    # 5-1. index.html 총 자산 동기화
    index_path = f"{WORKSPACE}/public/index.html"
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            idx_html = f.read()

        total_str = fmt_krw(total_val_krw)
        profit_sign = '+' if total_profit >= 0 else ''
        profit_str = fmt_krw(abs(total_profit))
        pct_str = f"{profit_sign}{total_pct:.1f}%"

        # 총 자산 카드 업데이트
        import re as _re
        idx_html = _re.sub(
            r'(<div class="pval">)₩[\d.]+억(</div>\s*<div class="plbl">총 자산)',
            f'\\g<1>{total_str}\\2',
            idx_html
        )
        # 수익률 업데이트
        idx_html = _re.sub(
            r'(<div class="pchg">\+?[\d.]+% \(\+?₩[\d.]+억\) YTD)',
            f'<div class="pchg">{pct_str} ({profit_sign}{profit_str}) YTD',
            idx_html
        )
        # 총 매수금액 업데이트
        cost_str = fmt_krw(total_cost_krw)
        idx_html = _re.sub(
            r'(<div class="pval">)₩[\d.]+억(</div>\s*<div class="plbl">총 매수금액)',
            f'\\g<1>{cost_str}\\2',
            idx_html
        )
        # 평가손익 업데이트
        idx_html = _re.sub(
            r'(<div class="pval" style="color:var\(--red\)">)\+?₩[\d.]+억(</div>\s*<div class="plbl">평가손익)',
            f'\\g<1>{profit_sign}{profit_str}\\2',
            idx_html
        )
        # 마지막 업데이트 시각
        idx_html = _re.sub(
            r'<div class="mstat"[^>]*>.*?</div>',
            f'<div class="mstat" id="ms">● 업데이트: {updated_at}</div>',
            idx_html, count=1
        )

        # 가상자산 비중 업데이트
        crypto_pct = crypto_val_krw / total_val_krw * 100 if total_val_krw > 0 else 0
        crypto_level = '중위험' if crypto_pct < 15 else '고위험'
        crypto_badge = 'rm' if crypto_pct < 15 else 'rh'
        crypto_note = '현재 양호' if crypto_pct < 15 else '권장 15% 이하 초과'
        idx_html = _re.sub(
            r'가상자산[^\d]*[\d.]+%[^<\n]*',
            f'가상자산 비중 {crypto_pct:.1f}% (권장 15% 이하 — {crypto_note})',
            idx_html
        )

        # ── 시장 지수 embed (JS 초기값으로 삽입)
        try:
            mkt_symbols = [
                ('KOSPI',  '^KS11'),
                ('KOSDAQ', '^KQ11'),
                ('NASDAQ', '^IXIC'),
                ('SP500',  '^GSPC'),
                ('USDKRW', 'KRW=X'),
            ]
            mkt_js_parts = []
            for mid, sym in mkt_symbols:
                try:
                    mr = requests.get(
                        f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d',
                        headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
                    meta = mr.json()['chart']['result'][0]['meta']
                    cur = meta.get('regularMarketPrice', 0)
                    prev = meta.get('chartPreviousClose') or meta.get('previousClose', cur)
                    chg = cur - prev
                    pct = chg/prev*100 if prev else 0
                    mkt_js_parts.append(f'{{id:"{mid}",cur:{cur},chg:{chg:.4f},pct:{pct:.4f}}}')
                except: pass
            if mkt_js_parts:
                mkt_init = f'const MKT_INIT=[{",".join(mkt_js_parts)}];MKT_INIT.forEach(m=>renderMkt(m.id,"",m.cur,m.chg,m.pct));'
                # 기존 MKT_INIT 교체 또는 loadMarketData 앞에 삽입
                idx_html = _re.sub(r'const MKT_INIT=\[.*?\];MKT_INIT\.forEach[^;]+;', mkt_init, idx_html)
                if 'MKT_INIT' not in idx_html:
                    idx_html = idx_html.replace('loadMarketData(false);', mkt_init + '\nloadMarketData(false);')
                log(f"✅ 시장 지수 embed 완료 ({len(mkt_js_parts)}개)")
        except Exception as me:
            log(f"⚠️ 시장 지수 embed 실패: {me}")

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(idx_html)
        log(f"✅ index.html 총 자산 동기화 완료: {total_str} · 가상자산 {crypto_pct:.1f}%")
    except Exception as e:
        log(f"⚠️ index.html 동기화 실패: {e}")

    # 6. Cloudflare 배포
    log("🚀 Cloudflare 배포 중...")
    result = subprocess.run(
        ['/opt/homebrew/bin/wrangler', 'pages', 'deploy', '.',
         '--project-name=investment-command', '--branch=main', '--commit-dirty=true'],
        cwd=f"{WORKSPACE}/public",
        capture_output=True, text=True, timeout=120
    )

    if result.returncode == 0:
        # URL 추출
        url_match = re.search(r'https://[a-z0-9]+\.investment-command\.pages\.dev', result.stdout)
        deploy_url = url_match.group(0) if url_match else "배포 완료"
        log(f"✅ 배포 성공: {deploy_url}")
    else:
        log(f"❌ 배포 실패: {result.stderr[:200]}")

    log("🏁 포트폴리오 업데이터 완료")


if __name__ == '__main__':
    main()
