const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('[CONSOLE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('[PAGE ERROR]', err.message));
  page.on('requestfailed', request => {
    console.log('[NETWORK FAIL]', request.url(), request.failure()?.errorText);
  });

  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 2000));
  
  const rootHtml = await page.evaluate(() => {
    const r = document.getElementById('root');
    return r ? r.innerHTML : 'NO ROOT ELEMENT';
  });
  console.log('[ROOT HTML LENGTH]', rootHtml.length);
  
  await browser.close();
})();
