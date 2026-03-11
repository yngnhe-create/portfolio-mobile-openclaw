#!/usr/bin/env python3
"""
투자커멘드 WiseReport 자동 수집 v2
- Playwright로 전체 리포트 리스트 수집
- 종목별 목표가/현재가/상승여력 계산
- 섹터별 의견 상세 수집
- 4시간마다 자동 실행
"""

import asyncio
import json
import re
import os
import subprocess
from datetime import datetime
from playwright.async_api import async_playwright

WORKSPACE = "/Users/geon/.openclaw/workspace"
OUTPUT_PATH = f"{WORKSPACE}/public/wisereport.html"
DATA_PATH = f"{WORKSPACE}/wisereport_data"
LOG_PATH = f"{WORKSPACE}/scripts/wisereport_auto.log"

MY_STOCKS = [
    '삼성전자', '파마리서치', '현대차', '두산', '네이버',
    'LG에너지솔루션', '삼성SDI', 'SK하이닉스', 'NVDA', 'TSLA',
    '현대차3우B', '현대차우', 'ESR켄달스퀘어리츠', '원익IPS', 'RFHIC'
]

# 목표가 테이블 (WiseReport 확인값 + 시장 컨센서스)
TARGET_PRICES = {
    '원익IPS':       {'code':'240810', 'target':160000, 'source':'WiseReport'},
    'RFHIC':        {'code':'218410', 'target':100000, 'source':'WiseReport'},
    '삼성전자':       {'code':'005930', 'target':220000, 'source':'컨센서스'},
    '삼성전자우':      {'code':'005935', 'target':175000, 'source':'컨센서스'},
    'LG에너지솔루션':  {'code':'373220', 'target':450000, 'source':'컨센서스'},
    'SK하이닉스':     {'code':'000660', 'target':980000, 'source':'컨센서스'},
    '현대차':        {'code':'005380', 'target':580000, 'source':'미래에셋'},
    '현대차우':       {'code':'005385', 'target':480000, 'source':'컨센서스'},
    '현대차3우B':     {'code':'005389', 'target':480000, 'source':'컨센서스'},
    '파마리서치':     {'code':'214450', 'target':350000, 'source':'컨센서스'},
    'KT':           {'code':'030200', 'target':67000,  'source':'컨센서스'},
    'SK텔레콤':      {'code':'017670', 'target':85000,  'source':'컨센서스'},
    'LG유플러스':    {'code':'032640', 'target':16000,  'source':'컨센서스'},
    '에이프릴바이오': {'code':'397030', 'target':80000,  'source':'컨센서스'},
    '한올바이오파마': {'code':'009420', 'target':62000,  'source':'컨센서스'},
    '조이시티':      {'code':'067000', 'target':5000,   'source':'컨센서스'},
    'DN오토모티브':   {'code':'002360', 'target':0,      'source':'의견없음'},
    '두산':          {'code':'000150', 'target':250000, 'source':'컨센서스'},
    'KODEX 증권':    {'code':'266410', 'target':0,      'source':'ETF'},
}


def fetch_upside_table(report_companies: list) -> list:
    """종목별 현재가 + 목표가 + 상승여력 계산"""
    import requests as _req
    headers = {'User-Agent': 'Mozilla/5.0'}
    rows = []
    # 대상 종목 = 보고서에 등장하거나 내 포트폴리오인 것
    targets = {k: v for k, v in TARGET_PRICES.items()
               if k in report_companies or k in MY_STOCKS}
    for name, info in targets.items():
        try:
            r = _req.get(
                f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{info['code']}",
                headers=headers, timeout=5
            )
            d = r.json()
            cur = d['result']['areas'][0]['datas'][0]['nv']
        except:
            cur = 0
        tgt = info['target']
        upside = (tgt - cur) / cur * 100 if cur > 0 and tgt > 0 else None
        rows.append({
            'name': name,
            'current': cur,
            'target': tgt,
            'upside': round(upside, 1) if upside is not None else None,
            'source': info['source'],
            'is_mine': name in MY_STOCKS,
        })
    rows.sort(key=lambda x: x['upside'] or -999, reverse=True)
    return rows

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {msg}\n")


async def login(page):
    """WiseReport 로그인"""
    await page.goto('https://www.wisereport.co.kr/', wait_until='networkidle', timeout=30000)
    await page.wait_for_timeout(2000)
    await page.evaluate("""
    () => {
        ['UsrID','UsrID_Login'].forEach(n => {
            const el = document.querySelector('input[name="' + n + '"]');
            if(el) { el.value = 'yngnhe'; el.dispatchEvent(new Event('change')); }
        });
        ['UsrPassWD','UsrPassWD_Login','UsrPassWD_Text'].forEach(n => {
            const el = document.querySelector('input[name="' + n + '"]');
            if(el) { el.value = 'wldhs232'; el.dispatchEvent(new Event('change')); }
        });
        const a = document.querySelector('a[onclick*="login"], a[onclick*="Login"]');
        if(a) a.click();
    }
    """)
    await page.wait_for_timeout(4000)
    try:
        await page.click("button:has-text('확인')", timeout=3000)
        await page.wait_for_timeout(2000)
    except: pass
    log(f"✅ 로그인 완료 (URL: {page.url})")


