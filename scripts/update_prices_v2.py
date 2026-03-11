#!/usr/bin/env python3
"""
포트폴리오 주가 업데이터 — KIS API 기반
pykrx 의존 제거, 한국투자증권 Open API 사용
"""
import os, csv, json, time, re, requests
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
CSV_PATH = WORKSPACE / "portfolio_full.csv"

# .env 로드
env_path = Path.home() / ".openclaw" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ.setdefault(k, v)

APP_KEY    = os.environ.get("KIS_APP_KEY", "")
APP_SECRET = os.environ.get("KIS_APP_SECRET", "")
BASE_URL   = "https://openapi.koreainvestment.com:9443"
TOKEN_CACHE_FILE = Path.home() / ".openclaw" / "kis_token_cache.json"

def get_token():
    """토큰 파일 캐시 사용 — 만료 전까지 재발급 안 함"""
    now = time.time()
    # 캐시 파일 확인
    if TOKEN_CACHE_FILE.exists():
        try:
            cache = json.loads(TOKEN_CACHE_FILE.read_text())
            if cache.get("token") and now < cache.get("expires", 0):
                return cache["token"]
        except:
            pass
    # 신규 발급
    for attempt in range(3):
        try:
            r = requests.post(f"{BASE_URL}/oauth2/tokenP",
                headers={"content-type": "application/json"},
                json={"grant_type": "client_credentials",
                      "appkey": APP_KEY, "appsecret": APP_SECRET},
                timeout=10)
            data = r.json()
            token = data.get("access_token")
            if token:
                cache = {"token": token, "expires": now + data.get("expires_in", 86400) - 300}
                TOKEN_CACHE_FILE.write_text(json.dumps(cache))
                print("  🔑 새 토큰 발급 완료")
                return token
            if "EGW00133" in data.get("error_code", ""):
                if attempt < 2:
                    print("  ⏳ 토큰 1분 제한 대기 중...")
                    time.sleep(62)
        except Exception as e:
            print(f"  토큰 오류: {e}")
    return None

def get_price_kis(code: str):
    """KIS API로 현재가·전일비·등락률 조회"""
    token = get_token()
    if not token:
        return None
    r = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
        headers={
            "authorization": f"Bearer {token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": "FHKST01010100",
            "custtype": "P",
        },
        params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": code},
        timeout=10)
    d = r.json()
    out = d.get("output", {})
    if not out or d.get("rt_cd") != "0":
        msg = d.get("msg1", "")
        if "초당" in msg or "건수" in msg:
            time.sleep(1.0)
        return None
    # 현재가 우선, 0이면 종가 사용 (장 마감 후)
    price = int(out.get("stck_prpr", 0) or 0)
    if price == 0:
        price = int(out.get("stck_clpr", 0) or 0)
    change = int(out.get("prdy_vrss", 0) or 0)
    change_rate = float(out.get("prdy_ctrt", 0) or 0)
    mcap = out.get("hts_avls", "")
    if price == 0:
        return None  # KIS에서 0이면 Naver fallback으로
    return {"price": price, "change": change, "change_rate": change_rate, "mcap": mcap}

