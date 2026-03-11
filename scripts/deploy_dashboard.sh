#!/bin/bash
# GitHub Pages 자동 배포 스크립트

cd /Users/geon/.openclaw/workspace/public/iran-dashboard

echo "🚀 GitHub Pages 배포 시작..."

# Git 초기화 (첫 실행 시)
if [ ! -d ".git" ]; then
    git init
    git config user.name "OpenClaw Bot"
    git config user.email "bot@openclaw.local"
fi

# 변경사항 추가
git add .

# 커밋
git commit -m "Update dashboard: $(date '+%Y-%m-%d %H:%M')"

# GitHub에 푸시 (remote가 설정되어 있다면)
if git remote | grep -q "origin"; then
    git push origin main
    echo "✅ 배포 완료!"
    echo "🌐 접속 링크: https://geon.github.io/iran-dashboard"
else
    echo "⚠️ GitHub remote가 설정되지 않았습니다."
    echo "아래 명령어를 실행해주세요:"
    echo "git remote add origin https://github.com/geon/iran-dashboard.git"
    echo "git branch -M main"
    echo "git push -u origin main"
fi