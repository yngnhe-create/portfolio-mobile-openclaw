/**
 * WiseReport Report Summary 스크래퍼 — 최종 버전
 *
 * 핵심 발견:
 * - company.wisereport.co.kr 접근 시 URL에 enc= 토큰 필요
 * - 이 토큰은 www.wisereport.co.kr 의 MP Summary 페이지에서 링크 클릭 시 발급됨
 * - 직접 URL 접근(goto) 대신 실제 링크 클릭으로 새 탭 열기 필요
 *
 * 동작:
 * 1. www.wisereport.co.kr 로그인 (JS 직접 값 설정 + form submit)
 * 2. wiseMP/Summary.aspx 이동
 * 3. Report Summary 링크 클릭 → 새 탭에서 enc= 토큰 포함 URL 열림
 * 4. 기업/산업/정기 탭 데이터 추출
 */

const { chromium } = require('playwright');
const fs   = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'wisereport_data');

async function scrape() {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-web-security',   // 크로스도메인 링크 허용
    ],
  });

  // 새 탭을 같은 컨텍스트에서 열기 위해 waitForEvent 사용
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  try {
    // ── 1. 메인 로드 ───────────────────────────────────────────
    console.log('📍 메인 페이지 로드...');
    await page.goto('https://www.wisereport.co.kr', { waitUntil: 'domcontentloaded', timeout: 30000 });

    // 팝업 닫기
    try { await page.click('#closeBtn', { timeout: 2000 }); } catch (_) {}

    // ── 2. 로그인 ─────────────────────────────────────────────
    console.log('🔑 로그인 시도...');
    await page.evaluate(() => {
      ['UsrID_Login', 'UsrID'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.value = 'yngnhe'; el.dispatchEvent(new Event('input', {bubbles:true})); }
      });
      ['UsrPassWD_Login', 'UsrPassWD'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.value = 'wldhs232'; el.dispatchEvent(new Event('input', {bubbles:true})); }
      });
    });

    // form submit
    await page.evaluate(() => document.querySelector('form')?.submit());
    await page.waitForTimeout(5000);

    // 중복 로그인 팝업
    try {
      const btn = page.locator('button:has-text("확인")').first();
      if (await btn.isVisible({ timeout: 2000 })) { await btn.click(); await page.waitForTimeout(2000); }
    } catch (_) {}

    const loggedIn = await page.evaluate(() => document.body.innerText.includes('YNGNHE'));
    console.log(loggedIn ? '✅ 로그인 확인' : '⚠ 로그인 불명확 (계속 진행)');

    // ── 3. MP Summary로 이동 ───────────────────────────────────
    console.log('📄 MP Summary 이동...');
    await page.goto('https://www.wisereport.co.kr/wiseMP/Summary.aspx', {
      waitUntil: 'domcontentloaded', timeout: 30000,
    });
    await page.waitForTimeout(2000);

    // ── 4. Report Summary 링크 클릭 → 새 탭 대기 ─────────────
    console.log('📊 Report Summary 링크 클릭 (새 탭)...');
    const [newPage] = await Promise.all([
      context.waitForEvent('page', { timeout: 15000 }),
      page.evaluate(() => {
        const link = Array.from(document.querySelectorAll('a'))
          .find(a => a.href?.includes('ReportSummary'));
        if (link) { link.target = '_blank'; link.click(); return link.href; }
        return null;
      }),
    ]);

    await newPage.waitForLoadState('networkidle', { timeout: 30000 });
    const reportUrl = newPage.url();
    console.log('🔗 Report Summary URL:', reportUrl);

    const isError = await newPage.evaluate(() =>
      document.body.innerText.includes('권한 오류') ||
      document.body.innerText.includes('접속한 사용자가 아닙니다')
    );
    if (isError) {
      console.error('❌ 권한 오류 — 로그인 실패');
      fs.writeFileSync(path.join(DATA_DIR, 'error.html'), await newPage.content());
      await browser.close();
      return null;
    }

    console.log('🎉 Report Summary 접근 성공!');

    // ── 5. enc 토큰 저장 (재사용 가능한지 확인용) ─────────────
    const encToken = new URL(reportUrl).searchParams.get('enc');
    if (encToken) {
      fs.writeFileSync(path.join(__dirname, 'enc_token.txt'), reportUrl);
      console.log('💾 enc 토큰 저장됨');
    }

    // ── 6. 기업 탭 수집 ────────────────────────────────────────
    const dateStr = new Date().toISOString().split('T')[0];
    const result = {
      date: dateStr,
      scrape_time: new Date().toISOString(),
      url: reportUrl,
      tabs: {},
    };

    console.log('  📋 기업 탭...');
    result.tabs.company = await extractTab(newPage);

    // 산업 탭
    console.log('  📋 산업 탭...');
    await newPage.evaluate(() => {
      const a = Array.from(document.querySelectorAll('a')).find(el => el.innerText.trim() === '산업');
      if (a) a.click();
    });
    await newPage.waitForTimeout(2000);
    result.tabs.industry = await extractTab(newPage);

    // 정기 탭
    console.log('  📋 정기 탭...');
    await newPage.evaluate(() => {
      const a = Array.from(document.querySelectorAll('a')).find(el => el.innerText.trim() === '정기');
      if (a) a.click();
    });
    await newPage.waitForTimeout(2000);
    result.tabs.regular = await extractTab(newPage);

    const total = Object.values(result.tabs).reduce((s, a) => s + a.length, 0);
    console.log(`\n📊 수집: 기업 ${result.tabs.company.length}건 / 산업 ${result.tabs.industry.length}건 / 정기 ${result.tabs.regular.length}건 = 총 ${total}건`);

    // 스크린샷
    await newPage.screenshot({ path: path.join(DATA_DIR, `summary_${dateStr}.png`), fullPage: true });

    // JSON 저장
    const jsonPath = path.join(DATA_DIR, `wisereport_complete_${dateStr}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
    console.log(`💾 ${jsonPath}`);

    await browser.close();
    return result;

  } catch (err) {
    console.error('❌ 오류:', err.message);
    try { await page.screenshot({ path: path.join(DATA_DIR, 'error.png') }); } catch (_) {}
    await browser.close();
    return null;
  }
}

async function extractTab(page) {
  return await page.evaluate(() => {
    const rows = [];
    document.querySelectorAll('table tr').forEach(tr => {
      const tds = Array.from(tr.querySelectorAll('td'));
      if (tds.length < 3) return;
      const cells = tds.map(td => td.innerText.trim().replace(/\s+/g, ' '));
      // 헤더/빈 행 스킵
      if (!cells[0] || cells[0].length > 60) return;
      if (/종목명|구분|일자|증권사명/.test(cells[0])) return;

      rows.push({
        name:        cells[0] || '',
        opinion:     cells[1] || '',
        target:      cells[2] || '',
        current:     cells[3] || '',
        title:       cells[4] || '',
        description: cells[5] || '',
        firm:        cells[6] || '',
        date:        cells[7] || '',
      });
    });
    return rows;
  });
}

// ── 실행 ─────────────────────────────────────────────────────────
scrape().then(r => {
  if (r) {
    const total = Object.values(r.tabs).reduce((s, a) => s + a.length, 0);
    console.log(`\n✅ 완료: 총 ${total}건`);
  } else {
    console.log('\n❌ 실패');
    process.exit(1);
  }
}).catch(err => { console.error(err); process.exit(1); });
