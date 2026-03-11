import json
from datetime import datetime

# Read the data
with open('/Users/geon/.openclaw/workspace/dashboard_data.json', 'r') as f:
    D = json.load(f)

# Generate HTML
html = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>모바일 포트폴리오 인사이트</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{margin:0;background:#0b1220;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
.wrap{{padding:14px;max-width:760px;margin:0 auto}}
.card{{background:#131c2f;border:1px solid #223052;border-radius:14px;padding:12px;margin-bottom:10px}}
.kpis{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.k{{font-size:12px;color:#93a4c3}}
.v{{font-weight:700;font-size:18px}}
.sub{{color:#94a3b8;font-size:12px}}
.table{{width:100%;font-size:12px;border-collapse:collapse}}
.table td,.table th{{padding:6px;border-bottom:1px solid #24345a;text-align:right}}
.table td:first-child,.table th:first-child{{text-align:left}}
.good{{color:#34d399}}
.bad{{color:#f87171}}
.btns button{{margin:4px 4px 0 0;padding:4px 8px;border-radius:8px;border:1px solid #3b4d77;background:#1b2742;color:#dbe7ff}}
ul{{margin:6px 0 0 16px;padding:0}}
li{{margin:4px 0}}
.alert{{border:1px solid #f59e0b;background:#1b2a1a}}
.action{{border:1px solid #34d399;background:#1a2a22}}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h2 style="margin:0">📱 포트폴리오 현황</h2>
<div class="sub" id="up"></div>
<div class="kpis" style="margin-top:8px">
<div><div class="k">총 자산</div><div class="v" id="total"></div></div>
<div><div class="k">보유 종목수</div><div class="v" id="count"></div></div>
</div>
</div>
<div class="card alert">
<h3>🚨 알림</h3>
<ul id="alerts"></ul>
</div>
<div class="card action">
<h3>⚡ 권장 액션</h3>
<ul id="actions"></ul>
</div>
<div class="card">
<h3>🏆 보유 종목 리스트 (손익액 높은 순)</h3>
<div style="overflow:auto;max-height:420px"><table class="table" id="tbl"></table></div>
</div>
<div class="card">
<h3>📊 섹터 비중(%)</h3>
<canvas id="pie" height="200"></canvas>
</div>
</div>
<script>
const D = {json.dumps(D, ensure_ascii=False, indent=2)};
const fmt=n=>new Intl.NumberFormat('ko-KR').format(n);
document.getElementById('up').innerText='업데이트: '+D.updated;
document.getElementById('total').innerText='₩'+fmt(D.total);
document.getElementById('count').innerText=D.count+'개';

const alertsEl = document.getElementById('alerts');
if(D.alerts && D.alerts.length){{
    D.alerts.forEach(t=>{{
        const li=document.createElement('li');
        li.textContent=t;
        alertsEl.appendChild(li);
    }});
}} else {{
    alertsEl.innerHTML='<li style="color:#94a3b8">현재 알림 없음</li>';
}}

const actionsEl = document.getElementById('actions');
if(D.actions && D.actions.length){{
    D.actions.slice(0, 10).forEach(t=>{{
        const li=document.createElement('li');
        li.textContent=t;
        actionsEl.appendChild(li);
    }});
}} else {{
    actionsEl.innerHTML='<li style="color:#94a3b8">현재 권장 액션 없음</li>';
}}

document.getElementById('tbl').innerHTML='<tr><th>종목</th><th>매수가</th><th>현재가</th><th>손익%</th></tr>'+D.items.map(r=>`<tr><td>${{r.asset}}</td><td>${{r.buy}}</td><td>${{r.now}}</td><td class="${{r.pnlPct>=0?'good':'bad'}}">${{r.pnlPct>=0?'+':''}}${{r.pnlPct.toFixed(2)}}%</td></tr>`).join('');

new Chart(document.getElementById('pie'),{{
    type:'doughnut',
    data:{{
        labels:D.cats.map(x=>`${{x.name}} (${{x.pct}}%)`),
        datasets:[{{data:D.cats.map(x=>x.value)}}]
    }},
    options:{{plugins:{{legend:{{display:false}}}}}}
}});
</script>
</body>
</html>'''

with open('/Users/geon/.openclaw/workspace/portfolio_mobile_dashboard.html', 'w') as f:
    f.write(html)

print("Mobile dashboard updated!")