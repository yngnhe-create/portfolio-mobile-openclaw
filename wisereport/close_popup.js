const { chromium } = require('playwright');
const fs = require('fs');

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
    await page.waitForTimeout(3000);
    
    // 2. 팝업 닫기
    console.log('📌 팝업 닫기...');
    await page.evaluate(() => {
      const popup = document.getElementById('popup_overlay');
      if (popup) popup.remove();
      const closeBtns = document.querySelectorAll('.popup_close, .btn_close, [onclick*="close"], [onclick*="Close"]');
      closeBtns.forEach(btn => btn.click());
    });
    await page.waitForTimeout(1000);
    
    // 3. 로그인
    console.log('🔐 로그인...');
    await page.fill('input[type=text]', 'yngnhe');
    await page.fill('input[type=password]', 'wldhs232');
    await page.evaluate(() => document.querySelector('form').submit());
    await page.waitForTimeout(4000);
    console.log('✅ 로그인 완료');
    
    // 4. 팝업 다시 닫기
    await page.evaluate(() => {
      const popup = document.getElementById('popup_overlay');
      if (popup) popup.style.display = 'none';
    });
    await page.waitForTimeout(1000);
    
    // 5. JavaScript로 직접 이동
    console.log('📊 Top 페이지로 이동...');
    await page.evaluate(() => {
      if (typeof na_Report_Login === 'function') {
        na_Report_Login('menu5', '', '', '', '');
      } else {
        location.href = '/report/popular';
      }
    });
    await page.waitForTimeout(5000);
    
    console.log('현재 URL:', page.url());
    
    // 6. 스크린샷
    await page.screenshot({ path: '/tmp/top_page.png', fullPage: true });
    console.log('📸 스크린샷: /tmp/top_page.png');
    
    // 7. PDF 추출
    const content = await page.content();
    const pdfs = [...content.matchAll(/['"]([^'"]*\.pdf)['"]/g)]
      .map(m => m[1])
      .filter((v, i, a) => a.indexOf(v) === i);
    
    console.log(`\n📋 PDF 파일 ${pdfs.length}개:`);
    pdfs.slice(0, 10).forEach((f, i) => console.log(`  ${i+1}. ${f}`));
    
    console.log('\n✨ 완료!');
    
  } catch (err) {
    console.error('❌ 오류:', err.message);
    await page.screenshot({ path: '/tmp/error.png' });
  } finally {
    await browser.close();
    console.log('👋 종료');
  }
}

main();
