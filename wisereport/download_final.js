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
    await page.waitForTimeout(3000);
    
    // 2. 상단 로그인 폼에 ID/PW 입력 (스크린샷 기준)
    console.log('✉️ 로그인 정보 입력 중...');
    
    // 상단의 ID 입력 필드 (placeholder나 주변 텍스트 없이 순수 input)
    await page.fill('input[type="text"]:nth-of-type(1)', USERNAME);
    console.log('  ✓ ID 입력 완료');
    
    // 상단의 PW 입력 필드
    await page.fill('input[type="password"]', PASSWORD);
    console.log('  ✓ PW 입력 완료');
    
    // 3. 로그인 버튼 클릭 (주황색 버튼 - 텍스트 "로그인")
    console.log('🔐 로그인 버튼 찾는 중...');
    
    // 모든 가능한 로그인 버튼 선택자
    const loginButtonSelectors = [
      'button:has-text("로그인")',
      'a:has-text("로그인")',
      'input[value="로그인"]',
      '.btn-login',
      '.login-btn',
      'button[type="submit"]',
      'input[type="submit"]',
      'button.orange',
      '.orange-btn',
      '[class*="login"] button',
      '[class*="login"] a',
      'form button',
      'form input[type="submit"]'
    ];
    
    let buttonClicked = false;
    for (const selector of loginButtonSelectors) {
      try {
        const btn = await page.$(selector);
        if (btn) {
          console.log(`  ✓ 버튼 찾음: ${selector}`);
          await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }).catch(() => {}),
            btn.click()
          ]);
          buttonClicked = true;
          console.log('  ✓ 클릭 완료');
          break;
        }
      } catch (e) {
        // 계속 다음 선택자 시도
      }
    }
    
    if (!buttonClicked) {
      console.log('  ⚠️ 일반 버튼 못찾음, 다른 방법 시도...');
      // form submit 시도
      try {
        await page.evaluate(() => {
          const form = document.querySelector('form');
          if (form) form.submit();
        });
        console.log('  ✓ Form submit 완료');
        await page.waitForTimeout(3000);
      } catch (e) {
        console.log('  ❌ Form submit도 실패');
      }
    }
    
    console.log('✅ 로그인 시도 완료');
    await page.waitForTimeout(5000);
    
    // 로그인 성공 확인
    const currentUrl = page.url();
    console.log('현재 URL:', currentUrl);
    
    // 로그인 후 페이지 확인
    const pageContent = await page.content();
    if (pageContent.includes('로그아웃') || pageContent.includes('마이페이지') || !currentUrl.includes('login')) {
      console.log('✅ 로그인 성공 확인!');
    } else {
      console.log('⚠️ 로그인 상태 확인 중...');
      await page.screenshot({ path: '/tmp/after_login.png' });
      console.log('📸 스크린샷 저장: /tmp/after_login.png');
    }
    
    // 4. 인기 리포트/조회수 TOP 페이지로 이동
    console.log('📊 인기 리포트 페이지로 이동...');
    
    // 메뉴에서 "리포트" 또는 "인기" 클릭
    const menuSelectors = [
      'a:has-text("리포트")',
      'a:has-text("인기")',
      'a:has-text("조회수")',
      '.menu a[href*="report"]',
      'nav a[href*="report"]'
    ];
    
    let reportMenuClicked = false;
    for (const selector of menuSelectors) {
      try {
        const menu = await page.$(selector);
        if (menu) {
          await menu.click();
          console.log('  ✓ 리포트 메뉴 클릭:', selector);
          reportMenuClicked = true;
          await page.waitForTimeout(3000);
          break;
        }
      } catch (e) {}
    }
    
    if (!reportMenuClicked) {
      console.log('  ⚠️ 메뉴 못찾음, 여러 URL 시도...');
      const urls = [
        'https://www.wisereport.co.kr/report/popular',
        'https://www.wisereport.co.kr/report/best',
        'https://www.wisereport.co.kr/Report/Popular',
        'https://www.wisereport.co.kr/report/ranking'
      ];
      for (const url of urls) {
        try {
          console.log(`    시도: ${url}`);
          await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
          await page.waitForTimeout(2000);
          const content = await page.content();
          if (!content.includes('404') && !content.includes('Error')) {
            console.log('    ✓ 페이지 로딩 성공');
            break;
          }
        } catch (e) {}
      }
    }
    
    // 5. 최근 1주일 필터 설정
    console.log('📅 최근 1주일 필터 설정...');
    
    // 기간 선택 (있는 경우)
    const periodSelectors = [
      'select[name="period"]',
      'select[name="dateRange"]',
      '.period-select',
      'button:has-text("1주일")',
      'button:has-text("7일")'
    ];
    
    for (const selector of periodSelectors) {
      try {
        const period = await page.$(selector);
        if (period) {
          // select 요소면 option 선택
          const tagName = await period.evaluate(el => el.tagName.toLowerCase());
          if (tagName === 'select') {
            await period.selectOption('1week');
          } else {
            await period.click();
          }
          console.log('  ✓ 기간 필터 설정');
          await page.waitForTimeout(2000);
          break;
        }
      } catch (e) {}
    }
    
    // 6. 페이지 스크린샷
    await page.screenshot({ path: '/tmp/report_list.png' });
    console.log('📸 리포트 목록 스크린샷: /tmp/report_list.png');
    
    // 7. 리포트 다운로드
    console.log('💾 리포트 다운로드 시작...');
    
    const downloadPath = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadPath)) {
      fs.mkdirSync(downloadPath, { recursive: true });
    }
    
    // 다운로드 링크들 찾기
    const downloadLinks = await page.$$('a[href*="download"], .btn-download, a[href$=".pdf"]');
    console.log(`📋 찾은 다운로드 링크: ${downloadLinks.length}개`);
    
    let successCount = 0;
    
    for (let i = 0; i < Math.min(5, downloadLinks.length); i++) {
      try {
        console.log(`  📥 파일 ${i + 1} 다운로드 중...`);
        
        const [download] = await Promise.all([
          page.waitForEvent('download', { timeout: 30000 }),
          downloadLinks[i].click()
        ]);
        
        const suggestedFilename = download.suggestedFilename();
        const filePath = path.join(downloadPath, suggestedFilename);
        
        await download.saveAs(filePath);
        
        // 파일 크기 확인
        const stats = fs.statSync(filePath);
        console.log(`  ✅ 저장 완료: ${suggestedFilename} (${(stats.size / 1024).toFixed(1)} KB)`);
        
        successCount++;
        await page.waitForTimeout(2000);
        
      } catch (err) {
        console.log(`  ⚠️ 다운로드 실패: ${err.message}`);
      }
    }
    
    // 8. 결과 출력
    console.log('\n🎉 작업 완료!');
    console.log(`📂 다운로드 경로: ${downloadPath}`);
    console.log(`📄 성공적으로 다운로드: ${successCount}개`);
    
    const files = fs.readdirSync(downloadPath);
    if (files.length > 0) {
      console.log('\n📄 다운로드된 파일 목록:');
      files.forEach((file, idx) => {
        const filePath = path.join(downloadPath, file);
        const stats = fs.statSync(filePath);
        console.log(`  ${idx + 1}. ${file}`);
        console.log(`     크기: ${(stats.size / 1024).toFixed(1)} KB`);
      });
      
      console.log('\n📤 Google Drive 업로드 준비 완료!');
      console.log('  파일을 Google Drive에 업로드하려면 다음 단계를 진행하세요.');
      
    } else {
      console.log('❌ 다운로드된 파일이 없습니다.');
      console.log('   페이지 구조를 확인하기 위해 스크린샷을 확인해주세요.');
    }
    
  } catch (error) {
    console.error('\n❌ 오류 발생:', error.message);
    console.error(error.stack);
    
    // 오류 시 스크린샷
    try {
      await page.screenshot({ path: '/tmp/error_screenshot.png' });
      console.log('📸 오류 스크린샷: /tmp/error_screenshot.png');
    } catch (e) {}
    
  } finally {
    await browser.close();
    console.log('\n👋 브라우저 종료');
  }
}

console.log('🚀 Wise Report 자동 다운로드 시작\n');
downloadReports();
