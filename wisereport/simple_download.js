const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function main() {
  console.log('🚀 Wise Report 다운로더 시작');
  
  const browser = await chromium.launch({ 
    headless: true,
    
    args: ['--no-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    // 1. 접속 및 로그인
    console.log('📍 접속 중...');
    await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log('🔐 로그인...');
    await page.fill('input[type=text]', 'yngnhe');
    await page.fill('input[type=password]', 'wldhs232');
    await page.evaluate(() => document.querySelector('form').submit());
    await page.waitForTimeout(5000);
    console.log('✅ 로그인 완료');
    
    // 2. 조회수 Top 메뉴로 이동
    console.log('📊 조회수 Top 메뉴 클릭...');
    await page.click('a:has-text("조회수")');
    await page.waitForTimeout(5000);
    
    // 3. 페이지 내용 확인
    const url = page.url();
    console.log('현재 URL:', url);
    
    // 4. 스크린샷 저장
    await page.screenshot({ path: '/tmp/wisereport_result.png', fullPage: true });
    console.log('📸 스크린샷 저장: /tmp/wisereport_result.png');
    
    // 5. 다운로드 링크 추출
    const links = await page.$$eval('a[href*="pdf"], a[onclick*="pdf"]', as => 
      as.map(a => a.href || a.getAttribute('onclick'))
    );
    
    console.log(`📋 PDF 링크 ${links.length}개 발견`);
    links.slice(0, 5).forEach((l, i) => console.log(`  ${i+1}. ${l?.substring(0, 80)}...`));
    
    console.log('\n💡 다음 단계:');
    console.log('  스크린샷을 확인하고 다운로드 방법을 결정합니다.');
    
  } catch (err) {
    console.error('❌ 오류:', err.message);
    await page.screenshot({ path: '/tmp/wisereport_error.png' });
  } finally {
    await browser.close();
    console.log('👋 종료');
  }
}

main();
