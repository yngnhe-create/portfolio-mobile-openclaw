#!/bin/bash
# WiseReport Downloader using curl
# Login and download top reports

set -e

echo "🚀 WiseReport 자동 다운로드 시작"
echo "================================"

# Variables
LOGIN_URL="https://wisereport.co.kr/login"
USERNAME="yngnhe"
PASSWORD="wldhs232"
COOKIE_FILE="/tmp/wisereport_cookies.txt"
DOWNLOAD_DIR="/Users/geon/.openclaw/workspace/wisereport/downloads"

# Create download directory
mkdir -p "$DOWNLOAD_DIR"

# Step 1: Get login page and extract CSRF token (if exists)
echo "📍 Step 1: 로그인 페이지 접속..."
curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "$LOGIN_URL" > /tmp/login_page.html

# Check if already logged in or get form data
if grep -q "로그아웃\|logout" /tmp/login_page.html; then
  echo "✅ 이미 로그인되어 있음"
else
  echo "🔐 Step 2: 로그인 시도..."
  
  # Try POST login
  curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Referer: $LOGIN_URL" \
    -X POST \
    -d "id=$USERNAME&pw=$PASSWORD" \
    "$LOGIN_URL" > /tmp/login_result.html
  
  # Check login success
  if grep -q "로그인 실패\|잘못된\|Invalid" /tmp/login_result.html; then
    echo "❌ 로그인 실패: 아이디/비밀번호 확인 필요"
    exit 1
  else
    echo "✅ 로그인 성공"
  fi
fi

# Step 3: Access popular reports page
echo "📊 Step 3: 인기 리포트 페이지 접속..."
curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://wisereport.co.kr" \
  "https://wisereport.co.kr/report/popular" > /tmp/popular.html

# Step 4: Extract download links
echo "🔍 Step 4: 다운로드 링크 추출..."
grep -oE 'href="([^"]*download[^"]*)"' /tmp/popular.html | \
  sed 's/href="//;s/"$//' | \
  head -5 > /tmp/download_links.txt

if [ ! -s /tmp/download_links.txt ]; then
  echo "⚠️ 다운로드 링크를 찾을 수 없음. 사이트 구조 확인 필요"
  # Try alternative pattern
  grep -oE 'href="([^"]*pdf[^"]*)"' /tmp/popular.html | \
    sed 's/href="//;s/"$//' | \
    head -5 > /tmp/download_links.txt
fi

echo "📋 찾은 다운로드 링크:"
cat /tmp/download_links.txt

# Step 5: Download files
echo "💾 Step 5: 리포트 다운로드..."
COUNT=0
while IFS= read -r link; do
  if [ -n "$link" ]; then
    COUNT=$((COUNT + 1))
    FILENAME="report_$COUNT.pdf"
    
    # Handle relative URLs
    if [[ $link == /* ]]; then
      FULL_URL="https://wisereport.co.kr$link"
    else
      FULL_URL="$link"
    fi
    
    echo "  📥 다운로드 중: $FILENAME"
    curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" \
      -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
      -H "Referer: https://wisereport.co.kr/report/popular" \
      -L "$FULL_URL" > "$DOWNLOAD_DIR/$FILENAME"
    
    # Check if file is valid (not HTML error page)
    if file "$DOWNLOAD_DIR/$FILENAME" | grep -q "PDF"; then
      echo "  ✅ PDF 저장 완료: $FILENAME"
    else
      echo "  ⚠️ PDF가 아님 (로그인 필요 또는 링크 오류)"
      # Remove invalid file
      rm -f "$DOWNLOAD_DIR/$FILENAME"
    fi
    
    sleep 2
  fi
done < /tmp/download_links.txt

echo ""
echo "🎉 작업 완료!"
echo "📂 다운로드 경로: $DOWNLOAD_DIR"
echo ""
echo "📄 다운로드된 파일 목록:"
ls -lh "$DOWNLOAD_DIR"

# Cleanup
rm -f "$COOKIE_FILE" /tmp/login_page.html /tmp/login_result.html /tmp/popular.html /tmp/download_links.txt
