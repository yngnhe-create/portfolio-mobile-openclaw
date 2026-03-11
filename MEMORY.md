# 🧠 Long-term Memory

## Google Calendar & Gmail Integration

**Status:** ✅ Active  
**Connected:** 2026-02-17  
**Account:** aqueous-impact-487708-r7 (geonnyun@gmail.com)

**Commands:**
```bash
# Calendar
node ~/workspace/calendar/calendar_fetcher.js [days]

# Gmail (unread)
node ~/workspace/calendar/gmail_fetcher.js [count]
```

**Automation:**
- Daily calendar summary at 8:00 AM KST
- Heartbeat checks for upcoming events

## Daily Stock Market Report (Enhanced)

**Status:** ✅ Active  
**Created:** 2026-02-17  
**Updated:** 2026-02-17 (Enhanced Version)  
**Schedule:** Every day at 7:50 AM KST

**Features:**
- 📊 Comprehensive market analysis with detailed insights
- 🇰🇷 KOSPI/KOSDAQ detailed analysis (price, change, moving averages)
- 🌍 Global markets overview framework
- 📰 Categorized market news (Macro, Earnings, Sector trends)
- 💡 Investment strategies (Short-term & Mid-term)
- ⚠️ Risk factors analysis
- 📋 Professional report format with Executive Summary
- Auto-delivered via Telegram

**Cron Job:** `daily-stock-market-report`

## WiseReport 분석 요청 시 (자동화)

**트리거:** "와이즈리포트 분석해줘" 또는 "WiseReport 분석"

**실행 시점:** 오늘 날짜 기준 (KST)

**절차:**
1. **Executive Summary 생성 (가장 먼저 제공)**
   - Today Top/Hot/Best 3종목 요약
   - 목표주가 상향/하향 종목 Top 5
   - 주요 투자 테마 4가지
   - 시장 현황 (KOSPI, 환율, 유가, 금리)
   - 이번 주 주요 이벤트

2. **브라우저 자동화 데이터 수집**
   - https://wisereport.co.kr 접속
   - 로그인: yngnhe / wldhs232
   - 중복 로그인 팝업 시 "확인" 클릭
   - Report Summary 페이지 이동
   - 기업/산업 탭 데이터 수집
   - 주요 리포트 팝업 상세 내용 추출

3. **상세 분석 보고서 작성**
   - 기업 리포트 분석 (목표주가 변경 표)
   - 산업/섹터별 핵심 이슈
   - 투자 전략 제언
   - 리스크 알림

4. **최종 결과물 형식**
   ```
   # Executive Summary (1페이지 분량)
   
   # 상세 분석 보고서
   ## 1. Today Top Picks
   ## 2. 목표주가 변경 종목
   ## 3. 섹터별 분석
   ## 4. 투자 전략
   ## 5. 리스크 알림
   ```

**보고서 구조:**
1. 데일리 핵심 요약 (Executive Summary)
2. 기업 리포트 분석 (표 형식)
3. 산업/섹터별 핵심 이슈
4. 투자 전략 제언 (Upside 분석)
5. 종합 의견

**출력 형식:**
- 한국어
- 전문적 금융 분석 보고서 톤
- 표(Table) 적극 사용
- 핵심 데이터 강조 (굵게, 색상)

**관련 링크:**
- 투자커맨드: https://portfolio-mobile-openclaw.pages.dev
- WiseReport 상세: https://portfolio-mobile-openclaw.pages.dev/wisereport_complete.html
4. `memory/YYYY-MM-DD-wisereport-summary.md` 에 저장
5. HTML 빌드: `python3 scripts/build_wisereport_page.py`

**참고:** KeyPoint 메뉴가 아니라 Report Summary 메뉴에서 추출 (2026.02.27부터 적용)

See TOOLS.md for detailed setup info.

## Discord 서버 채널 구성

**서버 ID:** `1479685693855895843`  
**설정일:** 2026-03-11

- `#주식-가격알림` → `channel:1481256145426321409` — 현대차 우선주 임계가 돌파 즉시 알림
- `#와이즈리포트` → `channel:1481256169971388546` — 매일 오전 와이즈리포트 분석 결과
- `#시장-시황` → `channel:1481256186081968289` — KOSPI/KOSDAQ 마감 시황
- `#모닝-브리핑` → `channel:1481256204180131840` — 매일 오전 8시 캘린더·날씨·일정
- `#이슈-뉴스` → `channel:1481256219602849954` — 주요 이슈·속보
- `#크론-로그` → `channel:1481256234890956812` — 자동화 크론 실행 결과·에러
- `#ai-대화` → `channel:1481256251290681438` — AI 대화·명령·질문

**라우팅 규칙:**
- 현대차 가격 알림 → `#주식-가격알림`
- 와이즈리포트 일일 분석 → `#와이즈리포트`
- 모닝 브리핑(캘린더/날씨) → `#모닝-브리핑`
- 크론 에러/결과 → `#크론-로그`

## Web Search 설정

**Provider:** Perplexity (기본값 모델)  
**설정일:** 2026-03-10  
**비용:** 검색 1회 약 $0.01~0.10  
**규칙:** 웹 검색 필요 시 Perplexity 기본 사용
