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
  
  // Report Summary 페이지로 직접 이동
  console.log('📊 Report Summary 페이지 이동...');
  await page.goto('https://company.wisereport.co.kr/wiseReport/summary/ReportSummary.aspx?cn=wisefn', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(5000);
  
  // 스크린샷
  await page.screenshot({ path: '/tmp/wisereport_summary2.png', fullPage: true });
  console.log('📸 스크린샷 저장');
  
  // 텍스트 추출
  const text = await page.evaluate(() => document.body.innerText);
  require('fs').writeFileSync('/tmp/wisereport_summary2.txt', text);
  
  // HTML 저장
  const html = await page.content();
  require('fs').writeFileSync('/tmp/wisereport_summary2.html', html);
  
  await browser.close();
  console.log('👋 완료');
}

main().catch(console.error);
