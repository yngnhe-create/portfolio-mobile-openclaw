#!/bin/bash

# WiseReport Cron Auto-Setup Script (Non-interactive)
# This script automatically sets up the daily 7:00 AM update without prompts

echo "🕖 WiseReport 자동 업데이트 설정을 시작합니다..."
echo ""

# Check if script exists
SCRIPT_PATH="/Users/geon/.openclaw/workspace/scripts/daily_wisereport_update.sh"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 스크립트를 찾을 수 없습니다: $SCRIPT_PATH"
    exit 1
fi

# Make script executable
chmod +x "$SCRIPT_PATH"
echo "✅ 스크립트 권한 설정 완료"

# Create logs directory
mkdir -p /Users/geon/.openclaw/workspace/logs
echo "✅ 로그 디렉토리 생성 완료"

# Get existing crontab
crontab -l 2>/dev/null > /tmp/current_cron.txt || true

# Remove old entry if exists
grep -v "daily_wisereport_update" /tmp/current_cron.txt > /tmp/new_cron.txt 2>/dev/null || touch /tmp/new_cron.txt

# Add new cron job
echo "" >> /tmp/new_cron.txt
echo "# WiseReport Daily Auto-Update - 7:00 AM KST" >> /tmp/new_cron.txt
echo "0 7 * * * $SCRIPT_PATH >> /Users/geon/.openclaw/workspace/logs/cron_wisereport.log 2>&1" >> /tmp/new_cron.txt

# Apply new crontab
crontab /tmp/new_cron.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 크론 작업 등록 완료!"
    echo ""
    echo "📋 설정 내용:"
    echo "  • 실행 시간: 매일 07:00 KST"
    echo "  • 실행 스크립트: $SCRIPT_PATH"
    echo "  • 로그 파일: /Users/geon/.openclaw/workspace/logs/cron_wisereport.log"
    echo ""
    echo "🔍 등록된 크론 작업:"
    crontab -l | grep -A1 "WiseReport"
    echo ""
    echo "🧪 수동 테스트 명령어:"
    echo "  $SCRIPT_PATH"
    echo ""
    echo "🗑️ 삭제하려면:"
    echo "  crontab -e"
    echo "  (해당 라인 삭제 후 저장)"
else
    echo "❌ 크론 작업 등록 실패"
    exit 1
fi

# Cleanup
rm -f /tmp/current_cron.txt /tmp/new_cron.txt