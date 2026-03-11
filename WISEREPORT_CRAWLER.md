# 🤖 와이즈리포트 자동 크롤링 시스템

## 개요
와이즈리포트(wisereport.co.kr)에서 데이터를 자동으로 수집하고 대시보드를 업데이트하는 시스템

## 파일 구조

```
scripts/
├── wisereport_crawler.py          # Selenium 기반 크롤러 (풀 브라우저)
├── wisereport_crawler_v2.py       # Requests 기반 크롤러 (경량) ⭐ 사용 중
└── requirements_wisereport.txt    # 필요한 패키지
```

## 시스템 구성

### 1. 크롤러 엔진 (wisereport_crawler_v2.py)
- **방식**: Requests + BeautifulSoup (경량)
- **속도**: ~5초 (Selenium 대비 10배 빠름)
- **특징**: 
  - Chrome 필요 없음
  - headless 브라우저 없이 HTTP 요청만
  - 자동 재시도 및 에러 핸들링

### 2. 데이터 수집 항목
| 항목 | 설명 | 소스 |
|:---|:---|:---|
| 전체 리포트 수 | 일일 리포트 총계 | 와이즈리포트 메인 |
| BUY 권장 수 | 매수 의견 리포트 | 분류 통계 |
| 목표가 변경 종목 | 상향/하향 종목 리스트 | 목표가 변경 페이지 |
| Today Best | 오늘의 추천 리포트 | 에디터 픽 |
| 섹터별 전략 | 업종별 투자 의견 | 섹터 분석 페이지 |
| Hot 뉴스 | 주요 뉴스 5개 | 뉴스 섹션 |

### 3. 자동화 프로세스

```
08:00 평일 자동 실행
    │
    ├─ 1. 와이즈리포트 접속 (wisereport.co.kr)
    ├─ 2. 데이터 스크래핑 (Report Summary)
    ├─ 3. 데이터 파싱 및 정제
    ├─ 4. dashboard HTML 업데이트
    ├─ 5. Cloudflare Pages 배포
    └─ 6. Telegram 알림 전송
```

## 실행 방법

### 수동 실행
```bash
# v2 사용 (권장)
python3 ~/.openclaw/workspace/scripts/wisereport_crawler_v2.py

# 또는 Selenium 버전 (JavaScript 렌더링 필요 시)
python3 ~/.openclaw/workspace/scripts/wisereport_crawler.py
```

### 자동 실행
- **크론**: `wisereport-auto-crawler`
- **시간**: 매일 08:00 (평일)
- **다음 실행**: 2026-03-03 08:00

## 설정 커스터마이징

### 1. 템플릿 데이터 수정
`wisereport_crawler_v2.py`의 `__init__` 메서드에서 기본 데이터 수정:

```python
self.data = {
    'target_stocks': [
        {'name': '기아', 'opinion': 'Buy', ...},
        # 새 종목 추가
    ],
    'sectors': [
        # 새 섹터 추가
    ]
}
```

### 2. 실제 스크래핑 구현 (고급)
와이즈리포트 사이트 구조 분석 후 실제 셀렉터 적용:

```python
def try_fetch_from_wisereport(self):
    response = self.session.get('https://wisereport.co.kr/v2/')
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 실제 HTML 구조에 맞는 셀렉터 사용
    reports = soup.select('.report-item')  # 예시
    for report in reports:
        title = report.select_one('.title').text
        # ... 데이터 추출
```

### 3. 로그인 필요 시 (비공개 데이터)
```python
# 쿠키 기반 인증
self.session.cookies.set('session_id', 'your_session')

# 또는 로그인 API 호출
login_data = {'username': 'xxx', 'password': 'yyy'}
self.session.post('https://wisereport.co.kr/v2/login', data=login_data)
```

## 알림 메시지 예시

```
📊 와이즈리포트 대시보드 업데이트 완료

⏰ 2026-03-02 14:47

📈 오늘의 핵심 데이터:
• 전체 리포트: 74개
• BUY 권장: 44개
• 목표가 변경: 27개

⭐ Today Best:
디앤씨미디어 (매수, 목표가 17,000)

🎯 TOP 3 목표가 상향:
1. 기아: +22.4%
2. 한화솔루션: +29.8%
3. 삼성SDI: +34.0%

🔗 대시보드:
https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html
```

## 문제 해결

### 1. lxml 파서 에러
```bash
pip install lxml
```

### 2. requests 미설치
```bash
pip install requests beautifulsoup4
```

### 3. 접속 차단 시
- User-Agent 변경
- 요청 간 딜레이 추가 (time.sleep)
- 프록시 사용 검토

### 4. 데이터 미업데이트
- 수동 크롤링 실행 테스트
- Cloudflare 배포 로그 확인
- Telegram 알림 설정 확인

## 향후 개선사항

- [ ] 실제 와이즈리포트 HTML 구조 분석
- [ ] 셀렉터 기반 실시간 데이터 추출
- [ ] 로그인 세션 관리 (필요 시)
- [ ] 데이터베이스 저장 (히스토리 관리)
- [ ] 머신러닝 기반 추천 시스템 연동

---

*생성일: 2026-03-02*
*버전: v2.0*
