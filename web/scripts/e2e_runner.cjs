const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:5173';
const SCREENSHOTS_DIR = path.resolve(__dirname, '../../reports/ui_screenshots');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function runE2ETests() {
  console.log('--- Starting Playwright End-to-End Test Suite ---');
  console.log(`Target URL: ${BASE_URL}`);
  console.log(`Screenshots will be saved to: ${SCREENSHOTS_DIR}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  page.on('response', resp => {
    if (resp.status() === 404) {
      console.log('404 Response URL:', resp.url());
    }
  });

  const testResults = [];
  function record(name, passed, details = '') {
    testResults.push({ name, passed, details });
    console.log(`${passed ? '✓ PASS' : '✗ FAIL'}: ${name} ${details ? '(' + details + ')' : ''}`);
  }

  try {
    // 1. Unauthenticated redirects
    console.log('\n[Phase 1] Testing Unauthenticated Guards...');
    await page.goto(`${BASE_URL}/`);
    await page.waitForURL('**/login', { timeout: 10000 });
    record('Root redirect to /login when unauthenticated', page.url().includes('/login'));

    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForURL('**/login', { timeout: 10000 });
    record('/dashboard redirect to /login', page.url().includes('/login'));

    await page.goto(`${BASE_URL}/diet-planner`);
    await page.waitForURL('**/login', { timeout: 10000 });
    record('/diet-planner redirect to /login', page.url().includes('/login'));

    await page.goto(`${BASE_URL}/history`);
    await page.waitForURL('**/login', { timeout: 10000 });
    record('/history redirect to /login', page.url().includes('/login'));

    // Capture unauthenticated screenshots
    await captureResponsive(page, 'login', `${BASE_URL}/login`);

    // 2. Invalid Login Handling
    console.log('\n[Phase 2] Testing Invalid Credentials...');
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#email', 'invalid.user@example.com');
    await page.fill('#password', 'WrongPassword999!');
    await page.click('button[type="submit"]');
    await page.waitForSelector('text=Invalid email or password', { timeout: 8000 });
    record('Invalid login shows generic error message', true);

    // 3. Registration Flow
    console.log('\n[Phase 3] Testing Registration & Onboarding Flow...');
    const timestamp = Date.now().toString().slice(-6);
    const testEmail = `clinical.user_${timestamp}@clinical-test.org`;
    const testName = `Jordan Clinical_${timestamp}`;
    const testPassword = 'Password123!';

    await page.goto(`${BASE_URL}/register`);
    await captureResponsive(page, 'register', `${BASE_URL}/register`);

    await page.fill('#fullName', testName);
    await page.fill('#regEmail', testEmail);
    await page.fill('#regPassword', testPassword);
    await page.fill('#confirmPassword', testPassword);
    await page.click('input[type="checkbox"]');
    await page.click('button[type="submit"]');

    // Wait for redirect to onboarding
    await page.waitForURL('**/onboarding', { timeout: 12000 });
    record('Registration redirects first-time user to /onboarding', page.url().includes('/onboarding'));

    // Onboarding Step 1: Basics
    await page.waitForSelector('text=Step 1: Anthropometric Metrics', { timeout: 6000 });
    await page.click('button:has-text("Continue")');

    // Onboarding Step 2: Lifestyle
    await page.waitForSelector('text=Step 2: Activity Level', { timeout: 6000 });
    await page.click('button:has-text("Continue")');

    // Onboarding Step 3: Health Context
    await page.waitForSelector('text=Step 3: Clinical Context', { timeout: 6000 });
    await page.click('button:has-text("Hypertension")');
    await page.click('button:has-text("Dairy")');
    await page.click('button:has-text("Low Sodium")');
    await page.click('button:has-text("Finish & Launch Dashboard")');

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    await page.waitForSelector('text=Welcome back, Jordan', { timeout: 10000 });
    record('Onboarding completes and lands on /dashboard with user first name', true);

    // 4. Capture responsive screenshots of all authenticated pages
    console.log('\n[Phase 4] Testing Nav Links & Capturing Responsive Screenshots (1440px and 390px)...');
    const authPages = [
      { name: 'dashboard', path: '/dashboard' },
      { name: 'health_check', path: '/health-check' },
      { name: 'risk_predictor', path: '/risk-predictor' },
      { name: 'diet_planner', path: '/diet-planner' },
      { name: 'food_explorer', path: '/food-explorer' },
      { name: 'condition_advisor', path: '/condition-advisor' },
      { name: 'progress_alerts', path: '/progress-alerts' },
      { name: 'history', path: '/history' },
      { name: 'profile', path: '/profile' },
    ];

    for (const p of authPages) {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.evaluate((targetPath) => {
        window.history.pushState({}, '', targetPath);
        window.dispatchEvent(new PopStateEvent('popstate'));
      }, p.path);
      await page.waitForTimeout(600);

      // Desktop 1440px
      const overflow1440 = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, `${p.name}_1440px.png`), fullPage: true });

      // Mobile 390px
      await page.setViewportSize({ width: 390, height: 844 });
      await page.waitForTimeout(300);
      const overflow390 = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, `${p.name}_390px.png`), fullPage: true });

      console.log(`Navigated to ${p.name}: ${page.url()}`);
      record(`Page /${p.name} renders cleanly without horizontal overflow`, !overflow1440 && !overflow390);
    }

    // 5. Test Logout and Back-Button Protection
    console.log('\n[Phase 5] Testing Logout and Browser Back Guard...');
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.waitForTimeout(1000);
    console.log('Phase 5 start URL:', page.url());
    const hasUserBtn = await page.$('#user-menu-btn');
    console.log('Is #user-menu-btn found:', !!hasUserBtn);
    if (!hasUserBtn) {
      console.log('Page title/text:', await page.title(), await page.evaluate(() => document.body.innerText.slice(0, 200)));
    }
    await page.waitForSelector('#user-menu-btn', { timeout: 15000 });
    await page.click('#user-menu-btn');
    await page.waitForSelector('#logout-btn', { timeout: 8000 });
    await page.click('#logout-btn');
    await page.waitForURL('**/login', { timeout: 10000 });
    record('Logout navigates to /login', page.url().includes('/login'));

    // Test back button
    await page.goBack();
    await page.waitForTimeout(1000);
    record('Browser Back does not reveal protected content', page.url().includes('/login'));

    // 6. Test Session Expiration Notification
    console.log('\n[Phase 6] Testing Session Expiry Toast...');
    // Login again
    await page.fill('#email', testEmail);
    await page.fill('#password', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForFunction(() => window.location.pathname !== '/login', { timeout: 12000 });

    // Trigger session expired event directly
    await page.evaluate(() => {
      window.dispatchEvent(new Event('nutrition_app:session_expired'));
    });
    await page.waitForSelector('text=Session expired, please sign in again', { timeout: 8000 });
    record('Expired session triggers toast and redirects to /login', page.url().includes('/login'));

    // 7. Check for Console Errors
    const filteredErrors = consoleErrors.filter(err => !err.includes('favicon') && !err.includes('401'));
    if (filteredErrors.length > 0) {
      console.log('Console errors captured:', filteredErrors);
    }
    record('Nav links rendered without unhandled console errors', filteredErrors.length === 0, `${filteredErrors.length} errors`);

  } catch (err) {
    console.error('E2E Test Execution Error:', err);
    record('Test Suite Run', false, err.message);
  } finally {
    await browser.close();
  }

  console.log('\n--- E2E Test Summary ---');
  const total = testResults.length;
  const passed = testResults.filter(r => r.passed).length;
  console.log(`Total: ${total}, Passed: ${passed}, Failed: ${total - passed}`);
  
  const allPassed = total > 0 && passed === total;
  process.exit(allPassed ? 0 : 1);
}

async function captureResponsive(page, pageName, url) {
  // Desktop 1440px
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);

  const overflow1440 = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });

  const desktopPath = path.join(SCREENSHOTS_DIR, `${pageName}_1440px.png`);
  await page.screenshot({ path: desktopPath, fullPage: true });

  // Mobile 390px (resize in-place without reloading)
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(300);

  const overflow390 = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });

  const mobilePath = path.join(SCREENSHOTS_DIR, `${pageName}_390px.png`);
  await page.screenshot({ path: mobilePath, fullPage: true });

  return {
    hasHorizontalScroll1440: overflow1440,
    hasHorizontalScroll390: overflow390,
  };
}

runE2ETests();
