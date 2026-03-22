#!/usr/bin/env python3
"""뉴스 RSS 수집기 - Google News에서 한국 경제 뉴스 가져와 JSON 저장"""

import json
import urllib.request
import urllib.parse
import ssl
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "public" / "data" / "news_latest.json"

RSS_URLS = [
    "https://news.google.com/rss/search?q=코스피+주식+경제+증시&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=삼성전자+OR+현대차+OR+비트코인+OR+반도체&hl=ko&gl=KR&ceid=KR:ko",
]

PORTFOLIO_KEYS = {
    "삼성전자": ["삼성전자", "삼성", "samsung", "반도체", "HBM", "메모리"],
    "BTC": ["비트코인", "bitcoin", "btc", "가상화폐", "암호화폐", "코인"],
    "현대차": ["현대차", "현대자동차", "hyundai", "기아"],
    "NVIDIA": ["엔비디아", "nvidia", "nvda", "AI칩"],
    "테슬라": ["테슬라", "tesla", "전기차", "EV"],
    "채권": ["금리", "연준", "Fed", "FOMC", "국채", "기준금리"],
    "원유": ["유가", "oil", "원유", "중동", "이란", "호르무즈"],
    "환율": ["환율", "달러", "원화"],
    "리츠": ["부동산", "리츠", "REIT", "임대", "건설"],
}

CATEGORIES = {
    "HIGH_IMPACT": {"color": "#ff4757", "label": "🔴 HIGH IMPACT", "keys": ["폭락","급락","전쟁","위기","제재","관세","폭등","사상최고","긴급","속보"]},
    "MARKET": {"color": "#f9ca24", "label": "🟡 MARKET", "keys": ["실적","목표가","상향","하향","분기","매출","영업이익","컨센서스"]},
    "POSITIVE": {"color": "#4ecdc4", "label": "🟢 POSITIVE", "keys": ["급등","호재","상승","성장","신고가","수혜","호실적"]},
    "CRYPTO": {"color": "#a55eea", "label": "🟣 CRYPTO", "keys": ["비트코인","이더리움","코인","가상자산","암호화폐"]},
    "MACRO": {"color": "#0984e3", "label": "🔵 MACRO", "keys": ["금리","연준","Fed","CPI","고용","GDP","인플레","환율","무역"]},
}

def fetch_url(url):
    ctx = ssl.create_default_context()
    # Encode non-ASCII characters in URL
    parts = urllib.parse.urlsplit(url)
    encoded_query = urllib.parse.quote(parts.query, safe="=&+")
    encoded_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, encoded_query, parts.fragment))
    req = urllib.request.Request(encoded_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return r.read().decode("utf-8", errors="ignore")

def clean_title(title):
    # Google News adds " - Source Name" at end
    parts = title.rsplit(" - ", 1)
    return parts[0].strip() if len(parts) > 1 else title.strip()

def categorize(title):
    lower = title.lower()
    for cat_id, cat in CATEGORIES.items():
        for k in cat["keys"]:
            if k.lower() in lower:
                return {"label": cat["label"], "color": cat["color"]}
    return {"label": "📋 GENERAL", "color": "#8b9dc3"}

def find_impacts(title):
    lower = title.lower()
    impacts = []
    for asset, keywords in PORTFOLIO_KEYS.items():
        for k in keywords:
            if k.lower() in lower:
                impacts.append(asset)
                break
    return list(set(impacts))

def main():
    all_articles = []
    seen = set()

    for rss_url in RSS_URLS:
        try:
            xml_text = fetch_url(rss_url)
            root = ET.fromstring(xml_text)
            items = root.findall(".//item")
            for item in items:
                raw_title = item.find("title").text or ""
                title = clean_title(raw_title)
                if not title or title in seen:
                    continue
                seen.add(title)
                link = item.find("link").text or ""
                pub_date = item.find("pubDate").text or ""
                source_el = item.find("source")
                source = source_el.text if source_el is not None else ""
                all_articles.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "source": source,
                })
        except Exception as e:
            print(f"  RSS 오류: {e}")

    # Sort by date descending, take top 10
    def parse_date(art):
        try:
            return parsedate_to_datetime(art.get("pubDate", ""))
        except Exception:
            return datetime.min
    all_articles.sort(key=parse_date, reverse=True)
    articles = []
    for art in all_articles[:10]:
        cat = categorize(art["title"])
        impacts = find_impacts(art["title"])
        articles.append({
            **art,
            "category": cat,
            "impacts": impacts,
        })

    output = {
        "timestamp": datetime.now().isoformat(),
        "count": len(articles),
        "articles": articles,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"  {len(articles)}개 뉴스 저장: {OUTPUT}")

if __name__ == "__main__":
    print(f"📰 뉴스 수집 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    main()
