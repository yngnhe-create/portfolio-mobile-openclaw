#!/usr/bin/env python3
"""
투자커멘드 플레이북 자동 생성
- CSV 포트폴리오 분석 → 리스크 지표 계산 → 투자 전략 자동 생성 → HTML 배포
- 실행 주기: 4시간마다 (cron)
"""

import pandas as pd
import json
import os
import re
import subprocess
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
CSV_PATH = f"{WORKSPACE}/portfolio_full.csv"
OUTPUT_PATH = f"{WORKSPACE}/public/playbook.html"
LOG_PATH = f"{WORKSPACE}/scripts/playbook_auto.log"


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {msg}\n")


def clean_number(val):
    if pd.isna(val) or str(val).strip() in ['-', 'nan', '']:
        return 0
    s = str(val).replace(',', '').replace('₩', '').replace('$', '').replace('+', '').strip()
    s = re.sub(r'\(.*?\)', '', s).strip()
    try:
        return float(s)
    except:
        return 0


def load_portfolio():
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    df.columns = ['자산', '분류', '수량', '자산가치', '매수가', '현재가', '손익', '배당월', '투자배당률']
    return df


def analyze_portfolio(df):
    """포트폴리오 분석 지표 계산"""
    analysis = {
        'total_stocks': len(df),
        'sectors': {},
        'top_gainers': [],
        'top_losers': [],
        'dividend_stocks': [],
        'risk_items': [],
        'recommendations': [],
        'total_val': 0,
        'total_cost': 0,
    }

    USD_KRW = 1400  # 근사 환율

    sector_vals = {}
    total_val = 0
    total_cost = 0

    for _, row in df.iterrows():
        name = str(row['자산'])
        cat = str(row['분류'])
        qty = float(row['수량']) if not pd.isna(row['수량']) else 0

        # 자산가치
        raw_val = str(row['자산가치'])
        if '₩' in raw_val:
            val_krw = clean_number(raw_val)
        else:
            val_krw = clean_number(raw_val) * USD_KRW

        # 손익률 파싱
        손익_str = str(row['손익'])
        pct_match = re.search(r'([+-]?\d+\.?\d*)%', 손익_str)
        pct = float(pct_match.group(1)) if pct_match else 0

        if cat != '현금':
            total_val += val_krw
            sector_vals[cat] = sector_vals.get(cat, 0) + val_krw

            # 매수금액 계산
            raw_cost = str(row['매수가'])
            if raw_cost not in ['-', 'nan', '']:
                if '₩' in raw_cost:
                    cost_per = clean_number(raw_cost)
                else:
                    cost_per = clean_number(raw_cost) * USD_KRW
                total_cost += cost_per * qty

            # 상위 수익
            if pct > 50:
                analysis['top_gainers'].append({'name': name, 'pct': pct, 'val': val_krw})
            # 손실
            if pct < -10:
                analysis['top_losers'].append({'name': name, 'pct': pct, 'val': val_krw})

        # 배당 종목
        div = str(row['배당월'])
        if div and div != '-' and div != 'nan':
            div_yield = str(row['투자배당률'])
            analysis['dividend_stocks'].append({'name': name, 'div_month': div, 'yield': div_yield[:20]})

    analysis['total_val'] = total_val
    analysis['total_cost'] = total_cost
    total_profit = total_val - total_cost
    analysis['total_profit'] = total_profit
    analysis['total_pct'] = (total_profit / total_cost * 100) if total_cost > 0 else 0

    # 섹터 비중 계산
    for cat, val in sorted(sector_vals.items(), key=lambda x: x[1], reverse=True):
        pct = val / total_val * 100 if total_val > 0 else 0
        analysis['sectors'][cat] = {'val': val, 'pct': pct}

    # 리스크 항목 도출
    # 1. 가상자산 비중
    crypto_val = sum(v['val'] for k, v in analysis['sectors'].items() if '가상자산' in k)
    crypto_pct = crypto_val / total_val * 100 if total_val > 0 else 0
    if crypto_pct > 20:
        analysis['risk_items'].append({
            'level': 'high', 'icon': '🔴',
            'title': '가상자산 과다비중',
            'desc': f'현재 {crypto_pct:.1f}% (권장 15% 이하) — 1~2억 분할 매도 검토'
        })

    # 2. 단일 종목 집중
    top3 = analysis['top_gainers'][:3]
    for g in top3:
        w = g['val'] / total_val * 100 if total_val > 0 else 0
        if w > 10:
            analysis['risk_items'].append({
                'level': 'medium', 'icon': '🟡',
                'title': f'{g["name"]} 집중도',
                'desc': f'단일 종목 비중 {w:.1f}% — 부분 익실 또는 스탑로스 설정'
            })

    # 3. 손실 종목 경고
    for l in analysis['top_losers'][:3]:
        analysis['risk_items'].append({
            'level': 'medium', 'icon': '⚠️',
            'title': f'{l["name"]} 손실',
            'desc': f'현재 {l["pct"]:.1f}% 손실 중 — 손절 기준 재검토'
        })

    # 전략 생성
    total_pct = analysis['total_pct']
    if total_pct > 20:
        analysis['recommendations'].append({
            'type': '수익 실현', 'icon': '💰', 'priority': '즉시',
            'title': f'연간 목표 초과 달성 (+{total_pct:.1f}%)',
            'desc': '수익의 10~15% 현금화 검토. 리밸런싱으로 리스크 관리.'
        })

    analysis['recommendations'].append({
        'type': '리밸런싱', 'icon': '⚖️', 'priority': '1개월 내',
        'title': '섹터 리밸런싱',
        'desc': '가상자산 비중 축소 → 채권/배당주 비중 확대 (안정성 강화)'
    })

    analysis['recommendations'].append({
        'type': '분할 매수', 'icon': '📈', 'priority': '모니터링',
        'title': '신규 매수 종목 관리',
        'desc': '현대차: 단기 하락 구간 분할 매수 전략 유지. 목표 수익률 +15%'
    })

    # 정렬
    analysis['top_gainers'].sort(key=lambda x: x['pct'], reverse=True)
    analysis['top_losers'].sort(key=lambda x: x['pct'])

    return analysis


