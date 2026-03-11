#!/usr/bin/env python3
"""5대그룹 시가총액 대시보드 생성 스크립트"""

import requests
import json
import time
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

GROUPS = {
    "삼성": {
        "color": "#3b82f6",
        "stocks": {
            "005930": "삼성전자", "005935": "삼성전자우", "006400": "삼성SDI",
            "207940": "삼성바이오로직스", "028260": "삼성물산", "000810": "삼성화재해상",
            "032830": "삼성생명", "010140": "삼성중공업", "028050": "삼성엔지니어링",
            "018260": "삼성SDS", "009150": "삼성전기", "012750": "에스원",
            "030000": "제일기획", "029780": "삼성카드",
        },
    },
    "LG": {
        "color": "#ef4444",
        "stocks": {
            "066570": "LG전자", "051910": "LG화학", "373220": "LG에너지솔루션",
            "034220": "LG디스플레이", "011070": "LG이노텍", "032640": "LG유플러스",
            "003550": "LG", "051900": "LG생활건강", "037560": "LG헬로비전",
        },
    },
    "현대차": {
        "color": "#10b981",
        "stocks": {
            "005380": "현대차", "000270": "기아", "012330": "현대모비스",
            "086280": "현대글로비스", "011210": "현대위아", "307950": "현대오토에버",
            "004020": "현대제철", "064350": "현대로템",
        },
    },
    "한화": {
        "color": "#f59e0b",
        "stocks": {
            "012450": "한화에어로스페이스", "009830": "한화솔루션", "272210": "한화시스템",
            "042660": "한화오션", "088350": "한화생명", "000880": "한화",
            "003530": "한화투자증권",
        },
    },
    "SK": {
        "color": "#8b5cf6",
        "stocks": {
            "000660": "SK하이닉스", "017670": "SK텔레콤", "096770": "SK이노베이션",
            "034730": "SK", "011790": "SKC", "402340": "SK스퀘어",
            "326030": "SK바이오팜", "018670": "SK가스",
        },
    },
}


def parse_mcap_value(raw: str) -> int:
    """시총 문자열 파싱 -> 억원 단위. 예: '1,140조 1,223억' -> 11401223"""
    mc = raw.replace(",", "").replace(" ", "")
    mcap_eok = 0
    if "조" in mc:
        parts = mc.split("조")
        jo = float(parts[0]) if parts[0] else 0
        eok = 0
        if len(parts) > 1:
            rest = parts[1].replace("억", "").replace("원", "").strip()
            if rest:
                eok = float(rest)
        mcap_eok = int(jo * 10000 + eok)
    elif "억" in mc:
        mcap_eok = int(float(mc.replace("억", "").replace("원", "")))
    else:
        try:
            mcap_eok = int(float(mc))
        except:
            pass
    return mcap_eok


def fetch_stock_data(code: str, name: str) -> dict:
    """네이버 모바일 API로 종목 데이터 수집"""
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        total_infos = data.get("totalInfos") or []

        # totalInfos에서 필요한 값 추출
        price = 0
        mcap_eok = 0
        for item in total_infos:
            c = item.get("code", "")
            v = item.get("value", "")
            if c == "marketValue":
                mcap_eok = parse_mcap_value(v)

        # dealTrendInfos에서 최신 가격/등락 정보
        deal_infos = data.get("dealTrendInfos") or []
        change = 0
        change_pct = 0.0
        if deal_infos:
            latest = deal_infos[0]
            price_str = latest.get("closePrice", "0")
            price = int(str(price_str).replace(",", ""))
            comp = latest.get("compareToPreviousClosePrice", "0")
            change = int(str(comp).replace(",", "").replace("+", ""))
            # 등락 방향
            direction = latest.get("compareToPreviousPrice", {})
            if direction.get("name") == "FALLING":
                change = -abs(change)
            # 등락률 계산
            prev = price - change
            if prev > 0:
                change_pct = round(change / prev * 100, 2)

        return {
            "code": code, "name": name,
            "price": price, "change": change, "change_pct": change_pct,
            "mcap_eok": mcap_eok,
        }
    except Exception as e:
        print(f"  [ERROR] {code} {name}: {e}")
        return {
            "code": code, "name": name,
            "price": 0, "change": 0, "change_pct": 0.0, "mcap_eok": 0,
        }


