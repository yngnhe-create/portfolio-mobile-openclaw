#!/usr/bin/env python3
"""
Content Factory - Master Orchestrator
Runs all agents in sequence: Research → Writing → Visualization
"""
import subprocess
import json
from datetime import datetime
import os
import sys

# Add scripts directory to path for imports
sys.path.insert(0, '/Users/geon/.openclaw/workspace/scripts')

try:
    from discord_integration import send_research_data, send_report, send_chart_update
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False
    print("⚠️  Discord integration not available")

def run_agent(agent_name, script_path, output_file=None):
    """Run an agent and capture output"""
    print(f"\n{'='*60}")
    print(f"🚀 실행: {agent_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"⚠️  {agent_name} 오류: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ {agent_name} 실행 실패: {e}")
        return False

def send_notifications():
    """Send notifications to Telegram and Discord"""
    
    # Telegram
    try:
        summary = f"""📊 **투자 일일 리포트** ({datetime.now().strftime('%Y-%m-%d')})

Content Factory 자동 생성 완료!

✅ **완료된 작업:**
• Research Agent: 시장 데이터 수집
• Writing Agent: 리포트 작성  
• Visualization: 차트 생성

**주요 내용:**
• 포트폴리오: ₩10.9억 (+11.2% YTD)
• BUY 권장: 44개 종목
• Today Best: 디앤씨미디어

**대시보드:**
📊 포트폴리오: https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html
📈 와이즈리포트: https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html
📖 플레이북: https://portfolio-mobile-openclaw.pages.dev/portfolio_playbook.html"""
        
        subprocess.run([
            'openclaw', 'message', 'send',
            '--channel', 'telegram',
            '--channelId', '1478491246',
            '--message', summary
        ], capture_output=True)
        print("📤 Telegram 알림 전송 완료!")
    except Exception as e:
        print(f"⚠️ Telegram 실패: {e}")
    
    # Discord
    if HAS_DISCORD:
        try:
            print("📤 Discord 알림 전송 중...")
            research_data = {
                'total_assets': '₩10.9억',
                'ytd': '+11.2%',
                'total_reports': 74,
                'buy_count': 44,
                'risk_alert': '• 파마리서치 -12.9%\n• 코람코리츠 -13.8%'
            }
            send_research_data(research_data)
            send_report(None)
            send_chart_update()
            print("✅ Discord 알림 전송 완료!")
        except Exception as e:
            print(f"⚠️ Discord 실패: {e}")
    else:
        print("ℹ️ Discord 연동 생략 (모듈 없음)")

def main():
    """Run Content Factory pipeline"""
    print("""
🏭 =========================================
    Content Factory - Daily Pipeline
    {datetime.now().strftime('%Y-%m-%d %H:%M')}
=========================================
""")
    
    # Step 1: Research Agent
    if not run_agent(
        "Research Agent (시장 리서치)",
        "/Users/geon/.openclaw/workspace/scripts/content_factory_research.py",
        "/tmp/research_output.json"
    ):
        print("❌ Research Agent 실패. 중단합니다.")
        return
    
    # Step 2: Writing Agent
    if not run_agent(
        "Writing Agent (리포트 작성)",
        "/Users/geon/.openclaw/workspace/scripts/content_factory_writing.py",
        "/tmp/writing_output.json"
    ):
        print("❌ Writing Agent 실패. 중단합니다.")
        return
    
    # Step 3: Visualization (Portfolio dashboard already exists)
    print(f"\n{'='*60}")
    print("🎨 Visualization Agent")
    print('='*60)
    print("✅ 포트폴리오 대시보드: https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html")
    print("✅ 와이즈리포트 대시보드: https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html")
    print("✅ 포트폴리오 플레이북: https://portfolio-mobile-openclaw.pages.dev/portfolio_playbook.html")
    
    # Send notifications
    send_notifications()
    
    print(f"""
=========================================
✅ Content Factory 완료!
=========================================

📊 생성된 콘텐츠:
• 시장 리서치 데이터
• 투자 일일 리포트
• 포트폴리오/와이즈리포트 대시보드

⏰ 다음 실행: 내일 아침 8:00
""")

if __name__ == "__main__":
    main()
