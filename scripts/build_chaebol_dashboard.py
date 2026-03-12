#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
import yfinance as yf

ROOT = Path('/Users/geon/.openclaw/workspace')
PUBLIC = ROOT / 'public' / 'chaebol-groups'
PUBLIC.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / 'data' / 'chaebol_groups'
CACHE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 현행 상장 계열사 기준 (코스피/코스닥, 우선주 포함)
GROUPS: Dict[str, dict] = {
    '삼성': {
        'color': '#3b82f6',
        'stocks': {
            '005930': '삼성전자', '005935': '삼성전자우', '006400': '삼성SDI',
            '207940': '삼성바이오로직스', '028260': '삼성물산', '032830': '삼성생명',
            '000810': '삼성화재', '000815': '삼성화재우', '018260': '삼성SDS',
            '009150': '삼성전기', '010140': '삼성중공업', '028050': '삼성E&A',
            '016360': '삼성증권', '029780': '삼성카드', '012750': '에스원',
            '030000': '제일기획', '008770': '호텔신라', '008775': '호텔신라우',
            '067280': '멀티캠퍼스',
        },
    },
    'LG': {
        'color': '#ef4444',
        'stocks': {
            '003550': 'LG', '003555': 'LG우', '066570': 'LG전자', '066575': 'LG전자우',
            '051910': 'LG화학', '051915': 'LG화학우', '373220': 'LG에너지솔루션',
            '034220': 'LG디스플레이', '011070': 'LG이노텍', '032640': 'LG유플러스',
            '051900': 'LG생활건강', '051905': 'LG생활건강우', '037560': 'LG헬로비전',
            '064400': 'LG씨엔에스', '035000': 'HS애드'
        },
    },
    '한화': {
        'color': '#f59e0b',
        'stocks': {
            '000880': '한화', '000885': '한화우', '00088K': '한화3우B',
            '012450': '한화에어로스페이스', '009830': '한화솔루션', '009835': '한화솔루션우',
            '042660': '한화오션', '272210': '한화시스템', '088350': '한화생명',
            '003530': '한화투자증권', '003535': '한화투자증권우', '000370': '한화손해보험',
            '489790': '한화비전', '082740': '한화엔진', '452260': '한화갤러리아',
            '45226K': '한화갤러리아우', '452260': '한화갤러리아', '451800': '한화리츠',
            '317320': '한화에어로스페이스?대체아님'
        },
    },
    'SK': {
        'color': '#8b5cf6',
        'stocks': {
            '034730': 'SK', '03473K': 'SK우', '000660': 'SK하이닉스',
            '402340': 'SK스퀘어', '096770': 'SK이노베이션', '096775': 'SK이노베이션우',
            '017670': 'SK텔레콤', '011790': 'SKC', '326030': 'SK바이오팜',
            '302440': 'SK바이오사이언스', '361610': 'SK아이이테크놀로지', '006120': 'SK디스커버리',
            '006125': 'SK디스커버리우', '285130': 'SK케미칼', '28513K': 'SK케미칼우',
            '018670': 'SK가스', '001740': 'SK네트웍스', '001745': 'SK네트웍스우',
            '100090': 'SK오션플랜트', '475150': 'SK이터닉스', '395400': 'SK리츠',
            '210980': 'SK디앤디', '039860': '나노엔텍'
        },
    },
    '현대차': {
        'color': '#10b981',
        'stocks': {
            '005380': '현대차', '005385': '현대차우', '005387': '현대차2우B', '005389': '현대차3우B',
            '000270': '기아', '012330': '현대모비스', '086280': '현대글로비스',
            '011210': '현대위아', '004020': '현대제철', '307950': '현대오토에버',
            '000720': '현대건설', '267270': '현대건설우', '214320': '이노션',
            '064350': '현대로템', '004560': '현대비앤지스틸', '004565': '현대비앤지스틸우',
            '001500': '현대차증권', '001515': '현대차증권우', '079430': '현대리바트'
        },
    },
}

# clearly wrong placeholder / duplicate cleanup helper below handles removal
INVALID_NAMES = {'한화에어로스페이스?대체아님'}