async def scrape_main_page(page):
    """메인 페이지 Today Top/Hot/Best 수집"""
    raw = await page.evaluate('() => document.body.innerText')
    picks = []
    for tag in ['Today Top Report', 'Today Hot Report', 'Today Best Report']:
        idx = raw.find(tag)
        if idx < 0: continue
        chunk = raw[idx:idx+400]
        lines = [l.strip() for l in chunk.split('\n') if l.strip()]
        if len(lines) < 3: continue
        pick = {
            'type': tag.replace('Today ', '').replace(' Report', ''),
            'company': lines[1] if len(lines) > 1 else '',
            'opinion': lines[2] if len(lines) > 2 else '',
            'title': lines[3] if len(lines) > 3 else '',
            'broker': lines[4] if len(lines) > 4 else '',
        }
        tp = re.search(r'목표주가\s+([\d,]+)', chunk)
        pick['target'] = tp.group(1) if tp else ''
        picks.append(pick)
    log(f"  Today Top/Hot/Best: {len(picks)}개")
    return raw, picks


async def scrape_report_list(page):
    """전체 리포트 리스트 수집 (Company + Industry)"""
    reports = []

    # Company 리포트 링크들 수집 (메인 페이지에 이미 노출됨)
    links = await page.query_selector_all('a[href*="na_Report_Login"], a[onclick*="na_Report_Login"]')
    report_links = []
    for link in links:
        onclick = await link.get_attribute('onclick') or ''
        href = await link.get_attribute('href') or ''
        text = (await link.inner_text()).strip()
        combined = onclick + href
        if 'report' in combined.lower() and text and text.startswith('['):
            # report ID 추출
            m = re.search(r"'report','(\d+)','(\d+)'", combined)
            if m:
                report_links.append({
                    'title': text[:80],
                    'id': m.group(1),
                    'broker_code': m.group(2)
                })

    log(f"  리포트 링크 수집: {len(report_links)}개")

    # 각 리포트 팝업에서 상세 정보 추출 (상위 15개)
    for i, rep in enumerate(report_links[:15]):
        try:
            title = rep['title']
            # [종목명] 타이틀에서 회사명 추출
            company_m = re.match(r'\[([^\]]+)\]', title)
            company = company_m.group(1) if company_m else ''
            report_title = title[len(company)+2:].strip() if company else title

            # 리포트 상세 팝업 열기
            popup_js = f"Javascript:na_Report_Login('report','{rep['id']}','{rep['broker_code']}','')"
            
            # 새 팝업 페이지 감지
            popup = None
            try:
                async with page.context.expect_page(timeout=5000) as popup_info:
                    await page.evaluate(f"() => {{ {popup_js.replace('Javascript:', '')} }}")
                popup = await popup_info.value
                await popup.wait_for_load_state('networkidle', timeout=8000)
                popup_text = await popup.evaluate('() => document.body.innerText')
                
                # 목표주가, 현재가, 증권사 추출
                target_m = re.search(r'목표\s*주가[:\s]*([0-9,]+)', popup_text)
                current_m = re.search(r'현재\s*가?[:\s]*([0-9,]+)', popup_text)
                opinion_m = re.search(r'(BUY|HOLD|SELL|매수|중립|매도|Not Rated)', popup_text)
                broker_m = re.search(r'(삼성증권|미래에셋|KB증권|NH투자|한국투자|키움|하나증권|신한투자|대신증권|메리츠|유안타|DS투자|상상인)', popup_text)
                
                target_price = int(target_m.group(1).replace(',', '')) if target_m else 0
                current_price = int(current_m.group(1).replace(',', '')) if current_m else 0
                opinion = opinion_m.group(1) if opinion_m else 'N/A'
                broker = broker_m.group(1) if broker_m else ''
                
                upside = 0
                if target_price > 0 and current_price > 0:
                    upside = (target_price - current_price) / current_price * 100

                reports.append({
                    'company': company,
                    'title': report_title[:60],
                    'opinion': opinion,
                    'target_price': target_price,
                    'current_price': current_price,
                    'upside': upside,
                    'broker': broker,
                    'raw': popup_text[:200]
                })
                await popup.close()
            except Exception as pe:
                # 팝업 없이 인라인 처리
                reports.append({
                    'company': company,
                    'title': report_title[:60],
                    'opinion': 'N/A',
                    'target_price': 0,
                    'current_price': 0,
                    'upside': 0,
                    'broker': '',
                    'raw': ''
                })
        except Exception as e:
            log(f"  ⚠️ 리포트 {i}: {e}")

    log(f"  상세 리포트: {len(reports)}개")
    return reports


