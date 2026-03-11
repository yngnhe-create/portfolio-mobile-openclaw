#!/bin/bash
# 투자커멘드 통합 실행기 — 스마트 스케줄링
# 호출 방식: ./runner.sh [portfolio|wisereport|playbook|all]

WORKSPACE="/Users/geon/.openclaw/workspace"
SCRIPTS="$WORKSPACE/scripts"
LOG="$SCRIPTS/runner.log"
STATE="$SCRIPTS/runner_state.json"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

# ── 현재 시각 (KST = UTC+9)
HOUR=$(TZ=Asia/Seoul date +%H)
MIN=$(TZ=Asia/Seoul date +%M)
DOW=$(TZ=Asia/Seoul date +%u)   # 1=월 ~ 7=일
TIME_NUM=$(TZ=Asia/Seoul date +%H%M)  # HHMM 숫자

TARGET=${1:-smart}

# ── 포트폴리오 업데이터
run_portfolio() {
    log "📊 포트폴리오 업데이터 실행"
    python3 "$SCRIPTS/portfolio_live_updater.py" >> "$SCRIPTS/portfolio_updater.log" 2>&1
    log "✅ 포트폴리오 완료"
}

# ── WiseReport 스크래퍼
run_wisereport() {
    log "📋 WiseReport 스크래퍼 실행"
    python3 "$SCRIPTS/wisereport_auto.py" >> "$SCRIPTS/wisereport_auto.log" 2>&1
    log "✅ WiseReport 완료"
}

# ── 플레이북 생성기
run_playbook() {
    log "📖 플레이북 생성기 실행"
    python3 "$SCRIPTS/playbook_auto.py" >> "$SCRIPTS/playbook_auto.log" 2>&1
    log "✅ 플레이북 완료"
}

# ── 스마트 스케줄링 로직
smart_run() {
    log "═══════════════════════════════════"
    log "🤖 스마트 스케줄링 시작 (KST ${HOUR}:${MIN}, DOW=${DOW})"

    # ── 포트폴리오 현재가 업데이트
    # 주말이 아니고 (주중=1~5):
    #   - 장중 (09:00~15:30): 매 30분 실행 (이 스크립트 자체가 30분마다 호출됨)
    #   - 미장 (22:30~06:00): 매 1시간 (짝수 시에만)
    #   - 나머지 시간: 3시간에 1회 (TIME_NUM이 000,300,600,900... 에 가까울 때)
    # 주말: 6시간에 1회 (장 안 열림)

    RUN_PORTFOLIO=false

    if [ "$DOW" -le 5 ]; then
        # 주중
        if [ "$TIME_NUM" -ge 900 ] && [ "$TIME_NUM" -le 1530 ]; then
            # 장중 — 30분마다 (매번 실행)
            RUN_PORTFOLIO=true
            log "  📈 장중 시간대 → 포트폴리오 30분 업데이트"
        elif [ "$TIME_NUM" -ge 2230 ] || [ "$TIME_NUM" -le 600 ]; then
            # 미장 시간대 — 짝수 시에만 (1시간 간격)
            if [ $((HOUR % 2)) -eq 0 ]; then
                RUN_PORTFOLIO=true
                log "  🌃 미장 시간대 → 포트폴리오 1시간 업데이트"
            fi
        else
            # 그 외 — 3시간 간격 (00,03,06,09,12,15,18,21시)
            if [ $((HOUR % 3)) -eq 0 ] && [ "$MIN" -lt 30 ]; then
                RUN_PORTFOLIO=true
                log "  💤 장외 시간대 → 포트폴리오 3시간 업데이트"
            fi
        fi
    else
        # 주말 — 6시간 간격 (00,06,12,18시)
        if [ $((HOUR % 6)) -eq 0 ] && [ "$MIN" -lt 30 ]; then
            RUN_PORTFOLIO=true
            log "  📅 주말 → 포트폴리오 6시간 업데이트"
        fi
    fi

    # ── WiseReport — 평일 08:30 1회
    RUN_WISEREPORT=false
    if [ "$DOW" -le 5 ] && [ "$HOUR" -eq 8 ] && [ "$MIN" -ge 25 ] && [ "$MIN" -le 40 ]; then
        RUN_WISEREPORT=true
        log "  📋 WiseReport 08:30 — 일일 1회 수집"
    fi
    # 또는 수동 실행 시
    if [ "$TARGET" = "wisereport" ] || [ "$TARGET" = "all" ]; then
        RUN_WISEREPORT=true
    fi

    # ── 플레이북 — 매일 07:00 1회
    RUN_PLAYBOOK=false
    if [ "$HOUR" -eq 7 ] && [ "$MIN" -ge 0 ] && [ "$MIN" -le 15 ]; then
        RUN_PLAYBOOK=true
        log "  📖 플레이북 07:00 — 일일 전략 업데이트"
    fi
    if [ "$TARGET" = "playbook" ] || [ "$TARGET" = "all" ]; then
        RUN_PLAYBOOK=true
    fi

    # ── 실행
    $RUN_PORTFOLIO && run_portfolio
    $RUN_WISEREPORT && run_wisereport
    $RUN_PLAYBOOK && run_playbook

    if ! $RUN_PORTFOLIO && ! $RUN_WISEREPORT && ! $RUN_PLAYBOOK; then
        log "⏭️  이번 주기 건너뜀 (조건 미충족)"
    fi
}

# ── 진입점
case "$TARGET" in
    portfolio)  run_portfolio ;;
    wisereport) run_wisereport ;;
    playbook)   run_playbook ;;
    all)
        run_portfolio
        run_wisereport
        run_playbook
        ;;
    *)
        smart_run
        ;;
esac

log "🏁 러너 완료"