def clean_groups(groups: Dict[str, dict]) -> Dict[str, dict]:
    cleaned = {}
    for g, info in groups.items():
        seen = {}
        for code, name in info['stocks'].items():
            if name in INVALID_NAMES:
                continue
            if code in seen:
                continue
            seen[code] = name
        cleaned[g] = {'color': info['color'], 'stocks': seen}
    return cleaned

GROUPS = clean_groups(GROUPS)


def to_yf_symbol(code: str) -> str:
    # 우선주/특수코드도 Yahoo가 .KS/.KQ 접미만 쓰는 경우가 많음
    return code


def resolve_symbol(code: str) -> Optional[str]:
    cache_file = CACHE / 'symbol_map.json'
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    if code in cache:
        return cache[code]

    for suffix in ['.KS', '.KQ']:
        symbol = f'{code}{suffix}'
        try:
            hist = yf.download(symbol, period='5d', interval='1d', auto_adjust=False, progress=False, threads=False)
            if hist is not None and len(hist) > 0:
                cache[code] = symbol
                cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
                return symbol
        except Exception:
            pass
    cache[code] = None
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    return None


def fetch_naver_current(code: str) -> dict:
    url = f'https://m.stock.naver.com/api/stock/{code}/integration'
    try:
        data = requests.get(url, headers=HEADERS, timeout=10).json()
        deal = (data.get('dealTrendInfos') or [{}])[0]
        total_infos = data.get('totalInfos') or []
        market_cap = 0
        for item in total_infos:
            if item.get('code') == 'marketValue':
                market_cap = parse_mcap_string(item.get('value', ''))
        price = int(str(deal.get('closePrice', '0')).replace(',', '') or 0)
        prev_close = price - signed_change_from_deal(deal)
        return {'price': price, 'prev_close': prev_close, 'market_cap': market_cap}
    except Exception:
        return {'price': 0, 'prev_close': 0, 'market_cap': 0}


def signed_change_from_deal(deal: dict) -> int:
    comp = str(deal.get('compareToPreviousClosePrice', '0')).replace(',', '').replace('+', '')
    try:
        change = int(comp or 0)
    except Exception:
        change = 0
    direction = (deal.get('compareToPreviousPrice') or {}).get('name')
    if direction == 'FALLING':
        change = -abs(change)
    return change


def parse_mcap_string(s: str) -> int:
    s = str(s).replace(',', '').replace(' ', '')
    if not s:
        return 0
    # returns KRW
    try:
        if '조' in s:
            a, b = s.split('조', 1)
            jo = float(a) if a else 0
            eok = float(b.replace('억', '').replace('원', '') or 0)
            return int((jo * 10000 + eok) * 100000000)
        if '억' in s:
            return int(float(s.replace('억', '').replace('원', '')) * 100000000)
        return int(float(s.replace('원', '')))
    except Exception:
        return 0


def get_month_labels(start_years=10):
    today = pd.Timestamp.now(tz='Asia/Seoul').tz_localize(None)
    start = (today - pd.DateOffset(years=start_years)).replace(day=1)
    return pd.date_range(start=start, end=today, freq='ME')


def load_ticker_history(symbol: str, start: str) -> pd.DataFrame:
    hist = yf.download(symbol, start=start, interval='1d', auto_adjust=False, progress=False, threads=False)
    if hist is None or len(hist) == 0:
        return pd.DataFrame()
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)
    return hist


def load_shares(symbol: str, start: str) -> Optional[pd.Series]:
    try:
        s = yf.Ticker(symbol).get_shares_full(start=start)
        if s is not None and len(s) > 0:
            s.index = pd.to_datetime(s.index).tz_localize(None)
            return s.sort_index()
    except Exception:
        pass
    return None


def infer_current_shares_from_naver(market_cap: int, price: int) -> Optional[float]:
    if market_cap and price:
        return market_cap / price
    return None


def fmt_krw(v: float) -> str:
    return f"₩{int(round(v)):,}" if v and not math.isnan(v) else '—'


def fmt_jo(v: float) -> str:
    if not v or math.isnan(v):
        return '—'
    return f"{v/1e12:,.2f}조"


def pct_change(cur: float, prev: float) -> float:
    return ((cur - prev) / prev * 100) if prev else 0.0


