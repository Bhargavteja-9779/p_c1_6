const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({userAgent:'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'});
await p.goto(process.argv[2],{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(8000);
const t=await p.evaluate(()=>document.body.innerText);require('fs').writeFileSync(process.argv[3],t);console.log(t.length);await b.close();})();
