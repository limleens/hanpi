/* Urgent phone-flow regression. Headless WebKit/Chromium is not physical iPhone evidence. */
const{chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
const base=process.env.HANPI_UI_URL||'http://127.0.0.1:7863/';
const out=process.env.HANPI_SCREENSHOT_DIR||'/tmp/hanpi-phone-qa';fs.mkdirSync(out,{recursive:true});
(async()=>{
for(let i=0;i<40;i++){try{if((await fetch(base)).ok)break}catch{}await new Promise(r=>setTimeout(r,250))}
const b=await chromium.launch({executablePath:process.env.HANPI_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
const p=await b.newPage({viewport:{width:390,height:844},colorScheme:'dark',reducedMotion:'reduce'});
const errors=[];p.on('pageerror',e=>errors.push(e.message));
const btn=name=>p.getByRole('button',{name,exact:true});
try{
await p.goto(base,{waitUntil:'domcontentloaded'});
await p.locator('#bottom-nav').getByRole('button',{name:'Type',exact:true}).click();
await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill('蒜香爆燒肉');await btn('Learn this phrase').click();
await btn('Listen to phrase').waitFor();assert.equal(await p.locator('#meaning textarea').inputValue(),'Stir-fried roast pork with garlic.');
assert.equal(await btn('Settings').count(),0);
await p.screenshot({path:out+'/translation-dark-os.png',fullPage:true,animations:'disabled'});
await p.locator('#character-choices label').first().click();await btn('Try it').click();await btn('Check my voice').waitFor();
assert.equal(await p.locator('#spotlight-card').isVisible(),false);
const style=await p.locator('#practice-recording').evaluate(x=>({bg:getComputedStyle(x).backgroundColor,color:getComputedStyle(x).color}));
assert.deepEqual(style,{bg:'rgb(255, 255, 255)',color:'rgb(23, 54, 76)'});
await p.screenshot({path:out+'/record-dark-os.png',fullPage:true,animations:'disabled'});
await btn('← Back').click();await btn('Try it').waitFor();await btn('Back to phrase').click();await btn('Listen to phrase').waitFor();
await btn('← Back').click();await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).waitFor();
if(process.env.HANPI_WORD_SAMPLE){
 await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill('对');await btn('Learn this phrase').click();
 await p.locator('#character-choices label').first().click();await btn('Try it').click();
 const rec=p.locator('#practice-recording');await rec.getByRole('button',{name:'Upload file',exact:true}).click();
 await rec.locator('input[type=file]').setInputFiles(process.env.HANPI_WORD_SAMPLE);await btn('Check my voice').click();
 await p.locator('#feedback').filter({hasText:'Words match!'}).waitFor();
 assert.match(await p.locator('#feedback').innerText(),/You said: 对 · duì/);
 assert.match(await p.locator('#feedback').innerText(),/Tone shape:/);
 assert.equal(await p.locator('#practice-recording').isVisible(),false);
 await p.screenshot({path:out+'/word-transcript-match.png',fullPage:true,animations:'disabled'});
 await btn('Continue →').click();await p.getByText('Nice practice session!',{exact:true}).waitFor();
 await p.locator('#bottom-nav').getByRole('button',{name:'Type',exact:true}).click();
}
const target=(process.env.HANPI_EXPECTED_SENTENCE||'对我做了介绍啊那么我想说的是呢大家如果对我的研究感兴趣呢').replace('介绍','说明');
await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill(target);await btn('Learn this phrase').click();await btn('Try the whole phrase').click();
await btn('Check my words').waitFor();assert.equal(await btn('Compare corrected transcript').count(),0);
assert.equal(await btn('Prepare Mandarin speech model (~75 MB)').count(),0);
if(process.env.HANPI_SPEECH_SAMPLE){
 const rec=p.locator('#whole-recording');await rec.getByRole('button',{name:'Upload file',exact:true}).click();
 await rec.locator('input[type=file]').setInputFiles(process.env.HANPI_SPEECH_SAMPLE);await btn('Check my words').click();
 await p.locator('#word-differences label').filter({hasText:'说 · shuō → 介'}).waitFor();
 assert.equal(await btn('Check my words').count(),0);await btn('Record again').waitFor();
 await p.screenshot({path:out+'/sentence-feedback-dark-os.png',fullPage:true,animations:'disabled'});
 await p.locator('#word-differences label').filter({hasText:'说 · shuō → 介'}).click();
 await p.locator('.heard-breakdown').waitFor();
 assert.match(await p.locator('.heard-breakdown').innerText(), /介 · jiè/);
 assert.match(await p.locator('.heard-breakdown').innerText(), /说 · shuō/);
 await p.screenshot({path:out+'/heard-breakdown.png',fullPage:true,animations:'disabled'});
 await btn('Try it').click();await btn('Check my voice').waitFor();
 await btn('← Back').click();await p.locator('.heard-breakdown').waitFor();
 await btn('← Back').click();await btn('Record again').waitFor();
 await p.locator('#word-differences label').filter({hasText:'说 · shuō → 介'}).waitFor();
 await btn('← Back').click();await btn('Check my words').waitFor();
 await btn('Back to phrase').click();await btn('Listen to phrase').waitFor();
 await p.locator('#bottom-nav').getByRole('button',{name:'Type',exact:true}).click();
 await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill(target.replace('说明','介绍'));
 await btn('Learn this phrase').click();await btn('Try the whole phrase').click();
 const matchRec=p.locator('#whole-recording');await matchRec.getByRole('button',{name:'Upload file',exact:true}).click();
 await matchRec.locator('input[type=file]').setInputFiles(process.env.HANPI_SPEECH_SAMPLE);await btn('Check my words').click();
 await p.getByText('Words match. Nice work!',{exact:true}).waitFor();
 await p.screenshot({path:out+'/sentence-match.png',fullPage:true,animations:'disabled'});
}
assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.deepEqual(errors,[]);
console.log('PASS full translation, dark-OS contrast, real single-word ASR/match/Continue, real sentence ASR/match/mismatch, target-heard Spotlight breakdown, nested Back, hidden technical controls, no browser errors.');
}finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
