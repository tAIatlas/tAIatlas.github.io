const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');

const dom = new JSDOM(html, { 
  url: "https://taiatlas.org/",
  runScripts: "dangerously",
  resources: "usable"
});

dom.window.document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    console.log("Input element:", !!dom.window.document.getElementById('species-search'));
    // Since scripts might need mocking, let's just test the path logic:
    const pathname = dom.window.location.pathname;
    const currentPage = pathname.split('/').pop() || 'index.html';
    console.log("pathname:", pathname, "currentPage:", currentPage);
  }, 1000);
});
