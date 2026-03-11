#!/usr/bin/env python3
"""
Yellow.kr 경제 게시판 모니터링 스크립트
- 매일 최신 글 체크
- 새 글 있으면 요약 저장
- 리포트 페이지에 반영
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
import urllib.request
from html.parser import HTMLParser

class YellowKRCrawler:
    def __init__(self):
        self.base_url = "https://yellow.kr/blog/economy-board/"
        self.data_dir = Path("~/workspace/yellow_monitor").expanduser()
        self.data_dir.mkdir(exist_ok=True)
        self.state_file = self.data_dir / "last_check.json"
        self.summary_file = self.data_dir / "daily_summary.json"
        
    def load_last_state(self):
        """마지막 체크 상태 로드"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"last_check": "", "last_uid": 0, "checked_posts": []}
    
    def save_state(self, state):
        """상태 저장"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def fetch_board(self):
        """게시판 목록 가져오기"""
        try:
            req = urllib.request.Request(
                self.base_url,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching board: {e}")
            return None
    
    def parse_posts(self, html):
        """게시글 목록 파싱"""
        posts = []
        # 정규식으로 게시글 목록 추출
        pattern = r'<a href="(/blog/economy-board/\?mod=document&uid=(\d+))"[^>]*>\s*\[New\s+([^\]]+)\]</a>'
        matches = re.findall(pattern, html)
        
        for match in matches[:10]:  # 최신 10개만
            url_path, uid, title = match
            posts.append({
                "uid": int(uid),
                "title": title.strip(),
                "url": f"https://yellow.kr{url_path}",
                "is_new": True
            })
        
        return posts
    
    def fetch_post_content(self, url):
        """개별 글 내용 가져오기"""
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')
                # 본문 추출 (간단한 파싱)
                content_match = re.search(r'<div class="document-content">(.*?)</div>', html, re.DOTALL)
                if content_match:
                    content = content_match.group(1)
                    # HTML 태그 제거
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    return content[:2000]  # 2000자까지만
                return ""
        except Exception as e:
            print(f"Error fetching post {url}: {e}")
            return ""
    
    def summarize_content(self, title, content):
        """내용 요약 (간단 키워드 추출)"""
        keywords = []
        
        # 투자 관련 키워드 체크
        investment_keywords = {
            "반도체": ["반도체", "삼성전자", "SK하이닉스", "HBM", "메모리"],
            "AI": ["AI", "인공지능", "엔비디아", "오라클", "클로드"],
            "배터리": ["배터리", "ESS", "이차전지", "LG에너지", "삼성SDI"],
            "자동차": ["기아", "현대차", "자동차", "로봇"],
            "리스크": ["리스크", "위험", "폭락", "조정", "경고"],
            "매수": ["매수", "Buy", "투자", "상승"],
            "금리": ["금리", "연준", "FOMC", "인플레이션"]
        }
        
        full_text = f"{title} {content}".lower()
        
        for category, words in investment_keywords.items():
            for word in words:
                if word.lower() in full_text:
                    keywords.append(category)
                    break
        
        return list(set(keywords)) if keywords else ["일반"]
    
    def check_new_posts(self):
        """새 글 체크"""
        state = self.load_last_state()
        html = self.fetch_board()
        
        if not html:
            return None
        
        posts = self.parse_posts(html)
        new_posts = []
        
        for post in posts:
            if post["uid"] > state.get("last_uid", 0):
                # 새 글 내용 가져오기
                content = self.fetch_post_content(post["url"])
                post["content"] = content[:500]  # 요약
                post["keywords"] = self.summarize_content(post["title"], content)
                post["checked_at"] = datetime.now().isoformat()
                new_posts.append(post)
        
        if new_posts:
            # 상태 업데이트
            state["last_uid"] = max(p["uid"] for p in new_posts)
            state["last_check"] = datetime.now().isoformat()
            state["checked_posts"] = state.get("checked_posts", []) + [p["uid"] for p in new_posts]
            self.save_state(state)
            
            # 일일 요약 저장
            self.save_daily_summary(new_posts)
            
            return new_posts
        
        return []
    
    def save_daily_summary(self, posts):
        """일일 요약 저장"""
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "checked_at": datetime.now().isoformat(),
            "new_count": len(posts),
            "posts": posts
        }
        
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📊 {len(posts)}개 새 글 저장 완료")
    
    def get_portfolio_impact(self):
        """포트폴리오 영향 분석"""
        if not self.summary_file.exists():
            return None
        
        with open(self.summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        impact_keywords = {
            "반도체": ["삼성전자", "SK하이닉스", "파마리서치"],
            "배터리": ["삼성SDI", "LG에너지솔루션", "포스코퓨처엠"],
            "자동차": ["기아", "현대차"],
            "리츠": ["코람코"]
        }
        
        alerts = []
        for post in summary.get("posts", []):
            for keyword in post.get("keywords", []):
                if keyword in impact_keywords:
                    alerts.append({
                        "title": post["title"],
                        "keyword": keyword,
                        "stocks": impact_keywords[keyword],
                        "url": post["url"]
                    })
        
        return alerts

def main():
    crawler = YellowKRCrawler()
    print("🕵️ Yellow.kr 모니터링 시작...")
    
    new_posts = crawler.check_new_posts()
    
    if new_posts is None:
        print("❌ 게시판 접속 실패")
        return
    
    if new_posts:
        print(f"\n🆕 {len(new_posts)}개 새 글 발겱:")
        for post in new_posts:
            print(f"  • [{post['uid']}] {post['title']}")
            print(f"    키워드: {', '.join(post['keywords'])}")
            print(f"    URL: {post['url']}")
        
        # 포트폴리오 영향 분석
        alerts = crawler.get_portfolio_impact()
        if alerts:
            print(f"\n⚠️ 포트폴리오 관련 알림 {len(alerts)}건:")
            for alert in alerts:
                print(f"  • [{alert['keyword']}] {alert['title']}")
                print(f"    관련종목: {', '.join(alert['stocks'])}")
    else:
        print("✅ 새 글 없음")
    
    print(f"\n📁 저장 위치: {crawler.data_dir}")

if __name__ == "__main__":
    main()
