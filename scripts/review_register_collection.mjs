// Isolated Chromium review of native GitHub Markdown, not the user's browser.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'.review/folio');
fs.mkdirSync(out,{recursive:true});
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'hancore-folio-browser-'));
const base='http://127.0.0.1:8767';
const themes=JSON.parse(fs.readFileSync(path.join(root,'data/themes.json'),'utf8')).sort((a,b)=>a.name.toLowerCase()<b.name.toLowerCase()?-1:1);
const identity=JSON.parse(fs.readFileSync(path.join(root,'folio/identity.json'),'utf8'));
const config=JSON.parse(fs.readFileSync(path.join(root,'folio/popular-themes.json'),'utf8'));
const popular=Object.entries(config.star_snapshot).filter(([,stars])=>stars>30).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,6);
const browser=spawn('chromium',['--headless','--disable-gpu','--no-first-run','--disable-extensions','--disable-background-networking','--user-data-dir='+profile,'--remote-debugging-port=0','about:blank'],{stdio:['ignore','ignore','pipe']});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const assert=(ok,message)=>{if(!ok)throw new Error(message);};
let stderr='',ws,seq=0;
browser.stderr.on('data',d=>stderr+=d);
try {
  const portFile=path.join(profile,'DevToolsActivePort');
  for(let i=0;i<100&&!fs.existsSync(portFile);i++) {
    if(browser.exitCode!==null)throw new Error(stderr);
    await delay(100);
  }
  const port=fs.readFileSync(portFile,'utf8').split('\n')[0];
  const pages=await(await fetch('http://127.0.0.1:'+port+'/json')).json();
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const pending=new Map(),errors=[],results=[];
  ws.onmessage=e=>{
    const m=JSON.parse(e.data);
    if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);
    if(!pending.has(m.id))return;
    const p=pending.get(m.id);clearTimeout(p.timer);pending.delete(m.id);
    m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);
  };
  const call=(method,params={})=>new Promise((resolve,reject)=>{
    const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(new Error('Timeout '+method));},15000);
    pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));
  });
  const evaluate=async expression=>{
    const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };
  const loaded=async()=>{
    for(let i=0;i<100;i++) {
      if(await evaluate('document.readyState==="complete" && !!document.querySelector("article")'))break;
      await delay(50);
    }
    await evaluate('Promise.all([...document.images].map(i=>i.decode().catch(()=>null)))');
  };
  const navigate=async(route,width,mode,view='readme')=>{
    await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:false});
    await call('Page.navigate',{url:base+'/'+route+'?theme='+mode+'&view='+view});await loaded();
  };
  const metrics=()=>evaluate(`({width:innerWidth,scroll:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,articleHeight:document.querySelector('article').clientHeight,images:[...document.querySelectorAll('article img')].map(i=>({src:i.currentSrc,fallback:i.getAttribute('src'),alt:i.alt,loaded:i.complete&&i.naturalWidth>0,width:i.clientWidth,height:i.clientHeight,declaredWidth:i.getAttribute('width'),declaredHeight:i.getAttribute('height'),themed:!!i.closest('picture')?.querySelector('source'),x:i.getBoundingClientRect().x,y:i.getBoundingClientRect().y})),links:[...document.querySelectorAll('article a')].map(a=>a.href),tables:document.querySelectorAll('article table').length,details:document.querySelectorAll('article details').length})`);
  const valid=(m,width,mode)=>{
    assert(m.scroll<=width,'Page overflow '+width);
    assert(m.images.every(i=>i.loaded),'Missing images '+JSON.stringify(m.images.filter(i=>!i.loaded)));
    assert(m.images.filter(i=>i.themed).every(i=>i.src.endsWith('-'+mode+'.png')),'Wrong image mode');
    assert(!m.tables&&!m.details,'The old inline archive should not remain');
  };
  const save=async(name,m)=>{
    const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:m.width,height:m.height,scale:1}});
    fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(shot.data,'base64'));
  };
  await call('Page.enable');await call('Runtime.enable');
  if(!process.argv.includes('--register-only')) {
    for(const [width,mode,view] of [[1440,'dark','profile'],[1440,'light','profile'],[1440,'dark','readme'],[1280,'dark','profile'],[1279,'light','profile'],[1024,'dark','profile'],[900,'light','profile'],[768,'dark','profile'],[390,'dark','profile'],[390,'light','readme'],[320,'light','readme']]) {
      await navigate('folio.html',width,mode,view);
      const m=await metrics();valid(m,width,mode);
      assert(m.images.length===21&&m.links.length===18,'Main profile count');
      const cards=m.images.filter(i=>i.fallback.includes('/collection/assets/'));
      assert(cards.length===6&&cards.every((i,n)=>i.fallback.endsWith('/'+popular[n][0]+'-light.png')),'Popular order/count');
      assert(cards.every(i=>i.src.includes('/connected-theme-')===(width>=1280)),'Popular connector breakpoint');
      assert(cards.every(i=>i.declaredWidth==='248'&&i.declaredHeight==='196'),'Profile card dimensions changed');
      assert(cards.every(i=>i.alt.includes('ANSI colors 00–07')&&i.alt.includes('GitHub stars, checked ')),'Accessible palettes/badges');
      assert(m.images[0].src.endsWith('wordmark-'+identity.selected+'-'+mode+'.png'),'Unapproved identity became default');
      const projects=m.images.filter(i=>/\/(?:connected-)?(shibumi|omaq|marketplace)-(dark|light)\.png$/.test(i.src));
      assert(projects.length===3&&projects.every(i=>i.declaredWidth==='248'&&i.declaredHeight==='278'),'Project card footprint changed');
      assert(projects.map(i=>i.src.split('/').at(-1).replace(/^connected-/,'').replace(/-(dark|light)\.png$/,'')).join(',')==='shibumi,omaq,marketplace','Project order');
      assert(projects.every(i=>i.src.includes('/connected-')===(width>=1280)),'Native connection breakpoint');
      if(width>=1280) {
        assert(new Set(projects.map(i=>i.y)).size===1,'Circuit slices must share a row');
        for(let n=1;n<projects.length;n++)assert(Math.abs(projects[n].x-projects[n-1].x-projects[n-1].width)<0.1,'Gap between circuit slices');
        assert(projects.every(i=>Math.abs(i.height-248*900/624)<1),'Original mount scale changed');
      }
      const labels=m.images.filter(i=>i.src.includes('/label-'));
      assert(labels.length===2&&labels.every(i=>i.declaredWidth==='248'&&i.declaredHeight==='28'),'Readable section labels');
      assert(labels.map(i=>i.alt).join('|')==='Linux themes & interfaces.|Most starred themes','Section label text');
      for(const url of ['https://github.com/HANCORE-linux/OmaQ','https://github.com/omacom/omarchy-plugin-marketplace','https://github.com/HANCORE-linux/waybar-themes','https://github.com/HANCORE-linux/quickshell-dots'])assert(m.links.includes(url),'Lost project '+url);
      const details=m.images.filter(i=>i.fallback.includes('/info-'));
      assert(details.length===6&&details.every(i=>i.declaredWidth==='248'&&i.declaredHeight==='76'),'Info cards or archive card missing');
      assert(details.some(i=>i.alt==='Banish — Newest theme.')&&details.filter(i=>i.alt.endsWith('Ships with Omarchy.')).length===2,'Lost latest/official notes');
      assert(details.some(i=>i.alt==='All 27 themes — Open collection →'),'Archive link must be a card');
      if(width>=1280) {
        const bridge=details.slice(0,2), highlights=details.slice(2,5);
        assert(bridge.every(i=>i.width===372)&&new Set(bridge.map(i=>i.y)).size===1,'Two wide bridge slices');
        assert(Math.abs(projects[0].y+projects[0].height-bridge[0].y)<1,'Project-to-bridge vertical seam');
        assert(Math.abs(bridge[0].y+bridge[0].height-highlights[0].y)<1,'Bridge-to-highlight vertical seam');
        assert(Math.abs(projects[0].x-bridge[0].x)<1&&Math.abs(projects[0].x-highlights[0].x)<1,'Connection group left edges');
        assert(Math.abs(bridge[1].x-bridge[0].x-bridge[0].width)<1,'Bridge center rail seam');
        for(let n=0;n<3;n++)assert(Math.abs(cards[n].y+cards[n].height-cards[n+3].y)<1&&Math.abs(cards[n].x-cards[n+3].x)<1,'Theme network vertical seam');
        const archiveNode=details.find(i=>i.fallback.endsWith('/info-archive-light.png'));
        assert(Math.abs(cards[4].x-archiveNode.x)<1&&Math.abs(cards[4].y+cards[4].height-archiveNode.y)<1,'Final theme line must end at the archive CTA');
        assert(m.images.filter(i=>i.src.includes('/connected-')).length===15,'Both complete connection networks and final archive node');
      } else assert(!m.images.some(i=>i.src.includes('/connected-')),'Narrow layouts must use original cards');
      const socials=m.images.filter(i=>i.src.includes('/social-'));
      assert(socials.length===3&&socials.every(i=>i.declaredWidth==='44'&&i.declaredHeight==='44'),'Missing accessible footer icons');
      assert(socials.map(i=>i.alt).join(',')==='Discord,Ko-fi,Acknowledgements','Footer icon order');
      assert(new Set(socials.map(i=>i.y)).size===1&&socials[2].x>socials[1].x,'Acknowledgements must sit to the right of Ko-fi');
      if(width===1440) {
        assert(m.articleHeight<1560,'Main profile too tall');
        assert(new Set(cards.map(i=>Math.round(i.y))).size===2,'Expected 3×2 compact grid');
        assert(new Set(projects.map(i=>Math.round(i.y))).size===1,'Project row changed');
      }
      if(width<=390)assert(new Set(cards.map(i=>Math.round(i.y))).size===6,'Cards do not wrap on mobile');
      await save(`${width}-${mode}-${view}`,m);results.push({route:'folio.html',mode,view,...m});
      console.log('OK profile',width,mode,view,'height',m.articleHeight);
    }
  }
  for(const route of ['collection.html','identity.html','register-profile.html','folio-acknowledgements.html']) {
    for(const width of [1440,768,390,320])for(const mode of ['dark','light']) {
      await navigate(route,width,mode);
      const m=await metrics();valid(m,width,mode);
      const archive=route==='collection.html';
      const thanks=route==='folio-acknowledgements.html';
      assert(m.images.length===(archive?28:thanks?1:21),'Unexpected image count '+route);
      assert(m.links.length===(archive?29:thanks?8:18),'Unexpected links '+route);
      if(archive) {
        const archiveCards=m.images.filter(i=>i.src.includes('/collection/assets/'));
        const label=m.images.find(i=>i.src.endsWith('/label-archive-'+mode+'.png'));
        assert(label?.declaredWidth==='280'&&label.declaredHeight==='76'&&label.alt==='Theme archive — 27 themes · color00–07 · A–Z','Readable archive heading tile');
        assert(label.y+label.height<=archiveCards[0].y,'Archive header tile overlaps the themes');
        assert(archiveCards.length===27&&archiveCards.every((i,n)=>i.src.endsWith('/'+themes[n].slug+'-'+mode+'.png')),'Archive A–Z order');
        assert(new Set(archiveCards.map(i=>i.src)).size===27,'Repeated archive card');
        assert(archiveCards.every(i=>i.declaredWidth==='396'&&i.declaredHeight==='312'),'Large archive dimensions');
        assert(archiveCards.every(i=>i.alt.includes('ANSI colors 00–07')&&i.alt.includes('GitHub stars, checked ')),'Archive alt text');
        const newCards=archiveCards.filter(i=>i.alt.includes('— NEW;'));
        assert(newCards.length===1&&newCards[0].src.endsWith('/banish-'+mode+'.png'),'Only Banish should be marked NEW');
        const rowSizes=Object.values(archiveCards.reduce((rows,i)=>{const y=Math.round(i.y);rows[y]=(rows[y]||0)+1;return rows;},{}));
        if(width===1440)assert(rowSizes.length===14&&rowSizes.filter(n=>n===2).length===13,'Archive must have two large cards per row');
        if(width<=390)assert(rowSizes.every(n=>n===1),'Archive mobile wrapping');
        for(const theme of themes)assert(m.links.includes('https://github.com/HANCORE-linux/omarchy-'+theme.slug+'-theme'),'Missing archive link '+theme.slug);
      } else if(thanks) {
        assert(m.images[0].alt==='Acknowledgements'&&m.images[0].src.endsWith('/label-acknowledgements-'+mode+'.png'),'Acknowledgements heading');
        const items=await evaluate('[...document.querySelectorAll("article li")].map(li=>li.textContent.trim())');
        assert(items.join('|')==='Amit / Content Creator|OldJobobo / Minister of Taste|Miqim / Visual Stylist|Bypass / Theme-hook-script|bjarneo / Aether|Taha / Omarchist|DHH / Omarchy','Exact acknowledgements and order');
        assert(!await evaluate('/Credits|Contributions/.test(document.querySelector("article").textContent)'),'Wrong acknowledgements label');
        assert(!await evaluate('!!document.querySelector(".folio-pins")'),'Acknowledgements should not show profile pins');
      } else if(route==='identity.html') {
        assert(m.images[0].src.endsWith('/identity-'+mode+'.png'),'Missing custom wordmark');
        assert(!await evaluate('!!document.querySelector("#preview-wordmark")'),'Font selector overrides custom lettering');
      }
      await save(`${route.replace('.html','')}-${width}-${mode}`,m);results.push({route,mode,...m});
      console.log('OK',route,width,mode);
    }
  }
  await navigate('folio.html',1440,'dark');
  const clickedProjects=await evaluate(`['shibumi','omaq','marketplace'].map(slug=>{
    const img=document.querySelector('article img[src$="/'+slug+'-light.png"]');
    const r=img.getBoundingClientRect();img.scrollIntoView({block:'center'});
    const p=img.getBoundingClientRect();return document.elementFromPoint(p.x+p.width/2,p.y+p.height/2)?.closest('a')?.href;
  })`);
  assert(clickedProjects.join('|')==='https://github.com/HANCORE-linux/Shibumi-Shell|https://github.com/HANCORE-linux/OmaQ|https://github.com/omacom/omarchy-plugin-marketplace','Project click targets must remain independent');
  await evaluate('document.querySelector("article a[href*=collection]").focus()');
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',text:'\r',windowsVirtualKeyCode:13});
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await loaded();
  assert(await evaluate('location.pathname==="/collection.html"&&location.search.includes("theme=dark")'),'Native archive link');
  await evaluate('document.querySelector("article a[href*=folio]").click()');await loaded();
  assert(await evaluate('location.pathname==="/folio.html"'),'Back to profile');
  await evaluate('document.querySelector("article a[title=Acknowledgements]").focus()');
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',text:'\r',windowsVirtualKeyCode:13});
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await loaded();
  assert(await evaluate('location.pathname==="/folio-acknowledgements.html"&&location.search.includes("theme=dark")&&location.search.includes("view=readme")'),'Acknowledgements keyboard link');
  await evaluate('document.querySelector("article a[href*=folio]").click()');await loaded();
  assert(await evaluate('location.pathname==="/folio.html"'),'Acknowledgements return link');
  for(const {id} of identity.variants) {
    await evaluate(`document.querySelector('#preview-wordmark').value='${id}';document.querySelector('#preview-wordmark').dispatchEvent(new Event('change'))`);await loaded();
    assert(await evaluate(`document.querySelector('article img').currentSrc.endsWith('wordmark-${id}-dark.png')`),'Wordmark selector '+id);
  }
  await evaluate('document.querySelector("#preview-theme").value="light";document.querySelector("#preview-theme").dispatchEvent(new Event("change"))');await loaded();
  assert(await evaluate('[...document.querySelectorAll("article picture:has(source) img")].every(i=>i.currentSrc.endsWith("-light.png"))'),'Theme control');
  for(const mode of ['dark','light']) {
    await navigate('register.html',390,mode);
    const m=await metrics();valid(m,390,mode);
    assert(m.images.length===3&&m.images[1].width===m.images[2].width&&m.images[1].height===m.images[2].height,'Original Solitude comparison');
  }
  for(const route of ['/.git/config','/.review/folio-manifest.json','/folio/collection/sources/banish.png','/folio/collection/provenance.json','/folio/collection/sources.json','/folio/collection/IDENTITY.md','/folio/THEMES.md','/folio/collection/assets/','/folio/series-solitude-dark.svg','/folio/README.md','/folio/ACKNOWLEDGEMENTS.md','/folio/%2e%2e/.git/config'])assert((await fetch(base+route)).status===404,'Private route exposed '+route);
  for(const route of ['/','/collection.html','/identity.html','/register.html','/register-profile.html','/folio-acknowledgements.html','/folio/assets/social-acknowledgements-dark.png','/folio/collection/assets/solitude-dark.png'])assert((await fetch(base+route)).status===200,'Public route missing '+route);
  assert(!errors.length,'Browser errors');
  // Prove the README itself, not preview JS/CSS, selects and joins the images.
  await call('Emulation.setScriptExecutionDisabled',{value:true});
  for(const width of [1440,1280,1279,390])for(const mode of ['dark','light']) {
    await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:mode}]});
    await navigate('folio.html',width,mode);
    const m=await metrics();
    const projects=m.images.filter(i=>/\/(?:connected-)?(shibumi|omaq|marketplace)-(dark|light)\.png$/.test(i.src));
    assert(projects.length===3&&projects.every(i=>i.loaded&&i.src.endsWith('-'+mode+'.png')&&i.src.includes('/connected-')===(width>=1280)),'No-JS native picture selection');
    if(width>=1280) {
      assert(new Set(projects.map(i=>i.y)).size===1,'No-JS circuit wrapping');
      for(let n=1;n<3;n++)assert(Math.abs(projects[n].x-projects[n-1].x-projects[n-1].width)<0.1,'No-JS seam gap');
    }
    assert(m.scroll<=width,'No-JS page overflow');
    // Source dimensions must also work without the preview's height:auto rule.
    await evaluate('[...document.styleSheets].forEach(sheet=>sheet.disabled=true)');
    const bare=await metrics();
    const bareProjects=bare.images.filter(i=>/\/(?:connected-)?(shibumi|omaq|marketplace)-(dark|light)\.png$/.test(i.src));
    assert(bareProjects.length===3&&bareProjects.every(i=>i.width===248&&i.height===(width>=1280?358:278)),'Native source dimensions without CSS');
    console.log('OK native no-JS connections',width,mode);
  }
  await call('Emulation.setScriptExecutionDisabled',{value:false});
  fs.writeFileSync(path.join(out,'metrics.json'),JSON.stringify({results,errors,controls:'passed',archiveKeyboardNavigation:'passed',acknowledgementsKeyboardNavigation:'passed',privateRoutes:'passed',independentProjectHitTargets:'passed',nativeConnectionsWithoutScriptsOrStyles:'8 cases passed'},null,2)+'\n');
  console.log('OK independent project hit targets, native no-JS connectors, archive links, light/dark controls, private routes and browser console');
} finally {
  if(ws)ws.close();
  browser.kill('SIGTERM');
}
