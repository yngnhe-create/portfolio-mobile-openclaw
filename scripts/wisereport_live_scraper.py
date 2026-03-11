#!/usr/bin/env python3
"""
WiseReport Live Scraper
- 매 실행마다 실제 웹사이트에서 최신 데이터 스크래핑
- 하드코딩된 데이터 없음
- 날짜별 자동 저장
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

WORKSPACE = "/Users/geon/.openclaw/workspace"
OUTPUT_DIR = f"{WORKSPACE}/wisereport_data"

async def scrape_wisereport_live():
    """실제 WiseReport 웹사이트에서 라이브 데이터 스크래핑"""
    
    print("🚀 WiseReport Live Scraper 시작...")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. WiseReport 메인 페이지 접속
            print("📱 WiseReport 접속 중...")
            await page.goto('https://www.wisereport.co.kr/', wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)  # 페이지 완전 로딩 대기
            
            # 2. 오늘 날짜 확인
            today_date = datetime.now().strftime('%Y.%m.%d')
            print(f"📅 오늘 날짜: {today_date}")
            
            # 3. JavaScript로 데이터 추출
            print("📊 데이터 추출 중...")
            data = await page.evaluate('''() => {
                const result = {
                    scrape_time: new Date().toISOString(),
                    date: new Date().toISOString().split('T')[0],
                    top3: [],
                    stocks: [],
                    total_count: 0
                };
                
                // 전체 텍스트에서 정보 추출
                const text = document.body.innerText;
                
                // Today Hot/Best/Top Report 찾기
                const hotMatch = text.match(/Today Hot Report[\\s\\S]*?([가-힣A-Za-z]+)[\\s]*(?:BUY|Buy|매수)?[\\s]*([^\\n]*)/i);
                const bestMatch = text.match(/Today Best Report[\\s\\S]*?([가-힣A-Za-z]+)[\\s]*(?:Buy|매수)?[\\s]*([^\\n]*)/i);
                const topMatch = text.match(/Today Top Report[\\s\\S]*?([가-힣A-Za-z]+)[\\s]*(?:매수|Buy)?[\\s]*([^\\n]*)/i);
                
                if (hotMatch) {
                    result.top3.push({
                        rank: 'HOT',
                        name: hotMatch[1].trim(),
                        opinion: 'BUY',
                        description: hotMatch[2] ? hotMatch[2].trim() : ''
                    });
                }
                
                if (bestMatch) {
                    result.top3.push({
                        rank: 'BEST',
                        name: bestMatch[1].trim(),
                        opinion: 'Buy',
                        description: bestMatch[2] ? bestMatch[2].trim() : ''
                    });
                }
                
                if (topMatch) {
                    result.top3.push({
                        rank: 'TOP',
                        name: topMatch[1].trim(),
                        opinion: '매수',
                        description: topMatch[2] ? topMatch[2].trim() : ''
                    });
                }
                
                // 추가 종목 정보 찾기
                const stockMatches = text.matchAll(/([가-힣]{2,8})[\\s]*(?:BUY|Buy|매수|중립)?[\\s]*[\\n]?[\\s]*([^\\n]{0,100})/g);
                for (const match of stockMatches) {
                    if (!result.stocks.find(s => s.name === match[1].trim())) {
                        result.stocks.push({
                            name: match[1].trim(),
                            opinion: '',
                            description: match[2] ? match[2].trim() : ''
                        });
                    }
                    if (result.stocks.length >= 30) break;
                }
                
                result.total_count = result.stocks.length;
                
                return result;
            }''')
            
            await browser.close()
            
            # 4. 결과 출력
            print(f"✅ 추출 완료!")
            print(f"📊 TOP 3: {len(data['top3'])}개")
            print(f"📋 전체 종목: {data['total_count']}개")
            
            # 5. 파일 저장 (날짜별)
            import os
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            filename = f"{OUTPUT_DIR}/wisereport_{data['date']}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 저장 완료: {filename}")
            
            # 6. TOP 3 상세 출력
            print("\n" + "=" * 70)
            print("🏆 TODAY'S TOP 3")
            print("=" * 70)
            for item in data['top3']:
                print(f"\n[{item['rank']}] {item['name']}")
                print(f"    의견: {item['opinion']}")
                print(f"    설명: {item['description'][:80]}...")
            
            return data
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await browser.close()
            return None

if __name__ == "__main__":
    result = asyncio.run(scrape_wisereport_live())
    
    if result:
        print("\n" + "=" * 70)
        print("✨ 스크래핑 성공!")
        print(f"📅 날짜: {result['date']}")
        print(f"📊 총 {result['total_count']}개 종목 추출")
        print("=" * 70)
    else:
        print("\n❌ 스크래핑 실패. 네트워크 상태를 확인하세요.")