const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const WISE_REPORT_URL = 'https://wisereport.co.kr';
const USERNAME = 'yngnhe';
const PASSWORD = 'wldhs232';

async function downloadReports() {
  console.log('🚀 Wise Report 자동 다운로드 시작');
  console.log('================================');
  
  const chromePath = '/usr/bin/google-chrome';
  
  if (!fs.existsSync(chromePath)) {
    console.error('❌ Chrome을 찾을 수 없습니다:', chromePath);
    return;
  }
  
  console.log('✅ Chrome 경로:', chromePath);
  
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: chromePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    });
    
    const page = await context.newPage();
    
    // 1. 메인 페이지 접속
    console.log('📍 메인 페이지 접속 중...');
    await page.goto(WISE_REPORT_URL, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(2000);
    
    // 2. 오른쪽 상단 로그인 버튼 클릭
    console.log('🔐 오른쪽 상단 로그인 버튼 클릭...');
    
    const loginSelectors = [
      'header .login',
      'header a[href*="login"]',
      '.header .login',
      '.gnb .login',
      'a:has-text("로그인")',
      '.btn-login',
      '#login',
      '[class*="login"]'
    ];
    
    let loginClicked = false;
    for (const selector of loginSelectors) {
      try {
        const loginBtn = await page.$(selector);
        if (loginBtn) {
          await loginBtn.click();
          console.log('✅ 로그인 버튼 클릭됨:', selector);
          loginClicked = true;
          break;
        }
      } catch (e) {}
    }
    
    if (!loginClicked) {
      console.log('⚠️ 로그인 버튼 못찾음, 직접 이동...');
      await page.goto('https://wisereport.co.kr/login', { waitUntil: 'networkidle' });
    }
    
    await page.waitForTimeout(3000);
    
    // 3. ID/PW 입력
    console.log('✉️ 로그인 정보 입력 중...');
    
    await page.waitForSelector('input[type="text"], input[name="id"], input[name="username"], #id', { timeout: 10000 });
    await page.fill('input[type="text"], input[name="id"], input[name="username"], #id', USERNAME);
    
    await page.waitForSelector('input[type="password"], input[name="pw"], input[name="password"], #pw', { timeout: 10000 });
    await page.fill('input[type="password"], input[name="pw"], input[name="password"], #pw', PASSWORD);
    
    console.log('✅ 로그인 정보 입력 완료');
    
    // 4. 로그인 버튼 클릭
    console.log('⏳ 로그인 시도 중...');
    const submitSelectors = [
      'button[type="submit"]',
      '.btn-login',
      '.btn-primary',
      'button:has-text("로그인")'
    ];
    
    for (const selector of submitSelectors) {
      try {
        const submitBtn = await page.$(selector);
        if (submitBtn) {
          await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }).catch(() => {}),
            submitBtn.click()
          ]);
          console.log('✅ 로그인 제출됨');
          break;
        }
      } catch (e) {}
    }
    
    await page.waitForTimeout(3000);
    
    const currentUrl = page.url();
    console.log('현재 URL:', currentUrl);
    
    if (currentUrl.includes('login')) {
      console.log('❌ 로그인 실패');
      await page.screenshot({ path: '/tmp/login_failed.png' });
      return;
    }
    
    console.log('✅ 로그인 성공!');
    
    // 5. 인기 리포트 페이지로 이동
    console.log('📊 인기 리포트 페이지로 이동...');
    await page.goto('https://wisereport.co.kr/report/popular', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    await page.screenshot({ path: '/tmp/popular_page.png' });
    console.log('📸 인기 리포트 페이지 스크린샷: /tmp/popular_page.png');
    
    // 6. 리포트 다운로드
    console.log('💾 리포트 다운로드 중...');
    
    const downloadPath = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadPath)) {
      fs.mkdirSync(downloadPath, { recursive: true });
    }
    
    const reportItems = await page.$$('tr, .report-item, .list-item');
    console.log(`📋 찾은 리포트 항목: ${reportItems.length}`);
    
    let downloadCount = 0;
    
    for (let i = 0; i < Math.min(5, reportItems.length); i++) {
      try {
        const downloadBtn = await reportItems[i].$('a[href*="download"], .btn-download, .download');
        if (downloadBtn) {
          downloadCount++;
          console.log(`  📥 리포트 ${downloadCount} 다운로드 중...`);
          
          const [download] = await Promise.all([
            page.waitForEvent('download'),
            downloadBtn.click()
          ]);
          
          const filePath = path.join(downloadPath, download.suggestedFilename());
          await download.saveAs(filePath);
          console.log(`  ✅ 저장 완료: ${path.basename(filePath)}`);
          
          await page.waitForTimeout(2000);
        }
      } catch (err) {
        console.log(`  ⚠️ 항목 ${i + 1} 실패: ${err.message}`);
      }
    }
    
    console.log('\n🎉 작업 완료!');
    console.log(`📂 다운로드 경로: ${downloadPath}`);
    console.log(`📄 총 ${downloadCount}개 다운로드됨`);
    
    const files = fs.readdirSync(downloadPath);
    if (files.length > 0) {
      console.log('\n📄 다운로드된 파일:');
      files.forEach((file, idx) => {
        console.log(`  ${idx + 1}. ${file}`);
      });
    }
    
  } catch (error) {
    console.error('\n❌ 오류:', error.message);
    try {
      await page.screenshot({ path: '/tmp/error.png' });
    } catch(e) {}
  } finally {
    await browser.close();
    console.log('\n👋 종료');
  }
}

console.log('🚀 시작\n');
downloadReports();