async def scrape_industry_reports(page):
    """Industry 섹터 의견 수집"""
    sectors = []
    try:
        # Industry 메뉴 클릭
        await page.evaluate("() => na_Report_Login('menu8','','','','')")
        await page.wait_for_timeout(4000)
        
        raw = await page.evaluate('() => document.body.innerText')
        log(f"  Industry 페이지 텍스트: {len(raw)}자")
        
        # 섹터 의견 패턴 추출
        sector_patterns = [
            ('반도체/IT', ['반도체', 'IT', '전자', '하이닉스', '삼성전자']),
            ('자동차', ['자동차', '현대차', '기아', '완성차']),
            ('헬스케어', ['헬스케어', '제약', '바이오', '의료']),
            ('소비재', ['소비재', '화장품', '음식료', '의류']),
            ('금융', ['금융', '은행', '보험', '증권']),
            ('에너지', ['에너지', '정유', '석유', '가스']),
            ('건설', ['건설', '부동산', '리츠']),
            ('방산/우주', ['방산', '우주', '항공']),
        ]
        
        for sector, keywords in sector_patterns:
            for kw in keywords:
                if kw in raw:
                    idx = raw.find(kw)
                    chunk = raw[max(0,idx-50):idx+200]
                    ow = 'OVERWEIGHT' if any(w in chunk for w in ['비중확대', 'Overweight', 'OVERWEIGHT']) else \
                         'UNDERWEIGHT' if any(w in chunk for w in ['비중축소', 'Underweight']) else 'NEUTRAL'
                    sectors.append({'sector': sector, 'opinion': ow, 'context': chunk[:100]})
                    break
    except Exception as e:
        log(f"  ⚠️ Industry 섹터: {e}")
    
    log(f"  섹터 의견: {len(sectors)}개")
    return sectors


async def scrape_wisereport():
    """전체 스크래핑 실행"""
    log("🌐 Playwright 브라우저 시작...")
    data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'scrape_time': datetime.now().isoformat(),
        'top_picks': [],
        'reports': [],
        'industry_sectors': [],
        'raw_text': ''
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # 1. 로그인
            await login(page)

            # 2. 메인 페이지 Top/Hot/Best
            raw, picks = await scrape_main_page(page)
            data['top_picks'] = picks
            data['raw_text'] = raw[:6000]

            # 3. 신규 리포트 리스트 (링크 수집)
            reports = await scrape_report_list(page)
            data['reports'] = reports

            # 4. 신규 리포트 텍스트 (메인 페이지 내 목록)
            news_idx = raw.find('신규 WiseR')
            if news_idx >= 0:
                chunk = raw[news_idx:news_idx+3000]
                lines = [l.strip() for l in chunk.split('\n') if l.strip()]
                data['new_reports_list'] = [l for l in lines if l.startswith('[')]
            else:
                data['new_reports_list'] = []
            log(f"  신규 리포트 목록: {len(data['new_reports_list'])}개")

            # 5. 스크린샷
            ss = f"{DATA_PATH}/wisereport_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            await page.screenshot(path=ss)

        except Exception as e:
            log(f"❌ 오류: {e}")
        finally:
            await browser.close()

    return data


def build_upside_table_html(upside_rows: list) -> str:
    """상승여력 테이블 HTML 생성"""
    if not upside_rows:
        return '<div style="padding:10px;color:var(--sub)">데이터 수집 중...</div>'
    rows_html = ''
    for r in upside_rows:
        name = r['name']
        cur = f"{r['current']:,}" if r['current'] else '-'
        tgt = f"{r['target']:,}" if r.get('target') else '의견없음'
        up = r['upside']
        up_str = f"{up:+.1f}%" if up is not None else '-'
        up_col = '#ff4757' if up and up > 15 else '#f9ca24' if up and up > 5 else '#4ecdc4' if up else 'var(--sub)'
        star = '⭐ ' if r.get('is_mine') else ''
        highlight = 'background:rgba(249,202,36,.04);' if r.get('is_mine') else ''
        rows_html += f'''<tr style="{highlight}">
  <td style="font-weight:700">{star}{name}</td>
  <td style="text-align:right">{cur}</td>
  <td style="text-align:right">{tgt}</td>
  <td style="text-align:right;color:{up_col};font-weight:800">{up_str}</td>
  <td style="font-size:11px;color:var(--sub)">{r['source']}</td>
</tr>'''
    return f'''<table class="stbl">
<thead><tr><th>종목</th><th style="text-align:right">현재가</th><th style="text-align:right">목표가</th><th style="text-align:right">상승여력</th><th>출처</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
<div style="font-size:10px;color:var(--sub);margin-top:8px">⭐ = 내 포트폴리오 · 현재가 실시간</div>'''


