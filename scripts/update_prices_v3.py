#!/usr/bin/env python3
"""
Portfolio Price Updater v3 - Using KIS API for Korean stocks
Replaces pykrx with KIS API for more reliable Korean stock data
"""
import pandas as pd
import yfinance as yf
import requests
import os
import json
from datetime import datetime, timedelta

# Load environment variables
env_path = os.path.expanduser('~/.openclaw/.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

KIS_APP_KEY = os.environ.get('KIS_APP_KEY')
KIS_APP_SECRET = os.environ.get('KIS_APP_SECRET')
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"

# Stock code mapping
KOREAN_STOCKS = {
    '삼성전자': '005930',
    '삼성전자우': '005935',
    'SK하이닉스': '000660',
    '현대차': '005380',
    '현대차우': '005385',
    '현대차3우B': '005389',
    '기아': '000270',
    '네이버': '035420',
    '카카오': '035720',
    'LG화학': '051910',
    '삼성SDI': '006400',
    'LG에너지솔루션': '373220',
    '두산': '000150',
    '파마리서치': '214450',
    '코람코라이프인프라리츠': '357120',
    '피에스케이홀딩스': '319660',
    '포스코퓨처엠': '003670',
    '한화솔루션': '009830',
    '엔씨소프트': '036570',
    '디앤씨미디어': '086960',
    'SK텔레콤': '017670',
    'LG이노텍': '011070',
    '대한항공': '003490',
    '엘오티베큠': '089590',
    '현대건설': '000720',
    '세아베스틸지주': '001430',
    '코람코리츠': '356890',
    'SK리츠': '350730',
    '이지스밸류플러스리츠': '338220',
    '궐련형전환주': '042670',
    '한화에어로스페이스': '012450',
    'KT&G': '033780',
    '씨젠': '096530',
    '삼성바이오로직스': '207940',
    '카카오뱅크': '323410',
    '크래프톤': '259960',
    '현대모비스': '012330',
    '셀트리온': '068270',
    'POSCO홀딩스': '005490',
    'KB금융': '105560',
    '신한지주': '055550',
    '하나금융지주': '086790',
    '우리금융지주': '316140',
    '기업은행': '024110',
}

def get_kis_access_token():
    """Get KIS API access token"""
    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        data = response.json()
        return data.get("access_token")
    except Exception as e:
        print(f"  Token error: {e}")
        return None

def get_korean_price_kis(stock_code, access_token):
    """Fetch Korean stock price using KIS API"""
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if data.get("rt_cd") == "0":
            output = data.get("output", {})
            return {
                'price': int(output.get("stck_prpr", 0)),
                'change': int(output.get("prdy_vrss", 0)),
                'change_rate': float(output.get("prdy_ctrt", 0))
            }
        return None
    except Exception as e:
        print(f"  KIS error: {e}")
        return None

def get_us_stock_price(ticker):
    """Fetch US stock price using yfinance"""
    try:
        stock_data = yf.Ticker(ticker)
        info = stock_data.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        if current_price:
            return {'price': float(current_price)}
        return None
    except Exception as e:
        print(f"  yfinance error: {e}")
        return None

def get_crypto_price(symbol):
    """Fetch crypto price using yfinance"""
    try:
        crypto_map = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD',
            'SOL': 'SOL-USD',
            'LINK': 'LINK-USD'
        }
        
        yf_symbol = crypto_map.get(symbol, f'{symbol}-USD')
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if price:
            # Convert to KRW for Korean cryptos
            if symbol in ['BTC', 'ETH', 'SOL']:
                usd_krw = get_usd_krw_rate()
                if usd_krw:
                    return {'price': float(price) * usd_krw, 'currency': 'KRW'}
            return {'price': float(price), 'currency': 'USD'}
        return None
    except Exception as e:
        print(f"  crypto error: {e}")
        return None

def get_usd_krw_rate():
    """Get USD/KRW exchange rate"""
    try:
        ticker = yf.Ticker("KRW=X")
        info = ticker.info
        rate = info.get('currentPrice') or info.get('regularMarketPrice')
        return float(rate) if rate else 1300.0
    except:
        return 1300.0