def fetch_kospi():
    """코스피 지수 가져오기"""
    try:
        url = "https://m.stock.naver.com/api/index/KOSPI/basic"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        return {
            "value": data.get("closePrice", "—"),
            "change": data.get("compareToPreviousClosePrice", "0"),
            "change_pct": data.get("fluctuationsRatio", "0"),
        }
    except:
        return {"value": "—", "change": "0", "change_pct": "0"}


def collect_all():
    """모든 종목 데이터 수집"""
    result = {}
    all_stocks = []
    for group_name, group_info in GROUPS.items():
        print(f"\n[{group_name}] 수집 중...")
        stocks = []
        for code, name in group_info["stocks"].items():
            print(f"  {code} {name}...", end=" ", flush=True)
            data = fetch_stock_data(code, name)
            print(f"가격={data['price']:,} 시총={data['mcap_eok']:,}억")
            stocks.append(data)
            time.sleep(0.15)

        total_mcap = sum(s["mcap_eok"] for s in stocks)
        stocks.sort(key=lambda x: x["mcap_eok"], reverse=True)
        result[group_name] = {
            "color": group_info["color"],
            "total_mcap": total_mcap,
            "stocks": stocks,
        }
        all_stocks.extend(stocks)

    all_stocks.sort(key=lambda x: x["mcap_eok"], reverse=True)
    return result, all_stocks


def fmt_price(v):
    """숫자 포맷"""
    if v == 0:
        return "—"
    return f"{v:,}"


def fmt_mcap(eok):
    """시총 포맷: 조/억"""
    if eok == 0:
        return "—"
    if eok >= 10000:
        jo = eok / 10000
        return f"{jo:,.1f}조"
    return f"{eok:,}억"


def fmt_change(change, pct):
    """등락 포맷"""
    if change > 0:
        return f'<span style="color:#ef4444">▲ {change:,} ({pct:+.2f}%)</span>'
    elif change < 0:
        return f'<span style="color:#3b82f6">▼ {abs(change):,} ({pct:.2f}%)</span>'
    return f'<span style="color:#9ca3af">— 0 (0.00%)</span>'


def generate_html(groups_data, all_stocks, kospi):
    """HTML 대시보드 생성"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Sort groups by total_mcap
    sorted_groups = sorted(groups_data.items(), key=lambda x: x[1]["total_mcap"], reverse=True)
    total_all = sum(g["total_mcap"] for _, g in sorted_groups)

    # Kospi display
    kospi_val = kospi.get("value", "—")
    kospi_change = kospi.get("change", "0")
    kospi_pct = kospi.get("change_pct", "0")

    # Chart data
    chart_labels = json.dumps([g[0] for g in sorted_groups], ensure_ascii=False)
    chart_data = json.dumps([round(g[1]["total_mcap"] / 10000, 1) for g in sorted_groups])
    chart_colors = json.dumps([g[1]["color"] for g in sorted_groups])

    # Group cards
    group_cards_html = ""
    for rank, (gname, gdata) in enumerate(sorted_groups, 1):
        color = gdata["color"]
        mcap = gdata["total_mcap"]
        pct_of_total = (mcap / total_all * 100) if total_all else 0

        # Calculate group change (weighted average)
        group_changes = []
        for s in gdata["stocks"]:
            if s["change_pct"] != 0:
                group_changes.append(s["change_pct"])
        avg_change = sum(group_changes) / len(group_changes) if group_changes else 0

        change_class = "color:#ef4444" if avg_change > 0 else "color:#3b82f6" if avg_change < 0 else "color:#9ca3af"
        change_arrow = "▲" if avg_change > 0 else "▼" if avg_change < 0 else "—"

        rows = ""
        for s in gdata["stocks"]:
            rows += f"""<tr>