def fmt_krw(val):
    if val >= 100_000_000:
        return f"₩{val/100_000_000:.1f}억"
    elif val >= 10_000:
        return f"₩{val/10_000:.0f}만"
    return f"₩{val:,.0f}"


def generate_html(analysis):
    updated_at = datetime.now().strftime('%Y년 %m월 %d일 %H:%M KST')
    total_val = analysis['total_val']
    total_cost = analysis['total_cost']
    total_profit = analysis['total_profit']
    total_pct = analysis['total_pct']
    profit_sign = '+' if total_profit >= 0 else ''
    profit_color = '#ff4757' if total_profit >= 0 else '#4ecdc4'

    # 섹터 테이블 HTML
    sector_rows = ''
    for cat, d in list(analysis['sectors'].items())[:10]:
        bar_w = min(d['pct'], 100)
        sector_rows += f'''
<tr>
  <td style="padding:10px 8px;font-size:13px">{cat}</td>
  <td style="padding:10px 8px">
    <div style="height:8px;background:#2d3748;border-radius:4px;overflow:hidden">
      <div style="width:{bar_w:.0f}%;height:100%;background:var(--blu);border-radius:4px"></div>
    </div>
  </td>
  <td style="padding:10px 8px;font-size:13px;font-weight:700;text-align:right">{d['pct']:.1f}%</td>
  <td style="padding:10px 8px;font-size:11px;color:var(--sub);text-align:right">{fmt_krw(d['val'])}</td>
</tr>'''

    # 리스크 항목
    risk_html = ''
    level_colors = {'high': '#ff4757', 'medium': '#f9ca24', 'low': '#4ecdc4'}
    level_bg = {'high': 'rgba(255,71,87,.1)', 'medium': 'rgba(249,202,36,.1)', 'low': 'rgba(78,205,196,.1)'}
    for risk in analysis['risk_items'][:6]:
        col = level_colors.get(risk['level'], '#fff')
        bg = level_bg.get(risk['level'], '')
        risk_html += f'''
<div style="background:{bg};border-left:3px solid {col};border-radius:8px;padding:12px;margin-bottom:10px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
    <span>{risk['icon']}</span>
    <span style="font-size:13px;font-weight:700">{risk['title']}</span>
  </div>
  <div style="font-size:12px;color:var(--sub)">{risk['desc']}</div>
</div>'''

    if not risk_html:
        risk_html = '<div style="text-align:center;padding:20px;color:var(--sub)">리스크 항목 없음 ✅</div>'

    # 전략 추천
    rec_html = ''
    priority_colors = {'즉시': '#ff4757', '1개월 내': '#f9ca24', '모니터링': '#4ecdc4'}
    for rec in analysis['recommendations']:
        col = priority_colors.get(rec['priority'], '#8b9dc3')
        rec_html += f'''
<div style="background:var(--hdr);border-radius:10px;padding:14px;margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="font-size:13px;font-weight:700">{rec['icon']} {rec['title']}</span>
    <span style="padding:3px 8px;border-radius:10px;font-size:10px;font-weight:700;background:rgba(255,255,255,.1);color:{col}">{rec['priority']}</span>
  </div>
  <div style="font-size:12px;color:var(--sub)">{rec['desc']}</div>
</div>'''

    # 배당 종목 (상위 5개)
    div_html = ''
    for d in analysis['dividend_stocks'][:8]:
        div_html += f'''
<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--brd)">
  <span style="font-size:13px">{d['name']}</span>
  <div style="text-align:right">
    <div style="font-size:12px;color:#4ecdc4;font-weight:700">{d['yield']}</div>
    <div style="font-size:10px;color:var(--sub)">{d['div_month']}월 배당</div>
  </div>
</div>'''

    # 매수 신호 체크리스트
    buy_signals = [
        ('섹터 조정 15% 이상', True),
        ('거래량 평균 대비 3배 이상', False),
        ('RSI 30 이하 과매도', False),
        ('분기 실적 예상치 상회', True),
        ('목표주가 현재가 대비 20% 이상 상승여력', True),
    ]
    sell_signals = [
        ('수익률 +30% 이상 달성', True),
        ('펀더멘털 악화 (실적 하향 2분기 연속)', False),
        ('RSI 70 이상 과매수', False),
        ('섹터 전망 UNDERWEIGHT 전환', False),
        ('목표주가 달성', False),
    ]

    def checklist_html(items):
        html = ''
        for label, checked in items:
            icon = '✅' if checked else '⬜'
            style = 'color:var(--grn)' if checked else 'color:var(--sub)'
            html += f'<div style="padding:10px 0;border-bottom:1px solid var(--brd);font-size:13px;{style}">{icon} {label}</div>'
        return html

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>투자커멘드 | 플레이북</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0e1a;--card:#151b2d;--hdr:#1a1f2e;--brd:#2d3748;--txt:#e0e6ed;--sub:#8b9dc3;--red:#ff4757;--grn:#4ecdc4;--blu:#4834d4;--yel:#f9ca24}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;background:var(--bg);color:var(--txt);font-size:14px;padding-bottom:80px}}
.hdr{{background:var(--hdr);padding:15px;border-bottom:1px solid var(--brd);position:sticky;top:0;z-index:999}}
.hdr-ttl{{font-size:18px;font-weight:800;margin-bottom:4px}}
.upd{{font-size:11px;color:var(--sub)}}
.tcard{{background:linear-gradient(135deg,var(--blu),#686de0);padding:20px;margin:15px;border-radius:14px}}
.sec{{background:var(--card);margin:0 15px 15px;padding:18px;border-radius:12px}}
.sec-ttl{{font-size:15px;font-weight:700;margin-bottom:14px}}
.metric-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:0 15px 15px}}
.metric{{background:var(--card);padding:15px;border-radius:12px;text-align:center}}
.metric-val{{font-size:22px;font-weight:800;margin-bottom:4px}}
.metric-lbl{{font-size:11px;color:var(--sub)}}
.sector-table{{width:100%;border-collapse:collapse}}
.sector-table th{{text-align:left;padding:8px;font-size:11px;color:var(--sub);border-bottom:1px solid var(--brd)}}
.principle{{background:var(--hdr);border-left:4px solid var(--blu);border-radius:8px;padding:14px;margin-bottom:10px}}
.p-num{{font-size:22px;font-weight:900;color:var(--blu);margin-bottom:4px}}
.p-ttl{{font-size:14px;font-weight:700;margin-bottom:4px}}
.p-desc{{font-size:12px;color:var(--sub)}}
.bnav{{position:fixed;bottom:0;left:0;right:0;background:var(--hdr);border-top:1px solid var(--brd);display:flex;justify-content:space-around;padding:8px 0 20px;z-index:999}}
.bnav a{{display:flex;flex-direction:column;align-items:center;gap:3px;color:var(--sub);text-decoration:none;font-size:10px;padding:5px 10px}}
.bnav a.on{{color:var(--blu)}}.ni{{font-size:22px}}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-ttl">📖 플레이북</div>
  <div class="upd">⏱ 분석: {updated_at}</div>
</div>

<div class="tcard">
  <div style="font-size:12px;opacity:.8;margin-bottom:4px">포트폴리오 종합 현황</div>
  <div style="font-size:32px;font-weight:800;margin-bottom:4px">{fmt_krw(total_val)}</div>
  <div style="font-size:14px;font-weight:700">{profit_sign}{total_pct:.1f}% · {profit_sign}{fmt_krw(abs(total_profit))}</div>
</div>

<div class="metric-grid">
  <div class="metric"><div class="metric-val">{analysis['total_stocks']}</div><div class="metric-lbl">보유종목</div></div>
  <div class="metric"><div class="metric-val">{len(analysis['risk_items'])}</div><div class="metric-lbl">리스크 항목</div></div>
  <div class="metric"><div class="metric-val">{len(analysis['dividend_stocks'])}</div><div class="metric-lbl">배당종목</div></div>
  <div class="metric"><div class="metric-val">{len(analysis['sectors'])}</div><div class="metric-lbl">투자섹터</div></div>
</div>

<div class="sec">
  <div class="sec-ttl">⚠️ 포트폴리오 리스크 경고</div>
  {risk_html}
</div>

<div class="sec">
  <div class="sec-ttl">💡 투자 전략 추천</div>
  {rec_html}
</div>

<div class="sec">
  <div class="sec-ttl">📊 섹터별 비중 분석</div>
  <table class="sector-table">
    <thead><tr><th>섹터</th><th>비중 바</th><th>비중</th><th>금액</th></tr></thead>
    <tbody>{sector_rows}</tbody>
  </table>
</div>

<div class="sec">
  <div class="sec-ttl">✅ 매수 신호 체크리스트</div>
  {checklist_html(buy_signals)}
</div>

<div class="sec">
  <div class="sec-ttl">🚨 매도 신호 체크리스트</div>
  {checklist_html(sell_signals)}
</div>

<div class="sec">
  <div class="sec-ttl">💰 배당 포트폴리오</div>
  {div_html}
</div>

<div class="sec">
  <div class="sec-ttl">📌 투자 5원칙</div>
  <div class="principle"><div class="p-num">01</div><div class="p-ttl">분산 투자</div><div class="p-desc">단일 종목 10% 이상 비중 금지. 섹터별 20% 이상 금지.</div></div>
  <div class="principle"><div class="p-num">02</div><div class="p-ttl">손절 원칙</div><div class="p-desc">-15% 도달 시 무조건 재검토. -25% 도달 시 강제 손절.</div></div>
  <div class="principle"><div class="p-num">03</div><div class="p-ttl">분할 매수</div><div class="p-desc">한 번에 전액 투자 금지. 3회 이상 분할 매수 원칙.</div></div>
  <div class="principle"><div class="p-num">04</div><div class="p-ttl">수익 실현</div><div class="p-desc">+30% 달성 시 절반 익실. 연간 목표 초과 시 리밸런싱.</div></div>
  <div class="principle"><div class="p-num">05</div><div class="p-ttl">리뷰 사이클</div><div class="p-desc">주 1회 포트폴리오 리뷰. 월 1회 전략 재검토.</div></div>
</div>

<nav class="bnav">
  <a href="index.html"><span class="ni">🏠</span>홈</a>
  <a href="portfolio.html"><span class="ni">📊</span>포트폴리오</a>
  <a href="wisereport.html"><span class="ni">📋</span>리포트</a>
  <a href="playbook.html" class="on"><span class="ni">📖</span>플레이북</a>
</nav>
</body>
</html>'''


def main():
    log("=" * 60)
    log("🚀 플레이북 자동 생성 시작")

    df = load_portfolio()
    log(f"✅ CSV 로드: {len(df)}개 종목")

    analysis = analyze_portfolio(df)
    log(f"📊 분석 완료: 총 자산 {fmt_krw(analysis['total_val'])}, 수익률 {analysis['total_pct']:.1f}%")

    html = generate_html(analysis)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    log(f"✅ HTML 저장: {OUTPUT_PATH}")

    # 배포
    log("🚀 Cloudflare 배포 중...")
    result = subprocess.run(
        ['/opt/homebrew/bin/wrangler', 'pages', 'deploy', '.',
         '--project-name=investment-command', '--branch=main', '--commit-dirty=true'],
        cwd=f"{WORKSPACE}/public",
        capture_output=True, text=True, timeout=120
    )

    if result.returncode == 0:
        url_match = re.search(r'https://[a-z0-9]+\.investment-command\.pages\.dev', result.stdout)
        log(f"✅ 배포: {url_match.group(0) if url_match else '완료'}")
    else:
        log(f"❌ 배포 실패: {result.stderr[:200]}")

    log("🏁 플레이북 생성 완료")


if __name__ == '__main__':
    main()
