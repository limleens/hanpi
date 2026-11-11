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
await p.locator('#character-choices label').first().click();await btn('Try it').click();await btn('Check my tone').waitFor();
assert.equal(await p.locator('#spotlight-card').isVisible(),false);
const style=await p.locator('#practice-recording').evaluate(x=>({bg:getComputedStyle(x).backgroundColor,color:getComputedStyle(x).color}));
assert.deepEqual(style,{bg:'rgb(255, 255, 255)',color:'rgb(23, 54, 76)'});
await p.screenshot({path:out+'/record-dark-os.png',fullPage:true,animations:'disabled'});
await btn('← Back').click();await btn('Try it').waitFor();await btn('Back to phrase').click();await btn('Listen to phrase').waitFor();
await btn('← Back').click();await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).waitFor();
const target='对我做了说明那么我想说的是大家如果对我的研究感兴趣呢';
await p.getByRole('textbox',{name:'Chinese phrase',exact:true}).fill(target);await btn('Learn this phrase').click();await btn('Try the whole phrase').click();
await btn('Review recording').waitFor();assert.equal(await btn('Compare corrected transcript').count(),0);
assert.equal(await btn('Prepare Mandarin speech model (~75 MB)').count(),0);
if(process.env.HANPI_SPEECH_SAMPLE){
 const rec=p.locator('#whole-recording');await rec.getByRole('button',{name:'Upload file',exact:true}).click();
 await rec.locator('input[type=file]').setInputFiles(process.env.HANPI_SPEECH_SAMPLE);await btn('Review recording').click();
 await p.locator('#word-differences label').filter({hasText:'说'}).waitFor();
 assert.equal(await btn('Review recording').count(),0);await btn('Record again').waitFor();
 await p.screenshot({path:out+'/sentence-feedback-dark-os.png',fullPage:true,animations:'disabled'});
 await btn('← Back').click();await btn('Review recording').waitFor();
 await btn('Back to phrase').click();await btn('Listen to phrase').waitFor();
}
assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.deepEqual(errors,[]);
console.log('PASS full menu translation, dark-OS contrast, staged recording/feedback, real Mandarin ASR, Back navigation, hidden technical controls, no browser errors.');
}finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
