# WiseReport Daily Report Automation

## Description
Automatically fetch WiseReport daily summary and market analysis at 7:30 AM KST every day.

## Script
#!/bin/bash
# WiseReport Daily Summary Automation
# Runs at 7:30 AM KST daily

echo "📊 WiseReport Daily Report - $(date '+%Y-%m-%d %H:%M')"

# Note: This script requires manual browser interaction or additional setup
# since WiseReport login and report access need authentication

# For now, this serves as a placeholder/notification
# The actual report needs to be generated with proper login

echo "WiseReport 자동 리포트 생성 시도..."
echo "현재: WiseReport 로그인 문제로 수동 실행 필요"

# Send notification to user
node -e "
const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle', timeout: 60000 });
    await page.fill('input[type=\"text\"]', 'yngnhe');
    await page.fill('input[type=\"password\"]', 'wldhs232');
    await page.evaluate(() => document.querySelector('form').submit());
    await page.waitForTimeout(8000);
    
    if (page.url().includes('LoginProcess')) {
      console.log('⚠️ 로그인 실패 - 수동 확인 필요');
    } else {
      console.log('✅ 로그인 성공');
      // Navigate to reports...
    }
  } catch(e) {
    console.log('오류:', e.message);
  } finally {
    await browser.close();
  }
}

main();
"
