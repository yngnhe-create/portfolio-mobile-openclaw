# 한국투자증권(KIS) Open API 연동 가이드

## 개요
한국투자증권(KIS) 공식 Open API를 통해 실시간 주가를 수집하고 DB에 저장하는 시스템

## 아키텍처

```
┌─────────────────────────────────────────────┐
│         KIS Price Collector (WSL)          │
│  ┌─────────────┐    ┌─────────────────┐    │
│  │  REST API   │───▶│   SQLite DB     │    │
│  │  (30초 간격)│    │  prices.db      │    │
│  └─────────────┘    └─────────────────┘    │
└─────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│         Web Dashboard (Cloudflare)         │
│  ┌──────────────────────────────────────┐   │
│  │  HTML + JavaScript (SQLite 읽기)    │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 설정 방법

### 1. KIS Developers 가입 및 앱 등록

1. https://apiportal.koreainvestment.com 접속
2. 회원가입 및 로그인
3. "내 앱" → "앱 등록"
4. 앱 이름: "PortfolioDashboard"
5. 앱키, 앱시크릿 복사

### 2. 환경변수 설정

```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
export KIS_APP_KEY="your_app_key_here"
export KIS_APP_SECRET="your_app_secret_here"

# 적용
source ~/.zshrc
```

### 3. 실행

```bash
# 수동 실행
python3 ~/.openclaw/workspace/scripts/kis_price_collector.py

# 자동화 (크론)
*/5 * * * 1-5 /usr/bin/python3 /Users/geon/.openclaw/workspace/scripts/kis_price_collector.py
```

## 데이터베이스 구조

### stock_prices (현재가 테이블)
| 컬럼 | 타입 | 설명 |
|:---|:---|:---|
| symbol | TEXT PK | 종목코드 |
| name | TEXT | 종목명 |
| current_price | INTEGER | 현재가 |
| price_change | INTEGER | 전일대비 |
| change_rate | REAL | 등락률 |
| volume | INTEGER | 거래량 |
| updated_at | TIMESTAMP | 갱신시간 |

### price_history (히스토리 테이블)
| 컬럼 | 타입 | 설명 |
|:---|:---|:---|
| id | INTEGER PK | ID |
| symbol | TEXT | 종목코드 |
| price | INTEGER | 가격 |
| timestamp | TIMESTAMP | 시간 |

## API 호출 제한

- **초당 10회** (종목无关)
- **1일 100,000회** (계정 기준)
- 포트폴리오 57종목 × 30초 간격 = 약 1,700회/시간 (여유있음)

## 장점

✅ **공식 API** - DOM 변경/차단 이슈 없음  
✅ **안정적** - 99.9% 가동률  
✅ **실시간** - 30초 단위 갱신 가능  
✅ **확장성** - WebSocket 실시간 체결가도 지원  

## 단점/주의사항

⚠️ **인증 복잡** - 토큰, 해시키 등 인증 절차 필요  
⚠️ **온보딩 필요** - 계좌 개설, 앱키 발급 등  
⚠️ **호출 제한** - 초당 10회 제한 준수 필요  

## 다음 단계

1. KIS 계좌 개설 (온라인 가능)
2. KIS Developers 가입 및 앱 등록
3. 환경변수 설정
4. 테스트 실행
5. 크론 자동화 설정

## 참고 자료

- KIS Developers: https://apiportal.koreainvestment.com
- 공식 GitHub: https://github.com/koreainvestment/open-trading-api
