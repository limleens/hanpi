/* Run against an isolated HANPI_LIBRARY_PATH with the prepared Mandarin model. */
const { chromium }=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.HANPI_UI_URL || 'http://127.0.0.1:7862/';
const output=process.env.HANPI_SCREENSHOT_DIR || '/tmp/hanpi-release-qa';
const speech=process.env.HANPI_SPEECH_SAMPLE;
fs.mkdirSync(output,{recursive:true});
(async()=>{
 for(let i=0;i<40;i++){try{if((await fetch(base)).ok)break}catch{}await new Promise(r=>setTimeout(r,500));}
 const browser=await chromium.launch({executablePath:process.env.HANPI_CHROMIUM || '/usr/bin/chromium',args:['--no-sandbox'],headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const button=name=>page.getByRole('button',{name,exact:true});
 const mode=name=>page.locator('#search-mode').getByText(name,{exact:true});
 const query=async text=>{const input=page.getByRole('textbox',{name:'Search Chinese or English',exact:true});await input.fill(text);await button('Search').click();};
 const snapshot=async name=>{
   await page.screenshot({path:path.join(output,name+'.png'),fullPage:true,animations:'disabled'});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'horizontal overflow');
 };
 try{
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await mode('English → Chinese').click();await query('eat');
  await page.locator('#lookup-results').waitFor();
  const first=page.locator('#lookup-tone-1 label').first();assert.match(await first.innerText(),/吃.*chī/);
  await snapshot('offline-eat');
  await button('Translate English online').click();
  await page.locator('#notice').filter({hasText:'offline dictionary results are still usable'}).waitFor();
  assert.match(await first.innerText(),/吃/);
  await first.click();await button('Listen to phrase').waitFor();
  assert.match(await page.locator('#meaning textarea').inputValue(),/eat/);
  console.log('PASS eat offline, blocked online provider fallback, selectable Chinese lesson');

  await mode('Pinyin lookup').click();await query('ma');
  for(let i=1;i<=5;i++) await page.locator('#lookup-tone-'+i).waitFor();
  for(const [tone,word] of [[1,'妈'],[2,'麻'],[3,'马'],[4,'骂'],[5,'吗']])
    assert.match(await page.locator('#lookup-tone-'+tone).innerText(),new RegExp(word));
  await snapshot('pinyin-ma');
  await query('ma3');
  await page.waitForFunction(()=>document.querySelector('#lookup-results')?.innerText.includes('for ma3.') && document.querySelectorAll('#lookup-tone-1 label').length===0 && document.querySelectorAll('#lookup-tone-3 label').length>0);
  await page.locator('#lookup-tone-3 label').first().click();
  await page.locator('#character-choices label').first().click();await button('Try it').waitFor();
  assert.match(await page.locator('.focus-pinyin').innerText(),/mǎ/);
  console.log('PASS tone-grouped ma, numbered pinyin, dictionary reading in Spotlight');

  await mode('Chinese → English').click();await query('我喜欢咖啡');
  await button('Listen to phrase').waitFor();
  assert.equal(await page.locator('.vocab').count(),3);
  assert.match(await page.locator('#meaning textarea').inputValue(),/coffee/);
  console.log('PASS real offline dictionary segmentation and Chinese-to-English gloss');

  await page.locator('#bottom-nav').getByRole('button',{name:'Scan',exact:true}).click();
  await page.locator('input[type=file][accept="image/*"]').setInputFiles(path.resolve('tests/fixtures/synthetic-small-red-traditional.png'));
  await button('Recognize characters').click();
  const review=page.getByRole('textbox',{name:'Verify detected Chinese before learning',exact:true});await review.waitFor();
  assert.equal(await review.inputValue(),'免治牛肉石頭飯');
  assert.equal(await button('Listen to phrase').count(),0);
  await review.fill('牛肉石頭飯');await button('Use verified text').click();
  await button('Listen to phrase').waitFor();assert.equal(await page.locator('#character-choices label').count(),5);
  await snapshot('verified-ocr');
  console.log('PASS real small-red fixture OCR, Traditional preservation, mandatory editable confirmation');

  if(!speech) throw new Error('Set HANPI_SPEECH_SAMPLE to a real Mandarin WAV for the full release check.');
  const target='对我做了介绍那么我想说的是大家如果对我的研究感兴趣呢';
  await query(target);await button('Try the whole phrase').click();
  const recording=page.locator('#whole-recording');await recording.getByRole('button',{name:'Upload file',exact:true}).click();
  await recording.locator('input[type=file]').setInputFiles(speech);
  await button('Review recording').click();
  const heard=page.locator('#heard-transcript textarea');
  await page.waitForFunction(()=>document.querySelector('#heard-transcript textarea')?.value.length>10);
  assert.equal(await heard.inputValue(),target);
  await page.getByText('The transcript text matches the target. This does not verify pronunciation or tones.',{exact:true}).waitFor();
  const differentTarget=target.replace('介绍','说明');
  await query(differentTarget);await button('Try the whole phrase').click();
  await recording.getByRole('button',{name:'Upload file',exact:true}).click();
  await recording.locator('input[type=file]').setInputFiles(speech);
  await button('Review recording').click();
  await page.locator('#word-differences label').filter({hasText:'说'}).waitFor();
  assert.equal(await heard.inputValue(),target);
  await snapshot('sentence-word-comparison');
  await page.locator('#word-differences label').filter({hasText:'说'}).click();await button('Try it').waitFor();
  assert.equal(await page.locator('.focus-hanzi').innerText(),'说');
  console.log('PASS real Mandarin recording -> local ASR -> matching and mismatching targets -> highlighted target Spotlight');

  await page.setViewportSize({width:1280,height:900});
  await mode('English → Chinese').click();await query('coffee');await page.locator('#lookup-results').waitFor();await snapshot('desktop-lookup');
  await page.setViewportSize({width:390,height:844});
  await mode('Pinyin lookup').click();await query('mǎ');await page.waitForFunction(()=>document.querySelector('#lookup-results')?.innerText.includes('for mǎ.'));
  assert.match(await page.locator('#lookup-tone-3').innerText(),/马/);
  await snapshot('accented-pinyin');
  assert.deepEqual(errors,[]);
  console.log('PASS accented pinyin, phone/desktop layout, no browser page errors. Actual device camera/mic not tested.');
 }catch(error){await page.screenshot({path:path.join(output,'failure.png'),fullPage:true});console.error((await page.locator('body').innerText()).slice(-7000));throw error;}
 finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
