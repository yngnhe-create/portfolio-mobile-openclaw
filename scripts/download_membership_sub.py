#!/usr/bin/env python3
"""
유튜브 멤버십 자막 다운로드 Python 스크립트
사용법: python3 download_membership_sub.py "https://www.youtube.com/watch?v=VIDEO_ID" [--cookies /path/to/cookies.txt]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def check_yt_dlp():
    """yt-dlp 설치 확인"""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_subtitles(url: str, cookies_path: str, output_dir: str = "~/Downloads/youtube-subs"):
    """자막 다운로드"""
    output_path = Path(output_dir).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'yt-dlp',
        '--cookies', cookies_path,
        '--write-auto-sub',
        '--sub-langs', 'ko,en',
        '--convert-subs', 'vtt',
        '--skip-download',
        '--output', str(output_path / '%(title)s.%(ext)s'),
        '--sleep-interval', '5',
        '--max-sleep-interval', '15',
        url
    ]
    
    print(f"🎬 멤버십 영상 자막 다운로드 시작...")
    print(f"🔗 URL: {url}")
    print(f"🍪 Cookies: {cookies_path}")
    print(f"📁 저장 위치: {output_path}")
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n✅ 자막 다운로드 완료!")
        print(f"📂 저장 위치: {output_path}")
        # 다운로드된 파일 목록 표시
        files = list(output_path.glob("*.vtt")) + list(output_path.glob("*.srt"))
        for f in files:
            print(f"   - {f.name} ({f.stat().st_size:,} bytes)")
        return True
    else:
        print(f"\n❌ 다운로드 실패")
        print("쿠키 파일이 유효한지 확인하세요 (로그인 세션 만료 여부)")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='YouTube 멤버십 영상 자막 다운로더',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python3 download_membership_sub.py "https://www.youtube.com/watch?v=..."
  python3 download_membership_sub.py "URL" --cookies ~/Downloads/cookies.txt

쿠키 파일 준비 방법:
  1. Chrome에서 YouTube 멤버십 영상 페이지 열기 (로그인 상태)
  2. Chrome 확장 프로그램 'Get cookies.txt LOCALLY' 설치
  3. 확장 프로그램 클릭 → 'Export' → cookies.txt 저장
  4. 이 스크립트 실행 시 --cookies 로 경로 지정
        """
    )
    parser.add_argument('url', help='YouTube 멤버십 영상 URL')
    parser.add_argument('--cookies', 
                        default='~/.config/youtube-cookies/cookies.txt',
                        help='cookies.txt 파일 경로 (기본값: ~/.config/youtube-cookies/cookies.txt)')
    parser.add_argument('--output', '-o',
                        default='~/Downloads/youtube-subs',
                        help='출력 디렉토리 (기본값: ~/Downloads/youtube-subs)')
    
    args = parser.parse_args()
    
    # yt-dlp 확인
    if not check_yt_dlp():
        print("❌ yt-dlp가 설치되어 있지 않습니다.")
        print("설치 방법: brew install yt-dlp")
        sys.exit(1)
    
    # 쿠키 파일 경로 확장
    cookies_path = Path(args.cookies).expanduser()
    
    # 쿠키 파일 존재 확인
    if not cookies_path.exists():
        print(f"❌ 쿠키 파일을 찾을 수 없습니다: {cookies_path}")
        print()
        print("📋 쿠키 파일 준비 방법:")
        print("1. Chrome에서 YouTube 멤버십 영상 페이지 열기 (로그인 상태)")
        print("2. Chrome 확장 프로그램 'Get cookies.txt LOCALLY' 설치")
        print("   https://chrome.google.com/webstore/detail/get-cookiestxt-locally/...")
        print("3. 확장 프로그램 클릭 → 'Export' → cookies.txt 저장")
        print("4. 저장한 파일 경로를 --cookies 로 지정")
        print()
        print(f"💡 기본 쿠키 저장 위치 생성:")
        print(f"   mkdir -p ~/.config/youtube-cookies")
        print(f"   mv ~/Downloads/cookies.txt ~/.config/youtube-cookies/")
        sys.exit(1)
    
    # 다운로드 실행
    success = download_subtitles(args.url, str(cookies_path), args.output)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
