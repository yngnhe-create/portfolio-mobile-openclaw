const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * WiseReport 스크래퍼 v2
 * 핵심 수정: 로그인 후 같은 도메인 내에서 Report Summary로 이동
 * (company.wisereport.co.kr 직접 접근 시 세션 쿠키 미전달 문제 해결)
 */
async function main() {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();
  
  try {
    // Step 1: 로그인
    console.log('📍 로그인 중...');
    await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle', timeout: 60000 });
    
    // 로그인 폼 입력
    await page.fill('input[type="text"]', 'yngnhe');
    await page.fill('input[type="password"]', 'wldhs232');
    
    // 폼 제출
    await page.evaluate(() => {
      const form = document.querySelector('form');
      if (form) form.submit();
    });
    await page.waitForTimeout(5000);
    
    // 중복 로그인 팝업 처리
    try {
      const popup = await page.locator('text=확인').first();
      if (await popup.isVisible({ timeout: 3000 })) {
        await popup.click();
        await page.waitForTimeout(2000);
        console.log('✅ 중복 로그인 팝업 처리');
      }
    } catch (e) {
      // 팝업 없으면 무시
    }
    console.log('✅ 로그인 완료');
    
    // Step 2: 현재 쿠키 확인 후 Report Summary로 이동
    // wisereport.co.kr 내의 링크를 통해 이동 (쿠키 공유 위해)
    console.log('📊 Report Summary 페이지 이동...');
    
    // 방법 1: 메뉴 클릭으로 이동 시도
    try {
      // 기업분석 메뉴 찾기
      const menuLink = await page.locator('a:has-text("리포트"), a:has-text("Report"), a:has-text("기업")').first();
      if (await menuLink.isVisible({ timeout: 3000 })) {
        await menuLink.click();
        await page.waitForTimeout(3000);
        console.log('✅ 메뉴 클릭으로 이동');
      }
    } catch (e) {
      console.log('⚠️ 메뉴 클릭 실패, 직접 이동 시도');
    }
    
    // 방법 2: 쿠키를 company 서브도메인으로 복사 후 직접 이동
    const cookies = await context.cookies();
    console.log(`🍪 현재 쿠키: ${cookies.length}개`);
    
    // wisereport.co.kr 쿠키를 company.wisereport.co.kr에도 설정
    const companyCookies = cookies
      .filter(c => c.domain.includes('wisereport'))
      .map(c => ({
        ...c,
        domain: '.wisereport.co.kr', // 와일드카드 도메인으로 변경
      }));
    
    if (companyCookies.length > 0) {
      await context.addCookies(companyCookies);
      console.log(`🍪 서브도메인 쿠키 설정: ${companyCookies.length}개`);
    }
    
    // Report Summary 페이지 이동
    await page.goto('https://comp.wisereport.co.kr/company/c1070001.aspx', { 
      waitUntil: 'networkidle', 
      timeout: 60000 
    });
    await page.waitForTimeout(5000);
    
    // 오류 페이지 확인
    const pageText = await page.evaluate(() => document.body.innerText);
    if (pageText.includes('권한 오류') || pageText.includes('접속한 사용자가 아닙니다')) {
      console.log('⚠️ 권한 오류 감지, 대체 방법 시도...');
      
      // 방법 3: wisereport.co.kr에서 iframe/리다이렉트 방식으로 접근
      await page.goto('https://wisereport.co.kr', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      
      // 사이트 내 기업분석/리포트 링크 탐색
      const links = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('a')).map(a => ({
          href: a.href,
          text: a.innerText.trim()
        })).filter(l => l.href && l.text);
      });
      
      console.log('📋 사이트 내 링크:');
      links.forEach(l => console.log(`  - [${l.text}] ${l.href}`));
      
      // Report Summary 관련 링크 찾기
      const reportLink = links.find(l => 
        l.href.includes('summary') || 
        l.href.includes('report') ||
        l.text.includes('리포트') ||
        l.text.includes('Report')
      );
      
      if (reportLink) {
        console.log(`🔗 리포트 링크 발견: ${reportLink.href}`);
        await page.goto(reportLink.href, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(3000);
      }
    }
    
    // Step 3: 데이터 추출
    console.log('📝 데이터 추출 중...');
    const bodyText = await page.evaluate(() => document.body.innerText);
    const bodyHtml = await page.content();
    
    // 스크린샷 저장
    const dateStr = new Date().toISOString().split('T')[0];
    const screenshotPath = path.join(__dirname, '..', 'wisereport_data', `wisereport_${dateStr}_summary.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 스크린샷: ${screenshotPath}`);
    
    // 텍스트 저장
    const textPath = path.join(__dirname, '..', 'wisereport_data', `wisereport_${dateStr}_summary.txt`);
    fs.writeFileSync(textPath, bodyText);
    
    // HTML 저장
    const htmlPath = path.join(__dirname, '..', 'wisereport_data', `wisereport_${dateStr}_summary.html`);
    fs.writeFileSync(htmlPath, bodyHtml);
    
    console.log(`📄 텍스트: ${textPath}`);
    console.log(`📄 HTML: ${htmlPath}`);
    
    // Step 4: 테이블 데이터 파싱 시도
    const tableData = await page.evaluate(() => {
      const rows = [];
      document.querySelectorAll('table tr').forEach(tr => {
        const cells = [];
        tr.querySelectorAll('td, th').forEach(td => {
          cells.push(td.innerText.trim());
        });
        if (cells.length > 0) rows.push(cells);
      });
      return rows;
    });
    
    if (tableData.length > 0) {
      const jsonPath = path.join(__dirname, '..', 'wisereport_data', `wisereport_${dateStr}_parsed.json`);
      fs.writeFileSync(jsonPath, JSON.stringify({ date: dateStr, tables: tableData }, null, 2));
      console.log(`📊 파싱 데이터: ${jsonPath} (${tableData.length}행)`);
    }
    
    console.log('✅ 완료');
    
  } catch (error) {
    console.error('❌ 오류:', error.message);
    
    // 오류 시 현재 상태 스크린샷
    try {
      await page.screenshot({ 
        path: path.join(__dirname, '..', 'wisereport_data', 'error_screenshot.png'), 
        fullPage: true 
      });
    } catch (e) {}
    
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
