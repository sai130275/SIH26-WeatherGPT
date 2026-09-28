const puppeteer = require('puppeteer');
(async () => {
  const b = await puppeteer.launch({headless: true, args:['--no-sandbox']});
  const p = await b.newPage();
  p.on('console', msg => console.log('LOG:', msg.text()));
  p.on('response', req => { if(req.status() >= 400) console.log('HTTP', req.status(), req.url()); });
  await p.goto('http://localhost:5173', {waitUntil: 'networkidle0'});
  await new Promise(r => setTimeout(r, 2000));
  const t = await p.evaluate(() => document.body.innerText);
  console.log('TEXT:', t.substring(0, 100));
  await b.close();
})();
