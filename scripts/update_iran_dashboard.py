#!/usr/bin/env python3
"""
이란 전쟁 대시보드 자동 업데이트 스크립트
- 최신 뉴스 수집 (OpenClaw 서브에이전트 방식 대신 웹 검색 API 활용)
- HTML 현행화 후 Cloudflare Pages 배포
"""

import subprocess
import sys
import os
from datetime import datetime

WORKSPACE = "/Users/geon/.openclaw/workspace"
DASHBOARD_PATH = f"{WORKSPACE}/public/iran-dashboard-kr/index.html"
LOG_PATH = f"{WORKSPACE}/scripts/iran_update.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def run_openclaw_update():
    """OpenClaw에 이란 현황 분석 + 대시보드 업데이트 요청"""
    log("이란 대시보드 업데이트 시작...")
    
    prompt = """이란 전쟁 대시보드를 오늘 날짜 기준으로 현행화해줘.

1. 웹 검색으로 최신 이란 전쟁 상황 수집 (유가, 군사 현황, 외교, 호르무즈)
2. /Users/geon/.openclaw/workspace/public/iran-dashboard-kr/index.html 업데이트
3. wrangler pages deploy 실행

완료 후 "이란 대시보드 업데이트 완료" 라고 답해줘."""
    
    result = subprocess.run(
        ["openclaw", "ask", prompt],
        capture_output=True, text=True,
        cwd=WORKSPACE, timeout=300
    )
    
    if result.returncode == 0:
        log("✅ 업데이트 완료")
        return True
    else:
        log(f"❌ 오류: {result.stderr[:200]}")
        return False

if __name__ == "__main__":
    success = run_openclaw_update()
    sys.exit(0 if success else 1)
