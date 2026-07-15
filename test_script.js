const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('PAGE REQUEST FAILED:', request.url(), request.failure().errorText));
  
  await page.goto('https://taiatlas.org/');
  
  await page.waitForSelector('#species-search');
  await page.type('#species-search', 'human');
  
  // Wait a bit for debounce and fetch
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  const resultsHTML = await page.$eval('#search-results', el => el.innerHTML);
  console.log('Results HTML:', resultsHTML);
  
  await browser.close();
})();
