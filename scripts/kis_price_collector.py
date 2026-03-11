#!/usr/bin/env python3
"""
KIS (Korea Investment & Securities) Open API Integration
실시간 주가 조회 및 데이터베이스 저장

Required:
- KIS 개발자 계정 (https://apiportal.koreainvestment.com/)
- APP_KEY, APP_SECRET
- 계좌번호 (CANO)
"""
import os
import json
import sqlite3
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KISPriceCollector:
    """KIS API를 사용한 주가 수집기"""
    
    def __init__(self, app_key: str = None, app_secret: str = None, cano: str = None):
        self.app_key = app_key or os.environ.get('KIS_APP_KEY')
        self.app_secret = app_secret or os.environ.get('KIS_APP_SECRET')
        self.cano = cano or os.environ.get('KIS_CANO')
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.token_expires_at = None
        
        # SQLite DB 설정
        self.db_path = os.path.expanduser('~/.openclaw/workspace/prices.db')
        self.init_database()
    
    def init_database(self):
        """SQLite 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                symbol TEXT,
                market TEXT,
                price REAL,
                change REAL,
                change_pct REAL,
                volume INTEGER,
                timestamp TEXT,
                PRIMARY KEY (symbol, timestamp)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS latest_prices (
                symbol TEXT PRIMARY KEY,
                market TEXT,
                price REAL,
                change REAL,
                change_pct REAL,
                volume INTEGER,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def get_access_token(self) -> str:
        """접근 토큰 발급"""
        if self.access_token and datetime.now() < self.token_expires_at:
            return self.access_token
        
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            expires_in = int(data.get("expires_in", 86400))
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("Access token acquired successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise
    
    def get_kr_stock_price(self, symbol: str) -> Dict:
        """국내 주식 현재가 조회"""
        token = self.get_access_token()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("rt_cd") != "0":
                logger.warning(f"API Error for {symbol}: {data.get('msg1')}")
                return None
            
            output = data.get("output", {})
            return {
                "symbol": symbol,
                "market": "KR",
                "price": int(output.get("stck_prpr", 0)),
                "change": int(output.get("prdy_vrss", 0)),
                "change_pct": float(output.get("prdy_ctrt", 0)),
                "volume": int(output.get("acml_vol", 0)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def get_us_stock_price(self, symbol: str, exchange: str = "NAS") -> Dict:
        ""해외 주식 현재가 조회"""
        token = self.get_access_token()
        
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        headers = {
            "content-type": "application/json", 
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "HHDFS00000300"
        }
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("rt_cd") != "0":
                logger.warning(f"API Error for {symbol}: {data.get('msg1')}")
                return None
            
            output = data.get("output", {})
            return {
                "symbol": symbol,
                "market": "US",
                "price": float(output.get("last", 0)),
                "change": float(output.get("diff", 0)),
                "change_pct": float(output.get("rate", 0)),
                "volume": int(output.get("tvol", 0)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def save_price(self, price_data: Dict):
        """주가 데이터 저장"""
        if not price_data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 히스토리 저장
        cursor.execute('''
            INSERT OR REPLACE INTO prices 
            (symbol, market, price, change, change_pct, volume, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            price_data['symbol'],
            price_data['market'],
            price_data['price'],
            price_data['change'],
            price_data['change_pct'],
            price_data['volume'],
            price_data['timestamp']
        ))
        
        # 최신 가격 업데이트
        cursor.execute('''
            INSERT OR REPLACE INTO latest_prices 
            (symbol, market, price, change, change_pct, volume, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            price_data['symbol'],
            price_data['market'],
            price_data['price'],
            price_data['change'],
            price_data['change_pct'],
            price_data['volume'],
            price_data['timestamp']
        ))
        
        conn.commit()
        conn.close()
    
    def update_portfolio_prices(self, portfolio_file: str = None):
        """포트폴리오 종목 가격 업데이트"""
        if portfolio_file is None:
            portfolio_file = os.path.expanduser('~/.openclaw/workspace/portfolio_full.csv')
        
        import pandas as pd
        df = pd.read_csv(portfolio_file)
        
        kr_stocks = []
        us_stocks = []
        
        for _, row in df.iterrows():
            asset = str(row['자산'])
            if asset.endswith('.KS') or asset.isdigit() or len(asset) == 6:
                kr_stocks.append(asset)
            elif asset.isalpha() or '/' in asset:
                us_stocks.append(asset)
        
        logger.info(f"Updating {len(kr_stocks)} KR stocks and {len(us_stocks)} US stocks")
        
        # 국내 주식 업데이트
        for symbol in kr_stocks[:30]:  # API 제한 고려
            try:
                price = self.get_kr_stock_price(symbol[-6:] if len(symbol) > 6 else symbol)
                if price:
                    self.save_price(price)
                    logger.info(f"Updated {symbol}: ₩{price['price']:,}")
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
        
        # 미국 주식 업데이트
        for symbol in us_stocks[:10]:
            try:
                price = self.get_us_stock_price(symbol)
                if price:
                    self.save_price(price)
                    logger.info(f"Updated {symbol}: ${price['price']:.2f}")
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
    
    def get_latest_prices(self) -> List[Dict]:
        """최신 주가 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, market, price, change, change_pct, updated_at
            FROM latest_prices
            ORDER BY updated_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "symbol": row[0],
                "market": row[1],
                "price": row[2],
                "change": row[3],
                "change_pct": row[4],
                "updated_at": row[5]
            }
            for row in results
        ]

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KIS Price Collector')
    parser.add_argument('--update', action='store_true', help='Update portfolio prices')
    parser.add_argument('--list', action='store_true', help='List latest prices')
    parser.add_argument('--symbol', help='Get specific symbol price')
    
    args = parser.parse_args()
    
    collector = KISPriceCollector()
    
    if args.update:
        collector.update_portfolio_prices()
    elif args.list:
        prices = collector.get_latest_prices()
        for p in prices[:20]:
            print(f"{p['symbol']}: {p['price']:,} ({p['change_pct']:+.2f}%)")
    elif args.symbol:
        if args.symbol.isdigit() or len(args.symbol) == 6:
            price = collector.get_kr_stock_price(args.symbol)
        else:
            price = collector.get_us_stock_price(args.symbol)
        print(json.dumps(price, indent=2, ensure_ascii=False))
    else:
        # 기본: 포트폴리오 업데이트
        collector.update_portfolio_prices()

if __name__ == "__main__":
    main()
