const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const WISE_REPORT_URL = 'https://wisereport.co.kr';
const USERNAME = 'yngnhe';
const PASSWORD = 'wldhs232';

async function downloadReports() {
  console.log('🚀 Wise Report 자동 다운로드 시작');
  console.log('================================');
  
  // 시스템 설치된 Chrome 사용
  const chromePath = '/usr/bin/google-chrome';
  
  if (!fs.existsSync(chromePath)) {
    console.error('❌ Chrome을 찾을 수 없습니다:', chromePath);
    console.log('Chrome 설치 경로를 확인해주세요.');
    return;
  }
  
  console.log('✅ Chrome 경로:', chromePath);
  
  const browser = await chromium.launch({ 
    headless: true,  // 헤드리스 모드
    executablePath: chromePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    });
    
    const page = await context.newPage();
    
    // 1. 접속
    console.log('📍 사이트 접속 중...');
    await page.goto(WISE_REPORT_URL, { waitUntil: 'networkidle', timeout: 60000 });
    
    // 2. 로그인
    console.log('🔐 로그인 중...');
    
    // 로그인 버튼/링크 찾기
    const loginButton = await page.$('a[href*="login"], .login-btn, #login');
    if (loginButton) {
      await loginButton.click();
      await page.waitForTimeout(2000);
    }
    
    // ID/PW 입력
    await page.fill('input[name="id"], input[name="username"], #id', USERNAME);
    await page.fill('input[name="pw"], input[name="password"], #pw', PASSWORD);
    
    // 로그인 버튼 클릭
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }).catch(() => {}),
      page.click('button[type="submit"], .btn-login, #login_btn')
    ]);
    
    console.log('✅ 로그인 완료');
    await page.waitForTimeout(3000);
    
    // 3. 인기 리포트 페이지로 이동
    console.log('📊 인기 리포트 페이지로 이동...');
    await page.goto('https://wisereport.co.kr/report/popular', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    // 4. 리포트 목록에서 다운로드
    console.log('💾 리포트 다운로드 중...');
    
    // 다운로드 폴더 설정
    const downloadPath = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadPath)) {
      fs.mkdirSync(downloadPath, { recursive: true });
    }
    
    // 리포트 링크들 찾기 (최근 1주일 조회수 TOP)
    const reportLinks = await page.$$('a[href*="download"], .report-item a, .btn-download');
    
    console.log(`📋 찾은 리포트 수: ${reportLinks.length}`);
    
    // 상위 5개 리포트 다운로드
    for (let i = 0; i < Math.min(5, reportLinks.length); i++) {
      try {
        console.log(`  📥 리포트 ${i + 1} 다운로드 중...`);
        
        // 새 탭에서 다운로드 처리
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          reportLinks[i].click()
        ]);
        
        const filePath = path.join(downloadPath, download.suggestedFilename());
        await download.saveAs(filePath);
        console.log(`  ✅ 저장 완료: ${path.basename(filePath)}`);
        
        await page.waitForTimeout(2000);
      } catch (err) {
        console.log(`  ⚠️ 다운로드 실패: ${err.message}`);
      }
    }
    
    console.log('\n🎉 작업 완료!');
    console.log(`📂 다운로드 경로: ${downloadPath}`);
    
    // 다운로드된 파일 목록 출력
    const files = fs.readdirSync(downloadPath);
    console.log('\n📄 다운로드된 파일:');
    files.forEach((file, idx) => {
      console.log(`  ${idx + 1}. ${file}`);
    });
    
    // Google Drive 업로드 안내
    console.log('\n📤 다음 단계: Google Drive 업로드');
    console.log('  download/ 폴더의 파일을 확인해주세요.');
    
  } catch (error) {
    console.error('\n❌ 오류 발생:', error.message);
    
    // 스크린샷 저장 (디버깅용)
    try {
      await page.screenshot({ path: '/tmp/wisereport_error.png' });
      console.log('📸 스크린샷 저장: /tmp/wisereport_error.png');
    } catch(e) {}
    
  } finally {
    await browser.close();
    console.log('\n👋 브라우저 종료');
  }
}

// 실행
console.log('🚀 Wise Report 자동 다운로드 시작\n');
downloadReports();
