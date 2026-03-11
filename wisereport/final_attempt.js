const { chromium } = require('playwright');

async function main() {
  console.log('🚀 WiseReport 다운로드 시작');
  
  const browser = await chromium.launch({ 
    headless: true,
    
    args: ['--no-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    // 1. 접속
    await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // 2. 팝업 닫기 (있는 경우)
    try {
      const closeBtn = await page.$('.popup_close, .btn_close, [onclick*="close"]');
      if (closeBtn) {
        await closeBtn.click();
        console.log('📌 팝업 닫음');
        await page.waitForTimeout(1000);
      }
    } catch(e) {}
    
    // 3. 로그인
    console.log('🔐 로그인...');
    await page.fill('input[type=text]', 'yngnhe');
    await page.fill('input[type=password]', 'wldhs232');
    await page.evaluate(() => document.querySelector('form').submit());
    await page.waitForTimeout(4000);
    console.log('✅ 로그인 완료');
    
    // 4. JavaScript로 직접 페이지 이동
    console.log('📊 조회수 Top 페이지로 이동...');
    await page.evaluate(() => {
      if (typeof na_Report_Login === 'function') {
        na_Report_Login('menu5', '', '', '', '');
      }
    });
    await page.waitForTimeout(5000);
    
    // 5. 현재 상태 확인
    console.log('현재 URL:', page.url());
    await page.screenshot({ path: '/tmp/result.png', fullPage: true });
    console.log('📸 스크린샷: /tmp/result.png');
    
    // 6. PDF 링크 추출
    const content = await page.content();
    const pdfMatches = content.match(/['"]([^'"]*\.pdf)['"]/g);
    
    if (pdfMatches) {
      console.log(`\n📋 PDF 파일 ${pdfMatches.length}개 발견:`);
      [...new Set(pdfMatches)].slice(0, 10).forEach((f, i) => {
        console.log(`  ${i+1}. ${f.replace(/['"]/g, '')}`);
      });
    }
    
    console.log('\n✨ 완료! 스크린샷을 확인해주세요.');
    
  } catch (err) {
    console.error('❌ 오류:', err.message);
    await page.screenshot({ path: '/tmp/error.png' });
  } finally {
    await browser.close();
    console.log('👋 종료');
  }
}

main();
