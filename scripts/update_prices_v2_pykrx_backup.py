#!/usr/bin/env python3
"""
KIS API 기반 포트폴리오 가격 업데이트
- 한국 주식/ETF만 KIS API로 현재가 조회
- 미국 주식, 가상자산 등은 스킵
"""
import os
import re
import time
import requests
import pandas as pd
from datetime import datetime

# .env 로드
env_path = os.path.expanduser('~/.openclaw/.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

PORTFOLIO_PATH = '/Users/geon/.openclaw/workspace/portfolio_full.csv'
DASHBOARD_PATH = '/Users/geon/.openclaw/workspace/public/portfolio_dashboard_v4.html'
BASE_URL = "https://openapi.koreainvestment.com:9443"


def get_access_token():
    """KIS API 접근 토큰 발급"""
    app_key = os.environ.get('KIS_APP_KEY')
    app_secret = os.environ.get('KIS_APP_SECRET')
    if not app_key or not app_secret:
        print("KIS_APP_KEY / KIS_APP_SECRET 환경변수 없음")
        return None, None, None

    url = f"{BASE_URL}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    resp = requests.post(url, headers={"content-type": "application/json"}, json=body, timeout=10)
    data = resp.json()
    if 'access_token' in data:
        print(f"토큰 발급 성공 (만료: {data.get('expires_in', '?')}초)")
        return data['access_token'], app_key, app_secret
    else:
        print(f"토큰 발급 실패: {data}")
        return None, None, None


def get_stock_price(token, app_key, app_secret, symbol):
    """KIS API 국내 주식/ETF 현재가 조회"""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "FHKST01010100"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()
    if data.get("rt_cd") == "0":
        out = data.get("output", {})
        return {
            "price": int(out.get("stck_prpr", 0)),
            "change": int(out.get("prdy_vrss", 0)),
            "change_rate": float(out.get("prdy_ctrt", 0)),
        }
    return None


def is_korean_stock_code(code):
    """6자리 숫자 종목코드인지 확인"""
    return bool(re.match(r'^\d{6}$', str(code).strip()))


def update_portfolio():
    df = pd.read_csv(PORTFOLIO_PATH)

    # 종목코드 컬럼이 없으면 하드코딩 매핑 사용
    stock_code_map = {
        '삼성전자': '005930', '삼성전자우': '005935',
        '현대차3우B': '005387', '현대차우': '005385',
        '파마리서치': '214450', 'DL이앤씨우': '375500',
        '두산': '000150', '네이버': '035420',
        '삼성SDI': '006400', 'LG에너지솔루션': '373220',
        '엘오티베큠': '307750', '현대건설': '000720',
        '세아베스틸지주': '001430', '코람코라이프인프라리츠': '357120',
        'SK리츠': '395400', '신한서부티엔디리츠': '404990',
        '이지스밸류플러스리츠': '334890', 'ESR켄달스퀘어리츠': '365550',
        '기아': '000270', 'LG이노텍': '011070',
        'LG화학': '051910', '포스코퓨처엠': '003670',
        '한화솔루션': '009830', '피에스케이홀딩스': '031980',
        '한솔케미칼': '014680', '켐트로닉스': '089010',
        '한미약품': '128940', '유한양행': '000100',
        '씨젠': '096530', '엔씨소프트': '036570',
        '웹젠': '069080', '대한항공': '003490',
        'LG디스플레이': '034220', 'KT&G': '033780',
        '한국콜마': '161890', '아모레퍼시픽': '090430',
        '한섬': '020000', '이수페타시스': '007660',
        '파트론': '091700', '롯데렌탈': '089860',
        'KODEX 증권': '229200',
        # ETFs
        'TIGER 코리아AI전력기기TOP3+': '484880',
        'TIGER 글로벌AI액티브': '375570',
        'TIGER 미국테크TOP10 INDXX': '381170',
        'TIGER 테슬라채권혼합Fn': '382340',
        'TIGER 코스피고배당': '395160',
        'TIGER 미국초단기국채': '479430',
        'TIGER 글로벌멀티에셋TIF': '472160',
        'TIGER 미국달러단기채권': '329750',
        'TIGER 글로벌AI사이버보안': '489070',
        'KODEX 미국30년국채액티브(H)': '453850',
        'KODEX 미국30년국채울트라(H)': '304660',
        'KODEX 미국S&P500헬스케어': '453290',
        'KODEX TRF3070': '292190',
        'ACE 구글밸류체인액티브': '489250',
        'TIME 글로벌우주테크&방산': '487250',
        'HANARO 글로벌금채굴기업': '472430',
        'SOL 미국AI전력인프라': '488540',
    }

    # 토큰 발급
    token, app_key, app_secret = get_access_token()
    if not token:
        return

    updated = []
    failed = []
    skipped = []

    print(f"\n포트폴리오 가격 업데이트 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"총 {len(df)}개 자산\n")

    for idx, row in df.iterrows():
        asset = str(row['자산'])

        # 종목코드 결정
        code = stock_code_map.get(asset, '')
        if not is_korean_stock_code(code):
            skipped.append(asset)
            print(f"  [{asset}] 스킵 (비한국)")
            continue

        # KIS API 조회
        try:
            data = get_stock_price(token, app_key, app_secret, code)
        except Exception as e:
            failed.append(asset)
            print(f"  [{asset}] 오류: {e}")
            continue

        if not data or data['price'] == 0:
            failed.append(asset)
            print(f"  [{asset}] ({code}) 조회 실패")
            time.sleep(0.1)
            continue

        new_price = data['price']
        change = data['change']
        change_rate = data['change_rate']

        # 현재가 업데이트
        df.at[idx, '현재가'] = new_price

        # 자산가치 재계산
        qty = row['수량']
        new_value = qty * new_price
        df.at[idx, '자산가치'] = f"₩{new_value:,.0f}"

        # 손익 재계산
        purchase_str = str(row['매수가']).replace('₩', '').replace(',', '').replace(' ', '')
        try:
            purchase = float(purchase_str)
            if purchase > 0:
                profit = (new_price - purchase) * qty
                profit_pct = ((new_price - purchase) / purchase) * 100
                sign = '+' if profit >= 0 else ''
                df.at[idx, '손익'] = f"{sign}₩{profit:,.0f} ({sign}{profit_pct:.2f}%)"
        except (ValueError, TypeError):
            pass

        sign = '+' if change >= 0 else ''
        updated.append(asset)
        print(f"  [{asset}] ({code}) ₩{new_price:,} ({sign}{change:,}, {sign}{change_rate}%)")

        time.sleep(0.1)  # rate limit

    # CSV 저장
    df.to_csv(PORTFOLIO_PATH, index=False)

    # 대시보드 타임스탬프 업데이트
    if os.path.exists(DASHBOARD_PATH):
        try:
            with open(DASHBOARD_PATH, 'r', encoding='utf-8') as f:
                html = f.read()
            ts = datetime.now().strftime('%Y-%m-%d %H:%M')
            html = re.sub(
                r'최종 업데이트:.*?<',
                f'최종 업데이트: {ts}<',
                html
            )
            with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n대시보드 타임스탬프 업데이트: {ts}")
        except Exception as e:
            print(f"\n대시보드 업데이트 실패: {e}")

    # 결과 요약
    print(f"\n{'='*50}")
    print(f"성공: {len(updated)}개")
    print(f"실패: {len(failed)}개" + (f" ({', '.join(failed[:5])})" if failed else ""))
    print(f"스킵: {len(skipped)}개 (비한국 종목)")
    print(f"저장: {PORTFOLIO_PATH}")
    print(f"{'='*50}")


if __name__ == "__main__":
    update_portfolio()
