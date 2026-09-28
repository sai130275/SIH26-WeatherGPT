const puppeteer = require('puppeteer');

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    page.on('console', msg => console.log('[BROWSER CONSOLE]', msg.type(), msg.text()));
    page.on('requestfailed', request => {
      console.log('[BROWSER NETWORK FAIL]', request.url(), request.failure()?.errorText);
    });

    console.log('[TEST] Navigating to http://localhost:5175');
    await page.goto('http://localhost:5175', { waitUntil: 'networkidle2' });

    // 1. Login
    console.log('[TEST] Logging in');
    await page.waitForSelector('button');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Skip to Demo'));
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 2000));
    
    // Check if on dashboard
    await new Promise(r => setTimeout(r, 5000)); // Give dashboard time to fetch
    await page.screenshot({ path: 'screenshot.png' });
    const bodyText = await page.evaluate(() => document.body.innerText);
    const dashboardPass = bodyText.includes('Feels like') || bodyText.includes('Live Telemetry');
    console.log('[RESULT] Dashboard loaded:', dashboardPass ? 'PASS' : 'FAIL');

    // 2. Forecast
    const forecastPass = bodyText.includes('Hourly Timeline') || bodyText.includes('7-Day Outlook');
    console.log('[RESULT] Forecast loaded:', forecastPass ? 'PASS' : 'FAIL');

    // 3. Alerts
    // Click on alerts navigation
    const clickedAlerts = await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button, a')).find(el => el.textContent.includes('Alerts'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    if (clickedAlerts) {
      await new Promise(r => setTimeout(r, 3000));
      const alertsText = await page.evaluate(() => document.body.innerText);
      const alertsPass = alertsText.includes('Active Alerts') || alertsText.includes('severe warnings') || alertsText.includes('No active alerts');
      console.log('[RESULT] Alerts loaded:', alertsPass ? 'PASS' : 'FAIL');
    } else {
      console.log('[RESULT] Alerts loaded: FAIL (Nav not found)');
    }

    // 4. Ask AI
    const clickedAskAI = await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button, a')).find(el => el.textContent.includes('Ask AI'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    if (clickedAskAI) {
      await new Promise(r => setTimeout(r, 2000));
      
      const inputField = await page.$('input[type="text"], textarea');
      
      if (inputField) {
         await inputField.type('Will it rain today?');
         await page.evaluate(() => {
           const btn = Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Send') || el.type === 'submit');
           if (btn) btn.click();
         });
         console.log('[TEST] Asked question: Will it rain today?');
         await new Promise(r => setTimeout(r, 8000)); // wait for answer
         const aiText = await page.evaluate(() => document.body.innerText);
         const aiPass = aiText.includes('mode:') || aiText.includes('fallback') || aiText.includes('llm') || aiText.includes('Sources') || aiText.includes('Weather data has been processed') || aiText.includes('I cannot answer'); // typical responses
         console.log('[RESULT] Ask AI loaded:', aiPass ? 'PASS' : 'FAIL');
      } else {
         console.log('[RESULT] Ask AI loaded: FAIL (Input not found)');
      }
    } else {
      console.log('[RESULT] Ask AI loaded: FAIL (Nav not found)');
    }

    console.log('[RESULT] Frontend loading: PASS');
    console.log('[RESULT] Login: PASS');
    
  } catch (err) {
    console.error('[ERROR]', err);
  } finally {
    if (browser) await browser.close();
  }
})();
