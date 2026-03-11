# 🏭 Content Factory - 구축 완료

## 개요
Discord 기반 다중 에이전트 자동화 시스템 구축 완료

## 시스템 구조

```
┌─────────────────────────────────────────┐
│         Content Factory Pipeline        │
├─────────────────────────────────────────┤
│  8:00 AM 평일 자동 실행                  │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Research Agent (#리서치)               │
│  • 시장 데이터 수집                     │
│  • 포트폴리오 현황 분석                 │
│  • 와이즈리포트 인사이트                │
│  • 핫 뉴스 수집                        │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Writing Agent (#리포트)                │
│  • 투자 일일 리포트 작성                │
│  • 마크다운 형식 출력                   │
│  • 전략 및 리스크 분석                  │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Visualization Agent (#차트)            │
│  • 포트폴리오 대시보드                  │
│  • 와이즈리포트 대시보드                │
│  • 실시간 차트 연동                     │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Telegram 알림 전송                     │
│  • 요약 리포트 발송                     │
│  • 대시보드 링크 공유                   │
└─────────────────────────────────────────┘
```

## 파일 구조

```
scripts/
├── content_factory_master.py      # 마스터 오케스트레이터
├── content_factory_research.py    # Research Agent
├── content_factory_writing.py     # Writing Agent
└── (Visualization은 기존 대시보드 활용)
```

## 생성된 콘텐츠

### 1. 투자 일일 리포트
- **파일**: `/tmp/investment_report_YYYYMMDD.md`
- **내용**: 포트폴리오 요약, 와이즈리포트 인사이트, 투자 전략, 핫 뉴스
- **형식**: 마크다운 (읽기 쉬움)

### 2. 포트폴리오 대시보드
- **링크**: https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html
- **기능**: 57개 종목, 실시간 주가, 섹터별 비중, 손익 분석

### 3. 와이즈리포트 대시보드
- **링크**: https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html
- **기능**: 목표가 변경 종목, 섹터별 전략, Hot 뉴스

## 자동화 설정

### 크론 작업
```bash
이름: content-factory-daily
시간: 매일 08:00 (평일)
다음 실행: 2026-03-03 08:00
```

### 실행 순서
1. **Research Agent**: 포트폴리오/시장 데이터 수집 (1-2분)
2. **Writing Agent**: 리포트 작성 (1-2분)
3. **Visualization**: 대시보드 업데이트 확인 (즉시)
4. **Telegram**: 알림 전송 (즉시)

## 수동 실행

```bash
# 전체 파이프라인 실행
python3 ~/.openclaw/workspace/scripts/content_factory_master.py

# 개별 Agent 실행
python3 ~/.openclaw/workspace/scripts/content_factory_research.py
python3 ~/.openclaw/workspace/scripts/content_factory_writing.py
```

## 확장 계획

### Phase 2 (추천)
- [ ] Discord 웹훅 연동 (리서치/리포트 채널에 자동 포스팅)
- [ ] 이메일 뉴스레터 발송
- [ ] 주간/월간 리포트 추가

### Phase 3 (고급)
- [ ] 와이즈리포트 웹 스크래핑 (완전 자동화)
- [ ] GPT-4 기반 리포트 작성 고도화
- [ ] 투자 전략 백테스팅 연동

## 현재 상태

✅ **완료된 기능**:
- Research → Writing → Visualization 체인
- Telegram 알림 자동화
- 매일 아침 8시 자동 실행

⚠️ **수동 필요**:
- 와이즈리포트 데이터 업데이트 (웹 스크래핑 필요)
- 뉴스 기사 링크 수동 확인

---

*생성일: 2026-03-02*
*다음 실행: 2026-03-03 08:00*