def get_price_naver_http(code: str):
    """네이버 금융 HTTP fallback"""
    import re
    try:
        r = requests.get(f"https://finance.naver.com/item/main.naver?code={code}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=8)
        m = re.search(r'"_nowVal"[^>]*>([0-9,]+)', r.text)
        if not m:
            m = re.search(r'<strong[^>]*id="now_value"[^>]*>([0-9,]+)', r.text)
        if not m:
            m = re.search(r'<em[^>]*class="[^"]*num[^"]*"[^>]*>([0-9,]+)', r.text)
        price = int(m.group(1).replace(",", "")) if m else 0
        chg_m = re.search(r'class="(?:tdd_up|tdd_dw)"[^>]*>.*?<span[^>]*>([0-9,]+)', r.text, re.DOTALL)
        change = int(chg_m.group(1).replace(",", "")) if chg_m else 0
        if re.search(r'class="tdd_dw"', r.text):
            change = -abs(change)
        return {"price": price, "change": change, "change_rate": 0, "source": "naver-http"} if price > 0 else None
    except:
        return None

def get_price_naver_browser(name: str):
    """Playwright 브라우저로 네이버 증권 직접 검색 — 최후 fallback"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # 네이버 증권 검색
            page.goto(f"https://finance.naver.com/search/searchList.naver?query={requests.utils.quote(name)}", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
            # 첫 번째 검색 결과 클릭 (종목 페이지로 이동)
            try:
                link = page.locator("table.tbl_search a").first
                link.click(timeout=5000)
                page.wait_for_load_state("networkidle", timeout=8000)
            except:
                pass
            # 현재가 추출
            import re
            content = page.content()
            m = re.search(r'<strong[^>]*id="now_value"[^>]*>([\d,]+)', content)
            if not m:
                m = re.search(r'class="[^"]*price[^"]*"[^>]*>([\d,]+)', content)
            if not m:
                # JavaScript 변수에서 추출
                m = re.search(r'nowVal\s*[:=]\s*["\']?([\d,]+)', content)
            price = int(m.group(1).replace(",", "")) if m else 0
            # 등락
            chg_m = re.search(r'class="(?:up|down)[^"]*"[^>]*>.*?<span[^>]*>([\d,]+)', content, re.DOTALL)
            change = int(chg_m.group(1).replace(",", "")) if chg_m else 0
            if re.search(r'class="down', content):
                change = -abs(change)
            browser.close()
            return {"price": price, "change": change, "change_rate": 0, "source": "naver-browser"} if price > 0 else None
    except Exception as e:
        return None

def get_price_naver(code: str, name: str = ""):
    """네이버 금융 fallback — HTTP 먼저, 실패 시 브라우저"""
    result = get_price_naver_http(code)
    if result and result["price"] > 0:
        return result
    if name:
        return get_price_naver_browser(name)
    return None

def is_kr_stock(code: str) -> bool:
    return bool(re.fullmatch(r"\d{6}", str(code).strip()))

def format_krw(v):
    if not v:
        return ""
    try:
        return f"₩{int(str(v).replace(',','').replace('₩','')):,}"
    except:
        return str(v)

def main():
    print(f"\n{'='*50}")
    print(f"📈 포트폴리오 가격 업데이트 — KIS API")
    print(f"{'='*50}")

    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    ok, fail, skip = 0, 0, 0
    fail_names = []

    for row in rows:
        name = row.get("자산", "")
        # 종목코드 추출: 현재가 필드나 자산명에서
        # 네이버 코드 컬럼이 없으니 자산명으로 매핑
        # CSV에 종목코드 컬럼이 없어 skip — 네이버 파싱 방식 병행
        code = None

        # 현재가에서 코드 힌트 없음 → 종목코드 DB 사용
        KR_CODE_MAP = {
            "삼성전자": "005930", "삼성전자우": "005935",
            "삼성SDI": "006400", "삼성바이오로직스": "207940",
            "삼성물산": "028260", "삼성전기": "009150",
            "SK하이닉스": "000660", "SK텔레콤": "017670",
            "SK이노베이션": "096770", "SK": "034730",
            "SKC": "011790", "SK스퀘어": "402340",
            "SK바이오팜": "326030", "SK가스": "018670",
            "현대차": "005380", "현대차우": "005385",
            "현대차3우B": "005389", "기아": "000270",
            "현대모비스": "012330", "현대글로비스": "086280",
            "현대제철": "004020", "현대로템": "064350",
            "LG전자": "066570", "LG화학": "051910",
            "LG에너지솔루션": "373220", "LG디스플레이": "034220",
            "LG이노텍": "011070", "LG유플러스": "032640",
            "LG": "003550", "LG생활건강": "051900",
            "한화에어로스페이스": "012450", "한화솔루션": "009830",
            "한화시스템": "272210", "한화오션": "042660",
            "한화생명": "088350", "한화": "000880",
            "파마리서치": "214450", "네이버": "035420",
            "두산": "000150", "DL이앤씨우": "000215",
            "엘오티베큠": "036810", "현대건설": "000720",
            "ESR켄달스퀘어리츠": "365550", "SK리츠": "395400",
            "코람코라이프인프라리츠": "417310",
            "신한서부티엔디리츠": "404990",
            "이지스밸류플러스리츠": "334890",
            "세아베스틸지주": "001430",
            "TIGER 코리아AI전력기기TOP3+": "453810",
            "TIGER 글로벌AI액티브": "441540",
            "SOL 미국AI전력인프라": "486450",
            "KODEX 미국30년국채액티브(H)": "304660",
            "KODEX 미국30년국채울트라(H)": "267770",
            "TIGER 미국테크TOP10 INDXX": "381170",
            "TIGER 테슬라채권혼합Fn": "447770",
            "TIGER 코스피고배당": "211900",
            "TIGER 미국초단기국채": "329750",
            "TIGER 미국달러단기채권": "329200",
            "TIGER 글로벌멀티에셋TIF": "440340",
            "KODEX TRF3070": "329650",
            "ACE 구글밸류체인액티브": "449170",
            "TIGER 글로벌AI사이버보안": "418670",
            "TIME 글로벌우주테크&방산": "448710",
            "GRID ETF": None, "HANARO 글로벌금채굴기업": "473640",
            "KODEX 증권": "266410",
        }

        code = KR_CODE_MAP.get(name)
        if not code:
            skip += 1
            continue

        try:
            result = get_price_kis(code)
            # KIS 실패 시 재시도 1회
            if not result:
                time.sleep(0.5)
                result = get_price_kis(code)
            # 그래도 실패면 Naver fallback (HTTP → 브라우저 순)
            if not result:
                result = get_price_naver(code, name)
                if result and result["price"] > 0:
                    src = result.get("source", "naver")
                    print(f"  ✅ {name}: ₩{result['price']:,} ({src})")
                    ok += 1
                    # 손익 재계산
                    try:
                        bp = float(str(row.get("매수가","")).replace("₩","").replace(",","").strip())
                        qty = float(str(row.get("수량","")).replace(",","").strip())
                        p = result["price"]
                        row["현재가"] = f"₩{p:,}"
                        asset_val = p * qty
                        profit = (p - bp) * qty
                        profit_pct = ((p - bp) / bp * 100) if bp > 0 else 0
                        row["자산가치"] = f"₩{asset_val:,.0f}"
                        sign = "+" if profit >= 0 else ""
                        row["손익"] = f"{sign}₩{profit:,.0f} ({sign}{profit_pct:.2f}%)"
                    except: pass
                    continue
                else:
                    print(f"  ❌ {name}: KIS+Naver 모두 실패")
                    fail += 1
                    fail_names.append(name)
                    continue
            if result and result["price"] > 0:
                p = result["price"]
                chg = result["change"]
                chg_r = result["change_rate"]
                row["현재가"] = f"₩{p:,}"
                # 손익 재계산
                try:
                    buy_price_raw = str(row.get("매수가","")).replace("₩","").replace(",","").strip()
                    qty_raw = str(row.get("수량","")).replace(",","").strip()
                    if buy_price_raw and qty_raw:
                        bp = float(buy_price_raw)
                        qty = float(qty_raw)
                        asset_val = p * qty
                        profit = (p - bp) * qty
                        profit_pct = ((p - bp) / bp * 100) if bp > 0 else 0
                        row["자산가치"] = f"₩{asset_val:,.0f}"
                        sign = "+" if profit >= 0 else ""
                        row["손익"] = f"{sign}₩{profit:,.0f} ({sign}{profit_pct:.2f}%)"
                except:
                    pass
                print(f"  ✅ {name}: ₩{p:,} ({'+' if chg>=0 else ''}{chg:,}, {chg_r:+.2f}%)")
                ok += 1
            else:
                print(f"  ❌ {name}: API 응답 없음")
                fail += 1
                fail_names.append(name)
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            fail += 1
            fail_names.append(name)

        time.sleep(0.2)  # Rate limit 방지 (5req/s)

    # CSV 저장
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # 포트폴리오 HTML 타임스탬프 업데이트
    html_path = WORKSPACE / "public" / "portfolio_dashboard_v4.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        html = re.sub(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", ts, html, count=1)
        html_path.write_text(html, encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"✅ 성공: {ok}개  ❌ 실패: {fail}개  ⏭️ 스킵: {skip}개")
    print(f"💾 저장: {CSV_PATH}")
    if fail_names:
        print(f"실패 종목: {', '.join(fail_names[:5])}")
    print(f"⏰ 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