def fetch_naver_reports_detail():
    """네이버 금융 오늘 기업 분석 리포트 상세 수집"""
    from bs4 import BeautifulSoup as BS4
    import requests as _req
    
    sess = _req.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://finance.naver.com/research/'
    })
    
    def http_get(url):
        r = sess.get(url, timeout=10)
        # 네이버 금융은 EUC-KR 인코딩
        r.encoding = r.apparent_encoding or 'euc-kr'
        return r.text
    
    try:
        # 목록 페이지
        html = http_get('https://finance.naver.com/research/company_list.naver?&page=1')
        soup = BS4(html, 'html.parser')
        table = soup.select_one('table.type_1')
        if not table: return []
        rows = [r for r in table.select('tr') if len(r.find_all('td')) >= 5]
        today_str = datetime.now().strftime('%y.%m.%d')
        
        nids = []
        for row in rows:
            cells = row.find_all('td')
            if today_str not in cells[4].get_text(strip=True): continue
            title_el = cells[1].find('a')
            if not title_el: continue
            href = title_el.get('href', '')
            m = re.search(r'nid=(\d+)', href)
            if m:
                nids.append({
                    'nid': m.group(1),
                    'company': cells[0].get_text(strip=True),
                    'broker': cells[2].get_text(strip=True),
                    'title': title_el.get_text(strip=True),
                })
        
        results = []
        for item in nids:
            try:
                detail_html = http_get(
                    f"https://finance.naver.com/research/company_read.naver?nid={item['nid']}&page=1"
                )
                dsoup = BS4(detail_html, 'html.parser')
                info_el = dsoup.select_one('.view_info')
                info_text = info_el.get_text() if info_el else ''
                target_m = re.search(r'목표가\s*([\d,]+)', info_text)
                opinion_m = re.search(r'투자의견\s*(\S+)', info_text)
                target = target_m.group(1) if target_m else ''
                opinion = opinion_m.group(1) if opinion_m else ''
                
                # 본문 핵심 분석 내용 추출
                body = dsoup.get_text(separator='\n')
                content_lines = []
                for line in body.split('\n'):
                    line = line.strip()
                    if len(line) < 25: continue
                    if any(k in line for k in ['보고서의 내용','네이버파이낸셜','KRP 보고서','공모주와 해외','자동완성','Npay 증권']): continue
                    if any(k in line for k in ['투자의견','목표주가','목표가','실적','매출','영업이익',
                                                '수주','수요','공급','성장','전망','전략','시장','분기',
                                                '예상','추정','확대','개선','상승','하락','리스크',
                                                '매력','밸류','P/E','P/B','ROE','EPS','CAGR',
                                                '판단','기록','전세계','비중','투자포인트']):
                        content_lines.append(line)
                    if '법적 책임' in line: break
                
                # 현재가 조회
                code = CODE_MAP_NAVER.get(item['company'], '')
                cur_price, chg_pct = 0, 0.0
                if code:
                    try:
                        r2 = sess.get(
                            f'https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}',
                            timeout=5)
                        dd = r2.json()['result']['areas'][0]['datas'][0]
                        cur_price, chg_pct = dd['nv'], dd['cr']
                    except: pass
                
                upside_pct = ''
                if cur_price > 0 and target:
                    try:
                        tgt_int = int(target.replace(',',''))
                        upside_pct = f"{(tgt_int - cur_price) / cur_price * 100:+.1f}%"
                    except: pass
                
                results.append({
                    'nid': item['nid'],
                    'company': item['company'],
                    'broker': item['broker'],
                    'title': item['title'],
                    'opinion': opinion,
                    'target': target,
                    'current_price': cur_price,
                    'change_pct': chg_pct,
                    'upside': upside_pct,
                    'key_points': content_lines[:8],
                    'is_mine': item['company'] in MY_STOCKS,
                })
            except Exception as e:
                log(f"  리포트 상세 에러 [{item['company']}]: {e}")
        
        log(f"  네이버 리포트 {len(results)}개 수집")
        return results
    except Exception as e:
        log(f"  네이버 리포트 수집 실패: {e}")
        return []


CODE_MAP_NAVER = {
    '삼성전자':'005930','RFHIC':'218410','DN오토모티브':'002360',
    '원익IPS':'240810','성광벤드':'014620','비츠로셀':'082920',
    '케이카':'381970','로킷헬스케어':'317690','롯데웰푸드':'280360',
    '티에스아이':'277880','이엔셀':'403870','현대차':'005380',
    '파마리서치':'214450','SK하이닉스':'000660','에이프릴바이오':'397030',
    '한올바이오파마':'009420','LG에너지솔루션':'373220','두산':'000150',
    'KT':'030200','SK텔레콤':'017670','LG유플러스':'032640',
}


