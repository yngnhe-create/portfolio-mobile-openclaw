const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({ 
    headless: true,
    
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // 로그인
  console.log('📍 로그인 중...');
  await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle', timeout: 60000 });
  await page.fill('input[type="text"]', 'yngnhe');
  await page.fill('input[type="password"]', 'wldhs232');
  await page.evaluate(() => {
    const form = document.querySelector('form');
    if (form) form.submit();
  });
  await page.waitForTimeout(5000);
  console.log('✅ 로그인 완료');
  
  // Report Summary 페이지로 이동
  await page.goto('https://www.wisereport.co.kr/report/summary', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  // 기업/산업 탭 클릭 - 텍스트로 찾기
  console.log('🔍 기업/산업 탭 클릭...');
  
  try {
    await page.click('text=기업/산업', { timeout: 5000 });
    console.log('✅ 탭 클릭 완료');
    await page.waitForTimeout(3000);
  } catch(e) {
    console.log('⚠️ 탭을 못찾아서 수동 시도');
  }
  
  // 스크린샷
  await page.screenshot({ path: '/tmp/wisereport_company.png', fullPage: true });
  console.log('📸 스크린샷 저장');
  
  // 텍스트 추출
  const text = await page.evaluate(() => document.body.innerText);
  require('fs').writeFileSync('/tmp/wisereport_company.txt', text);
  console.log('💾 텍스트 저장 완료');
  
  await browser.close();
  console.log('👋 완료');
}

main().catch(console.error);
