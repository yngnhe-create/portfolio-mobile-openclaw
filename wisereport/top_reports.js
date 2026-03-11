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
    
    // 2. 상단 로그인
    console.log('✉️ 로그인 중...');
    await page.fill('input[type="text"]:nth-of-type(1)', USERNAME);
    await page.fill('input[type="password"]', PASSWORD);
    await page.evaluate(() => { document.querySelector('form').submit(); });
    console.log('  ✓ 로그인 제출');
    
    await page.waitForTimeout(5000);
    console.log('✅ 로그인 완료');
    
    // 3. "조회수 Top" 메뉴 찾기 및 클릭
    console.log('\n🔍 "조회수 Top" 메뉴 찾는 중...');
    
    const menuSelectors = [
      'a:has-text("조회수")',
      'a:has-text("조회수 TOP")',
      'a:has-text("조회수Top")',
      'a:has-text("조회수 Top")',
      'a:has-text("인기")',
      'a:has-text("인기 리포트")',
      'a:has-text("TOP")',
      'a[title*="조회수"]',
      'a[title*="인기"]',
      'nav a:has-text("조회")',
      '.gnb a:has-text("조회")',
      'header a:has-text("조회")',
      'a[href*="popular"]',
      'a[href*="best"]',
      'a[href*="top"]'
    ];
    
    let menuClicked = false;
    for (const selector of menuSelectors) {
      try {
        const menu = await page.$(selector);
        if (menu) {
          const text = await menu.textContent();
          console.log(`  ✓ 메뉴 발견: "${text?.trim()}" (${selector})`);
          
          await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle', timeout: 20000 }).catch(() => {}),
            menu.click()
          ]);
          
          menuClicked = true;
          console.log('  ✓ 메뉴 클릭 완료');
          await page.waitForTimeout(3000);
          break;
        }
      } catch (e) {
        // 다음 선택자 시도
      }
    }
    
    if (!menuClicked) {
      console.log('  ⚠️ 메뉴를 찾지 못함. 모든 링크에서 검색...');
      
      // 모든 링크에서 "조회수" 포함된 것 찾기
      const allLinks = await page.$$eval('a', as => 
        as.map(a => ({ href: a.href, text: a.textContent?.trim() }))
          .filter(l => l.text?.includes('조회') || l.text?.includes('인기') || l.text?.includes('TOP'))
      );
      
      console.log(`  ${allLinks.length}개 후보 발견:`);
      allLinks.slice(0, 5).forEach((l, i) => {
        console.log(`    ${i + 1}. "${l.text}" -> ${l.href}`);
      });
      
      if (allLinks.length > 0) {
        console.log(`  🖱️ 첫 번째 링크 클릭: "${allLinks[0].text}"`);
        await page.goto(allLinks[0].href, { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
      }
    }
    
    // 4. 현재 페이지 스크린샷
    await page.screenshot({ path: '/tmp/top_reports.png' });
    console.log('\n📸 스크린샷: /tmp/top_reports.png');
    
    // 5. 리포트 목록에서 PDF 다운로드
    console.log('\n💾 PDF 리포트 다운로드 중...');
    
    const downloadPath = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadPath)) {
      fs.mkdirSync(downloadPath, { recursive: true });
    }
    
    // JavaScript 링크에서 PDF 파일명 추출
    const jsLinks = await page.$$eval('a[href^="javascript:"]', as => 
      as.map(a => a.getAttribute('href')).filter(h => h.includes('pdf') || h.includes('report'))
    );
    
    console.log(`📋 JavaScript 링크 ${jsLinks.length}개 발견`);
    
    // PDF 파일명 추출 패턴
    const pdfFiles = [];
    for (const link of jsLinks.slice(0, 10)) {
      const match = link.match(/['"]([^'"]*\.pdf)['"]/);
      if (match && !pdfFiles.includes(match[1])) {
        pdfFiles.push(match[1]);
      }
    }
    
    console.log(`📄 PDF 파일 ${pdfFiles.length}개 추출됨:`);
    pdfFiles.forEach((f, i) => console.log(`  ${i + 1}. ${f}`));
    
    // 6. PDF 다운로드 시도
    let successCount = 0;
    
    for (let i = 0; i < Math.min(5, pdfFiles.length); i++) {
      try {
        const pdfUrl = `https://www.wisereport.co.kr/report/download/${pdfFiles[i]}`;
        console.log(`\n  📥 파일 ${i + 1} 다운로드 시도...`);
        console.log(`     URL: ${pdfUrl}`);
        
        // 직접 파일 다운로드
        const response = await page.evaluate(async (url) => {
          const res = await fetch(url, { credentials: 'include' });
          if (res.ok) {
            const blob = await res.blob();
            return { ok: true, size: blob.size };
          }
          return { ok: false, status: res.status };
        }, pdfUrl);
        
        if (response.ok) {
          console.log(`     ✅ 성공 (${response.size} bytes)`);
          successCount++;
        } else {
          console.log(`     ❌ 실패 (status: ${response.status})`);
        }
        
      } catch (err) {
        console.log(`     ⚠️ 오류: ${err.message}`);
      }
      
      await page.waitForTimeout(1000);
    }
    
    // 7. 결과
    console.log('\n🎉 작업 완료!');
    console.log(`✅ 다운로드 성공: ${successCount}/${pdfFiles.length}`);
    
    const files = fs.readdirSync(downloadPath);
    if (files.length > 0) {
      console.log('\n📄 다운로드된 파일:');
      files.forEach((f, i) => console.log(`  ${i + 1}. ${f}`));
    }
    
    console.log('\n💡 참고:');
    console.log('  - JavaScript 링크로 인해 직접 다운로드가 어려울 수 있습니다.');
    console.log('  - 브라우저에서 직접 클릭하면 다운로드됩니다.');
    
  } catch (error) {
    console.error('\n❌ 오류:', error.message);
    try {
      await page.screenshot({ path: '/tmp/error.png' });
      console.log('📸 오류 스크린샷: /tmp/error.png');
    } catch(e) {}
  } finally {
    await browser.close();
    console.log('\n👋 종료');
  }
}

console.log('🚀 시작\n');
downloadReports();
