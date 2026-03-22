#!/usr/bin/env python3
"""시장 데이터 수집기 - Yahoo Finance에서 데이터 가져와 JSON 저장"""

import json
import urllib.request
import ssl
from datetime import datetime
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "public" / "data" / "market_latest.json"

SYMBOLS = {
    "KOSPI":  "^KS11",
    "KOSDAQ": "^KQ11",
    "NASDAQ": "^IXIC",
    "SP500":  "^GSPC",
    "USDKRW": "KRW=X",
}

def fetch_symbol(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?interval=1d&range=1d"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        data = json.loads(r.read())
    meta = data["chart"]["result"][0]["meta"]
    cur = meta.get("regularMarketPrice", 0)
    prev = meta.get("chartPreviousClose", meta.get("previousClose", cur))
    chg = cur - prev
    pct = (chg / prev * 100) if prev else 0
    return {"cur": round(cur, 2), "chg": round(chg, 2), "pct": round(pct, 4)}

import urllib.parse

def main():
    results = []
    for label, sym in SYMBOLS.items():
        try:
            d = fetch_symbol(sym)
            results.append({"id": label, "label": label, **d})
            print(f"  {label}: {d['cur']:,.2f} ({d['pct']:+.2f}%)")
        except Exception as e:
            print(f"  {label}: FAILED - {e}")
            results.append({"id": label, "label": label, "cur": 0, "chg": 0, "pct": 0})

    output = {
        "timestamp": datetime.now().isoformat(),
        "data": results
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n저장: {OUTPUT}")

if __name__ == "__main__":
    print(f"📈 시장 데이터 수집 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    main()