<td><a href="https://m.stock.naver.com/domestic/stock/{s['code']}/total" target="_blank" style="color:#e2e8f0;text-decoration:none">{s['name']}</a></td>
<td style="text-align:right">{fmt_price(s['price'])}</td>
<td style="text-align:right">{fmt_mcap(s['mcap_eok'])}</td>
<td style="text-align:right">{fmt_change(s['change'], s['change_pct'])}</td>
</tr>"""

        group_cards_html += f"""
<div class="group-card" style="border-color:{color}">
  <div class="group-header">
    <div>
      <span class="rank-badge" style="background:{color}">{rank}</span>
      <span class="group-name">{gname}</span>
    </div>
    <div style="text-align:right">
      <div class="group-mcap">{fmt_mcap(mcap)}</div>
      <div style="{change_class};font-size:0.85rem">{change_arrow} 평균 {abs(avg_change):.2f}%</div>
    </div>
  </div>
  <div class="group-pct-bar">
    <div class="group-pct-fill" style="width:{pct_of_total:.1f}%;background:{color}"></div>
  </div>
  <div style="font-size:0.75rem;color:#9ca3af;margin-bottom:8px">전체 대비 {pct_of_total:.1f}%</div>
  <table class="stock-table">
    <thead><tr><th>종목</th><th style="text-align:right">현재가</th><th style="text-align:right">시총</th><th style="text-align:right">등락</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    # All stocks ranking table
    all_rows = ""
    for i, s in enumerate(all_stocks[:50], 1):
        # Find group
        group_name = ""
        group_color = "#9ca3af"
        for gn, gd in groups_data.items():
            for st in gd["stocks"]:
                if st["code"] == s["code"]:
                    group_name = gn
                    group_color = gd["color"]
                    break
        all_rows += f"""<tr>
<td>{i}</td>
<td><span style="color:{group_color};font-weight:600">[{group_name}]</span> <a href="https://m.stock.naver.com/domestic/stock/{s['code']}/total" target="_blank" style="color:#e2e8f0;text-decoration:none">{s['name']}</a></td>
<td style="text-align:right">{fmt_price(s['price'])}</td>
<td style="text-align:right;font-weight:600">{fmt_mcap(s['mcap_eok'])}</td>
<td style="text-align:right">{fmt_change(s['change'], s['change_pct'])}</td>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>5대그룹 시총 현황</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0a0e1a; color:#e2e8f0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; padding:16px; }}
.header {{ text-align:center; margin-bottom:24px; }}
.header h1 {{ font-size:1.6rem; margin-bottom:6px; background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent; }}
.header .meta {{ color:#9ca3af; font-size:0.85rem; }}
.kospi-badge {{ display:inline-block; background:#1e293b; padding:4px 12px; border-radius:20px; margin-top:6px; font-size:0.85rem; }}
.summary-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:24px; }}
.summary-card {{ background:#1e293b; border-radius:10px; padding:12px; text-align:center; border-left:3px solid; }}
.summary-card .label {{ font-size:0.75rem; color:#9ca3af; }}
.summary-card .value {{ font-size:1.1rem; font-weight:700; margin-top:2px; }}
.chart-container {{ background:#1e293b; border-radius:12px; padding:16px; margin-bottom:24px; max-width:800px; margin-left:auto; margin-right:auto; }}
.group-card {{ background:#1e293b; border-radius:12px; padding:16px; margin-bottom:16px; border-left:4px solid; }}
.group-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
.rank-badge {{ display:inline-block; width:28px; height:28px; border-radius:50%; text-align:center; line-height:28px; font-weight:700; font-size:0.85rem; color:#fff; margin-right:8px; }}
.group-name {{ font-size:1.2rem; font-weight:700; }}
.group-mcap {{ font-size:1.3rem; font-weight:700; }}
.group-pct-bar {{ height:6px; background:#0f172a; border-radius:3px; margin-bottom:4px; overflow:hidden; }}
.group-pct-fill {{ height:100%; border-radius:3px; transition:width 0.5s; }}
.stock-table {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
.stock-table th {{ text-align:left; color:#9ca3af; padding:6px 4px; border-bottom:1px solid #334155; font-weight:500; }}
.stock-table td {{ padding:5px 4px; border-bottom:1px solid #1a2332; }}
.stock-table tr:hover {{ background:#0f172a; }}
.section-title {{ font-size:1.2rem; font-weight:700; margin:24px 0 12px; padding-left:8px; border-left:3px solid #8b5cf6; }}
.all-table {{ width:100%; border-collapse:collapse; font-size:0.82rem; background:#1e293b; border-radius:12px; overflow:hidden; }}
.all-table th {{ text-align:left; color:#9ca3af; padding:8px 6px; border-bottom:1px solid #334155; background:#0f172a; }}
.all-table td {{ padding:6px; border-bottom:1px solid #1a2332; }}
.all-table tr:hover {{ background:#0f172a; }}
@media(max-width:600px) {{
  .summary-grid {{ grid-template-columns:repeat(2,1fr); }}
  .group-header {{ flex-direction:column; align-items:flex-start; gap:4px; }}
  .stock-table {{ font-size:0.75rem; }}
  .all-table {{ font-size:0.75rem; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>5대그룹 시가총액 현황</h1>
  <div class="meta">{now} 기준</div>
  <div class="kospi-badge">KOSPI {kospi_val} ({kospi_change} / {kospi_pct}%)</div>
</div>

<div class="summary-grid">
  <div class="summary-card" style="border-color:#6366f1">
    <div class="label">5대그룹 합계</div>
    <div class="value">{fmt_mcap(total_all)}</div>
  </div>
"""

    for gname, gdata in sorted_groups:
        html += f"""  <div class="summary-card" style="border-color:{gdata['color']}">
    <div class="label">{gname}</div>
    <div class="value" style="color:{gdata['color']}">{fmt_mcap(gdata['total_mcap'])}</div>
  </div>
"""

    html += f"""</div>

<div class="chart-container">
  <canvas id="mcapChart" height="200"></canvas>
</div>

{group_cards_html}

<div class="section-title">전체 계열사 시총 순위 (Top 50)</div>
<div style="overflow-x:auto">
<table class="all-table">
<thead><tr><th>#</th><th>종목</th><th style="text-align:right">현재가</th><th style="text-align:right">시총</th><th style="text-align:right">등락</th></tr></thead>
<tbody>{all_rows}</tbody>
</table>
</div>

<div style="text-align:center;color:#475569;font-size:0.75rem;margin-top:24px;padding-bottom:16px">
  OpenClaw 5대그룹 시총 대시보드 | 데이터: 네이버금융 | {now}
</div>

<script>
const ctx = document.getElementById('mcapChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: {chart_labels},
    datasets: [{{
      label: '시가총액 (조원)',
      data: {chart_data},
      backgroundColor: {chart_colors},
      borderColor: {chart_colors},
      borderWidth: 1,
      borderRadius: 6,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: ctx => ctx.parsed.x.toFixed(1) + '조원'
        }}
      }}
    }},
    scales: {{
      x: {{
        grid: {{ color: '#1e293b' }},
        ticks: {{ color: '#9ca3af', callback: v => v + '조' }}
      }},
      y: {{
        grid: {{ display: false }},
        ticks: {{ color: '#e2e8f0', font: {{ size: 14, weight: 'bold' }} }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html


def main():
    print("=" * 50)
    print("5대그룹 시총 대시보드 생성")
    print("=" * 50)

    kospi = fetch_kospi()
    print(f"KOSPI: {kospi['value']}")

    groups_data, all_stocks = collect_all()

    print("\n[HTML 생성 중...]")
    html = generate_html(groups_data, all_stocks, kospi)

    out_path = "/Users/geon/.openclaw/workspace/public/group-mcap/index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✓ 저장 완료: {out_path}")

    # Summary
    print("\n=== 그룹별 시총 요약 ===")
    sorted_groups = sorted(groups_data.items(), key=lambda x: x[1]["total_mcap"], reverse=True)
    for i, (gn, gd) in enumerate(sorted_groups, 1):
        print(f"  {i}. {gn}: {fmt_mcap(gd['total_mcap'])}")
    total = sum(g["total_mcap"] for _, g in sorted_groups)
    print(f"  합계: {fmt_mcap(total)}")


if __name__ == "__main__":
    main()
