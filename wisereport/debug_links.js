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
    
    // 2. 상단 로그인 폼에 ID/PW 입력
    console.log('✉️ 로그인 정보 입력 중...');
    await page.fill('input[type="text"]:nth-of-type(1)', USERNAME);
    console.log('  ✓ ID 입력 완료');
    await page.fill('input[type="password"]', PASSWORD);
    console.log('  ✓ PW 입력 완료');
    
    // 3. 로그인
    console.log('🔐 로그인 시도 중...');
    await page.evaluate(() => {
      const form = document.querySelector('form');
      if (form) form.submit();
    });
    console.log('  ✓ Form submit 완료');
    
    await page.waitForTimeout(5000);
    
    const currentUrl = page.url();
    console.log('현재 URL:', currentUrl);
    console.log('✅ 로그인 완료!');
    
    // 4. 메인 페이지에서 모든 링크 확인
    console.log('\n📋 메인 페이지에서 모든 링크 검색 중...');
    
    const links = await page.$$eval('a', as => as.map(a => ({
      href: a.href,
      text: a.textContent?.trim(),
      class: a.className
    })));
    
    console.log(`총 ${links.length}개 링크 발견`);
    
    // 리포트 관련 링크 찾기
    const reportLinks = links.filter(l => 
      l.text?.includes('리포트') || 
      l.text?.includes('인기') || 
      l.text?.includes('조회수') ||
      l.href?.includes('report')
    );
    
    console.log('\n📊 리포트 관련 링크:');
    reportLinks.forEach((l, i) => {
      console.log(`  ${i + 1}. ${l.text} -> ${l.href}`);
    });
    
    // 5. 첫 번째 리포트 링크 클릭
    if (reportLinks.length > 0) {
      console.log('\n🖱️ 리포트 링크 클릭...');
      await page.goto(reportLinks[0].href, { waitUntil: 'networkidle' });
      await page.waitForTimeout(3000);
    } else {
      console.log('⚠️ 리포트 링크 없음, 메인 페이지에서 계속');
    }
    
    // 6. 스크린샷
    await page.screenshot({ path: '/tmp/current_page.png' });
    console.log('\n📸 현재 페이지 스크린샷: /tmp/current_page.png');
    
    // 7. 페이지에서 모든 PDF/다운로드 링크 찾기
    console.log('\n🔍 다운로드 가능한 파일 검색 중...');
    
    const allLinks = await page.$$eval('a', as => as.map(a => ({
      href: a.href,
      text: a.textContent?.trim().substring(0, 50)
    })));
    
    const downloadables = allLinks.filter(l => 
      l.href?.includes('.pdf') || 
      l.href?.includes('download') ||
      l.href?.includes('file')
    );
    
    console.log(`📥 다운로드 가능한 링크: ${downloadables.length}개`);
    downloadables.forEach((l, i) => {
      console.log(`  ${i + 1}. ${l.text} -> ${l.href}`);
    });
    
    // 8. 파일 다운로드
    const downloadPath = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadPath)) {
      fs.mkdirSync(downloadPath, { recursive: true });
    }
    
    let successCount = 0;
    
    for (let i = 0; i < Math.min(5, downloadables.length); i++) {
      try {
        console.log(`\n  📥 파일 ${i + 1} 다운로드 중...`);
        console.log(`     URL: ${downloadables[i].href}`);
        
        await page.goto(downloadables[i].href, { waitUntil: 'download', timeout: 30000 });
        
        successCount++;
        await page.waitForTimeout(2000);
        
      } catch (err) {
        console.log(`     ⚠️ 실패: ${err.message}`);
      }
    }
    
    // 9. 결과
    console.log('\n🎉 작업 완료!');
    console.log(`✅ 다운로드 시도: ${successCount}개`);
    console.log(`📂 저장 경로: ${downloadPath}`);
    
    const files = fs.readdirSync(downloadPath);
    if (files.length > 0) {
      console.log('\n📄 다운로드된 파일:');
      files.forEach((f, i) => console.log(`  ${i + 1}. ${f}`));
    } else {
      console.log('\n❌ 다운로드된 파일 없음');
      console.log('   위 링크 목록을 확인하여 실제 다운로드 URL을 찾아야 합니다.');
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
