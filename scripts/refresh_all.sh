#!/bin/bash
# 전체 데이터 현행화 스크립트
# 시장 데이터 + 뉴스 + WiseReport + Git 배포

WORKSPACE="/Users/geon/.openclaw/workspace"
LOG="$WORKSPACE/logs/refresh_all.log"
PYTHON="/usr/bin/python3"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$WORKSPACE/logs"
echo "[$DATE] === 전체 현행화 시작 ===" >> "$LOG"

# 1. 시장 데이터 (KOSPI, KOSDAQ, NASDAQ, S&P500, USD/KRW)
echo "[$DATE] 📈 시장 데이터 수집..." >> "$LOG"
$PYTHON "$WORKSPACE/scripts/market_data_fetcher.py" >> "$LOG" 2>&1
echo "[$DATE]   → market_latest.json 완료" >> "$LOG"

# 2. 뉴스 수집
echo "[$DATE] 📰 뉴스 수집..." >> "$LOG"
$PYTHON "$WORKSPACE/scripts/news_fetcher.py" >> "$LOG" 2>&1
echo "[$DATE]   → news_latest.json 완료" >> "$LOG"

# 3. WiseReport (평일 장시간만 실행 - 주말/공휴일은 스킵)
DOW=$(date +%u)  # 1=Mon ... 7=Sun
HOUR=$(date +%H)
if [ "$DOW" -le 5 ] && [ "$HOUR" -ge 8 ] && [ "$HOUR" -le 18 ]; then
  echo "[$DATE] 📋 WiseReport 수집..." >> "$LOG"
  $PYTHON "$WORKSPACE/scripts/wisereport_auto.py" >> "$LOG" 2>&1
  echo "[$DATE]   → wisereport_latest.json 완료" >> "$LOG"
else
  echo "[$DATE] ⏭️  WiseReport 스킵 (주말/장외시간)" >> "$LOG"
fi

# 4. Git push
echo "[$DATE] 🚀 GitHub 배포..." >> "$LOG"
cd "$WORKSPACE"
git add public/data/market_latest.json public/data/news_latest.json public/data/wisereport_latest.json 2>> "$LOG"
git diff --cached --quiet
if [ $? -ne 0 ]; then
  git commit -m "auto: 데이터 현행화 $DATE" >> "$LOG" 2>&1
  git push origin main >> "$LOG" 2>&1
  echo "[$DATE]   → GitHub 푸시 완료" >> "$LOG"
else
  echo "[$DATE]   → 변경 없음, 스킵" >> "$LOG"
fi

DATE_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$DATE_END] === 전체 현행화 완료 ===" >> "$LOG"
echo "" >> "$LOG"
