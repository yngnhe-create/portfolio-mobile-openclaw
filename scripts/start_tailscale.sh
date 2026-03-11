#!/bin/bash
# Tailscale 완전 설정 스크립트

echo "🚀 Tailscale 설정 시작..."
echo "========================"
echo ""

# 1. 서비스 중지 (충돌 방지)
echo "1️⃣ 기존 서비스 중지..."
brew services stop tailscale 2>/dev/null
sleep 2

# 2. 백그라운드에서 tailscaled 직접 실행
echo "2️⃣ Tailscale 데몬 시작..."
sudo mkdir -p /var/lib/tailscale /var/run/tailscale
sudo /opt/homebrew/opt/tailscale/bin/tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/var/run/tailscale/tailscaled.sock \
  --port=41641 &

sleep 3

# 3. 로그인
echo "3️⃣ Tailscale 네트워크에 연결..."
echo "   브라우저에서 로그인 URL이 열립니다..."
sudo /opt/homebrew/opt/tailscale/bin/tailscale up \
  --advertise-exit-node \
  --ssh \
  --accept-dns \
  --hostname=geon-mac-mini

echo ""
echo "✅ 설정 완료!"
echo ""
echo "📋 확인 명령어:"
echo "   tailscale status"
echo "   tailscale ip -4"
echo ""
echo "📱 모바일에서 Tailscale 앱 설치 후"
echo "   같은 계정으로 로그인하면 자동 연결됩니다!"
