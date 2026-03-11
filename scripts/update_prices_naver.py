#!/usr/bin/env python3
"""
Naver Finance Real-time Price Updater
Fetches live stock prices from Naver Finance and updates portfolio
"""
import requests
import pandas as pd
import json
from datetime import datetime
import os

def get_naver_price(stock_code):
    """Fetch real-time price from Naver Finance"""
    try:
        url = f"https://api.finance.naver.com/service/itemSummary.nhn?itemcode={stock_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'current_price': int(data.get('now', 0)),
                'change': int(data.get('change', 0)),
                'change_rate': float(data.get('changeRate', 0)),
                'open': int(data.get('open', 0)),
                'high': int(data.get('high', 0)),
                'low': int(data.get('low', 0)),
                'volume': int(data.get('accumulVolume', 0))
            }
        return None
    except Exception as e:
        print(f"Error fetching {stock_code}: {e}")
        return None

def extract_stock_code(asset_name):
    """Extract stock code from asset name or mapping"""
    # Manual mapping for common stocks
    stock_mapping = {
        '삼성전자': '005930',
        '삼성전자우': '005935',
        '현대차3우B': '005387',
        '현대차우': '005387',
        '파마리서치': '214450',
        'DL이앤씨우': '002210',
        '두산': '000150',
        '네이버': '035420',
        '삼성SDI': '006400',
        'LG에너지솔루션': '373220',
        '엘오티베큠': '307750',
        '현대건설': '005440',
        '세아베스틸지주': '003030',
        '코람코라이프인프라리츠': '357250',
        'SK리츠': '439200',
        '신한서부티엔디리츠': '449950',
        '이지스밸류플러스리츠': '330590',
        'ESR켄달스퀘어리츠': '431980',
        '기아': '000270',
        'LG이노텍': '011070',
        '삼성SDI': '006400',
        'LG화학': '051910',
        '포스코퓨처엠': '003670',
        '한화솔루션': '009830',
        '피에스케이홀딩스': '031980',
        '한솔케미칼': '014680',
        '켐트로닉스': '089010',
        '한미약품': '128940',
        '유한양행': '000100',
        '씨젠': '096530',
        '엔씨소프트': '036570',
        '웹젠': '069080',
        '대한항공': '003490',
        'LG디스플레이': '034220',
        'KT&G': '033780',
        '한국콜마': '161890',
        '아모레퍼시픽': '090430',
        '한화손핵보험': '000370',
        '한섬': '020000',
        '이수페타시스': '007660',
        '파트론': '091700',
        '롯데렌탈': '089860',
    }
    
    # Try to get from mapping
    if asset_name in stock_mapping:
        return stock_mapping[asset_name]
    
    return None

def update_portfolio_prices():
    """Update all stock prices in portfolio"""
    
    # Read current portfolio
    portfolio_path = '/Users/geon/.openclaw/workspace/portfolio_full.csv'
    df = pd.read_csv(portfolio_path)
    
    updated_count = 0
    errors = []
    
    print(f"🔄 Updating portfolio prices... {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📊 Total stocks: {len(df)}")
    print("-" * 60)
    
    for idx, row in df.iterrows():
        asset = row['자산']
        
        # Skip non-Korean stocks, ETFs, crypto, cash
        if any(skip in asset for skip in ['USD', 'BTC', 'ETH', 'SOL', 'LINK', 'TIGER', 'KODEX', 'KOSEF', 'ACE', 'TIME', 'HANARO', 'KRW']):
            continue
            
        # Skip US stocks
        if asset in ['NVDA', 'INTC', 'AMD', 'TSLA', 'AMZN', 'MSFT', 'GOOGL', 'LLY', 'RTX', 'PLTR', 'NLR', 'GRID', 'HSAI', 'ARTY', '샤오미']:
            continue
        
        stock_code = extract_stock_code(asset)
        
        if stock_code:
            price_data = get_naver_price(stock_code)
            
            if price_data:
                old_price = row['현재가']
                new_price = price_data['current_price']
                
                # Update price
                df.at[idx, '현재가'] = f"₩{new_price:,}"
                
                # Recalculate asset value
                quantity = row['수량']
                new_value = quantity * new_price
                df.at[idx, '자산가치'] = f"₩{new_value:,.0f}"
                
                # Recalculate profit/loss
                purchase_price_str = str(row['매수가']).replace('₩', '').replace(',', '')
                try:
                    purchase_price = float(purchase_price_str)
                    if purchase_price > 0:
                        profit = (new_price - purchase_price) * quantity
                        profit_pct = ((new_price - purchase_price) / purchase_price) * 100
                        
                        if profit >= 0:
                            df.at[idx, '손익'] = f"+₩{profit:,.0f} (+{profit_pct:.2f}%)"
                        else:
                            df.at[idx, '손익'] = f"₩{profit:,.0f} ({profit_pct:.2f}%)"
                except:
                    pass
                
                updated_count += 1
                
                # Show significant changes
                if abs(price_data['change_rate']) > 5:
                    print(f"📈 {asset}: ₩{new_price:,} ({price_data['change_rate']:+.2f}%)")
            else:
                errors.append(asset)
        else:
            errors.append(asset)
    
    # Save updated portfolio
    df.to_csv(portfolio_path, index=False)
    
    print("-" * 60)
    print(f"✅ Updated: {updated_count} stocks")
    if errors:
        print(f"⚠️  Failed: {len(errors)} stocks - {', '.join(errors[:5])}")
    print(f"💾 Saved to: {portfolio_path}")
    
    return updated_count, errors

if __name__ == "__main__":
    update_portfolio_prices()
