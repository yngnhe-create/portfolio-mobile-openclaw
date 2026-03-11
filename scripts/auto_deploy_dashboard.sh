#!/bin/bash
# 이란 대시보드 자동 업데이트 및 배포 스크립트
# 4시간마다 실행

LOG_FILE="/Users/geon/.openclaw/workspace/logs/iran_dashboard.log"
DATE=$(date '+%Y-%m-%d %H:%M')

echo "[$DATE] 업데이트 시작" >> $LOG_FILE

# 1. 데이터 수집 및 HTML 업데이트
/usr/bin/python3 /Users/geon/.openclaw/workspace/scripts/update_iran_dashboard.py >> $LOG_FILE 2>&1

# 2. GitHub에 푸시
cd /Users/geon/.openclaw/workspace/public/iran-dashboard

git add .
git commit -m "Auto update: $DATE"
git push https://${GITHUB_TOKEN}@github.com/yngnhe-create/iran-dashboard-kr.git main >> $LOG_FILE 2>&1

echo "[$DATE] 업데이트 완료" >> $LOG_FILE