/* ASR is stubbed to homophone/short-ending transcripts; real Praat analyzes
 * synthetic F0. This tests practice/UI, not human speech or ASR accuracy. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),net=require('node:net');
const assert=require('node:assert/strict');
(async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'hanpi-homophone-'));
 const listener=net.createServer();await new Promise(r=>listener.listen(0,'127.0.0.1',r));
 const port=listener.address().port;await new Promise(r=>listener.close(r));
 const child=spawn(process.env.HANPI_PYTHON||path.resolve('.venv/bin/python'),['-u','-c',`
import os, numpy as np, soundfile as sf, app
sr=16000; t=np.arange(int(sr*.85))/sr
contour=np.interp(t/.85,np.linspace(0,1,5),[3,1,-1,-3,-4])
phase=2*np.pi*np.cumsum(195*2**(contour/12))/sr
envelope=np.minimum(1,np.minimum(t/.07,(.85-t)/.07)).clip(0,1)
sf.write(os.path.join(os.environ['HANPI_QA_FOLDER'],'falling.wav'),envelope*(.28*np.sin(phase)+.1*np.sin(2*phase)),sr)
transcripts=iter(('算','算了','算儿','酸了'))
app._transcribe=lambda audio:(next(transcripts),'Controlled ASR stub for practice regressions')
app.launch_app()
`],{env:{...process.env,HANPI_QA_FOLDER:folder,HANPI_LIBRARY_PATH:path.join(folder,'library.sqlite3'),HANPI_HOST:'127.0.0.1',HANPI_SHARE:'0',PORT:String(port),BROWSER:'true',MPLBACKEND:'Agg',MPLCONFIGDIR:path.join(folder,'mpl'),GRADIO_ANALYTICS_ENABLED:'False'}});
 let log='',browser;child.stdout.on('data',x=>log+=x);child.stderr.on('data',x=>log+=x);
 try{
  const base=`http://127.0.0.1:${port}/`;
  for(let i=0;i<120;i++){
   if(child.exitCode!==null)throw new Error(log);
   try{if((await fetch(base)).ok)break}catch{}
   if(i===119)throw new Error('Startup failed: '+log);
   await new Promise(r=>setTimeout(r,250));
  }
  browser=await chromium.launch({executablePath:process.env.HANPI_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
  const p=await browser.newPage({viewport:{width:390,height:844},colorScheme:'dark',reducedMotion:'reduce'});
  const errors=[];p.on('pageerror',e=>errors.push(e.message));
  const button=name=>p.getByRole('button',{name,exact:true});
  await p.goto(base,{waitUntil:'domcontentloaded'});
  for(const [i,heard] of ['算','算了','算儿','酸了'].entries()){
   await p.locator('#bottom-nav').getByRole('button',{name:'Type',exact:true}).click();
   await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill('蒜');await button('Learn this phrase').click();
   await p.locator('#character-choices label').first().click();await button('Try it').click();
   const rec=p.locator('#practice-recording');await rec.getByRole('button',{name:'Upload file',exact:true}).click();
   await rec.locator('input[type=file]').setInputFiles(path.join(folder,'falling.wav'));await button('Check my voice').click();
   await p.locator('#feedback').filter({hasText:i===0?'Sounds match!':'Syllable matches!'}).waitFor();
   const text=await p.locator('#feedback').innerText();
   assert(text.includes(`You said: ${heard}`));assert.match(text,/Target: 蒜 · suàn/);
   assert.match(text,/falling \(fourth tone\) — matches the target/);assert(!text.includes('may have misheard'));
   if(i>0)assert(text.includes('Extra ending ignored'));
   const next=await button('Continue →').boundingBox(),nav=await p.locator('#bottom-nav').boundingBox();
   assert(next.y>=0&&next.y+next.height<=nav.y,'Continue must be visible above the bottom navigation.');
   const out=process.env.HANPI_SCREENSHOT_DIR||folder;fs.mkdirSync(out,{recursive:true});
   await p.screenshot({path:path.join(out,`suan-practice-${i}.png`),fullPage:true,animations:'disabled'});
   await button('Continue →').click();await p.getByText('Nice practice session!',{exact:true}).waitFor();
  }
  assert.deepEqual(errors,[]);
  console.log('PASS 算/算了/算儿/酸了 accepted for 蒜, real falling-pitch extraction, full transcripts preserved, visible Continue/completion, phone dark layout; ASR stubbed.');
 }finally{
  if(browser)await browser.close();child.kill('SIGTERM');
 }
})().catch(e=>{console.error(e);process.exitCode=1});