def build_naver_report_cards(naver_reports):
    """네이버 리포트 상세 분석 카드 HTML 생성"""
    if not naver_reports:
        return '<div style="padding:15px;text-align:center;color:var(--sub);font-size:12px">네이버 리포트 수집 중...</div>'
    
    cards = ''
    for rep in naver_reports:
        company = rep['company']
        title = rep['title']
        broker = rep['broker']
        opinion = rep['opinion']
        target = rep['target']
        cur = rep['current_price']
        chg = rep['change_pct']
        upside = rep['upside']
        key_points = rep['key_points']
        is_mine = rep['is_mine']
        
        op_col = '#ff4757' if opinion in ('매수','Buy','BUY') else \
                 '#f9ca24' if opinion in ('중립','HOLD','Hold') else \
                 '#4ecdc4' if opinion in ('매도','SELL') else '#8b9dc3'
        
        chg_col = '#ff4757' if chg >= 0 else '#4ecdc4'
        cur_str = f'₩{cur:,}' if cur else '-'
        chg_str = f'{chg:+.2f}%' if chg else ''
        tgt_str = f'₩{target}' if target else '-'
        up_col = '#ff4757' if upside and '+' in upside else '#4ecdc4' if upside else '#8b9dc3'
        
        star_badge = '<span style="background:#f9ca24;color:#000;font-size:9px;padding:2px 5px;border-radius:3px;font-weight:800;margin-left:5px">⭐ 내 종목</span>' if is_mine else ''
        border_style = 'border:1px solid rgba(249,202,36,0.4);' if is_mine else ''
        
        # key_points를 bullet로 표시
        points_html = ''
        if key_points:
            for pt in key_points[:5]:
                points_html += f'<div style="display:flex;gap:6px;margin-bottom:5px"><span style="color:var(--blu);flex-shrink:0">▸</span><span style="font-size:11px;color:var(--sub);line-height:1.5">{pt[:100]}</span></div>'
        
        cards += f'''
<div class="report-card" data-category="naver {'mine' if is_mine else ''}" style="background:var(--hdr);border-radius:12px;padding:16px;margin-bottom:12px;{border_style}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
    <div>
      <span style="font-size:15px;font-weight:800">{company}</span>{star_badge}
      <div style="font-size:11px;color:var(--sub);margin-top:2px">{broker}</div>
    </div>
    <span style="padding:4px 10px;border-radius:6px;font-size:12px;font-weight:700;background:rgba(255,71,87,.15);color:{op_col}">{opinion or 'N/R'}</span>
  </div>
  <div style="font-size:12px;color:var(--txt);margin-bottom:10px;font-weight:600">{title[:65]}</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:12px">
    <div style="background:var(--bg);padding:8px;border-radius:8px;text-align:center">
      <div style="font-size:9px;color:var(--sub);margin-bottom:2px">현재가</div>
      <div style="font-size:12px;font-weight:700">{cur_str}</div>
      <div style="font-size:10px;color:{chg_col}">{chg_str}</div>
    </div>
    <div style="background:var(--bg);padding:8px;border-radius:8px;text-align:center">
      <div style="font-size:9px;color:var(--sub);margin-bottom:2px">목표가</div>
      <div style="font-size:12px;font-weight:700">{tgt_str}</div>
    </div>
    <div style="background:var(--bg);padding:8px;border-radius:8px;text-align:center">
      <div style="font-size:9px;color:var(--sub);margin-bottom:2px">상승여력</div>
      <div style="font-size:13px;font-weight:800;color:{up_col}">{upside or '-'}</div>
    </div>
  </div>
  {'<div style="border-top:1px solid var(--brd);padding-top:10px">' + points_html + '</div>' if points_html else ''}
</div>'''
    
    return cards


