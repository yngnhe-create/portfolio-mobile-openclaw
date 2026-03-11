import pandas as pd
import json
from datetime import datetime

# Read portfolio
df = pd.read_csv('/Users/geon/.openclaw/workspace/portfolio_full.csv')

# Parse values
def parse_value(val):
    if pd.isna(val) or val == '-':
        return 0
    val = str(val).replace('₩', '').replace('$', '').replace(',', '').replace('+', '').strip()
    try:
        return float(val)
    except:
        return 0

# Parse PnL
def parse_pnl(pnl_str):
    if pd.isna(pnl_str) or pnl_str == '-':
        return 0, 0
    pnl_str = str(pnl_str)
    # Extract amount
    if '₩' in pnl_str:
        amt = pnl_str.split('₩')[1].split('(')[0].replace(',', '').strip()
        try:
            amount = float(amt)
        except:
            amount = 0
    elif '$' in pnl_str:
        amt = pnl_str.split('$')[1].split('(')[0].replace(',', '').strip()
        try:
            amount = float(amt)
        except:
            amount = 0
    else:
        amount = 0
    
    # Extract percentage
    if '(' in pnl_str and ')' in pnl_str:
        pct_str = pnl_str.split('(')[1].split(')')[0].replace('%', '').replace('+', '')
        try:
            pct = float(pct_str)
        except:
            pct = 0
    else:
        pct = 0
    
    return amount, pct

# Calculate detailed data
stocks = []
for _, row in df.iterrows():
    asset = row['자산']
    sector = row['분류']
    qty = row['수량']
    
    # Parse asset value
    val_str = str(row['자산가치'])
    if '₩' in val_str:
        value = parse_value(val_str)
        currency = 'KRW'
    elif '$' in val_str:
        value = parse_value(val_str) * 1450  # Convert to KRW
        currency = 'USD'
    else:
        value = 0
        currency = 'KRW'
    
    # Parse PnL
    pnl_amt, pnl_pct = parse_pnl(row['손익'])
    
    stocks.append({
        'asset': asset,
        'sector': sector,
        'qty': qty,
        'value': value,
        'pnl_amt': pnl_amt,
        'pnl_pct': pnl_pct,
        'current_price': str(row['현재가']),
        'purchase_price': str(row['매수가'])
    })

# Sort by PnL amount
stocks_sorted = sorted(stocks, key=lambda x: x['pnl_amt'], reverse=True)

print(f"Total stocks: {len(stocks_sorted)}")
print(f"Top 5 by PnL:")
for i, s in enumerate(stocks_sorted[:5]):
    print(f"{i+1}. {s['asset']}: ₩{s['pnl_amt']:,.0f} ({s['pnl_pct']:+.1f}%)")

# Sector allocation
total_value = sum(s['value'] for s in stocks)
sector_alloc = {}
for s in stocks:
    if s['sector'] not in sector_alloc:
        sector_alloc[s['sector']] = 0
    sector_alloc[s['sector']] += s['value']

sector_pct = {k: (v/total_value*100) for k, v in sector_alloc.items()}
sector_sorted = sorted(sector_pct.items(), key=lambda x: x[1], reverse=True)

print(f"\nSector allocation:")
for sector, pct in sector_sorted:
    print(f"{sector}: {pct:.1f}%")

# Save data for HTML
with open('/Users/geon/.openclaw/workspace/dashboard_data.json', 'w') as f:
    json.dump({
        'stocks': stocks_sorted,
        'sectors': sector_sorted,
        'total_value': total_value,
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M')
    }, f, indent=2, default=str)

print("\nData saved to dashboard_data.json")
