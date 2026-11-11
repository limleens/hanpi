/* Real Gradio authentication; random QA credentials never printed or committed. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const {randomBytes}=require('node:crypto');
const net=require('node:net'),fs=require('node:fs'),path=require('node:path');
const assert=require('node:assert/strict');

(async()=>{
 const listener=net.createServer();
 await new Promise(r=>listener.listen(0,'127.0.0.1',r));
 const port=listener.address().port;await new Promise(r=>listener.close(r));
 const base=`http://127.0.0.1:${port}/`,password=randomBytes(24).toString('base64url');
 const out=process.env.HANPI_SCREENSHOT_DIR||'/tmp/hanpi-auth-qa';fs.mkdirSync(out,{recursive:true});
 const child=spawn(process.env.HANPI_PYTHON||path.resolve('.venv/bin/python'),['-u','-c',`
import os, app
app.build_app().launch(server_name='127.0.0.1',server_port=${port},inbrowser=False,
 auth=('qa-demo',os.environ['HANPI_AUTH_QA_PASSWORD']),auth_message=app.AUTH_MESSAGE,
 theme=app.make_theme(),css=app.CSS)
`],{env:{...process.env,HANPI_AUTH_QA_PASSWORD:password,MPLBACKEND:'Agg',MPLCONFIGDIR:process.env.MPLCONFIGDIR||'/tmp/hanpi-auth-mpl',GRADIO_ANALYTICS_ENABLED:'False'}});
 let log='';child.stdout.on('data',x=>log+=x);child.stderr.on('data',x=>log+=x);
 let browser;
 try{
  for(let i=0;i<120;i++){
   if(child.exitCode!==null)throw new Error(log);
   try{if((await fetch(base)).ok)break}catch{}
   if(i===119)throw new Error('Auth server did not start: '+log);
   await new Promise(r=>setTimeout(r,250));
  }
  browser=await chromium.launch({executablePath:process.env.HANPI_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
  const errors=[];
  for(const [width,height,colorScheme] of [[390,844,'dark'],[1280,900,'light'],[320,640,'dark']]){
   const page=await browser.newPage({viewport:{width,height},colorScheme,reducedMotion:'reduce'});
   page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base,{waitUntil:'domcontentloaded'});await page.locator('#hanpi-welcome').waitFor();
   await page.evaluate(()=>document.fonts.ready);
   const styles=await page.evaluate(()=>({
    body:getComputedStyle(document.body).backgroundColor,
    title:getComputedStyle(document.querySelector('.welcome-title')).fontFamily,
    input:getComputedStyle(document.querySelector('input')).fontFamily,
    button:getComputedStyle(document.querySelector('button.primary')).backgroundColor,
    overflow:document.documentElement.scrollWidth>innerWidth+1,
    loaded:[...document.fonts].filter(f=>/Fredoka|Plus Jakarta Sans/.test(f.family)&&f.status==='loaded').length
   }));
   assert.equal(styles.body,'rgb(255, 250, 240)');assert.match(styles.title,/Fredoka/);
   assert.match(styles.input,/Plus Jakarta Sans/);assert.equal(styles.button,'rgb(255, 149, 10)');assert(!styles.overflow);
   assert.equal(styles.loaded,2,'Both bundled brand fonts must actually load.');
   await page.screenshot({path:`${out}/login-${width}-${colorScheme}.png`,fullPage:true,animations:'disabled'});
   assert.equal((await page.request.get(base+'config')).status(),401);
   if(width===390){
    await page.getByLabel(/username/i).fill('qa-demo');await page.getByLabel(/password/i).fill('wrong-demo-password');
    await page.getByRole('button',{name:'Login',exact:true}).click();await page.locator('.creds').waitFor();
    assert.equal((await page.request.get(base+'config')).status(),401);
    await page.getByLabel(/username/i).fill('qa-demo');await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button',{name:'Login',exact:true}).click();
    await page.getByRole('button',{name:'Recognize characters',exact:true}).waitFor();
    assert.equal((await page.request.get(base+'config')).status(),200);
    assert.equal(await page.locator('#hanpi-welcome').count(),0);
    await page.reload();await page.getByRole('button',{name:'Recognize characters',exact:true}).waitFor();
   }
   await page.close();
  }
  assert.deepEqual(errors,[]);
  console.log('PASS branded login at 320/390/1280px, light/dark contrast/fonts, wrong-password rejection, protected config, successful login and reload session.');
 }finally{
  if(browser)await browser.close();
  child.kill('SIGTERM');
 }
})().catch(e=>{console.error(e);process.exitCode=1});
