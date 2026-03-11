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
  
  // 모든 팝업/오버레이 제거
  console.log('🔍 팝업 제거...');
  await page.evaluate(() => {
    const overlay = document.getElementById('popup_overlay');
    if (overlay) overlay.style.display = 'none';
    const overlays = document.querySelectorAll('[class*="popup"], [class*="modal"], [class*="overlay"]');
    overlays.forEach(o => o.style.display = 'none');
  });
  await page.waitForTimeout(1000);
  
  // 로그인 버튼 클릭 (우측 상단)
  console.log('🔍 로그인 버튼 클릭...');
  const loginLink = await page.locator('a').filter({ hasText: '로그인' }).first();
  if (await loginLink.isVisible()) {
    await loginLink.click();
    console.log('✅ 로그인 버튼 클릭');
    await page.waitForTimeout(3000);
  }
  
  // 팝업 제거
  await page.evaluate(() => {
    document.getElementById('popup_overlay')?.remove();
  });
  
  // ID/PW 입력
  console.log('📝 ID/PW 입력...');
  await page.fill('input[type="text"]', 'yngnhe');
  await page.fill('input[type="password"]', 'wldhs232');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(10000);
  
  console.log('✅ 로그인 후 URL:', page.url());
  
  // 팝업 제거
  await page.evaluate(() => {
    const overlay = document.getElementById('popup_overlay');
    if (overlay) overlay.remove();
  });
  await page.waitForTimeout(2000);
  
  // Report Summary 링크 찾기
  console.log('🔍 Report Summary 찾기...');
  const rsLink = await page.locator('a').filter({ hasText: 'Report Summary' }).first();
  
  if (await rsLink.isVisible({ timeout: 5000 })) {
    console.log('✅ Report Summary 발견, 클릭...');
    await rsLink.click();
    await page.waitForTimeout(8000);
  } else {
    console.log('⚠️ 직접 URL 이동...');
    // company.wisereport.co.kr로 이동
    await page.goto('https://company.wisereport.co.kr', { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(5000);
  }
  
  console.log('📍 최종 URL:', page.url());
  
  await page.screenshot({ path: '/tmp/wisereport_final.png', fullPage: true });
  console.log('📸 스크린샷');
  
  const text = await page.evaluate(() => document.body.innerText);
  console.log('텍스트:', text.substring(0, 3000));
  
  await browser.close();
}

main().catch(console.error);
