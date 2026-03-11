#!/usr/bin/env python3
"""
KIS Portfolio Price Updater
포트폴리오 종목 실시간 가격 조회 및 업데이트
"""
import os
import sys
import json
import sqlite3
import requests
from datetime import datetime

# .env 로드
env_path = os.path.expanduser('~/.openclaw/.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# 종목명 → 코드 매핑 (주요 종목만)
STOCK_MAP = {
    '삼성전자': '005930',
    '삼성전자우': '005935',
    'SK하이닉스': '000660',
    '현대차': '005380',
    '현대차3우B': '005389',
    '현대차우': '005385',
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
}

class KISPortfolioUpdater:
    def __init__(self):
        self.app_key = os.environ.get('KIS_APP_KEY')
        self.app_secret = os.environ.get('KIS_APP_SECRET')
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.db_path = os.path.expanduser('~/.openclaw/workspace/prices.db')
        
    def init_database(self):
        """SQLite 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                price INTEGER,
                change INTEGER,
                change_pct REAL,
                volume INTEGER,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ DB 준비 완료: {self.db_path}")
    
    def get_access_token(self):
        """토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data["access_token"]
                return True
            else:
                print(f"❌ 토큰 발급 실패: {data}")
                return False
        except Exception as e:
            print(f"❌ 오류: {e}")
            return False
    
    def get_price(self, symbol):
        """주식 가격 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            if data.get("rt_cd") == "0":
                output = data.get("output", {})
                return {
                    'price': int(output.get("stck_prpr", 0)),
                    'change': int(output.get("prdy_vrss", 0)),
                    'change_pct': float(output.get("prdy_ctrt", 0)),
                    'volume': int(output.get("acml_vol", 0))
                }
            return None
        except Exception as e:
            print(f"❌ {symbol} 조회 오류: {e}")
            return None
    
    def update_portfolio(self):
        """포트폴리오 가격 업데이트"""
        print("=" * 60)
        print("🚀 KIS 포트폴리오 가격 업데이트")
        print("=" * 60)
        print()
        
        # DB 초기화
        self.init_database()
        
        # 토큰 발급
        print("1️⃣ 토큰 발급 중...")
        if not self.get_access_token():
            return
        print("✅ 토큰 발급 완료")
        print()
        
        # 종목 조회
        print("2️⃣ 종목 가격 조회 중...")
        print("-" * 60)
        
        results = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for name, symbol in STOCK_MAP.items():
            data = self.get_price(symbol)
            if data:
                print(f"✅ {name:15s} ({symbol}): ₩{data['price']:,} ({data['change_pct']:+.2f}%)")
                
                # DB 저장
                cursor.execute('''
                    INSERT OR REPLACE INTO prices (symbol, name, price, change, change_pct, volume, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, name, data['price'], data['change'], data['change_pct'], data['volume'], datetime.now().isoformat()))
                
                results.append({
                    'name': name,
                    'symbol': symbol,
                    **data
                })
            else:
                print(f"❌ {name:15s} ({symbol}): 조회 실패")
        
        conn.commit()
        conn.close()
        
        print("-" * 60)
        print(f"\n✅ {len(results)}개 종목 업데이트 완료")
        print(f"💾 DB 저장 완료: {self.db_path}")
        
        return results

def main():
    updater = KISPortfolioUpdater()
    updater.update_portfolio()

if __name__ == "__main__":
    main()