def update_portfolio():
    """Update portfolio prices"""
    print("=" * 60)
    print("🚀 Portfolio Price Update - KIS API Edition")
    print("=" * 60)
    print()
    
    # Get KIS token once for all Korean stocks
    print("🔑 Getting KIS access token...")
    access_token = get_kis_access_token()
    if access_token:
        print("✅ KIS token obtained")
    else:
        print("⚠️  KIS token failed, will skip Korean stocks")
    print()
    
    # Load portfolio
    portfolio_path = os.path.expanduser('~/.openclaw/workspace/portfolio_full.csv')
    if not os.path.exists(portfolio_path):
        print(f"❌ Portfolio file not found: {portfolio_path}")
        return
    
    df = pd.read_csv(portfolio_path)
    print(f"📊 Loaded {len(df)} assets from portfolio")
    print(f"📋 Columns: {list(df.columns)}")
    print()
    
    updated = 0
    failed = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        name = row['자산']
        asset_type = row.get('분류', 'Stock')
        
        print(f"[{idx+1}/{len(df)}] {name}...", end=' ')
        
        result = None
        
        # Determine asset type from name
        is_korean = name in KOREAN_STOCKS
        is_us = any(x in str(name).upper() for x in ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'AMD', 'NLR', 'LLY', 'RTX', 'PLTR', 'HSAI'])
        is_crypto = any(x in str(name).upper() for x in ['BTC', 'ETH', 'SOL', 'LINK'])
        
        # Korean stocks - KIS API
        if is_korean and access_token:
            stock_code = KOREAN_STOCKS[name]
            result = get_korean_price_kis(stock_code, access_token)
            if result:
                df.at[idx, '현재가'] = result['price']
                print(f"✅ ₩{result['price']:,}")
                updated += 1
            else:
                print("❌ Failed")
                failed += 1
        
        # US stocks - yfinance
        elif is_us:
            # Extract ticker from name or use mapping
            ticker_map = {
                '엔비디아': 'NVDA', '티슬라': 'TSLA', '애플': 'AAPL', '마이크로소프트': 'MSFT',
                '아마존': 'AMZN', '구글': 'GOOGL', 'AMD': 'AMD', 'NLR': 'NLR',
                '릴리': 'LLY', 'RTX': 'RTX', '팔란티어': 'PLTR', '허사이': 'HSAI'
            }
            ticker = ticker_map.get(name, name)
            result = get_us_stock_price(ticker)
            if result:
                df.at[idx, '현재가'] = f"${result['price']:.2f}"
                print(f"✅ ${result['price']:.2f}")
                updated += 1
            else:
                print("❌ Failed")
                failed += 1
        
        # Crypto
        elif is_crypto:
            crypto_symbol = None
            for c in ['BTC', 'ETH', 'SOL', 'LINK']:
                if c in str(name).upper():
                    crypto_symbol = c
                    break
            result = get_crypto_price(crypto_symbol) if crypto_symbol else None
            if result:
                if result.get('currency') == 'KRW':
                    df.at[idx, '현재가'] = f"₩{result['price']:,.0f}"
                else:
                    df.at[idx, '현재가'] = f"${result['price']:.2f}"
                print(f"✅ {df.at[idx, '현재가']}")
                updated += 1
            else:
                print("❌ Failed")
                failed += 1
        
        # ETFs and others
        elif 'ETF' in str(asset_type) or any(x in str(name) for x in ['TIGER', 'KODEX', 'ACE', 'RISE']):
            print("⏭️  ETF - skipped")
            skipped += 1
        
        # Cash
        elif '현금' in str(name) or asset_type == '현금':
            print("💵 Cash - skipped")
            skipped += 1
        
        else:
            print("⏭️  Skipped")
            skipped += 1
    
    print()
    print("=" * 60)
    print(f"✅ Updated: {updated} | ❌ Failed: {failed} | ⏭️ Skipped: {skipped}")
    print("=" * 60)
    
    # Save updated portfolio
    df.to_csv(portfolio_path, index=False)
    print(f"\n💾 Saved to: {portfolio_path}")

if __name__ == "__main__":
    update_portfolio()