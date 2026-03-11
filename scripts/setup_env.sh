#!/bin/bash
# OpenClaw Environment Setup Script
# 이 스크립트는 ~/.openclaw/.env 파일을 생성합니다

echo "📝 OpenClaw 환경 변수 설정"
echo "=========================="
echo ""

# 소스 파일 경로
SOURCE_ENV="$HOME/.openclaw/workspace/.env"
TARGET_ENV="$HOME/.openclaw/.env"

# 이미 존재하는지 확인
if [ -f "$TARGET_ENV" ]; then
    echo "⚠️  ~/.openclaw/.env 파일이 이미 존재합니다."
    read -p "덮어쓰시겠습니까? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "❌ 취소되었습니다. 기존 파일을 유지합니다."
        exit 0
    fi
fi

# 템플릿 복사
echo "📋 템플릿 파일 복사 중..."
cp "$SOURCE_ENV" "$TARGET_ENV"

# 권한 설정 (소유자만 읽기/쓰기 가능)
chmod 600 "$TARGET_ENV"

echo ""
echo "✅ ~/.openclaw/.env 파일 생성 완료!"
echo ""
echo "🔧 다음 단계:"
echo "1. 아래 명령어로 파일을 열어서 실제 API 키를 입력하세요:"
echo ""
echo "   nano ~/.openclaw/.env"
echo "   # 또는"
echo "   vim ~/.openclaw/.env"
echo ""
echo "2. 다음 항목들을 반드시 실제 값으로 교체하세요:"
echo "   - KIS_APP_KEY"
echo "   - KIS_APP_SECRET"
echo "   - KIS_CANO"
echo "   - DISCORD_WEBHOOK_*"
echo ""
echo "3. 저장 후 스크립트에서 환경 변수를 불러오는지 테스트:"
echo "   source ~/.openclaw/.env && echo \$KIS_APP_KEY"
echo ""
