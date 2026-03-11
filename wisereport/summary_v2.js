const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({ 
    headless: true,
    
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  console.log('📍 Wisereport 접속...');
  await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(3000);
  
  // 팝업 오버레이 제거
  console.log('🔍 팝업 제거...');
  await page.evaluate(() => {
    const overlay = document.getElementById('popup_overlay');
    if (overlay) overlay.remove();
  });
  await page.waitForTimeout(1000);
  
  // 우측 상단 로그인 버튼 찾기
  console.log('🔍 로그인 버튼 클릭...');
  try {
    await page.locator('a:has-text("로그인")').first().click({ timeout: 5000 });
    console.log('✅ 로그인 버튼 클릭');
    await page.waitForTimeout(3000);
  } catch(e) {
    console.log('⚠️ 로그인 버튼 못찾음');
  }
  
  // ID/PW 입력
  console.log('📝 ID/PW 입력...');
  await page.fill('input[type="text"]', 'yngnhe');
  await page.fill('input[type="password"]', 'wldhs232');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(10000);
  
  console.log('✅ 로그인 후 URL:', page.url());
  
  // 팝업 제거
  await page.evaluate(() => {
    document.getElementById('popup_overlay')?.remove();
  });
  
  // Summary 탭으로 이동
  console.log('📊 Summary 탭 이동...');
  try {
    await page.locator('a:has-text("Summary"), a:has-text("Report Summary")').first().click({ timeout: 5000 });
    console.log('✅ Summary 클릭');
    await page.waitForTimeout(5000);
  } catch(e) {
    console.log('⚠️ 직접 URL 이동');
    await page.goto('https://company.wisereport.co.kr/wiseReport/summary/ReportSummary.aspx?cn=wisefn', { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(5000);
  }
  
  console.log('📍 최종 URL:', page.url());
  
  await page.screenshot({ path: '/tmp/wisereport_summary_v2.png', fullPage: true });
  console.log('📸 스크린샷');
  
  const text = await page.evaluate(() => document.body.innerText);
  console.log('텍스트:', text.substring(0, 2500));
  
  await browser.close();
  console.log('👋 완료');
}

main().catch(console.error);
