#!/bin/bash
# Tailscale Setup Script for OpenClaw

echo "🚀 Tailscale 설정 시작..."

# 1. Tailscale 시작
echo "1️⃣ Tailscale 시작 중..."
sudo tailscale up --advertise-exit-node --ssh

echo ""
echo "2️⃣ Tailscale 상태 확인..."
tailscale status

echo ""
echo "✅ 설정 완료!"
echo ""
echo "📱 이제 모바일에서 Tailscale 앱을 설치하고"
echo "   같은 계정으로 로그인하면 어디서든 접속 가능!"
echo ""
echo "🔗 접속 URL: https://$(tailscale status --json | grep -o '"DNSName":"[^"]*' | cut -d'"' -f4)"
