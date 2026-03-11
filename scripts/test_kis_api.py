#!/usr/bin/env python3
"""
KIS API Test - 주식 현재가 조회
"""
import os
import requests
import json
from datetime import datetime

# .env에서 환경변수 로드
env_path = os.path.expanduser('~/.openclaw/.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

class KISTest:
    def __init__(self):
        self.app_key = os.environ.get('KIS_APP_KEY')
        self.app_secret = os.environ.get('KIS_APP_SECRET')
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        
    def get_access_token(self):
        """접근 토큰 발급"""
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
                print(f"✅ 토큰 발급 성공!")
                print(f"   만료: {data.get('expires_in', 'unknown')}초")
                return True
            else:
                print(f"❌ 토큰 발급 실패: {data}")
                return False
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            return False
    
    def get_stock_price(self, symbol):
        """국내 주식 현재가 조회"""
        if not self.access_token:
            print("❌ 토큰 없음. get_access_token() 먼저 실행")
            return None
        
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
                result = {
                    "종목코드": symbol,
                    "종목명": output.get("stck_name", "-"),
                    "현재가": output.get("stck_prpr", "-"),
                    "전일대비": output.get("prdy_vrss", "-"),
                    "등락률": output.get("prdy_ctrt", "-"),
                    "거래량": output.get("acml_vol", "-"),
                    "시가": output.get("stck_oprc", "-"),
                    "고가": output.get("stck_hgpr", "-"),
                    "저가": output.get("stck_lwpr", "-"),
                    "시간": datetime.now().strftime('%H:%M:%S')
                }
                return result
            else:
                print(f"❌ API 오류: {data.get('msg1', 'unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            return None

def main():
    print("=" * 60)
    print("🚀 KIS API 테스트 - 주식 현재가 조회")
    print("=" * 60)
    print()
    
    # KIS 설정 확인
    kis = KISTest()
    
    if not kis.app_key or kis.app_key == 'your-kis-app-key-here':
        print("❌ KIS_APP_KEY가 설정되지 않았습니다.")
        print("   ~/.openclaw/.env 파일에 실제 키를 입력하세요.")
        return
    
    print(f"✅ APP_KEY 확인: {kis.app_key[:10]}...")
    print()
    
    # 토큰 발급
    print("1️⃣ 접근 토큰 발급 중...")
    if not kis.get_access_token():
        return
    print()
    
    # 테스트 종목들
    test_stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
        ("041510", "SM엔터"),
    ]
    
    print("2️⃣ 주식 현재가 조회 중...")
    print("-" * 60)
    
    for symbol, name in test_stocks:
        print(f"\n📊 {name} ({symbol})")
        result = kis.get_stock_price(symbol)
        
        if result:
            print(f"   현재가: ₩{int(result['현재가']):,}")
            print(f"   등락: {result['전일대비']} ({result['등락률']}%)")
            print(f"   거래량: {int(result['거래량']):,}")
        else:
            print("   ❌ 조회 실패")
    
    print()
    print("=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
