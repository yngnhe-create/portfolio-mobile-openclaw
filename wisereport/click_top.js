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
    // 1. 접속 및 로그인
    await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log('🔐 로그인...');
    await page.fill('input[type=text]', 'yngnhe');
    await page.fill('input[type=password]', 'wldhs232');
    await page.evaluate(() => document.querySelector('form').submit());
    await page.waitForTimeout(4000);
    console.log('✅ 로그인 완료');
    
    // 2. 상단 "Top" 메뉴 클릭
    console.log('📊 Top 메뉴 클릭...');
    await page.click('a:has-text("Top")');
    await page.waitForTimeout(5000);
    
    console.log('현재 URL:', page.url());
    
    // 3. 스크린샷
    await page.screenshot({ path: '/tmp/top_page.png', fullPage: true });
    console.log('📸 스크린샷: /tmp/top_page.png');
    
    // 4. PDF 파일명 추출
    const content = await page.content();
    const pdfs = [...content.matchAll(/['"]([^'"]*\.pdf)['"]/g)]
      .map(m => m[1])
      .filter((v, i, a) => a.indexOf(v) === i); // 중복 제거
    
    console.log(`\n📋 PDF 파일 ${pdfs.length}개 발견:`);
    pdfs.slice(0, 10).forEach((f, i) => console.log(`  ${i+1}. ${f}`));
    
    // 5. 다운로드 경로 준비
    const downloadDir = '/Users/geon/.openclaw/workspace/wisereport/downloads';
    if (!fs.existsSync(downloadDir)) fs.mkdirSync(downloadDir, { recursive: true });
    
    console.log('\n💡 완료!');
    console.log('  PDF 파일 목록을 확인했습니다.');
    console.log('  브라우저에서 직접 다운로드하거나');
    console.log('  파일명으로 다운로드 URL을 구성할 수 있습니다.');
    
  } catch (err) {
    console.error('❌ 오류:', err.message);
    await page.screenshot({ path: '/tmp/error.png' });
  } finally {
    await browser.close();
    console.log('👋 종료');
  }
}

main();
