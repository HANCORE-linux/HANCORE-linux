// Local Chromium/CDP smoke test. No packages, browser downloads or personal profile.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const concept = process.argv.includes('--concept');
const out = path.join(root, concept ? '.review/concept' : '.review/current');
fs.mkdirSync(out, {recursive:true});
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'hancore-profile-browser-'));
const base = process.argv.slice(2).find(arg => arg.startsWith('http')) || (concept ? 'http://127.0.0.1:8766' : 'http://127.0.0.1:8765');
const browser = spawn('chromium', ['--headless', '--disable-gpu', '--no-first-run', '--disable-extensions',
  '--disable-background-networking', '--user-data-dir='+profile, '--remote-debugging-port=0', 'about:blank'], {stdio:['ignore','ignore','pipe']});
let stderr = '', ws, sequence = 0;
browser.stderr.on('data', d => stderr += d);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (test, message) => { if (!test) throw new Error(message); };
const errors = [];
try {
  const activePort = path.join(profile, 'DevToolsActivePort');
  for(let i=0; i<100 && !fs.existsSync(activePort); i++) {
    if(browser.exitCode !== null) throw new Error(stderr);
    await delay(100);
  }
  assert(fs.existsSync(activePort), 'Browser did not open its debugging port: '+stderr);
  const port=fs.readFileSync(activePort,'utf8').split('\n')[0];
  const pages=await (await fetch('http://127.0.0.1:'+port+'/json')).json();
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const pending=new Map();
  ws.onmessage=e=>{
    const msg=JSON.parse(e.data);
    if(msg.method==='Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails);
    if(msg.id && pending.has(msg.id)) {
      const {resolve,reject,timer}=pending.get(msg.id);clearTimeout(timer);pending.delete(msg.id);
      msg.error ? reject(msg.error) : resolve(msg.result);
    }
  };
  const call=(method,params={})=>new Promise((resolve,reject)=>{
    const id=++sequence;
    const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout: '+method));},15000);
    pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));
  });
  const evaluate=async expression=>{
    const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };
  await call('Page.enable');await call('Runtime.enable');
  const loaded=async()=>{
    for(let i=0;i<100;i++) {
      if(await evaluate('document.readyState === "complete" && !!document.querySelector("article")')) break;
      await delay(50);
    }
    await evaluate('Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))');
  };
  const results=[];
  const cases = concept ? [
    ['concept',1440,'dark','readme'],['concept',1440,'light','readme'],
    ['concept',1440,'dark','profile'],['concept',900,'dark','profile'],
    ['concept',390,'dark','readme'],['concept',320,'light','readme']
  ] : [
    ['preview',1440,'dark'],['preview',1440,'light'],['preview',900,'dark'],
    ['preview',390,'dark'],['preview',320,'light'],['themes',390,'light'],['acknowledgements',390,'dark']
  ];
  for(const [page,width,theme,view='profile'] of cases) {
    await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:false});
    await call('Page.navigate',{url:base+'/'+page+'.html?theme='+theme+'&view='+view});
    await loaded();
    const metrics=await evaluate(`({
      page:location.pathname,viewport:innerWidth,width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,
      theme:document.documentElement.dataset.theme,
      view:document.documentElement.dataset.view,
      articleColor:getComputedStyle(document.querySelector('article')).color,
      articleBackground:getComputedStyle(document.querySelector('article')).backgroundColor,
      links:[...document.querySelectorAll('article a[href]')].map(a=>a.getAttribute('href')),
      images:[...document.images].map(i=>({src:i.currentSrc,width:i.clientWidth,height:i.clientHeight,loaded:i.complete&&i.naturalWidth>0})),
      headings:[...document.querySelectorAll('article h2')].map(h=>({text:h.querySelector('img')?.alt || h.textContent,y:Math.round(h.getBoundingClientRect().top+scrollY)})),
      captions:[...document.querySelectorAll('article p sub')].map(s=>({size:parseFloat(getComputedStyle(s).fontSize),text:s.textContent})),
      articleFontSize:parseFloat(getComputedStyle(document.querySelector('article')).fontSize)
    })`);
    assert(metrics.width<=width, 'Horizontal overflow: '+page+' at '+width);
    assert(metrics.images.every(i=>i.loaded), 'Broken image: '+page+' at '+width);
    assert(metrics.theme===theme, 'Theme did not apply');
    assert(metrics.view===view, 'View did not apply');
    assert(metrics.articleBackground===(theme==='dark'?'rgb(13, 17, 23)':'rgb(255, 255, 255)'), 'Wrong Markdown theme background');
    if(page==='preview') {
      assert(metrics.headings[0].text==='Shibumi Shell','Wrong flagship order');
      assert(metrics.headings.length===5,'Expected five visual project sections');
      assert(metrics.captions.length>5 && metrics.captions.every(c=>c.size<metrics.articleFontSize), 'Descriptions must remain visually secondary');
      assert(metrics.images.some(i=>i.src.endsWith(width<=600?'selected-mobile.webp':'selected.webp')), 'Wrong responsive theme image');
    }
    if(page==='concept') {
      assert(metrics.images.some(i=>i.src.endsWith('signature-'+theme+'.png')), 'Wrong concept signature for theme');
      assert(!metrics.images.some(i=>i.src.includes('section-') || i.src.endsWith('hero.webp')), 'Retired banners leaked into concept');
      assert(metrics.links.includes('https://github.com/HANCORE-linux/omarchy-roseofdune-theme'), 'Missing desktop attribution');
      assert(await evaluate('document.querySelectorAll("article h3").length === 1 && document.querySelector("article h3").textContent === "Shibumi Shell"'), 'Missing current project');
      assert(await evaluate('document.querySelectorAll("article img")[1].getBoundingClientRect().width > document.querySelectorAll("article img")[0].getBoundingClientRect().width'), 'Signature overwhelms opening image');
    }
    const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:metrics.height,scale:1}});
    fs.writeFileSync(path.join(out,`${page}-${width}-${theme}${concept?'-'+view:''}.png`),Buffer.from(shot.data,'base64'));
    results.push(metrics);console.log('OK',page,width,theme,'height='+metrics.height);
  }
  // Real control changes and navigation, with preferences carried to the next page.
  if(concept) {
    await evaluate('document.querySelector("#preview-theme").value="dark";document.querySelector("#preview-theme").dispatchEvent(new Event("change"))');
    await loaded();
    assert(await evaluate('[...document.querySelectorAll("article img")].some(i=>i.currentSrc.endsWith("signature-dark.png"))'), 'Concept image did not follow theme toggle');
    await evaluate('document.querySelector("#preview-view").value="profile";document.querySelector("#preview-view").dispatchEvent(new Event("change"))');
    assert(await evaluate('getComputedStyle(document.querySelector(".profile-sidebar")).display !== "none"'), 'Profile frame control failed');
    await evaluate('document.querySelector("nav a[href*=preview]").click()');await loaded();
    assert(await evaluate('location.pathname.endsWith("preview.html") && location.search.includes("theme=dark") && location.search.includes("view=profile")'), 'Comparison link lost preferences');
    for(const url of ['/concept.html','/concept/README.md','/concept/DIRECTION.md','/concept/assets/','/.review/concept-manifest.json']) {
      const response = await fetch(new URL(url,base));
      assert(response.status === (url==='/concept.html'?200:404), 'Unexpected concept server exposure: '+url);
    }
  } else {
  await evaluate('document.querySelector("#preview-theme").value="light";document.querySelector("#preview-theme").dispatchEvent(new Event("change"));document.querySelector("#preview-view").value="readme";document.querySelector("#preview-view").dispatchEvent(new Event("change"))');
  assert(await evaluate('getComputedStyle(document.querySelector(".profile-sidebar")).display === "none"'), 'README-only control failed');
  await evaluate('document.querySelector("nav a[href*=themes]").click()');await loaded();
  assert(await evaluate('location.search.includes("theme=light") && location.search.includes("view=readme") && document.documentElement.dataset.theme === "light"'), 'Preferences lost during navigation');
  await evaluate('[...document.querySelectorAll("article a")].find(a=>a.textContent.includes("Back to profile")).click()');await loaded();
  assert(await evaluate('location.pathname.endsWith("preview.html")'), 'Back-to-profile link failed');
  }
  for(const url of ['/','.git/config','/.review/preview-manifest.json','/assets/sources/shibumi-bars.png']) {
    const r=await fetch(new URL(url,base));
    assert(r.status === (url==='/'?200:404),'Unexpected server exposure/status: '+url+' '+r.status);
  }
  assert(!errors.length,'Browser exceptions: '+JSON.stringify(errors));
  fs.writeFileSync(path.join(out,'metrics.json'),JSON.stringify({results,errors,navigation:'passed',controls:'passed'},null,2)+'\n');
  console.log('OK navigation, theme/view controls, console and server access checks');
} finally {
  if(ws)ws.close();
  browser.kill('SIGTERM');
  // The isolated browser profile lives in OS temp; no user browser data is touched.
}
