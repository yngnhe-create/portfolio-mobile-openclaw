#!/bin/bash
# 뉴스 수집 + Telegram 발송 + HTML 업데이트 통합 스크립트
# 매일 08:00 실행

echo "🚀 뉴스 리포트 자동화 시작..."
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"

# 1. RSS 수집
echo "📰 1/3 RSS 수집 중..."
python3 ~/.openclaw/workspace/scripts/news_rss_crawler.py

# 2. Telegram 발송
echo "📱 2/3 Telegram 발송 중..."
python3 ~/.openclaw/workspace/scripts/send_news_telegram.py

# 3. HTML 대시보드 업데이트 (선택)
echo "🌐 3/3 HTML 대시보드 업데이트 중..."
python3 ~/.openclaw/workspace/scripts/build_wisereport_v3.py 2>/dev/null || echo "  (대시보드 업데이트 스킵)"

echo "✅ 완료: $(date '+%H:%M:%S')"
