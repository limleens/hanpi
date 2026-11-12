/* Actual ASR + speech filtering; browser speech is stubbed to verify queuing.
 * Microphone capture uses Chromium's fake device fed a public human WAV.
 * This is not a physical microphone or audible phone-playback test. */
const{chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base=process.env.HANPI_UI_URL||'http://127.0.0.1:7893/';
const word=process.env.HANPI_WORD_SAMPLE,device=process.env.HANPI_MIC_SAMPLE,noise=process.env.HANPI_NOISE_SAMPLE;
if(!word||!device||!noise)throw new Error('Set HANPI_WORD_SAMPLE, HANPI_MIC_SAMPLE and HANPI_NOISE_SAMPLE.');
const out=process.env.HANPI_SCREENSHOT_DIR||'/tmp/hanpi-tutor';fs.mkdirSync(out,{recursive:true});
(async()=>{
 for(let i=0;i<120;i++){
  try{if((await fetch(base)).ok)break}catch{}
  if(i===119)throw new Error('Hanpi did not become ready.');
  await new Promise(r=>setTimeout(r,250));
 }
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream',`--use-file-for-fake-audio-capture=${device}%noloop`]});
 const p=await b.newPage({viewport:{width:390,height:844},colorScheme:'dark',reducedMotion:'reduce',permissions:['microphone']});
 const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(()=>{
  window.__spoken=[];window.__cancellations=0;window.__guardPauses=0;
  window.SpeechSynthesisUtterance=class {constructor(text){this.text=text;}};
  window.speechSynthesis.getVoices=()=>[{name:'QA English',lang:'en-GB'},{name:'QA Mandarin',lang:'zh-CN'}];
  window.speechSynthesis.cancel=()=>window.__cancellations++;
  window.speechSynthesis.speak=u=>{window.__lastTip=u;window.__spoken.push({text:u.text,lang:u.lang,recording:!!window.__hanpiRecording});};
 });
 const button=name=>p.getByRole('button',{name,exact:true});
 const learn=async text=>{
  await p.locator('#bottom-nav').getByRole('button',{name:'Type',exact:true}).click();
  await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill(text);await button('Learn this phrase').click();
  await p.locator('#character-choices label').first().click();await button('Try it').click();
 };
 try{
  await p.goto(base,{waitUntil:'domcontentloaded'});await learn('蒜');
  await p.waitForFunction(()=>window.__spoken.some(x=>x.text.includes('Your turn')));
  const rec=p.locator('#practice-recording');await rec.getByRole('button',{name:'Upload file',exact:true}).click();
  await rec.locator('input[type=file]').setInputFiles(word);await button('Check my voice').click();
  await p.locator('#feedback').filter({hasText:'You said: 对'}).waitFor();
  await p.waitForFunction(()=>window.__lastTip?.text.includes('transcript came out differently'));
  await p.evaluate(()=>{window.__savedTip=window.__lastTip;window.__lastTip.onend();});
  assert.deepEqual(await p.evaluate(()=>window.__spoken.at(-1)),{text:'蒜',lang:'zh-CN',recording:false});
  await p.getByRole('checkbox',{name:'Spoken tips',exact:true}).uncheck();
  await button('Hear tip').click();await p.waitForFunction(()=>window.__spoken.at(-1)?.lang==='en-GB');
  const count=await p.evaluate(()=>window.__spoken.length);await button('Try phrase').click();await button('Check my words').waitFor();
  assert.equal(await p.evaluate(()=>window.__spoken.length),count,'Muting stops automatic narration.');
  await learn('对');await p.getByRole('checkbox',{name:'Spoken tips',exact:true}).check();
  if(!await rec.getByRole('button',{name:'Record',exact:true}).isVisible())await rec.getByRole('button',{name:'Record audio',exact:true}).click();
  const before=await p.evaluate(()=>window.__cancellations);
  await rec.getByRole('button',{name:'Record',exact:true}).click();
  await p.waitForFunction(()=>window.__hanpiRecording===true);
  await p.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent.trim()==='Check my voice'&&b.disabled));
  assert((await p.evaluate(()=>window.__cancellations))>before);
  await p.evaluate(()=>{
   window.__countBefore=window.__spoken.length;window.__savedTip.onend();
   const audio=document.createElement('audio');audio.pause=()=>window.__guardPauses++;
   document.body.append(audio);audio.dispatchEvent(new Event('play'));audio.remove();
  });
  assert.equal(await p.evaluate(()=>window.__spoken.length),await p.evaluate(()=>window.__countBefore));
  assert.equal(await p.evaluate(()=>window.__guardPauses),1);
  await p.waitForTimeout(2300);
  await rec.getByRole('button',{name:'Stop',exact:true}).click();
  await p.locator('#feedback').filter({hasText:'Words match!'}).waitFor({timeout:45000});
  assert.match(await p.locator('#feedback').innerText(),/You said: 对 · duì/);
  assert.equal(await p.evaluate(()=>window.__hanpiRecording),false);
  assert(await p.evaluate(()=>window.__spoken.every(x=>!x.recording)));
  await p.screenshot({path:out+'/microphone-tutor.png',fullPage:true,animations:'disabled'});
  await button('Try again').click();await rec.getByRole('button',{name:'Upload file',exact:true}).click();
  await rec.locator('input[type=file]').setInputFiles(noise);await button('Check my voice').click();
  await p.locator('#feedback').filter({hasText:/clear speech|background sound/}).waitFor();
  assert(!(await p.locator('#feedback').innerText()).includes('matches the target'));
  await p.screenshot({path:out+'/noise-retry.png',fullPage:true,animations:'disabled'});
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.deepEqual(errors,[]);
  console.log('PASS actual ASR with fake-device human microphone input, one word once, speech/noise filtering, guided tutor, EN→ZH queue, mute/replay, echo guard and Try phrase; speech output stubbed.');
 }catch(error){
  console.error('Browser errors:',errors,(await p.locator('body').innerText()).slice(-4500));
  await p.screenshot({path:out+'/failure.png',fullPage:true});throw error;
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
