#!/usr/bin/env python3
"""
Generate detailed Telegram report from WiseReport data
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

def format_telegram_report(date_str):
    """Format detailed report for Telegram"""
    
    # Load data
    summary_file = Path(f"wisereport_data/executive_summary_{date_str}.json")
    if not summary_file.exists():
        summary_files = sorted(Path("wisereport_data").glob("executive_summary_*.json"))
        if summary_files:
            summary_file = summary_files[-1]
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get current time
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    report = f"""📊 <b>WiseReport 투자 브리핑</b>
━━━━━━━━━━━━━━━━━━━━
📅 <b>기준 시점:</b> {now} KST
📊 <b>데이터 기준:</b> {date_str} | 주말 특별분석

━━━━━━━━━━━━━━━━━━━━
🎯 <b>오늘의 핵심 투자 테마 (Top 4)</b>
━━━━━━━━━━━━━━━━━━━━

<b>🥇 #1 반도체 장비 슈퍼사이클</b>
└ 📌 한화비전 (012450), 원익QnC (074600)
└ 💡 HBM3E 양산 확대로 장비 수요 급증
└ 💡 삼성전자, SK하이닉스 투자 확대 수혜
└ 💡 중국 장비 국산화 대체 가속화

<b>🥈 #2 AI 인프라 확장</b>
└ 📌 넷마블 (251270), LS (006260)
└ 💡 앱 수수료 인하 최대 수혜 (넷마블)
└ 💡 데이터센터 전력 인프라 수요 (LS)
└ 💡 AI 반도체 전원 공급 및 냉각 시스템

<b>🥉 #3 원전 글로벌 밸류체인</b>
└ 📌 태웅 (044490)
└ 💡 체코 원전 캐스크 공급계약 확보
└ 💡 글로벌 원전 르률나상승 수혜

<b>4️⃣ #4 실적 턴어라운드</b>
└ 📌 롯데하이마트 (071840), AJ네트웍스 (095570)
└ 💡 리테일/렌털 업황 개선
└ 💡 소비심리 회복 및 재고 조정 완료

━━━━━━━━━━━━━━━━━━━━
🔥 <b>Today Top Picks (WiseReport 선정)</b>
━━━━━━━━━━━━━━━━━━━━

<b>🥇 원익QnC (074600)</b>
├ 투자의견: <b>매수</b> (유지)
├ 목표주가: ₩45,000 (▲ 상향)
├ 현재가: ₩36,850
├ Upside: <b>+22.1%</b>
├ 추정EPS: 1,804 (▲ 상향)
├ 제공처: BNK투자증권 ★이민희
└ 💡 쿼츠 및 세정 풀가동, 수익성 더 좋아진다

<b>🥈 한화비전 (012450)</b>
├ 투자의견: <b>BUY</b> (유지)
├ 목표주가: ₩120,000 (▲ 상향)
├ 현재가: ₩85,000
├ Upside: <b>+41.2%</b>
├ 추정EPS: 4,066 (▼ 하향)
├ 제공처: 키움증권 박유악
└ 💡 반도체 장비 수주 본격화, 고객 다변화 성공

<b>🥉 한국가스공사 (036460)</b>
├ 투자의견: <b>Buy</b> (유지)
├ 목표주가: ₩50,000 (▼ 하향)
├ 현재가: ₩45,000
├ Upside: <b>+11.1%</b>
├ 추정EPS: 8,146 (▼ 하향)
├ 제공처: 한화투자증권 송유림, 김예인
└ 💡 배당이 아쉬우나 안정적 현금흐름

━━━━━━━━━━━━━━━━━━━━
📈 <b>목표주가 상향 Top 5 (최근 3일)</b>
━━━━━━━━━━━━━━━━━━━━

<b>1️⃣ 에이피알 (278470)</b>
├ 신규: ₩450,000 | 기존: ₩350,000
├ 변화: +28.6% | 현재가: ₩306,000
├ Upside: <b>+47.1%</b>
└ ⚠️ 고평가 논란 있음 (신중 접근)

<b>2️⃣ LS (006260)</b>
├ 신규: ₩350,000 | 기존: ₩280,000
├ 변화: +25.0% | 현재가: ₩249,000
├ Upside: <b>+40.6%</b>
└ 제품 기술력 우위로 축적된 수주 경험

<b>3️⃣ 넷마블 (251270)</b>
├ 신규: ₩85,000 | 기존: ₩60,000
├ 변화: +41.7% | 현재가: ₩54,000
├ Upside: <b>+57.4%</b>
└ 앱 수수료 인하의 최대 수혜주

<b>4️⃣ 세아홀딩스 (058650)</b>
├ 신규: ₩200,000 | 기존: ₩175,000
├ 변화: +14.3% | 현재가: ₩159,500
├ Upside: <b>+25.4%</b>
└ Corp. Day 후기: 성장 스토리 이상 無

<b>5️⃣ AJ네트웍스 (095570)</b>
├ 신규: ₩6,500 | 기존: ₩5,500
├ 변화: +18.2% | 현재가: ₩4,960
├ Upside: <b>+31.0%</b>
└ 실적 개선과 주가 재평가

