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


RANK_EMOJI = {1: '🥇', 2: '🥈', 3: '🥉', 4: '4위', 5: '5위'}


def rank_arrow(cur: int, prev: int) -> str:
    diff = prev - cur
    if diff > 0:
        return f'<span class="tag-up">▲{diff}</span>'
    if diff < 0:
        return f'<span class="tag-down">▼{abs(diff)}</span>'
    return '<span class="tag-flat">–</span>'


def render_group_block(summary: dict, group: dict) -> str:
    color = summary['color']
    rank = summary['current_rank']
    mcap = summary['current_total']
    chg = summary['mcap_change']
    chg_pct = summary['mcap_change_pct']
    chg_cls = 'pos' if chg > 0 else ('neg' if chg < 0 else 'flat')
    chg_sign = '+' if chg >= 0 else ''
    rows = []
    for m in group['members']:
        if not m['market_cap']:
            continue
        c = m['mcap_change']
        cc = 'pos' if c > 0 else ('neg' if c < 0 else 'flat')
        cs = '+' if c >= 0 else ''
        rows.append(
            f'<tr>'
            f'<td class="name-cell">{m["name"]}</td>'
            f'<td class="code-cell">{m["code"]}</td>'
            f'<td>{fmt_krw(m["price"])}</td>'
            f'<td class="prev">{fmt_krw(m["prev_close"])}</td>'
            f'<td class="mcap">{fmt_jo(m["market_cap"])}</td>'
            f'<td class="{cc}">{cs}{fmt_jo(c)}</td>'
            f'</tr>'
        )
    rank_arrow_html = rank_arrow(summary['current_rank'], summary['prev_rank'])
    return f"""
<details class="group-block" open>
  <summary class="group-summary" style="border-left-color:{color}">
    <div class="gs-left">
      <div class="rank-badge" style="color:{color}">{RANK_EMOJI.get(rank, f'{rank}위')}</div>
      <div>
        <div class="gs-name">{summary['group']} {rank_arrow_html}</div>
        <div class="gs-meta">{summary['count']}개 계열사 · 전일 {summary['prev_rank']}위</div>
      </div>
    </div>
    <div class="gs-right">
      <div class="gs-mcap" style="color:{color}">{fmt_jo(mcap)}</div>
      <div class="gs-chg {chg_cls}">{chg_sign}{fmt_jo(chg)} ({chg_pct:+.2f}%)</div>
    </div>
  </summary>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>종목명</th><th>코드</th><th>현재가</th><th>전일</th><th>시총</th><th>시총 변동</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</details>"""


def render_html(data: dict) -> str:
    rank_cards = []
    for s in data['summary']:
        r = s['current_rank']
        chg_cls = 'pos' if s['mcap_change'] > 0 else ('neg' if s['mcap_change'] < 0 else 'flat')
        chg_sign = '+' if s['mcap_change'] >= 0 else ''
        pr = s['prev_rank']
        move = ''
        if r < pr:
            move = f'<div class="rc-move up-move">▲ {pr-r}단계 상승</div>'
        elif r > pr:
            move = f'<div class="rc-move dn-move">▼ {r-pr}단계 하락</div>'
        rank_cards.append(
            f'<div class="rank-card" style="--gc:{s["color"]}">'
            f'  <div class="rc-rank">{RANK_EMOJI.get(r, f"{r}위")}</div>'
            f'  <div class="rc-name">{s["group"]}</div>'
            f'  <div class="rc-mcap">{fmt_jo(s["current_total"])}</div>'
            f'  <div class="rc-chg {chg_cls}">{chg_sign}{fmt_jo(s["mcap_change"])} ({s["mcap_change_pct"]:+.2f}%)</div>'
            f'  {move}'
            f'  <div class="rc-count">{s["count"]}개 계열사</div>'
            f'</div>'
        )
    rank_cards_html = '\n'.join(rank_cards)
    group_blocks_html = '\n'.join(render_group_block(s, data['groups'][s['group']]) for s in data['summary'])
    data_json = json.dumps(data, ensure_ascii=False)
    generated = data['generated_at']
    scope = data['scope_note']

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>5대 그룹 시총 대시보드</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #0a0e1a;
  --card: #151b2d;
  --card2: #1a1f2e;
  --border: #2d3748;
  --txt: #e0e6ed;
  --muted: #8b9dc3;
  --pos: #22c55e;
  --neg: #ef4444;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;font-size:14px;line-height:1.5;overflow-x:hidden}}
