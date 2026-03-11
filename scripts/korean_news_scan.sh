#!/bin/bash

# Global + Korean Financial News Scanner
# Sources: Reddit, TechCrunch, OpenAI, RSS feeds (Korean + International)
# Categories: AI/Tech, Real Estate, Crypto, Global Market, Korea Market

set -e

WORKSPACE="/Users/geon/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"
MEMORY_DIR="$WORKSPACE/memory"
LOG_FILE="$WORKSPACE/logs/news_scan_$(date +%Y%m%d_%H%M).log"

# Create directories
mkdir -p "$MEMORY_DIR" "$WORKSPACE/logs"

# Log function
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting Global + Korean Financial News Scan"
log "📅 $(date '+%Y-%m-%d %H:%M KST')"
log ""

# Run scanner
cd "$SCRIPTS_DIR"
python3 global_news_scanner.py 2>&1 | tee -a "$LOG_FILE"

log ""
log "✅ News scan completed"
log "📝 Log: $LOG_FILE"