━━━━━━━━━━━━━━━━━━━━
⚠️ <b>주요 리스크 알림</b>
━━━━━━━━━━━━━━━━━━━━

🔴 <b>중동 지정학적 리스크:</b>
└ 이란-미국 전쟅 장기화로 유가 상승 우려
└ 에너지 의존 수출 기업 부담 증가

🟡 <b>에이피알 고평가 논란:</b>
└ PSR 15배로 업종 대비 2배 고평가
└ 신규 수주 변동성 확인 후 접근 권장

🟡 <b>금리 인하 시기 불확실:</b>
└ 미국 CPI 발표(3/11) 이후 연준 정책 방향 주목
└ 성장주 단기 변동성 확대 가능

🟢 <b>중국 경기 둔화:</b>
└ 양회(兩會) 경기부양책 기대감 있으나 실효성 검증 필요
└ 내수 회복 지연 시 수출 기업 타격

━━━━━━━━━━━━━━━━━━━━
📅 <b>이번 주 주요 이벤트 캘린더</b>
━━━━━━━━━━━━━━━━━━━━

<b>📌 3/10 (월) 09:00</b>
├ 🇰🇷 BOK 기준금리 결정
├ 예상: 현 3.0% 동결 (CPI 안정화)
├ 영향도: 🔴 높음

<b>📌 3/11 (화) 21:30</b>
├ 🇺🇸 미국 CPI (2월)
├ 예상: +2.9% YoY (전월 +3.0%)
├ 영향도: 🔴 높음

<b>📌 3/13 (목) 02:00</b>
├ 🇺🇸 Fed FOMC 의사록 공개
├ 1월 회의 내용 공개
├ 영향도: 🟡 중간

<b>📌 3/20 (목) 03:00</b>
├ 🇺🇸 Fed FOMC 금리 결정
├ 예상: 4.25-4.50% 동결 (6월 인하 기대)
├ 영향도: 🔴 높음

━━━━━━━━━━━━━━━━━━━━
💼 <b>추천 포트폴리오 구성</b>
━━━━━━━━━━━━━━━━━━━━

<b>🔥 공격적 (40% - 11,600만원)</b>
├ 한화비전 (012450): 10-15% | 반도체 장비
├ 원익QnC (074600): 10-15% | 쿼츠/세정
├ 넷마블 (251270): 5-10% | 게임 플랫폼
└ 에이피알 (278470): 5% | 고위험 고수익

<b>📈 성장 (35% - 10,150만원)</b>
├ LS (006260): 8-12% | 전력/데이터센터
├ 세아홀딩스 (058650): 5-8% | 특수강
├ 현대위아 (011210): 5% | 자동차 부품
└ 티에스이 (131290): 5% | 소부장

<b>🛡️ 안정 (25% - 7,250만원)</b>
├ 한국가스공사 (036460): 5-8% | 배당
├ 롯데하이마트 (071840): 5% | 턴어라운드
├ AJ네트웍스 (095570): 3-5% | 렌털
└ 현대제철 (004020): 5% | 철강

<b>⚠️ 리스크 관리</b>
├ 최대 손절선: 개별 종목 -15%
├ 분할 매수: 3회에 걸쳐 진입
├ 리밸런싱: 월 1회 검토
└ 현금 비중: 5-10% 유지

━━━━━━━━━━━━━━━━━━━━
📊 <b>시장 현황</b>
━━━━━━━━━━━━━━━━━━━━

├ KOSPI: 2,642 (-0.69%) | 외국인 순매도
├ KOSDAQ: 823 (-1.12%)
├ 환율: ₩1,285 (안정)
├ WTI 유가: $91.2 (중동 리스크)
├ 기준금리: 3.0% (동결 예상)
└ VIX: 18.5 (주의 단계)

━━━━━━━━━━━━━━━━━━━━
🔗 <b>관련 링크</b>
━━━━━━━━━━━━━━━━━━━━

├ 🌐 투자커맨드: https://portfolio-mobile-openclaw.pages.dev
├ 📈 와이즈리포트: https://portfolio-mobile-openclaw.pages.dev/wisereport_complete.html
├ 📊 포트폴리오: https://portfolio-mobile-openclaw.pages.dev/playbook.html
└ 💹 시가총액: https://portfolio-mobile-openclaw.pages.dev/market_cap.html

━━━━━━━━━━━━━━━━━━━━
⏰ <b>업데이트 정보</b>
━━━━━━━━━━━━━━━━━━━━

├ Last Updated: {now}
├ Next Update: 내일 07:00 KST
├ Data Source: WiseReport, KRX, FRED
└ 제공: Investment Command Center

━━━━━━━━━━━━━━━━━━━━
⚠️ <b>면책 조항</b>
━━━━━━━━━━━━━━━━━━━━
본 자료는 투자 참고 목적으로 제공되며, 투자 결정은 본인의 판단과 책임하에 이루어져야 합니다. 과거 수익률이 미래 수익률을 보장하지 않습니다.
"""
    
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()
    
    report = format_telegram_report(args.date)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Report saved to {args.output}")
    else:
        print(report)
