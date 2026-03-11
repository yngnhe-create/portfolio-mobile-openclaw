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
  
  // 팝업 제거
  await page.evaluate(() => {
    document.getElementById('popup_overlay')?.remove();
  });
  await page.waitForTimeout(1000);
  
  // 로그인 버튼 클릭 (우측 상단)
  console.log('🔍 로그인 버튼 클릭...');
  try {
    await page.click('a:has-text("로그인")', { timeout: 5000 });
    console.log('✅ 로그인 버튼 클릭');
    await page.waitForTimeout(3000);
  } catch(e) {
    console.log('⚠️ 실패');
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
    document.getElementById('popup_overlay')?.remove();
  });
  await page.waitForTimeout(2000);
  
  // 메인 페이지에서 Summary 링크 찾기
  console.log('🔍 Summary 링크 찾기...');
  const summaryLinks = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll('a'));
    return links.filter(l => l.textContent.includes('Summary') || l.textContent.includes('요약') || l.href?.includes('summary')).map(l => ({ text: l.textContent, href: l.href }));
  });
  
  console.log('Summary 관련 링크:', JSON.stringify(summaryLinks));
  
  // Report Summary 클릭
  console.log('📊 Report Summary 클릭...');
  try {
    await page.click('a:has-text("Report Summary")', { timeout: 5000 });
    console.log('✅ Report Summary 클릭');
    await page.waitForTimeout(8000);
  } catch(e) {
    console.log('⚠️ 실패');
  }
  
  console.log('📍 최종 URL:', page.url());
  
  await page.screenshot({ path: '/tmp/wisereport_summary_v3.png', fullPage: true });
  console.log('📸 스크린샷');
  
  const text = await page.evaluate(() => document.body.innerText);
  console.log('텍스트:', text.substring(0, 2000));
  
  await browser.close();
}

main().catch(console.error);
