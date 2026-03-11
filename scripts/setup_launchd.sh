#!/bin/bash

# WiseReport Launchd Auto-Setup for macOS
# This sets up a daily job at 7:00 AM using launchd

echo "🕖 WiseReport Launchd 설정을 시작합니다..."
echo ""

PLIST_NAME="com.openclaw.wisereport.daily"
PLIST_SOURCE="/Users/geon/.openclaw/workspace/scripts/${PLIST_NAME}.plist"
PLIST_DEST="~/Library/LaunchAgents/${PLIST_NAME}.plist"

# Check if plist exists
if [ ! -f "$PLIST_SOURCE" ]; then
    echo "❌ plist 파일을 찾을 수 없습니다: $PLIST_SOURCE"
    exit 1
fi

# Create LaunchAgents directory if needed
mkdir -p ~/Library/LaunchAgents
echo "✅ LaunchAgents 디렉토리 확인"

# Remove old version if exists
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "🔄 기존 작업 제거 중..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Copy plist file
cp "$PLIST_SOURCE" "$PLIST_DEST"
echo "✅ plist 파일 복사 완료"

# Load the launchd job
launchctl load "$PLIST_DEST"

if [ $? -eq 0 ]; then
    echo "✅ Launchd 작업 등록 완료!"
    echo ""
    echo "📋 설정 내용:"
    echo "  • 실행 시간: 매일 07:00 KST"
    echo "  • 설정 파일: $PLIST_DEST"
    echo "  • 로그 파일: /Users/geon/.openclaw/workspace/logs/launchd_wisereport.log"
    echo ""
    echo "🔍 등록된 작업 확인:"
    launchctl list | grep "$PLIST_NAME"
    echo ""
    echo "🧪 수동 테스트:"
    echo "  launchctl start $PLIST_NAME"
    echo ""
    echo "🛑 중지하려면:"
    echo "  launchctl unload ~/Library/LaunchAgents/${PLIST_NAME}.plist"
    echo ""
    echo "⏰ 다음 실행: 내일 07:00 KST"
else
    echo "❌ Launchd 작업 등록 실패"
    exit 1
fi