def build_dataset() -> dict:
    labels = get_month_labels(10)
    start = labels.min().strftime('%Y-%m-%d')

    group_series = {g: pd.Series(0.0, index=labels) for g in GROUPS}
    detail_groups = {}

    for group_name, info in GROUPS.items():
        members = []
        for code, name in info['stocks'].items():
            symbol = resolve_symbol(code)
            naver = fetch_naver_current(code)
            current_price = naver['price']
            prev_close = naver['prev_close']
            current_mcap = naver['market_cap']
            current_shares = infer_current_shares_from_naver(current_mcap, current_price)
            prev_mcap = current_shares * prev_close if current_shares and prev_close else 0

            hist_monthly_mcap = pd.Series(0.0, index=labels)
            if symbol:
                hist = load_ticker_history(symbol, start)
                if len(hist) > 0 and 'Close' in hist.columns:
                    close = hist['Close'].copy()
                    close.index = pd.to_datetime(close.index).tz_localize(None)
                    close_month = close.resample('ME').last().reindex(labels).ffill()
                    shares = load_shares(symbol, start)
                    if shares is not None and len(shares) > 0:
                        shares_month = shares.resample('ME').last().reindex(labels).ffill()
                    else:
                        shares_month = pd.Series(current_shares or 0, index=labels)
                    hist_monthly_mcap = (close_month * shares_month).fillna(0.0)

            group_series[group_name] = group_series[group_name].add(hist_monthly_mcap, fill_value=0.0)

            members.append({
                'code': code,
                'name': name,
                'symbol': symbol,
                'price': current_price,
                'prev_close': prev_close,
                'market_cap': current_mcap,
                'prev_market_cap': prev_mcap,
                'change_pct': pct_change(current_price, prev_close),
                'mcap_change': current_mcap - prev_mcap,
            })
            time.sleep(0.05)

        members.sort(key=lambda x: x['market_cap'], reverse=True)
        detail_groups[group_name] = {
            'color': info['color'],
            'members': members,
            'current_total': sum(x['market_cap'] for x in members),
            'prev_total': sum(x['prev_market_cap'] for x in members),
        }

    # ranking by month
    rank_map = {g: [] for g in GROUPS}
    totals_by_month = []
    for dt in labels:
        ranking = sorted(GROUPS.keys(), key=lambda g: group_series[g].get(dt, 0), reverse=True)
        month_row = {'date': dt.strftime('%Y-%m')}
        for i, g in enumerate(ranking, start=1):
            rank_map[g].append(i)
            month_row[g] = float(group_series[g].get(dt, 0))
        totals_by_month.append(month_row)

    current_rank = sorted(detail_groups.keys(), key=lambda g: detail_groups[g]['current_total'], reverse=True)
    prev_rank = sorted(detail_groups.keys(), key=lambda g: detail_groups[g]['prev_total'], reverse=True)

    summary = []
    for g in current_rank:
        cur = detail_groups[g]['current_total']
        prev = detail_groups[g]['prev_total']
        summary.append({
            'group': g,
            'color': detail_groups[g]['color'],
            'current_total': cur,
            'prev_total': prev,
            'current_rank': current_rank.index(g) + 1,
            'prev_rank': prev_rank.index(g) + 1,
            'mcap_change': cur - prev,
            'mcap_change_pct': pct_change(cur, prev),
            'count': len(detail_groups[g]['members']),
        })

    return {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        'labels': [d.strftime('%Y-%m') for d in labels],
        'rank_history': rank_map,
        'mcap_history': totals_by_month,
        'summary': summary,
        'groups': detail_groups,
        'scope_note': '현행 상장 계열사 기준 · 우선주 포함 · 10년 월말 종가/주식수 기반 시총 추정',
    }


