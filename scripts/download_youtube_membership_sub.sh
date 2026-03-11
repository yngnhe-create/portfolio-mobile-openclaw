#!/bin/bash
# 유튜브 멤버십 자막 다운로드 스크립트
# 사용법: ./download_membership_sub.sh "https://www.youtube.com/watch?v=VIDEO_ID"

# 설정
COOKIES_FILE="$HOME/.config/youtube-cookies/cookies.txt"
OUTPUT_DIR="$HOME/Downloads/youtube-subs"

# yt-dlp 설치 확인
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ yt-dlp가 설치되어 있지 않습니다."
    echo "설치 방법: brew install yt-dlp"
    exit 1
fi

# 쿠키 파일 확인
if [ ! -f "$COOKIES_FILE" ]; then
    echo "❌ 쿠키 파일을 찾을 수 없습니다: $COOKIES_FILE"
    echo ""
    echo "📋 쿠키 파일 준비 방법:"
    echo "1. Chrome에서 YouTube 멤버십 영상 페이지 열기 (로그인 상태)"
    echo "2. Chrome 확장 프로그램 'Get cookies.txt LOCALLY' 설치"
    echo "3. 확장 프로그램 클릭 → 'Export' → cookies.txt 저장"
    echo "4. 저장한 파일을 $COOKIES_FILE 경로로 이동"
    echo ""
    echo "💡 또는 수동으로 cookies.txt 경로를 지정하세요:"
    echo "   COOKIES_FILE=/path/to/cookies.txt ./download_membership_sub.sh \"URL\""
    exit 1
fi

# URL 입력 확인
if [ -z "$1" ]; then
    echo "❌ 유튜브 URL을 입력하세요"
    echo "사용법: $0 \"https://www.youtube.com/watch?v=...\""
    exit 1
fi

URL="$1"
mkdir -p "$OUTPUT_DIR"

echo "🎬 멤버십 영상 자막 다운로드 시작..."
echo "🔗 URL: $URL"
echo "📁 저장 위치: $OUTPUT_DIR"
echo ""

# 자막 다운로드
yt-dlp \
    --cookies "$COOKIES_FILE" \
    --write-auto-sub \
    --sub-langs ko,en \
    --convert-subs vtt \
    --skip-download \
    --output "$OUTPUT_DIR/%(title)s.%(ext)s" \
    --sleep-interval 5 \
    --max-sleep-interval 15 \
    "$URL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 자막 다운로드 완료!"
    echo "📂 저장 위치: $OUTPUT_DIR"
    ls -lh "$OUTPUT_DIR"/*.vtt 2>/dev/null || ls -lh "$OUTPUT_DIR"/*.*
else
    echo ""
    echo "❌ 다운로드 실패"
    echo "쿠키 파일이 유효한지 확인하세요 (로그인 세션 만료 여부)"
fi
