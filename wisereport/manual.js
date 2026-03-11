const { chromium } = require('playwright');
const fs = require('fs');

async function main() {
  console.log('🚀 WiseReport 접속 시도');
  
  const browser = await chromium.launch({
    headless: false,  // 브라우저 보이게
    
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // 1. 직접 접속
    console.log('📍 https://wisereport.co.kr 접속...');
    await page.goto('https://wisereport.co.kr', { timeout: 60000 });
    await page.waitForTimeout(3000);
    
    console.log('✅ 페이지 로드 완료!');
    console.log('🖱️ 수동으로 로그인하고 "조회수 Top" 메뉴를 클릭해주세요');
    console.log('   (브라우저가 60초 동안 열려있습니다)');
    
    // 60초 대기 (수동 작업 시간)
    await page.waitForTimeout(60000);
    
    console.log('✨ 브라우저 종료');
    
  } catch (err) {
    console.error('❌ 오류:', err.message);
  } finally {
    await browser.close();
  }
}

main();