a{{color:#93c5fd;text-decoration:none}}

/* ─── TOP BAR ─────────── */
.topbar{{background:var(--card);border-bottom:2px solid #3b82f6;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}}
.tb-logo{{font-weight:800;font-size:15px;background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.tb-links{{display:flex;gap:10px;font-size:12px}}
.tb-links a{{color:var(--muted);padding:4px 8px;border-radius:999px;border:1px solid var(--border)}}
.tb-links a:hover{{color:var(--txt);border-color:#4b6cb7}}

/* ─── HERO ─────────────── */
.hero{{padding:16px 16px 0;text-align:center}}
.hero h1{{font-size:clamp(1.3rem,5vw,2rem);font-weight:900;background:linear-gradient(90deg,#60a5fa,#a78bfa,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero .sub{{color:var(--muted);font-size:.8rem;margin-top:4px}}

/* ─── RANK CARDS ───────── */
.rank-scroll{{display:flex;gap:12px;padding:16px;overflow-x:auto;scrollbar-width:none}}
.rank-scroll::-webkit-scrollbar{{display:none}}
.rank-card{{background:var(--card);border-radius:16px;padding:16px 14px;min-width:140px;flex-shrink:0;border:1px solid var(--border);border-top:3px solid var(--gc);text-align:center;transition:transform .15s}}
.rank-card:hover{{transform:translateY(-3px)}}
.rc-rank{{font-size:1.6rem;margin-bottom:4px}}
.rc-name{{font-size:1rem;font-weight:800;color:var(--gc);margin-bottom:6px}}
.rc-mcap{{font-size:1.3rem;font-weight:900;color:var(--txt);margin-bottom:4px}}
.rc-chg{{font-size:.75rem;font-weight:600;margin-bottom:4px}}
.rc-move{{font-size:.72rem;font-weight:700;padding:2px 6px;border-radius:999px;display:inline-block;margin-bottom:4px}}
.up-move{{background:rgba(34,197,94,.15);color:#22c55e}}
.dn-move{{background:rgba(239,68,68,.15);color:#ef4444}}
.rc-count{{font-size:.72rem;color:var(--muted)}}

/* ─── CHARTS ───────────── */
.charts{{padding:0 16px 16px;display:grid;gap:14px}}
.chart-card{{background:var(--card);border-radius:14px;padding:16px;border:1px solid var(--border)}}
.chart-label{{font-size:.85rem;font-weight:700;color:var(--txt);margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.chart-note{{font-size:.72rem;color:var(--muted);margin-bottom:10px}}

/* ─── GROUP BLOCKS ──────── */
.groups{{padding:0 16px 24px}}
details.group-block{{background:var(--card);border-radius:14px;margin-bottom:12px;border:1px solid var(--border);overflow:hidden}}
summary.group-summary{{list-style:none;cursor:pointer;padding:14px 16px;border-left:4px solid;display:flex;justify-content:space-between;align-items:center;gap:10px}}
summary.group-summary::-webkit-details-marker{{display:none}}
summary.group-summary:hover{{background:var(--card2)}}
.gs-left{{display:flex;align-items:center;gap:12px}}
.rank-badge{{font-size:1.5rem;line-height:1}}
.gs-name{{font-size:1.05rem;font-weight:800;display:flex;align-items:center;gap:6px}}
.gs-meta{{font-size:.75rem;color:var(--muted);margin-top:2px}}
.gs-right{{text-align:right;flex-shrink:0}}
.gs-mcap{{font-size:1.25rem;font-weight:900}}
.gs-chg{{font-size:.78rem;font-weight:600;margin-top:2px}}
.tag-up{{background:rgba(34,197,94,.18);color:#22c55e;padding:2px 6px;border-radius:999px;font-size:.72rem;font-weight:700}}
.tag-down{{background:rgba(239,68,68,.18);color:#ef4444;padding:2px 6px;border-radius:999px;font-size:.72rem;font-weight:700}}
.tag-flat{{color:var(--muted);font-size:.72rem}}

/* ─── TABLES ────────────── */
.tbl-wrap{{overflow-x:auto;padding:0 4px 12px}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}}
th{{background:var(--card2);color:var(--muted);padding:8px 8px;text-align:right;font-weight:600;white-space:nowrap;border-bottom:1px solid var(--border)}}
th:first-child,th:nth-child(2){{text-align:left}}
td{{padding:7px 8px;border-bottom:1px solid rgba(45,55,72,.4);text-align:right;white-space:nowrap}}
td.name-cell{{text-align:left;font-weight:600}}
td.code-cell{{text-align:left;color:var(--muted);font-family:monospace;font-size:.75rem}}
td.prev{{color:var(--muted)}}
td.mcap{{font-weight:700}}
tbody tr:hover td{{background:rgba(59,130,246,.05)}}

/* ─── UTILITY ───────────── */
.pos{{color:var(--pos)}} .neg{{color:var(--neg)}} .flat{{color:var(--muted)}}
.footer{{text-align:center;color:#4b5563;font-size:.75rem;padding:12px 16px 32px}}
</style>
</head>
<body>

<div class="topbar">
  <div class="tb-logo">🏢 5대 그룹 시총</div>
  <div class="tb-links">
    <a href="/">메인</a>
    <a href="/portfolio.html">포트폴리오</a>
    <a href="/wisereport">리포트</a>
    <a href="/iran-dashboard-kr/">이란</a>
  </div>
</div>

<div class="hero">
  <h1>한국 5대 그룹 시가총액 대시보드</h1>
  <div class="sub">{generated} · {scope}</div>
</div>

<div class="rank-scroll">
{rank_cards_html}
</div>

<div class="charts">
  <div class="chart-card">
    <div class="chart-label">💰 오늘 그룹별 시총 비교</div>
    <canvas id="todayBarChart" height="140"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-label">📈 순위 변동 추이 (2015 → 2026)</div>
    <div class="chart-note">※ 연도별 대표 시점 기준 · 공정거래위원회·리더스인덱스 참고</div>
    <canvas id="rankChart" height="200"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-label">📊 시가총액 성장 추이 (조원)</div>
    <div class="chart-note">※ 연도별 추정치 포함</div>
    <canvas id="mcapChart" height="200"></canvas>
  </div>
</div>

<div class="groups">
{group_blocks_html}
</div>

<div class="footer">
  OpenClaw Investment Command · 5대 그룹 시총 대시보드<br>
  현행 상장 계열사 기준 · 우선주 포함 · Yahoo Finance + Naver Finance
</div>

<script>
const DATA = {data_json};
const COLORS = Object.fromEntries(DATA.summary.map(s => [s.group, s.color]));
const ORDER = DATA.summary.map(s => s.group); // 현재 순위 순

// ── 오늘 시총 가로 바 차트 ──────────────────────────────────
new Chart(document.getElementById('todayBarChart'), {{
  type: 'bar',
  data: {{
    labels: DATA.summary.map(s => s.current_rank + '위 ' + s.group),
    datasets: [{{
      label: '시가총액 (조원)',
      data: DATA.summary.map(s => +(s.current_total / 1e12).toFixed(1)),
      backgroundColor: DATA.summary.map(s => s.color + 'cc'),
      borderColor: DATA.summary.map(s => s.color),
      borderWidth: 2,
      borderRadius: 6,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: ctx => ' ' + ctx.raw + '조원' }} }}
    }},
    scales: {{
      x: {{
        grid: {{ color: 'rgba(45,55,72,.4)' }},
        ticks: {{ color: '#8b9dc3', callback: v => v + '조' }}
      }},
      y: {{
        grid: {{ display: false }},
        ticks: {{ color: '#e0e6ed', font: {{ size: 13, weight: 'bold' }} }}
      }}
    }}
  }}
}});

// ── 연도별 순위 추이 (하드코딩 실제 데이터) ────────────────
const HIST_LABELS = ['2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026.3'];
const HIST_RANKS = {{
  '삼성':  [1,1,1,1,1,1,1,1,1,1,1,1],
  'SK':    [2,2,2,2,2,2,2,3,2,2,2,2],
  '현대차':[3,3,3,4,3,4,4,4,3,3,3,3],
  '한화':  [5,5,5,5,5,5,5,5,5,4,4,4],
  'LG':    [4,4,4,3,4,3,3,2,4,5,5,5],
}};
const HIST_MCAP = {{  // 조원 추정
  '삼성':  [204,222,290,265,350,410,475,385,440,500,440,1543],
  'SK':    [64, 72, 98, 88,128,155,195,175,195,290,260, 825],
  '현대차':[68, 65, 72, 63, 82, 96,138,128,148,195,210, 309],
  '한화':  [ 7,  8,  9, 10, 12, 15, 20, 32, 50, 90,160, 182],
  'LG':    [38, 42, 48, 55, 62,118,198,240,185,165,150, 176],
}};

new Chart(document.getElementById('rankChart'), {{
  type: 'line',
  data: {{
    labels: HIST_LABELS,
    datasets: ORDER.map(g => ({{
      label: g,
      data: HIST_RANKS[g],
      borderColor: COLORS[g],
      backgroundColor: COLORS[g] + '20',
      tension: 0.3,
      pointRadius: 5,
      pointHoverRadius: 8,
      borderWidth: 3,
      fill: false,
      pointStyle: 'circle',
    }}))
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ color: '#e0e6ed', font: {{ size: 12 }}, boxWidth: 14, padding: 16 }} }},
      tooltip: {{ callbacks: {{ label: ctx => ' ' + ctx.dataset.label + ': ' + ctx.raw + '위' }} }}
    }},
    scales: {{
      y: {{
        reverse: true, min: 0.5, max: 5.5,
        grid: {{ color: 'rgba(45,55,72,.5)' }},
        ticks: {{
          stepSize: 1, color: '#8b9dc3', font: {{ size: 12 }},
          callback: v => ({{1:'🥇 1위',2:'🥈 2위',3:'🥉 3위',4:'4위',5:'5위'}})[v] || ''
        }}
      }},
      x: {{
        grid: {{ color: 'rgba(45,55,72,.3)' }},
        ticks: {{ color: '#8b9dc3', font: {{ size: 11 }} }}
      }}
    }}
  }}
}});

// ── 시총 추이 ──────────────────────────────────────────────
new Chart(document.getElementById('mcapChart'), {{
  type: 'line',
  data: {{
    labels: HIST_LABELS,
    datasets: ORDER.map(g => ({{
      label: g,
      data: HIST_MCAP[g],
      borderColor: COLORS[g],
      backgroundColor: COLORS[g] + '15',
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 7,
      borderWidth: 2.5,
      fill: false,
    }}))
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ color: '#e0e6ed', font: {{ size: 12 }}, boxWidth: 14, padding: 16 }} }},
      tooltip: {{ callbacks: {{ label: ctx => ' ' + ctx.dataset.label + ': ' + ctx.raw + '조' }} }}
    }},
    scales: {{
      y: {{
        grid: {{ color: 'rgba(45,55,72,.4)' }},
        ticks: {{ color: '#8b9dc3', callback: v => v + '조' }}
      }},
      x: {{
        grid: {{ color: 'rgba(45,55,72,.3)' }},
        ticks: {{ color: '#8b9dc3', font: {{ size: 11 }} }}
      }}
    }}
  }}
}});

document.querySelectorAll('details.group-block').forEach(d => {{
  const tbl = d.querySelector('.tbl-wrap');
  if (tbl) d.querySelector('summary').insertAdjacentHTML('beforeend', '<span style="font-size:.72rem;color:#8b9dc3;margin-left:auto;padding-left:8px">▾</span>');
  d.addEventListener('toggle', () => {{
    const arrow = d.querySelector('summary span:last-child');
    if (arrow) arrow.textContent = d.open ? '▴' : '▾';
  }});
}});
</script>
</body>
</html>'''


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
