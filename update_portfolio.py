import yfinance as yf
import pandas as pd
from datetime import datetime
import re
import json

# Read the portfolio data
df = pd.read_csv('/Users/geon/.openclaw/workspace/portfolio_full.csv')

# Comprehensive ticker mapping
ticker_map = {
    # Korean stocks
    '삼성전자': '005930.KS',
    '파마리서치': '028300.KS',
    '현대차3우B': '005387.KS',
    'DL이앤씨우': '002210.KS',
    '두산': '000150.KS',
    '삼성전자우': '005935.KS',
    'ESR켄달스퀘어리츠': '431980.KS',
    '네이버': '035420.KS',
    '현대차우': '005387.KS',  # Same as 현대차3우B
    '엘오티베큠': '307750.KS',
    '현대건설': '005440.KS',
    '세아베스틸지주': '003030.KS',
    'LG에너지솔루션': '373220.KS',
    '삼성SDI': '006400.KS',
    
    # Korean ETFs
    'TIGER 코리아AI전력기기TOP3+': '457180.KS',
    'TIGER 글로벌AI액티브': '375570.KS',
    'ARTY': '36430U.KS',
    'SOL 미국AI전력인프라': '363320.KS',
    'TIGER 미국테크TOP10 INDXX': '530067.KS',
    'TIGER 테슬라채권혼합Fn': '382340.KS',
    'KODEX 미국30년국채액티브(H)': '453250.KS',
    'KODEX 미국30년국채울트라(H)': '453260.KS',
    'KODEX 미국S&P500헬스케어': '453290.KS',
    'KODEX TRF3070': '453240.KS',
    'TIGER 코스피고배당': '051910.KS',
    'TIGER 미국초단기국채': '530358.KS',
    'TIGER 글로벌멀티에셋TIF': '530566.KS',
    'TIGER 미국달러단기채권': '530719.KS',
    'TIGER 글로벌AI사이버보안': '530566.KS',  # Check actual ticker
    'ACE 구글밸류체인액티브': '530343.KS',
    'TIME 글로벌우주테크&방산': '530657.KS',
    'HANARO 글로벌금채굴기업': '435310.KS',
    
    # Korean REITs
    '코람코라이프인프라리츠': '357250.KS',
    'SK리츠': '439200.KS',
    '신한서부티엔디리츠': '449950.KS',
    '이지스밸류플러스리츠': '330590.KS',
    
    # US stocks
    '샤오미': '1810.HK',
    'INTC': 'INTC',
    'NLR': 'NLR',
    'GRID ETF': 'GRID',
    'NVDA': 'NVDA',
    'HSAI': 'HSAI',
    'TSLA': 'TSLA',
    'AMD': 'AMD',
    'AMZN': 'AMZN',
    'LLY': 'LLY',
    'MSFT': 'MSFT',
    'GOOGL': 'GOOGL',
    'RTX': 'RTX',
    'PLTR': 'PLTR',
    
    # Crypto (using USD pairs)
    'BTC/KRW': 'BTC-USD',
    'ETH/KRW': 'ETH-USD',
    'SOL/KRW': 'SOL-USD',
    'LINK/USD': 'LINK-USD',
}

# Fetch current prices
print("Fetching current prices...")
prices = {}

for asset, ticker in ticker_map.items():
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPreviousClose') or info.get('previousClose')
        if current_price:
            prices[asset] = current_price
            print(f"✓ {asset}: {current_price}")
        else:
            print(f"✗ {asset}: No price found")
    except Exception as e:
        print(f"✗ {asset}: Error - {str(e)[:50]}")

print(f"\nTotal prices fetched: {len(prices)}")

# Save prices to JSON for reference
with open('/Users/geon/.openclaw/workspace/portfolio_prices.json', 'w') as f:
    json.dump(prices, f, indent=2)

print("Prices saved to portfolio_prices.json")