#!/usr/bin/env python3
"""
실시간 경제 뉴스 RSS 수집기
- 주요 경제/금융 뉴스 소스 자동 수집
- 핵심 키워드 필터링
- Telegram/Daily Report 연동
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse

class NewsRSSCrawler:
    def __init__(self):
        self.data_dir = Path("~/workspace/news_rss").expanduser()
        self.data_dir.parent.mkdir(parents=True, exist_ok=True)  # 부모 디렉토리 생성
        self.data_dir.mkdir(exist_ok=True)
        
        # RSS 피드 목록
        self.feeds = {
            "bloomberg": {
                "name": "Bloomberg",
                "url": "https://feeds.bloomberg.com/bloomberg/markets.rss",
                "category": "글로벌"
            },
            "reuters": {
                "name": "Reuters",
                "url": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
                "category": "글로벌"
            },
            "hankyung": {
                "name": "한국경제",
                "url": "https://www.hankyung.com/feed/economy",
                "category": "국내"
            },
            "mk": {
                "name": "매일경제",
                "url": "https://www.mk.co.kr/rss/50200011/",
                "category": "국내"
            },
            "chosun": {
                "name": "조선비즈",
                "url": "https://biz.chosun.com/site/data/rss/rss.xml",
                "category": "국내"
            },
            "edaily": {
                "name": "이데일리",
                "url": "https://www.edaily.co.kr/rss/Stock.xml",
                "category": "증시"
            },
            "fnnews": {
                "name": "파이낸셜뉴스",
                "url": "https://www.fnnews.com/rss/fn_realnews_stock.xml",
                "category": "증시"
            }
        }
        
        # 포트폴리오 관련 키워드
        self.keywords = {
            "삼성전자": ["삼성전자", "삼성", "samsung"],
            "SK하이닉스": ["SK하이닉스", "하이닉스", "sk hynix"],
            "반도체": ["반도체", "semiconductor", "HBM", "메모리", "chip"],
            "배터리": ["배터리", "이차전지", "ESS", "LG에너지", "삼성SDI"],
            "자동차": ["기아", "현대차", "자동차", "로봇"],
            "AI": ["AI", "인공지능", "엔비디아", "nvidia", "오픈AI"],
            "중동": ["이란", "이스라엘", "중동", "전쟁", "oil"],
            "금리": ["금리", "연준", "Fed", "FOMC", "인플레이션"],
            "원자재": ["유가", "금", "원자재", "commodity"],
            "리스크": ["폭락", "조정", "리스크", "위험", "경고"]
        }
    
    def fetch_rss(self, url, timeout=30):
        """RSS 피드 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except Exception as e:
            print(f"⚠️ RSS fetch error ({url}): {e}")
            return None
    
    def parse_rss(self, xml_content):
        """RSS XML 파싱"""
        if not xml_content:
            return []
        
        try:
            root = ET.fromstring(xml_content)
            
            # RSS 2.0
            items = root.findall('.//item')
            if items:
                return self._extract_items(items)
            
            # Atom
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns)
            if entries:
                return self._extract_atom_entries(entries, ns)
            
            return []
        except Exception as e:
            print(f"⚠️ RSS parse error: {e}")
            return []
    
    def _extract_items(self, items):
        """RSS 2.0 아이템 추출"""
        articles = []
        for item in items[:10]:  # 최신 10개만
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            desc = item.find('description')
            
            articles.append({
                "title": title.text if title is not None else "",
                "link": link.text if link is not None else "",
                "date": pub_date.text if pub_date is not None else "",
                "description": desc.text if desc is not None else "",
                "source": "RSS"
            })
        return articles
    
    def _extract_atom_entries(self, entries, ns):
        """Atom 엔트리 추출"""
        articles = []
        for entry in entries[:10]:
            title = entry.find('atom:title', ns)
            link = entry.find('atom:link', ns)
            pub_date = entry.find('atom:published', ns)
            
            articles.append({
                "title": title.text if title is not None else "",
                "link": link.get('href') if link is not None else "",
                "date": pub_date.text if pub_date is not None else "",
                "description": "",
                "source": "Atom"
            })
        return articles
    
    def extract_keywords(self, text):
        """텍스트에서 키워드 추출"""
        text_lower = text.lower()
        matched_keywords = []
        
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(category)
                    break
        
        return list(set(matched_keywords))
    
    def score_importance(self, article):
        """기사 중요도 점수화"""
        score = 0
        title_lower = article["title"].lower()
        
        # 포트폴리오 종목 언급
        portfolio_stocks = ["삼성전자", "SK하이닉스", "기아", "현대차", "파마리서치"]
        for stock in portfolio_stocks:
            if stock in article["title"]:
                score += 10
        
        # 핵심 키워드
        if any(k in title_lower for k in ["목표가", "상향", "buy", "매수"]):
            score += 5
        if any(k in title_lower for k in ["폭락", "경고", "리스크", "조정"]):
            score += 5
        if any(k in title_lower for k in ["반도체", "AI", "HBM", "배터리"]):
            score += 3
        
        # 키워드 매칭
        keywords = self.extract_keywords(article["title"] + " " + article["description"])
        score += len(keywords) * 2
        
        return score
    
    def collect_all(self):
        """모든 피드 수집"""
        all_articles = []
        
        print("📰 RSS 피드 수집 시작...")
        
        for feed_id, feed_info in self.feeds.items():
            print(f"  📡 {feed_info['name']} 수집 중...")
            
            xml = self.fetch_rss(feed_info["url"])
            articles = self.parse_rss(xml)
            
            for article in articles:
                article["feed"] = feed_info["name"]
                article["category"] = feed_info["category"]
                article["score"] = self.score_importance(article)
                article["keywords"] = self.extract_keywords(
                    article["title"] + " " + article["description"]
                )
            
            all_articles.extend(articles)
        
        # 중요도 순 정렬
        all_articles.sort(key=lambda x: x["score"], reverse=True)
        
        print(f"✅ 총 {len(all_articles)}개 기사 수집 완료")
        return all_articles
    
    def save_daily_summary(self, articles):
        """일일 요약 저장"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 상위 20개만
        top_articles = articles[:20]
        
        summary = {
            "date": today,
            "total_collected": len(articles),
            "top_articles": top_articles,
            "high_score_articles": [a for a in articles if a["score"] >= 10][:10]
        }
        
        output_file = self.data_dir / f"news_summary_{today}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📁 저장 완료: {output_file}")
        return summary
    
    def generate_markdown_report(self, summary):
        """마크다운 리포트 생성"""
        today = summary["date"]
        
        md = f"""# 📰 경제 뉴스 데일리 리포트 ({today})

