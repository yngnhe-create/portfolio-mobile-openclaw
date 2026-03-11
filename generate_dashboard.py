import pandas as pd
from datetime import datetime

# Read the updated portfolio data
df = pd.read_csv('/Users/geon/.openclaw/workspace/portfolio_full.csv')

# Parse value from string
def parse_value(val):
    if pd.isna(val):
        return 0
    val = str(val).replace('₩', '').replace('$', '').replace(',', '').replace('+', '').strip()
    try:
        return float(val)
    except:
        return 0

# Parse PnL amount from 손익 string like "+₩77,433,243 (+221.68%)" or "₩-6,540,408 (-12.93%)"
def parse_pnl_amount(val):
    if pd.isna(val):
        return 0
    val = str(val).strip()
    # Check if negative from the string
    is_negative = '-₩' in val or '-$' in val or '(-' in val
    # Extract amount before the parenthesis
    if '(' in val:
        amount_str = val.split('(')[0]
        # Remove currency symbols and commas
        amount_str = amount_str.replace('₩', '').replace('$', '').replace(',', '').replace('+', '').replace('-', '').strip()
        try:
            result = float(amount_str)
            return -result if is_negative else result
        except:
            return 0
    return 0

# Calculate totals
df['가치_원화'] = df['자산가치'].apply(lambda x: parse_value(x))
df['가치_USD'] = df['자산가치'].apply(lambda x: parse_value(x) if '$' in str(x) else 0)

usd_to_krw = 1450
total_krw = df['가치_원화'].sum() + (df['가치_USD'].sum() * usd_to_krw)

# Calculate category allocation
category_value = df.groupby('분류')['가치_원화'].sum().reset_index()
category_value = category_value.sort_values('가치_원화', ascending=False)

cats = []
for _, row in category_value.iterrows():
    pct = (row['가치_원화'] / total_krw) * 100
    cats.append({
        'name': row['분류'],
        'value': int(row['가치_원화']),
        'pct': round(pct, 2)
    })

# Calculate sub-sector allocation (simplified)
subs = []
# Map categories to sub-sectors
sub_map = {
    '첨단 기술': ['반도체', 'AI 전력', '소프트웨어', '사이버보안'],
    '경기 소비재': ['자동차', '가전', '자율주행/EV'],
    'ETF': ['고배당', '채권/국채'],
    '가상자산': ['디지털/암호화자산'],
    '헬스케어': ['헬스케어/의료'],
    '부동산': ['리츠'],
    '금융': ['산업재/지주사'],
    'IT': ['인터넷/플랫폼'],
    '현금': ['예수금'],
    '기타': ['에너지'],
    '산업재': ['건설/엔지니어링', '산업재/지주사'],
    '유틸리티': ['에너지']
}

for cat in cats:
    category = cat['name']
    if category in sub_map:
        for sub in sub_map[category]:
            subs.append({
                'name': sub,
                'value': int(cat['value'] / len(sub_map[category])),
                'pct': round(cat['pct'] / len(sub_map[category]), 2)
            })

# Calculate items (sorted by PnL)
items = []
for _, row in df.iterrows():
    asset = row['자산']
    buy = str(row['매수가'])
    now = str(row['현재가'])
    pnl_amt = parse_pnl_amount(row['손익'])
    # Parse PnL percentage from string
    pnl_str = str(row['손익'])
    pnl_pct = 0
    if '(' in pnl_str and ')' in pnl_str:
        try:
            pnl_pct = float(pnl_str.split('(')[1].replace('%)', '').replace('%', ''))
        except:
            pnl_pct = 0
    
    items.append({
        'asset': asset,
        'buy': buy,
        'now': now,
        'pnlAmt': int(pnl_amt),
        'pnlPct': round(pnl_pct, 2)
    })

# Sort by PnL amount
items = sorted(items, key=lambda x: x['pnlAmt'], reverse=True)

# Generate alerts and actions
alerts = []
actions = []

for item in items:
    if item['pnlPct'] < -30:
        alerts.append(f"손실 경고: {item['asset']} {item['pnlPct']:.1f}%")
        actions.append(f"⚠️ {item['asset']} 손실 {item['pnlPct']:.0f}% 도달. 손절 또는 분할 축소 검토")
    elif item['pnlPct'] < -15:
        actions.append(f"🔸 {item['asset']} 손실 {item['pnlPct']:.0f}% 접근. 관찰 필요")
    elif item['pnlPct'] > 30:
        actions.append(f"💰 {item['asset']} 수익 {item['pnlPct']:.0f}% 달성. 10~20% 분할 익절 검토")

# Generate risk metrics
risk = {
    'hhi': round(sum([c['pct']**2 for c in cats]), 1),
    'top5': round(sum([c['pct'] for c in cats[:5]]), 2),
    'top10': round(sum([c['pct'] for c in cats[:10]]), 2),
    'volAnn': 0.0,
    'var95': 11.13,
    'mdd': 0.0
}

# Output the data
print(f"Total: {total_krw}")
print(f"Count: {len(df)}")
print(f"Categories: {len(cats)}")
print(f"Items: {len(items)}")
print(f"Alerts: {len(alerts)}")
print(f"Actions: {len(actions)}")

# Save as JSON for use in HTML generation
import json
data = {
    'updated': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
    'total': int(total_krw),
    'count': len(df),
    'cats': cats,
    'subs': subs,
    'items': items,
    'risk': risk,
    'alerts': alerts,
    'actions': actions
}

with open('/Users/geon/.openclaw/workspace/dashboard_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Data saved to dashboard_data.json")
