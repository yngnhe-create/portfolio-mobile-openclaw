#!/usr/bin/env python3
"""Check Hyundai preferred shares and emit alert info for heartbeat use.

Fetches current prices from Naver Finance and compares against configured
thresholds. Persists last triggered state to avoid duplicate alerts.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

API_URL = "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={code}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

CONFIG: dict[str, dict[str, Any]] = {
    "현대차우": {
        "code": "005385",
        "up1": 280000,
        "up2": 295000,
        "down": 248000,
    },
    "현대차3우B": {
        "code": "005389",
        "up1": 264000,
        "up2": 274000,
        "down": 232000,
    },
}

STATE_PATH = Path("/Users/geon/.openclaw/workspace/memory/hyundai_monitor_state.json")


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"symbols": {}}



def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2))



def fetch_price(code: str) -> dict[str, Any]:
    # Prefer HTML scraping because the lightweight JSON endpoint can return blank.
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    r = requests.get(url, headers={**HEADERS, "Referer": "https://finance.naver.com/"}, timeout=10)
    r.raise_for_status()
    html = r.text

    import re

    price_match = re.search(r'<p class="no_today">.*?<span class="blind">([0-9,]+)</span>', html, re.S)
    rate_match = re.search(r'<p class="no_exday">.*?<span class="blind">([+\-]?[0-9.,]+)%</span>', html, re.S)
    change_match = re.search(r'<p class="no_exday">.*?<span class="blind">([0-9,]+)</span>', html, re.S)
    title_match = re.search(r'<title>(.*?)\s*:\s*Npay 증권</title>', html)

    if not price_match:
        # Fallback to API when available
        api_r = requests.get(API_URL.format(code=code), headers=HEADERS, timeout=10)
        api_r.raise_for_status()
        data = api_r.json()
        return {
            "price": int(data.get("now", 0)),
            "change": int(data.get("change", 0)),
            "change_rate": float(data.get("changeRate", 0)),
            "name": data.get("nm") or code,
        }

    price = int(price_match.group(1).replace(',', ''))
    change = int(change_match.group(1).replace(',', '')) if change_match else 0
    change_rate = float(rate_match.group(1).replace(',', '')) if rate_match else 0.0
    name = title_match.group(1).strip() if title_match else code
    return {
        "price": price,
        "change": change,
        "change_rate": change_rate,
        "name": name,
    }



def classify(price: int, cfg: dict[str, Any]) -> tuple[str, str]:
    if price >= cfg["up2"]:
        return "up2", "2차 분할매도"
    if price >= cfg["up1"]:
        return "up1", "1차 분할매도"
    if price <= cfg["down"]:
        return "down", "리스크 점검"
    return "none", "hold"



def materially_changed(last_trigger: str, last_price: int, trigger: str, price: int) -> bool:
    if trigger != last_trigger:
        return True
    if last_price <= 0:
        return True
    # same trigger band: only re-alert if moved by at least 2%
    return abs(price - last_price) / last_price >= 0.02



def main() -> int:
    state = load_state()
    state.setdefault("symbols", {})
    results: dict[str, Any] = {}
    alerts: list[dict[str, Any]] = []

    for symbol, cfg in CONFIG.items():
        data = fetch_price(cfg["code"])
        price = data["price"]
        trigger, action = classify(price, cfg)
        prior = state["symbols"].get(symbol, {})
        should_alert = trigger != "none" and materially_changed(
            str(prior.get("trigger", "none")),
            int(prior.get("price", 0) or 0),
            trigger,
            price,
        )

        results[symbol] = {
            "code": cfg["code"],
            "price": price,
            "change": data["change"],
            "change_rate": data["change_rate"],
            "trigger": trigger,
            "action": action,
            "thresholds": {
                "up1": cfg["up1"],
                "up2": cfg["up2"],
                "down": cfg["down"],
            },
        }
        if should_alert:
            alerts.append({"symbol": symbol, **results[symbol]})

        state["symbols"][symbol] = {
            "trigger": trigger,
            "price": price,
            "updatedAt": datetime.now().isoformat(),
        }

    state["updatedAt"] = datetime.now().isoformat()
    save_state(state)

    print(json.dumps({
        "updatedAt": state["updatedAt"],
        "results": results,
        "alerts": alerts,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
