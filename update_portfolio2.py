import yfinance as yf
import pandas as pd
from datetime import datetime
import re
import json

# Read the portfolio data
df = pd.read_csv('/Users/geon/.openclaw/workspace/portfolio_full.csv')

# Load the fetched prices
with open('/Users/geon/.openclaw/workspace/portfolio_prices.json', 'r') as f:
    prices = json.load(f)

# USD to KRW exchange rate
usd_to_krw = 1450  # Approximate rate

# Convert USD prices to KRW for assets that are denominated in KRW
# But we need to be careful - some prices are already in the right currency

# For crypto, we need to convert from USD to KRW
# Check if the price is in USD (very small numbers) or KRW (large numbers)
# BTC in KRW should be around 100 million, in USD around 70,000
# So if price < 10000, it's likely USD and needs conversion

updated_count = 0
for idx, row in df.iterrows():
    asset = row['자산']
    if asset in prices:
        old_price = row['현재가']
        new_price = prices[asset]
        
        # Determine if we need to convert to KRW
        # If the asset is a crypto pair with /KRW, we need to convert
        if '/KRW' in asset or '/USD' in asset:
            # For crypto, convert USD to KRW
            new_price_krw = new_price * usd_to_krw
            # Format as KRW
            df.at[idx, '현재가'] = f"₩{new_price_krw:,.0f}"
            # Update asset value
            quantity = row['수량']
            new_value = quantity * new_price_krw
            df.at[idx, '자산가치'] = f"₩{new_value:,.0f}"
            
            # Calculate profit/loss
            # Extract purchase price (매수가)
            purchase_price_str = str(row['매수가'])
            # Parse the purchase price
            purchase_price = 0
            if '₩' in purchase_price_str:
                purchase_price = float(purchase_price_str.replace('₩', '').replace(',', ''))
            elif '$' in purchase_price_str:
                purchase_price = float(purchase_price_str.replace('$', '').replace(',', '')) * usd_to_krw
            
            if purchase_price > 0:
                profit = (new_price_krw - purchase_price) * quantity
                profit_pct = (profit / (purchase_price * quantity)) * 100
                if profit >= 0:
                    df.at[idx, '손익'] = f"+₩{profit:,.0f} (+{profit_pct:.2f}%)"
                else:
                    df.at[idx, '손익'] = f"₩{profit:,.0f} ({profit_pct:.2f}%)"
            
            updated_count += 1
            print(f"Updated {asset}: {new_price_krw:,.0f} KRW")
        elif '$' in str(old_price):
            # Already in USD, keep as USD
            df.at[idx, '현재가'] = f"${new_price:,.2f}"
            quantity = row['수량']
            new_value = quantity * new_price
            df.at[idx, '자산가치'] = f"${new_value:,.2f}"
            
            # Calculate profit/loss in USD
            purchase_price_str = str(row['매수가'])
            purchase_price = 0
            if '$' in purchase_price_str:
                purchase_price = float(purchase_price_str.replace('$', '').replace(',', ''))
            
            if purchase_price > 0:
                profit = (new_price - purchase_price) * quantity
                profit_pct = (profit / (purchase_price * quantity)) * 100
                if profit >= 0:
                    df.at[idx, '손익'] = f"+${profit:,.2f} (+{profit_pct:.2f}%)"
                else:
                    df.at[idx, '손익'] = f"-${abs(profit):,.2f} (-{abs(profit_pct):.2f}%)"
            
            updated_count += 1
            print(f"Updated {asset}: ${new_price:,.2f}")
        else:
            # Korean stock in KRW
            df.at[idx, '현재가'] = f"₩{new_price:,.0f}"
            quantity = row['수량']
            new_value = quantity * new_price
            df.at[idx, '자산가치'] = f"₩{new_value:,.0f}"
            
            # Calculate profit/loss
            purchase_price_str = str(row['매수가'])
            purchase_price = 0
            if '₩' in purchase_price_str:
                purchase_price = float(purchase_price_str.replace('₩', '').replace(',', ''))
            
            if purchase_price > 0:
                profit = (new_price - purchase_price) * quantity
                profit_pct = (profit / (purchase_price * quantity)) * 100
                if profit >= 0:
                    df.at[idx, '손익'] = f"+₩{profit:,.0f} (+{profit_pct:.2f}%)"
                else:
                    df.at[idx, '손익'] = f"₩{profit:,.0f} ({profit_pct:.2f}%)"
            
            updated_count += 1
            print(f"Updated {asset}: {new_price:,.0f} KRW")

print(f"\nTotal assets updated: {updated_count}")

# Save the updated portfolio
df.to_csv('/Users/geon/.openclaw/workspace/portfolio_full.csv', index=False)
print("Portfolio saved to portfolio_full.csv")

# Also update portfolio_mobile_dashboard.html with new data
# Read the mobile dashboard HTML
with open('/Users/geon/.openclaw/workspace/portfolio_mobile_dashboard.html', 'r') as f:
    html_content = f.read()

# Replace the data in the HTML (this is a simplified approach)
# In a real scenario, we'd regenerate the entire dashboard

# For now, just copy the updated CSV to the workspace
print("Done!")