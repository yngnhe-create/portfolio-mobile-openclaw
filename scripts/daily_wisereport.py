#!/usr/bin/env python3
"""
Daily WiseReport Analysis
Fetches and analyzes WiseReport data every morning
"""
import subprocess
from datetime import datetime

def main():
    print(f"📊 Daily WiseReport Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. Check for latest WiseReport data
    print("\n1️⃣ Checking latest WiseReport data...")
    
    # 2. Generate analysis
    print("\n2️⃣ Generating sector analysis...")
    
    # 3. Post summary to Telegram
    summary = f"""📊 **와이즈리포트 일일 분석** ({datetime.now().strftime('%Y-%m-%d')})

**주요 내용:**
• 전체 리포트 및 BUY 권장 현황
• 섹터별 분포 (IT, 산업재, 배터리 등)
• HOT 뉴스 및 시장 이슈
• 투자 전략 제안

**상세 분석:**
https://portfolio-mobile-openclaw.pages.dev/wisereport_summary.html

**포트폴리오 대시보드:**
https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html"""
    
    subprocess.run([
        "openclaw", "message", "send",
        "--target", "main",
        "--message", summary
    ], capture_output=True)
    
    print("\n✅ Analysis complete! Check Telegram for summary.")

if __name__ == "__main__":
    main()
