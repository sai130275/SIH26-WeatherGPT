const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  const title = await page.title();
  const text = await page.evaluate(() => document.body.innerText);
  console.log('[TITLE]', title);
  console.log('[TEXT START]', text.substring(0, 100).replace(/\n/g, ' '));
  await browser.close();
})();
