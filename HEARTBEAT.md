# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## Stock Monitoring

- Check Hyundai preferred shares 2-4 times per market day when heartbeats run.
- Use this command first: `python3 /Users/geon/.openclaw/workspace/scripts/check_hyundai_alerts.py`
- Read the JSON output and alert only when `alerts` is non-empty.
- Focus symbols/targets:
  - 현대차3우B: alert at 264,000원 (1차 관심), 274,000원 (2차 관심), and if it falls below 232,000원 (리스크 체크)
  - 현대차우: alert at 280,000원 (1차 관심), 295,000원 (2차 관심), and if it falls below 248,000원 (리스크 체크)
- If any threshold is hit or crossed, send a concise alert with: current price, which threshold triggered, suggested action (hold / 1차 분할매도 / 2차 분할매도 / 리스크 점검).
- Only alert on meaningful changes; avoid repeating the same alert unless price moves materially past the prior trigger.