## 📊 수집 현황
- 총 수집 기사: {summary['total_collected']}개
- 핵심 기사: {len(summary['high_score_articles'])}개

## 🔥 핵심 기사 (점수 10점 이상)
"""
        
        for article in summary['high_score_articles'][:5]:
            md += f"""
### [{article['title']}]({article['link']})
- **출처**: {article['feed']} ({article['category']})
- **키워드**: {', '.join(article['keywords']) if article['keywords'] else '없음'}
- **점수**: {article['score']}점
"""
        
        md += f"""

## 📰 주요 기사 Top 10
"""
        
        for i, article in enumerate(summary['top_articles'][:10], 1):
            md += f"""
{i}. [{article['title']}]({article['link']}) - {article['feed']}
   - 키워드: {', '.join(article['keywords']) if article['keywords'] else '없음'}
"""
        
        output_file = self.data_dir / f"news_report_{today}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"📄 리포트 생성: {output_file}")
        return output_file

def main():
    crawler = NewsRSSCrawler()
    
    # 수집
    articles = crawler.collect_all()
    
    # 저장
    summary = crawler.save_daily_summary(articles)
    
    # 리포트 생성
    report_file = crawler.generate_markdown_report(summary)
    
    # 결과 출력
    print("\n" + "="*50)
    print("📰 오늘의 핵심 뉴스 (Top 5)")
    print("="*50)
    
    for i, article in enumerate(summary['high_score_articles'][:5], 1):
        print(f"\n{i}. [{article['feed']}] {article['title']}")
        print(f"   키워드: {', '.join(article['keywords']) if article['keywords'] else '없음'}")
        print(f"   점수: {article['score']}점")
    
    print(f"\n📁 리포트: {report_file}")

if __name__ == "__main__":
    main()
