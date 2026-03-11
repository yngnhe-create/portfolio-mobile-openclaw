#!/usr/bin/env python3
"""
WiseReport Report Summary Scraper for 2026-03-07
Collects corporate and industry report data
"""

import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_wisereport():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔗 Accessing WiseReport...")
        await page.goto("https://wisereport.co.kr", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        # Login
        print("🔐 Logging in...")
        await page.fill("input[name='user_id']", "yngnhe")
        await page.fill("input[name='password']", "wldhs232")
        await page.click("button[type='submit']")
        
        await page.wait_for_timeout(3000)
        
        # Handle duplicate login popup if exists
        try:
            popup = await page.wait_for_selector("text=중복 로그인", timeout=5000)
            if popup:
                await page.click("button:has-text('확인')")
                print("✅ Handled duplicate login popup")
        except:
            print("✅ No duplicate login popup")
        
        await page.wait_for_timeout(3000)
        
        # Navigate to Report Summary
        print("📊 Navigating to Report Summary...")
        await page.goto("https://wisereport.co.kr/report/summary", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Collect data
        data = {
            "date": "2026-03-07",
            "scrape_time": datetime.now().isoformat(),
            "corporate_reports": [],
            "industry_reports": [],
            "top_picks": []
        }
        
        # Extract Top/Hot/Best section
        try:
            top_section = await page.query_selector(".top-picks, .highlight-section, .today-picks")
            if top_section:
                items = await top_section.query_selector_all(".item, .stock-item, .pick-item")
                for item in items[:10]:
                    try:
                        name = await item.query_selector_eval(".name, .stock-name", "el => el.textContent")
                        target = await item.query_selector_eval(".target, .target-price", "el => el.textContent")
                        opinion = await item.query_selector_eval(".opinion, .rating", "el => el.textContent")
                        
                        data["top_picks"].append({
                            "name": name.strip() if name else "",
                            "target_price": target.strip() if target else "",
                            "opinion": opinion.strip() if opinion else ""
                        })
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Error extracting top picks: {e}")
        
        # Extract corporate reports
        try:
            corp_tab = await page.query_selector("text=기업, .corporate-tab, #corp-tab")
            if corp_tab:
                await corp_tab.click()
                await page.wait_for_timeout(2000)
                
                reports = await page.query_selector_all(".report-item, .corporate-item")
                for report in reports[:20]:
                    try:
                        title = await report.query_selector_eval(".title", "el => el.textContent")
                        company = await report.query_selector_eval(".company, .stock-name", "el => el.textContent")
                        
                        data["corporate_reports"].append({
                            "company": company.strip() if company else "",
                            "title": title.strip() if title else ""
                        })
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Error extracting corporate reports: {e}")
        
        # Extract industry reports  
        try:
            ind_tab = await page.query_selector("text=산업, .industry-tab, #ind-tab")
            if ind_tab:
                await ind_tab.click()
                await page.wait_for_timeout(2000)
                
                reports = await page.query_selector_all(".report-item, .industry-item")
                for report in reports[:20]:
                    try:
                        title = await report.query_selector_eval(".title", "el => el.textContent")
                        sector = await report.query_selector_eval(".sector, .industry-name", "el => el.textContent")
                        
                        data["industry_reports"].append({
                            "sector": sector.strip() if sector else "",
                            "title": title.strip() if title else ""
                        })
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Error extracting industry reports: {e}")
        
        # Save data
        output_file = f"wisereport_summary_2026-03-07.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Data saved to {output_file}")
        print(f"📊 Top Picks: {len(data['top_picks'])}")
        print(f"📊 Corporate Reports: {len(data['corporate_reports'])}")
        print(f"📊 Industry Reports: {len(data['industry_reports'])}")
        
        await browser.close()
        return data

if __name__ == "__main__":
    result = asyncio.run(scrape_wisereport())
    print("\n🔍 Sample Data:")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