def render_html(data: dict) -> str:
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>5대 그룹 시총 순위 대시보드</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0e1a;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;padding:16px;line-height:1.45}}
a{{color:#93c5fd;text-decoration:none}} a:hover{{text-decoration:underline}}
.header{{text-align:center;margin-bottom:20px}}
.header h1{{font-size:1.8rem;background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px}}
.sub{{color:#94a3b8;font-size:.9rem}}
.top-links{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:12px 0 18px}}
.top-links a{{background:#111827;border:1px solid #334155;padding:8px 12px;border-radius:999px;font-size:.85rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px}}
.card{{background:#111827;border:1px solid #253042;border-radius:14px;padding:14px}}
.card h3{{font-size:.82rem;color:#94a3b8;margin-bottom:8px}}
.big{{font-size:1.35rem;font-weight:800}}
.chart-card{{background:#111827;border:1px solid #253042;border-radius:14px;padding:16px;margin-bottom:18px}}
.chart-title{{font-size:1rem;font-weight:800;margin-bottom:10px}}
.rank-box{{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}}
.badge{{padding:4px 8px;border-radius:999px;font-size:.78rem;font-weight:700}}
.group-block{{background:#111827;border:1px solid #253042;border-radius:14px;padding:16px;margin-bottom:16px}}
.group-header{{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:10px;flex-wrap:wrap}}
.group-name{{font-size:1.2rem;font-weight:800}}
.group-meta{{font-size:.88rem;color:#94a3b8}}
.up{{color:#22c55e}} .down{{color:#ef4444}} .flat{{color:#94a3b8}}
.tbl-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:.83rem}}
th,td{{padding:8px 6px;border-bottom:1px solid #1f2937;text-align:right;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}
th:nth-child(2),td:nth-child(2){{text-align:left}}
tr:hover td{{background:#0b1220}}
.footer{{text-align:center;color:#64748b;font-size:.78rem;margin-top:24px}}
@media(max-width:720px){{body{{padding:12px}} .header h1{{font-size:1.45rem}}}}
</style>
</head>
<body>
<div class="header">
  <h1>🏢 한국 5대 그룹 시총 순위 대시보드</h1>
  <div class="sub">{data['generated_at']} · {data['scope_note']}</div>
</div>
<div class="top-links">
  <a href="/">메인</a>
  <a href="/portfolio.html">포트폴리오</a>
  <a href="/wisereport">와이즈리포트</a>
  <a href="/iran-dashboard-kr/">이란 대시보드</a>
</div>
<div class="grid">
  {''.join([f"<div class='card'><h3>{s['group']} · 현재 {s['current_rank']}위</h3><div class='big' style='color:{s['color']}'>{fmt_jo(s['current_total'])}</div><div class='{ 'up' if s['mcap_change']>0 else 'down' if s['mcap_change']<0 else 'flat'}'>전일 대비 {('+' if s['mcap_change']>=0 else '')}{fmt_jo(s['mcap_change'])} ({s['mcap_change_pct']:+.2f}%) · 계열사 {s['count']}개</div></div>" for s in data['summary']])}
</div>
<div class="chart-card"><div class="chart-title">📈 최근 10년 그룹별 순위 변동</div><canvas id="rankChart" height="110"></canvas></div>
<div class="chart-card"><div class="chart-title">💰 최근 10년 그룹별 시총 추이 (월말, 조원)</div><canvas id="mcapChart" height="120"></canvas></div>
{''.join(render_group_block(s, data['groups'][s['group']]) for s in data['summary'])}
<div class="footer">OpenClaw · 5대 그룹 시총 대시보드</div>
<script>
const DATA = {json.dumps(data, ensure_ascii=False)};
const rankCtx = document.getElementById('rankChart');
const mcapCtx = document.getElementById('mcapChart');
new Chart(rankCtx, {{
  type:'line',
  data:{{
    labels: DATA.labels,
    datasets: DATA.summary.map(s => ({{
      label:s.group,
      data: DATA.rank_history[s.group],
      borderColor:s.color,
      backgroundColor:s.color,
      tension:.25,
      pointRadius:0,
      pointHoverRadius:4,
      borderWidth:2
    }}))
  }},
  options:{{
    responsive:true,
    plugins:{{legend:{{position:'bottom'}}}},
    scales:{{
      y:{{reverse:true,min:1,max:5,ticks:{{stepSize:1}}}},
      x:{{ticks:{{maxTicksLimit:12}}}}
    }}
  }}
}});
new Chart(mcapCtx, {{
  type:'line',
  data:{{
    labels: DATA.labels,
    datasets: DATA.summary.map(s => ({{
      label:s.group,
      data: DATA.mcap_history.map(r => (r[s.group]||0)/1e12),
      borderColor:s.color,
      backgroundColor:s.color + '22',
      fill:false,
      tension:.2,
      pointRadius:0,
      borderWidth:2
    }}))
  }},
  options:{{
    responsive:true,
    plugins:{{legend:{{position:'bottom'}}}},
    scales:{{x:{{ticks:{{maxTicksLimit:12}}}}, y:{{ticks:{{callback:(v)=>v+'조'}}}}}}
  }}
}});
</script>
</body>
</html>'''


def render_group_block(summary: dict, group: dict) -> str:
    rank_change = summary['prev_rank'] - summary['current_rank']
    if rank_change > 0:
        rank_txt = f"▲ {rank_change}단계 상승"
        cls = 'up'
    elif rank_change < 0:
        rank_txt = f"▼ {abs(rank_change)}단계 하락"
        cls = 'down'
    else:
        rank_txt = '순위 변동 없음'
        cls = 'flat'
    rows = []
    for m in group['members']:
        rows.append(f"<tr><td>{m['name']}</td><td>{m['code']}</td><td>{fmt_krw(m['price'])}</td><td>{fmt_krw(m['prev_close'])}</td><td>{fmt_jo(m['market_cap'])}</td><td>{fmt_jo(m['prev_market_cap'])}</td><td class='{ 'up' if m['mcap_change']>0 else 'down' if m['mcap_change']<0 else 'flat'}'>{('+' if m['mcap_change']>=0 else '')}{fmt_jo(m['mcap_change'])}</td></tr>")
    return f"""
<div class='group-block'>
  <div class='group-header'>
    <div>
      <div class='group-name' style='color:{summary['color']}'>{summary['current_rank']}위 · {summary['group']}</div>
      <div class='group-meta'>{summary['count']}개 상장 계열사 · 전일 {summary['prev_rank']}위 → 오늘 {summary['current_rank']}위</div>
      <div class='{cls}' style='font-size:.88rem;margin-top:4px'>{rank_txt}</div>
    </div>
    <div style='text-align:right'>
      <div class='big' style='color:{summary['color']}'>{fmt_jo(summary['current_total'])}</div>
      <div class='{ 'up' if summary['mcap_change']>0 else 'down' if summary['mcap_change']<0 else 'flat'}'>전일 대비 {('+' if summary['mcap_change']>=0 else '')}{fmt_jo(summary['mcap_change'])} ({summary['mcap_change_pct']:+.2f}%)</div>
    </div>
  </div>
  <div class='tbl-wrap'>
    <table>
      <thead><tr><th>종목</th><th>코드</th><th>현재가</th><th>전일종가</th><th>시총</th><th>전일 시총</th><th>시총 변동</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</div>"""


def build_message(data: dict) -> str:
    lines = ["## 🏢 5대 그룹 시총 마감 브리핑", f"> {data['generated_at']} 기준"]
    for s in data['summary']:
        arrow = '▲' if s['mcap_change'] > 0 else '▼' if s['mcap_change'] < 0 else '—'
        rank_move = ''
        if s['prev_rank'] != s['current_rank']:
            rank_move = f" / 전일 {s['prev_rank']}위→오늘 {s['current_rank']}위"
        lines.append(f"- **{s['current_rank']}위 {s['group']}**: {fmt_jo(s['current_total'])} ({arrow} {fmt_jo(abs(s['mcap_change']))}, {s['mcap_change_pct']:+.2f}%){rank_move}")
    lines.append('')
    lines.append('🔗 대시보드: <https://investment-command.pages.dev/chaebol-groups/>')
    return '\n'.join(lines)


def main():
    import sys
    data = build_dataset()
    (CACHE / 'latest.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    html = render_html(data)
    (PUBLIC / 'index.html').write_text(html, encoding='utf-8')
    if '--summary' in sys.argv:
        print(build_message(data))
    else:
        print(f"built: {PUBLIC / 'index.html'}")
        print(build_message(data))


if __name__ == '__main__':
    main()
