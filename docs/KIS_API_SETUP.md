# 🔑 한국투자증권(KIS) Open API 연동 가이드

## 개요
한국투자증권 공식 API를 사용하여 실시간 주가 데이터 수집

## 장점
- ✅ **공식 API**: DOM 파싱/차단 이슈 없음
- ✅ **안정적**: REST API로 안정적인 폴링
- ✅ **실시간 가능**: WebSocket 실시간 체결가 지원
- ✅ **묣료**: 계좌 보유 시 API 호출 묣료

---

## 1. KIS 개발자 계정 설정

### 1.1 계정 생성
1. https://apiportal.koreainvestment.com/ 접속
2. 회원가입 (한국투자증권 계좌 필요)
3. 로그인 → "My 앱" → "앱 등록"

### 1.2 앱 등록
```
앱 이름: PortfolioBot
사용 권한: 
  ☑️ 주식현가 시세
  ☑️ 해외주식현가 시세
  ☑️ 주식잔고 조회 (선택)
```

### 1.3 인증 정보 확인
등록 후 다음 정보 복사:
- **APP_KEY**: xxxxxxxxxxxxxxxxxxxxxxxx
- **APP_SECRET**: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
- **CANO** (계좌번호): 12345678

---

## 2. 환경 변수 설정

### .env 파일 생성
```bash
cat > ~/.openclaw/workspace/.env << 'EOF'
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_CANO=your_account_number_here
EOF
```

### 또는 환경 변수 직접 설정
```bash
export KIS_APP_KEY="your_app_key"
export KIS_APP_SECRET="your_app_secret"
export KIS_CANO="your_account_number"
```

---

## 3. 데이터베이스 구조

### SQLite 스키마
```sql
-- prices: 히스토리 데이터
CREATE TABLE prices (
    symbol TEXT,
    market TEXT,
    price REAL,
    change REAL,
    change_pct REAL,
    volume INTEGER,
    timestamp TEXT,
    PRIMARY KEY (symbol, timestamp)
);

-- latest_prices: 최신 데이터 (빠른 조회용)
CREATE TABLE latest_prices (
    symbol TEXT PRIMARY KEY,
    market TEXT,
    price REAL,
    change REAL,
    change_pct REAL,
    volume INTEGER,
    updated_at TEXT
);
```

---

## 4. 사용 방법

### 4.1 단일 종목 조회
```bash
python3 scripts/kis_price_collector.py --symbol 005930
```

### 4.2 포트폴리오 전체 업데이트
```bash
python3 scripts/kis_price_collector.py --update
```

### 4.3 최신 가격 조회
```bash
python3 scripts/kis_price_collector.py --list
```

---

## 5. 자동화 설정 (크론)

### 5.1 크론 작업 등록
```bash
openclaw cron add \
  --name="kis-price-update" \
  --cron="*/5 9-16 * * 1-5" \
  --message="/exec python3 /Users/geon/.openclaw/workspace/scripts/kis_price_collector.py --update" \
  --description="KIS API 주가 업데이트 (5분 간격, 장중)"
```

### 5.2 주기별 업데이트
- **장중**: 5분 간격 (09:00-16:00)
- **장마감 후**: 일일 마감가 저장
- **주말**: 업데이트 생략

---

## 6. 아키텍처

```
┌─────────────────────────────────────────┐
│         KIS Price Collector            │
├─────────────────────────────────────────┤
│                                          │
│  1. KIS API 호출 (30초~5분 간격)        │
│     - 국내 주식: FHKST01010100          │
│     - 해외 주식: HHDFS00000300          │
│                                          │
│  2. SQLite 저장                         │
│     - prices (히스토리)                 │
│     - latest_prices (최신)              │
│                                          │
│  3. 대시보드 조회                       │
│     - SQLite에서 실시간 조회            │
│     - 외부 API 의존성 없음              │
│                                          │
└─────────────────────────────────────────┘
```

---

## 7. API 제한 사항

| 항목 | 제한 |
|:---|:---|
| 분당 호출 | 20회 (묣료 계정) |
| 일일 호출 | 1,000회 |
| 동시 연결 | 1개 |
| 토큰 유효기간 | 24시간 |

---

## 8. 오류 처리

### 8.1 토큰 만료
- 자동으로 재발급
- 24시간마다 토큰 갱신

### 8.2 API 호출 실패
- 재시도 로직 3회
- 실패 시 로그 기록
- 다음 주기에 재시도

### 8.3 데이터 유실 방지
- SQLite WAL 모드 사용
- 트랜잭션 기반 저장

---

## 9. 모니터링

### 로그 확인
```bash
tail -f ~/.openclaw/workspace/logs/kis_collector.log
```

### 데이터 확인
```bash
sqlite3 ~/.openclaw/workspace/prices.db "SELECT * FROM latest_prices LIMIT 10;"
```

---

## 10. 다음 단계

### Phase 1 (현재): REST API 폴링
- [x] 기본 주가 수집
- [x] SQLite 저장
- [ ] 대시보드 연동

### Phase 2: 실시간 WebSocket
- [ ] WebSocket 연결
- [ ] 실시간 체결가 수신
- [ ] 자동 알림 트리거

### Phase 3: 고급 분석
- [ ] 이동평균 계산
- [ ] 변동성 분석
- [ ] 알고리즘 트레이딩 시그널

---

## 참고 자료

- [KIS Developers](https://apiportal.koreainvestment.com/)
- [API 문서](https://apiportal.koreainvestment.com/apiservice)
- [GitHub 샘플](https://github.com/koreainvestment/open-trading-api)

---

*생성일: 2026-03-02*
