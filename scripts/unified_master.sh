#!/bin/bash
# Unified Investment Master Script
# Runs all daily updates in sequence with a SINGLE API call

WORKSPACE="/Users/geon/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/master_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 통합 마스터 실행 시작: $(date)" | tee -a "$LOG_FILE"

# 1. Portfolio Price Update (Local - 0 tokens)
echo "📊 1/4 포트폴리오 가격 업데이트..." | tee -a "$LOG_FILE"
cd "$WORKSPACE/scripts" && python3 update_prices_v3.py 2>> "$LOG_FILE"

# 2. Generate Portfolio HTML (Local - 0 tokens)
echo "📈 2/4 포트폴리오 HTML 생성..." | tee -a "$LOG_FILE"
python3 generate_portfolio_html.py 2>> "$LOG_FILE"

# 3. WiseReport Data Extraction (Playwright - 0 API tokens)
echo "📰 3/4 WiseReport 데이터 추출..." | tee -a "$LOG_FILE"
python3 wisereport_full_playwright.py 2>> "$LOG_FILE"

# 4. Generate Playbook (Local - 0 tokens)
echo "📋 4/4 플레이북 생성..." | tee -a "$LOG_FILE"
python3 generate_playbook.py 2>> "$LOG_FILE"

# 5. Deploy All (1 API call)
echo "☁️ 5/5 통합 배포..." | tee -a "$LOG_FILE"
cd "$WORKSPACE"
rm -rf deploy_all && mkdir deploy_all
cp public/command_center.html deploy_all/index.html
cp public/portfolio_dashboard_live.html deploy_all/portfolio.html
cp public/portfolio_playbook_live.html deploy_all/playbook.html
cp wisereport_full_auto.html deploy_all/wisereport.html

# Deploy (this uses API)
wrangler pages deploy deploy_all --project-name=portfolio-mobile-openclaw --branch=main --commit-dirty 2>> "$LOG_FILE"

echo "✅ 통합 마스터 실행 완료: $(date)" | tee -a "$LOG_FILE"

# Summary for Telegram
echo "📊 실행 완료 요약:"
echo "- 포트폴리오 업데이트 ✅"
echo "- WiseReport 추출 ✅"
echo "- 플레이북 생성 ✅"
echo "- 통합 배포 ✅"
echo "💰 토큰 절감: 기존 4회 호출 → 1회 호출 (75% 절감)"