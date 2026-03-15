# HEARTBEAT.md

Heartbeat는 **잡다한 확인**이 아니라, 플레이북 기준의 감시/준비 작업만 수행한다.

관련 기준:
- `playbooks/alert-priority.md`
- `playbooks/news-briefing.md`
- `playbooks/portfolio.md`
- `playbooks/geopolitics.md`

## 1) Stock Monitoring

- 현대차 우선주를 2~4회/시장일 체크
- 먼저 실행: `python3 /Users/geon/.openclaw/workspace/scripts/check_hyundai_alerts.py`
- JSON의 `alerts` 가 비어 있으면 알리지 말 것
- 집중 가격:
  - 현대차3우B: 264,000원 / 274,000원 / 232,000원 하향 이탈
  - 현대차우: 280,000원 / 295,000원 / 248,000원 하향 이탈
- 조건 충족 시:
  1. Discord `1481256145426321409` (#주식-가격알림) 으로만 전송
  2. 현재가 / 임계값 / suggested action(hold / 1차 분할매도 / 2차 분할매도 / 리스크 점검) 포함
  3. DM에는 상세 알림을 쓰지 말고 `HEARTBEAT_OK`만 반환
- 같은 알림 반복 금지. 의미 있는 가격 변화가 있을 때만 재전송

## 2) Quiet rule

- 00:00~08:00에는 긴급한 P1 아니면 먼저 말 걸지 말 것
- 급하지 않은 뉴스/트렌드는 heartbeat에서 즉시 보내지 말고 정기 브리핑으로 넘길 것

## 3) Geopolitics quick check

- 이란/호르무즈/유가에 **중대한 변화**가 있으면 P1만 고려
- 단순 반복 헤드라인은 무시
- 한국시장에 직접 충격 주는 변화만 즉시 알림 대상