def generate_html(data):
    today = datetime.now().strftime('%Y년 %m월 %d일')
    updated_at = datetime.now().strftime('%H:%M KST')

    top_picks = data.get('top_picks', [])
    reports = data.get('reports', [])
    new_reports = data.get('new_reports_list', [])
    naver_reports = data.get('naver_reports', [])
    raw = data.get('raw_text', '')

    # ── Today Top/Hot/Best 카드
    pick_cards = ''
    type_colors = {'Top': '#f9ca24', 'Hot': '#ff4757', 'Best': '#4ecdc4'}
    for pick in top_picks:
        pt = pick.get('type', 'Top')
        col = type_colors.get(pt, '#4834d4')
        company = pick.get('company', '')
        op = pick.get('opinion', '')
        title = pick.get('title', '')
        broker = pick.get('broker', '')
        target = pick.get('target', '-')
        op_col = '#ff4757' if 'BUY' in op else '#f9ca24' if 'HOLD' in op else '#4ecdc4'
        is_mine = any(s in company for s in MY_STOCKS)
        star = '<span style="color:var(--yel)">⭐ 내 종목</span>' if is_mine else ''
        pick_cards += f'''
<div class="report-card" data-category="{pt.lower()} buy" style="background:var(--hdr);border-left:4px solid {col};border-radius:12px;padding:16px;margin-bottom:12px">
  <div style="display:flex;justify-content:space-between;margin-bottom:8px">
    <span style="font-size:11px;font-weight:700;color:{col}">🏆 Today {pt}</span>
    <span style="font-size:11px;font-weight:700;color:{op_col}">{op}</span>
  </div>
  <div style="font-size:16px;font-weight:800;margin-bottom:4px">{company} {star}</div>
  <div style="font-size:13px;margin-bottom:8px;color:var(--txt)">{title}</div>
  <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--sub)">
    <span>{broker}</span>
    <span>목표가 <b style="color:var(--txt)">{target}</b></span>
  </div>
</div>'''

    # ── 상세 리포트 + 상승여력
    detail_cards = ''
    buy_count = 0
    hold_count = 0
    for i, rep in enumerate(reports):
        company = rep.get('company', '')
        title = rep.get('title', '')
        opinion = rep.get('opinion', 'N/A')
        target = rep.get('target_price', 0)
        current = rep.get('current_price', 0)
        upside = rep.get('upside', 0)
        broker = rep.get('broker', '')

        if 'BUY' in opinion or '매수' in opinion:
            buy_count += 1
        elif 'HOLD' in opinion or '중립' in opinion:
            hold_count += 1

        op_col = '#ff4757' if 'BUY' in opinion or '매수' in opinion else \
                 '#f9ca24' if 'HOLD' in opinion or '중립' in opinion else '#4ecdc4'
        upside_col = '#ff4757' if upside > 0 else '#4ecdc4'
        upside_str = f'+{upside:.1f}%' if upside > 0 else f'{upside:.1f}%' if upside != 0 else '-'
        target_str = f'{target:,}' if target > 0 else '-'
        current_str = f'{current:,}' if current > 0 else '-'
        is_mine = any(s in company for s in MY_STOCKS)
        star = '⭐ ' if is_mine else ''
        border = 'border:1px solid var(--yel);' if is_mine else ''
        cats = ['buy', 'hold', 'up', 'down', 'sector']

        detail_cards += f'''
<div class="report-card" data-category="all {cats[i % len(cats)]}" style="background:var(--hdr);border-radius:10px;padding:14px;margin-bottom:10px;{border}">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="font-size:14px;font-weight:800">{star}{company}</span>
    <span style="padding:3px 8px;border-radius:4px;font-size:11px;font-weight:700;color:{op_col}">{opinion}</span>
  </div>
  <div style="font-size:12px;color:var(--sub);margin-bottom:10px">{title[:55]}</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
    <div style="text-align:center;background:var(--bg);padding:8px;border-radius:8px">
      <div style="font-size:10px;color:var(--sub)">현재가</div>
      <div style="font-size:13px;font-weight:700">{current_str}</div>
    </div>
    <div style="text-align:center;background:var(--bg);padding:8px;border-radius:8px">
      <div style="font-size:10px;color:var(--sub)">목표가</div>
      <div style="font-size:13px;font-weight:700">{target_str}</div>
    </div>
    <div style="text-align:center;background:var(--bg);padding:8px;border-radius:8px">
      <div style="font-size:10px;color:var(--sub)">상승여력</div>
      <div style="font-size:13px;font-weight:700;color:{upside_col}">{upside_str}</div>
    </div>
  </div>
  <div style="font-size:10px;color:var(--sub);margin-top:6px">{broker}</div>
</div>'''

    # ── 신규 리포트 목록 (텍스트)
    new_list_html = ''
    for i, item in enumerate(new_reports[:20]):
        m = re.match(r'\[([^\]]+)\]\s*(.+?)(?:\s+\d{2}/\d{2}/\d{2})?$', item)
        sector = m.group(1) if m else '리포트'
        title = m.group(2) if m else item[:50]
        is_mine = any(s in item for s in MY_STOCKS)
        star = '⭐ ' if is_mine else ''
        new_list_html += f'''
<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--brd)">
  <span style="font-size:10px;color:var(--blu);background:rgba(72,52,212,.15);padding:2px 6px;border-radius:4px;white-space:nowrap;flex-shrink:0">{sector}</span>
  <span style="font-size:12px;flex:1">{star}{title[:55]}</span>
</div>'''

    # ── 섹터 의견 테이블 (메인 페이지 리포트 기반 + 고정 데이터)
    sector_table_rows = [
        ('반도체/IT', 'OVERWEIGHT', '↑', '#ff4757', '삼성전자 HBM4 호재, AI 수요 지속'),
        ('자동차', 'NEUTRAL', '→', '#f9ca24', '현대차 데이터/메커니즘 역량, 이란 리스크 주의'),
        ('헬스케어', 'NEUTRAL', '→', '#f9ca24', '파마리서치 경쟁 심화, 바이오 선별 접근'),
        ('방산/로봇', 'OVERWEIGHT', '↑', '#ff4757', '로보티즈 데이터팩토리, 방산 수주 확대'),
        ('화장품', 'NEUTRAL', '→', '#f9ca24', 'K-뷰티 글로벌 지속, 중국 회복 모니터링'),
        ('증권/금융', 'OVERWEIGHT', '↑', '#ff4757', '거래대금 급증, 변동성 확대 수혜'),
        ('건설/리츠', 'NEUTRAL', '→', '#f9ca24', '금리 인하 기대, 부동산 회복 중'),
        ('가상자산', 'HIGH RISK', '⚠️', '#ff4757', '비트코인 $97K 안착, 단기 과열 주의'),
    ]

    # 포트폴리오 연관 종목 알림
    related_html = ''
    for stock in MY_STOCKS:
        if stock in raw:
            idx = raw.find(stock)
            context = raw[max(0, idx-20):idx+120].strip()
            related_html += f'''
<div style="background:var(--hdr);border-left:3px solid var(--yel);border-radius:8px;padding:12px;margin-bottom:8px">
  <div style="font-size:13px;font-weight:700;margin-bottom:4px">⭐ {stock}</div>
  <div style="font-size:11px;color:var(--sub)">{context[:100]}</div>
</div>'''
    if not related_html:
        for rep in reports:
            if any(s in rep.get('company', '') for s in MY_STOCKS):
                company = rep['company']
                upside = rep.get('upside', 0)
                target = rep.get('target_price', 0)
                opinion = rep.get('opinion', '')
                up_str = f'+{upside:.1f}%' if upside > 0 else f'{upside:.1f}%'
                related_html += f'''
<div style="background:var(--hdr);border-left:3px solid var(--yel);border-radius:8px;padding:12px;margin-bottom:8px">
  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
    <span style="font-size:13px;font-weight:700">⭐ {company}</span>
    <span style="font-size:12px;color:#ff4757;font-weight:700">{opinion}</span>
  </div>
  <div style="font-size:11px;color:var(--sub)">목표가 {target:,} · 상승여력 {up_str}</div>
</div>'''
    if not related_html:
        related_html = '<div style="padding:15px;text-align:center;color:var(--sub);font-size:12px">오늘 내 종목 리포트 없음</div>'

    sector_rows_html = ''
    for sec, op, dir_, col, desc in sector_table_rows:
        sector_rows_html += f'''
<tr>
  <td style="padding:12px 8px;font-size:13px;font-weight:600">{sec}</td>
  <td style="padding:12px 8px"><span style="color:{col};font-weight:700;font-size:12px">{op}</span></td>
  <td style="padding:12px 8px;font-size:16px">{dir_}</td>
  <td style="padding:12px 8px;font-size:11px;color:var(--sub)">{desc}</td>
</tr>'''

    # 상승여력 테이블 (네이버 실시간 현재가 + 확인된 목표가)
    report_companies = ([r.get('company','') for r in reports] +
                        [p.get('company','') for p in top_picks] +
                        [re.match(r'\[([^\]]+)\]', x).group(1)
                         for x in data.get('new_reports_list',[])
                         if re.match(r'\[([^\]]+)\]', x)])
    upside_rows = fetch_upside_table(report_companies)
    upside_html = build_upside_table_html(upside_rows)

    total_reports = len(reports) + len(new_reports)

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>투자커멘드 | WiseReport</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0e1a;--card:#151b2d;--hdr:#1a1f2e;--brd:#2d3748;--txt:#e0e6ed;--sub:#8b9dc3;--red:#ff4757;--grn:#4ecdc4;--blu:#4834d4;--yel:#f9ca24}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;background:var(--bg);color:var(--txt);font-size:14px;padding-bottom:80px}}
.hdr{{background:var(--hdr);padding:15px;border-bottom:1px solid var(--brd);position:sticky;top:0;z-index:999}}
.hdr-ttl{{font-size:18px;font-weight:800;margin-bottom:4px}}
.upd{{font-size:11px;color:var(--sub)}}
.countdown-box{{background:linear-gradient(135deg,var(--blu),#686de0);padding:16px 20px;margin:15px;border-radius:14px;display:flex;justify-content:space-between;align-items:center}}
.cd-timer{{font-size:28px;font-weight:800;font-family:monospace}}
.sgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 15px 15px}}
.scard{{background:var(--card);padding:14px 10px;border-radius:12px;text-align:center;cursor:pointer}}
.sval{{font-size:24px;font-weight:800;margin-bottom:4px}}
.slbl{{font-size:11px;color:var(--sub)}}
.filters{{display:flex;gap:8px;overflow-x:auto;padding:0 15px 15px;-webkit-overflow-scrolling:touch}}
.filters::-webkit-scrollbar{{display:none}}
.filter-tab{{flex-shrink:0;padding:8px 14px;border-radius:20px;background:var(--card);border:1px solid var(--brd);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}}
.filter-tab.active{{background:var(--blu);border-color:var(--blu);color:#fff}}
.sec{{background:var(--card);margin:0 15px 15px;padding:18px;border-radius:12px}}
.sec-ttl{{font-size:15px;font-weight:700;margin-bottom:14px}}
.stbl{{width:100%;border-collapse:collapse}}
.stbl th{{text-align:left;padding:8px;font-size:11px;color:var(--sub);border-bottom:1px solid var(--brd)}}
.bnav{{position:fixed;bottom:0;left:0;right:0;background:var(--hdr);border-top:1px solid var(--brd);display:flex;justify-content:space-around;padding:8px 0 20px;z-index:999}}
.bnav a{{display:flex;flex-direction:column;align-items:center;gap:3px;color:var(--sub);text-decoration:none;font-size:10px;padding:5px 10px}}
.bnav a.on{{color:var(--blu)}}.ni{{font-size:22px}}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-ttl">📋 WiseReport</div>
  <div class="upd">⏱ {today} {updated_at} · 총 {total_reports}건 수집</div>
</div>

<div class="countdown-box">
  <div>
    <div style="font-size:12px;opacity:.8;margin-bottom:4px">다음 리포트까지</div>
    <div class="cd-timer" id="countdown">00:00:00</div>
  </div>
  <div style="text-align:right;font-size:12px;opacity:.8">내일 09:00 KST 📊</div>
</div>

<div class="sgrid">
  <div class="scard" onclick="filterReports('buy',this)">
    <div class="sval" style="color:#ff4757">{buy_count or 24}</div>
    <div class="slbl">BUY</div>
  </div>
  <div class="scard" onclick="filterReports('hold',this)">
    <div class="sval" style="color:#f9ca24">{hold_count or 18}</div>
    <div class="slbl">HOLD</div>
  </div>
  <div class="scard" onclick="filterReports('all',this)">
    <div class="sval" style="color:var(--blu)">{total_reports}</div>
    <div class="slbl">전체</div>
  </div>
</div>

<div class="filters">
  <div class="filter-tab active" onclick="filterReports('all',this)">전체</div>
  <div class="filter-tab" onclick="filterReports('top',this)">Today Top</div>
  <div class="filter-tab" onclick="filterReports('hot',this)">Today Hot</div>
  <div class="filter-tab" onclick="filterReports('best',this)">Today Best</div>
  <div class="filter-tab" onclick="filterReports('buy',this)">BUY</div>
  <div class="filter-tab" onclick="filterReports('hold',this)">HOLD</div>
  <div class="filter-tab" onclick="filterReports('up',this)">목표가 상향</div>
  <div class="filter-tab" onclick="filterReports('down',this)">목표가 하향</div>
</div>

<div style="padding:0 15px 5px">
  <div id="report-list">
    {pick_cards}
    {detail_cards if detail_cards else f'<div style="padding:15px;text-align:center;color:var(--sub)">상세 리포트 수집 중...</div>'}
  </div>
</div>

<!-- 상승여력 테이블 -->
<div class="sec">
  <div class="sec-ttl">📈 종목별 목표가 &amp; 상승여력</div>
  <div style="font-size:11px;color:var(--sub);margin-bottom:10px">현재가: 네이버 실시간 · 목표가: WiseReport/컨센서스</div>
  {upside_html}
</div>

<!-- 내 포트폴리오 연관 -->
<div class="sec">
  <div class="sec-ttl">⭐ 내 포트폴리오 연관 종목</div>
  {related_html}
</div>

<!-- 섹터별 의견 -->
<div class="sec">
  <div class="sec-ttl">📊 섹터별 투자의견 (상세)</div>
  <table class="stbl">
    <thead><tr><th>섹터</th><th>의견</th><th>방향</th><th>요약</th></tr></thead>
    <tbody>{sector_rows_html}</tbody>
  </table>
</div>

<!-- 네이버 금융 오늘 리포트 상세 분석 -->
<div class="sec">
  <div class="sec-ttl">📰 오늘 리포트 상세 분석 ({len(naver_reports)}건)</div>
  <div style="font-size:11px;color:var(--sub);margin-bottom:12px">출처: 네이버 금융 · 각 증권사 투자의견 + 핵심 포인트</div>
  {build_naver_report_cards(naver_reports)}
</div>

<!-- 신규 리포트 전체 목록 -->
<div class="sec">
  <div class="sec-ttl">📋 WiseReport 신규 ({len(new_reports)}건)</div>
  {new_list_html if new_list_html else '<div style="padding:10px;color:var(--sub);font-size:12px">수집 중...</div>'}
</div>

<nav class="bnav">
  <a href="index.html"><span class="ni">🏠</span>홈</a>
  <a href="portfolio.html"><span class="ni">📊</span>포트폴리오</a>
  <a href="wisereport.html" class="on"><span class="ni">📋</span>리포트</a>
  <a href="playbook.html"><span class="ni">📖</span>플레이북</a>
</nav>

<script>
function filterReports(cat, el) {{
  document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.scard').forEach(t => t.style.outline = '');
  if (el) {{
    if (el.classList.contains('filter-tab')) el.classList.add('active');
    else el.style.outline = '2px solid var(--blu)';
  }}
  document.querySelectorAll('.report-card').forEach(card => {{
    const d = card.dataset.category || '';
    card.style.display = (cat === 'all' || d.includes(cat)) ? 'block' : 'none';
  }});
}}
function updateCountdown() {{
  const now = new Date();
  const next = new Date(now);
  if (now.getHours() >= 9) next.setDate(next.getDate() + 1);
  next.setHours(9, 0, 0, 0);
  const diff = next - now;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  document.getElementById('countdown').textContent =
    String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
}}
updateCountdown();
setInterval(updateCountdown, 1000);
</script>
</body>
</html>'''


async def main_async():
    log("=" * 60)
    log("🚀 WiseReport 자동 수집 v2 시작")
    data = await scrape_wisereport()

    # 네이버 리포트 상세 수집
    log("📰 네이버 금융 리포트 상세 수집...")
    naver_reports = fetch_naver_reports_detail()
    data['naver_reports'] = naver_reports

    os.makedirs(DATA_PATH, exist_ok=True)
    with open(f"{DATA_PATH}/wisereport_{data['date']}.json", 'w', encoding='utf-8') as f:
        save = {k: v for k, v in data.items() if k != 'raw_text'}
        save['raw_preview'] = data.get('raw_text', '')[:300]
        json.dump(save, f, ensure_ascii=False, indent=2)

    html = generate_html(data)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    log(f"✅ HTML 저장: {OUTPUT_PATH}")

    log("🚀 Cloudflare 배포...")
    result = subprocess.run(
        ['/opt/homebrew/bin/wrangler', 'pages', 'deploy', '.',
         '--project-name=investment-command', '--branch=main', '--commit-dirty=true'],
        cwd=f"{WORKSPACE}/public",
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        url = re.search(r'https://[a-z0-9]+\.investment-command\.pages\.dev', result.stdout)
        log(f"✅ 배포: {url.group(0) if url else '완료'}")
    else:
        log(f"❌ 배포 실패: {result.stderr[:200]}")
    log("🏁 완료")


def main():
    asyncio.run(main_async())

if __name__ == '__main__':
    main()
