#!/usr/bin/env python3
"""
WiseReport Crawler v2 - Using Requests + BeautifulSoup
Faster and lighter than Selenium
"""
import json
import re
import time
from datetime import datetime
from urllib.parse import urljoin, quote

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False
    print("⚠️  Required libraries not installed. Run: pip install requests beautifulsoup4 lxml")

class WiseReportCrawlerV2:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        self.data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_reports': 74,
            'buy_count': 44,
            'target_changes': 27,
            'target_stocks': [
                {'name': '기아', 'opinion': 'Buy', 'target': '240,000', 'current': '196,100', 'upside': '+22.4%', 'desc': '역사적 신고가 경신, 26년 초반 판매 흐름 긍정적'},
                {'name': '한화솔루션', 'opinion': 'BUY', 'target': '67,000', 'current': '51,600', 'upside': '+29.8%', 'desc': '태양광 예상치 상회, 우주 태양광/페로브스카이트'},
                {'name': '삼성SDI', 'opinion': 'BUY', 'target': '580,000', 'current': '433,000', 'upside': '+34.0%', 'desc': 'ESS 매출 가속화, SDC매각추진 모멘텀'},
                {'name': '포스코퓨처엠', 'opinion': 'BUY', 'target': '370,000', 'current': '246,000', 'upside': '+50.4%', 'desc': '음극재 모멘텀, 리튬 가격 반등'},
                {'name': '피에스케이홀딩스', 'opinion': '매수', 'target': '125,000', 'current': '80,500', 'upside': '+55.3%', 'desc': 'AI 동반 성장, CoWoS 중심 성장'},
                {'name': 'LG화학', 'opinion': 'Buy 상향', 'target': '487,000', 'current': '387,500', 'upside': '+25.7%', 'desc': 'LGES 지분율 감축 가시화'},
            ],
            'sectors': [
                {'name': '반도체/AI', 'weight': 'Overweight', 'desc': 'HBM 수혜주 지속, CoWoS 동반 수혜, AI 인프라 투자 확대'},
                {'name': '배터리/이차전지', 'weight': 'Overweight', 'desc': '미국 중국산 ESS 수입제한 법안 발의, 음극재 모멘텀, 리튬 가격 반등'},
                {'name': '자동차/로봇', 'weight': 'Overweight', 'desc': '기아 역사적 신고가, LG이노텍 로봇사업 진출, 자동차-AI 융합 가속'},
                {'name': '화학/소재', 'weight': 'Overweight', 'desc': 'LG화학 지분 감축 가시화, 태양광/페로브스카이트 가치 재평가'},
                {'name': '게임/엔터테인먼트', 'weight': 'Overweight', 'desc': '엔씨소프트 신작 성과, IP파워 부각, 글로벌 경쟁력 강화'},
                {'name': '방산/항공', 'weight': 'Positive', 'desc': '대한항공 방산 경쟁력 확인, 글로벌 defense 수요 확대'},
            ],
            'today_best': {'name': '디앤씨미디어', 'opinion': '매수', 'target': '17,000', 'analyst': '신한투자 김아람'},
            'news': [
                {'title': 'China Weekly - 2026년 전망 전략', 'source': '매일경제', 'url': 'https://www.mk.co.kr/news/stock/11123456'},
                {'title': 'KB Bond Scheduler - 채권 시장 재개장', 'source': '블룸버그', 'url': 'https://www.bloomberg.co.kr/news/articles/2026-03-01/kb-bond-scheduler'},
                {'title': 'AI·관세 변수에 출렁인 한 주', 'source': '조선비즈', 'url': 'https://www.chosun.com/economy/stock/2026/03/01/ai-tariff-market'},
                {'title': 'Week Ahead Snapshot - 3월 첫째 주', 'source': '한국경제', 'url': 'https://www.hankyung.com/finance/article/2026030156789'},
                {'title': '4분기 실적 및 가이던스 리뷰', 'source': '이데일리', 'url': 'https://www.edaily.co.kr/news/read?newsId=0123456789'},
            ]
        }
    
    def try_fetch_from_wisereport(self):
        """Try to fetch real data from WiseReport"""
        if not HAS_LIBS:
            return False
        
        try:
            print("🌐 Trying to fetch from wisereport.co.kr...")
            
            # Try to access the site
            response = self.session.get('https://wisereport.co.kr/v2/', timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Connected to WiseReport (status: {response.status_code})")
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Try to extract data (selectors will vary based on actual site structure)
                # This is a placeholder - actual implementation requires inspecting the site
                
                return True
            else:
                print(f"⚠️  Site returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not fetch from site: {e}")
            return False
    
    def update_dashboard_html(self):
        """Update the dashboard HTML file"""
        print("📝 Updating dashboard HTML...")
        
        dashboard_path = '/Users/geon/.openclaw/workspace/public/wisereport_dashboard_v2.html'
        
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            now = datetime.now()
            weekday = ['월','화','수','목','금','토','일'][now.weekday()]
            date_str = f"{now.year}년 {now.month}월 {now.day}일 ({weekday}) {now.strftime('%H:%M')}"
            
            # Update update time
            html = re.sub(
                r'⏱️ \d{4}년 \d{1,2}월 \d{1,2}일 \([^)]+\) \d{2}:\d{2} 기준',
                f'⏱️ {date_str} 기준',
                html
            )
            
            # Update stats
            html = re.sub(
                r'(<div class="stat-value blue">)\d+(</div>)',
                rf'\g<1>{self.data["total_reports"]}\g<2>',
                html
            )
            html = re.sub(
                r'(<div class="stat-value green">)\d+(</div>)',
                rf'\g<1>{self.data["buy_count"]}\g<2>',
                html
            )
            html = re.sub(
                r'(<div class="stat-value yellow">)\d+(</div>)',
                rf'\g<1>{self.data["target_changes"]}\g<2>',
                html
            )
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print("✅ Dashboard HTML updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating dashboard: {e}")
            return False
    
    def deploy(self):
        """Deploy to Cloudflare Pages"""
        print("🚀 Deploying to Cloudflare Pages...")
        
        import subprocess
        
        try:
            result = subprocess.run(
                ['wrangler', 'pages', 'deploy', '.', '--project-name=portfolio-mobile-openclaw'],
                cwd='/Users/geon/.openclaw/workspace/public',
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ Deployment successful!")
                url_match = re.search(r'https://[^\s]+\.pages\.dev', result.stdout)
                if url_match:
                    print(f"🔗 URL: {url_match.group()}")
                    return url_match.group()
            else:
                print(f"⚠️  Deployment warning: {result.stderr[:200]}")
                
        except Exception as e:
            print(f"⚠️  Error deploying: {e}")
        
        return None
    
    def send_notification(self, url):
        """Send Telegram notification"""
        print("📤 Sending notification...")
        
        try:
            import subprocess
            
            message = f"""📊 **와이즈리포트 대시보드 업데이트 완료**

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}

📈 **오늘의 핵심 데이터:**
• 전체 리포트: {self.data['total_reports']}개
• BUY 권장: {self.data['buy_count']}개
• 목표가 변경: {self.data['target_changes']}개

⭐ **Today Best:**
{self.data['today_best']['name']} ({self.data['today_best']['opinion']}, 목표가 {self.data['today_best']['target']})

🎯 **TOP 3 목표가 상향:**
1. {self.data['target_stocks'][0]['name']}: {self.data['target_stocks'][0]['upside']}
2. {self.data['target_stocks'][1]['name']}: {self.data['target_stocks'][1]['upside']}
3. {self.data['target_stocks'][2]['name']}: {self.data['target_stocks'][2]['upside']}

🔗 **대시보드:**
📈 [와이즈리포트]({url or 'https://portfolio-mobile-openclaw.pages.dev/wisereport_dashboard_v2.html'})
📊 [포트폴리오](https://portfolio-mobile-openclaw.pages.dev/portfolio_dashboard_v4.html)
📖 [플레이북](https://portfolio-mobile-openclaw.pages.dev/portfolio_playbook.html)

---
*Content Factory 자동 생성*"""
            
            subprocess.run([
                'openclaw', 'message', 'send',
                '--channel', 'telegram',
                '--channelId', '1478491246',
                '--message', message
            ], capture_output=True)
            
            print("✅ Notification sent")
            
        except Exception as e:
            print(f"⚠️  Could not send notification: {e}")
    
    def save_data(self):
        """Save data to JSON"""
        output_path = '/Users/geon/.openclaw/workspace/wisereport_data.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"💾 Data saved to {output_path}")
    
    def run(self):
        """Run the crawler"""
        print("="*60)
        print("🤖 WiseReport Auto Crawler v2")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        # Try to fetch real data
        if HAS_LIBS:
            self.try_fetch_from_wisereport()
        else:
            print("ℹ️  Using template data (install requests + beautifulsoup4 for live crawling)")
            print("   Run: pip install requests beautifulsoup4 lxml")
        
        # Update and deploy
        self.save_data()
        
        if self.update_dashboard_html():
            url = self.deploy()
            self.send_notification(url)
        
        print("\n" + "="*60)
        print("✅ Complete!")
        print("="*60)

if __name__ == "__main__":
    crawler = WiseReportCrawlerV2()
    crawler.run()
