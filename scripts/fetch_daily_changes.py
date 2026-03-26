#!/usr/bin/env python3
"""
Fetch daily price changes for all portfolio stocks → public/data/daily_changes.json
Used by invest.html heatmap for real-time coloring.
"""
import requests
import json
import os
from datetime import datetime

STOCK_MAP = {
    '삼성전자': '005930', '삼성전자우': '005935', '파마리서치': '214450',
    '현대차3우B': '005387', '현대차우': '005385', 'DL이앤씨우': '375500',
    '두산': '000150', '네이버': '035420', '삼성SDI': '006400',
    'LG에너지솔루션': '373220', '엘오티베큠': '083310', '현대건설': '000720',
    '세아베스틸지주': '001430', '코람코라이프인프라리츠': '357120',
    'SK리츠': '395400', '신한서부티엔디리츠': '404990',
    '이지스밸류플러스리츠': '334890', 'ESR켄달스퀘어리츠': '365550',
    'KODEX 증권': '102970', 'TIGER 코스피고배당': '161510',
    'TIGER 미국테크TOP10 INDXX': '381170', 'KODEX TRF3070': '294400',
}

US_TICKER_MAP = {
    'INTC': 'INTC', 'NVDA': 'NVDA', 'TSLA': 'TSLA', 'AMD': 'AMD',
    'AMZN': 'AMZN', 'LLY': 'LLY', 'MSFT': 'MSFT', 'GOOGL': 'GOOGL',
    'RTX': 'RTX', 'PLTR': 'PLTR', 'ARTY': 'ARTY', 'HSAI': 'HSAI',
    'NLR': 'NLR', 'GRID ETF': 'GRID',
}

CRYPTO_MAP = {
    'BTC/KRW': 'bitcoin', 'ETH/KRW': 'ethereum', 'SOL/KRW': 'solana', 'LINK/USD': 'chainlink',
}

def fetch_naver_kr(name, code):
    """Fetch KR stock daily change from Naver"""
    try:
        url = f"https://m.stock.naver.com/api/stock/{code}/basic"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://m.stock.naver.com/'}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200:
            return None
        d = r.json()
        price = int(d.get('closePrice', '0').replace(',', ''))
        pct = float(d.get('fluctuationsRatio', '0'))
        chg = int(d.get('compareToPreviousClosePrice', '0').replace(',', ''))
        return {'name': name, 'price': price, 'pct': pct, 'chg': chg, 'src': 'naver'}
    except Exception as e:
        print(f"[KR] {name} ({code}): {e}")
        return None

def fetch_us_stock(name, ticker):
    """Fetch US stock via Yahoo Finance v8"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        meta = d['chart']['result'][0]['meta']
        cur = meta.get('regularMarketPrice', 0)
        prev = meta.get('chartPreviousClose', meta.get('previousClose', cur))
        if prev <= 0:
            return None
        pct = (cur - prev) / prev * 100
        return {'name': name, 'price': round(cur, 2), 'pct': round(pct, 2), 'chg': round(cur - prev, 2), 'src': 'yahoo'}
    except Exception as e:
        print(f"[US] {name} ({ticker}): {e}")
        return None

def fetch_crypto(name, coin_id):
    """Fetch crypto via CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=krw&include_24hr_change=true"
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        info = d.get(coin_id, {})
        price = info.get('krw', 0)
        pct = info.get('krw_24h_change', 0)
        return {'name': name, 'price': price, 'pct': round(pct, 2), 'chg': 0, 'src': 'coingecko'}
    except Exception as e:
        print(f"[Crypto] {name}: {e}")
        return None

def fetch_xiaomi():
    """Fetch Xiaomi (HK) via Yahoo"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/1810.HK?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        meta = d['chart']['result'][0]['meta']
        cur = meta.get('regularMarketPrice', 0)
        prev = meta.get('chartPreviousClose', cur)
        if prev <= 0:
            return None
        pct = (cur - prev) / prev * 100
        return {'name': '샤오미', 'price': round(cur, 2), 'pct': round(pct, 2), 'chg': round(cur - prev, 2), 'src': 'yahoo'}
    except:
        return None

def main():
    results = {}

    # Korean stocks
    print("Fetching KR stocks...")
    for name, code in STOCK_MAP.items():
        d = fetch_naver_kr(name, code)
        if d:
            results[name] = d
            print(f"  {name}: {d['pct']:+.2f}%")

    # US stocks
    print("Fetching US stocks...")
    for name, ticker in US_TICKER_MAP.items():
        d = fetch_us_stock(name, ticker)
        if d:
            results[name] = d
            print(f"  {name}: {d['pct']:+.2f}%")

    # Crypto
    print("Fetching Crypto...")
    for name, coin_id in CRYPTO_MAP.items():
        d = fetch_crypto(name, coin_id)
        if d:
            results[name] = d
            print(f"  {name}: {d['pct']:+.2f}%")

    # Xiaomi
    d = fetch_xiaomi()
    if d:
        results['샤오미'] = d
        print(f"  샤오미: {d['pct']:+.2f}%")

    # Save
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'public', 'data')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'daily_changes.json')

    output = {
        'timestamp': datetime.now().isoformat(),
        'count': len(results),
        'stocks': results
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(results)} stocks to {out_path}")

if __name__ == '__main__':
    main()
