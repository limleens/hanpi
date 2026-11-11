/* Run against a Hanpi server with an isolated HANPI_LIBRARY_PATH.
 * Requires Playwright and Chromium. No camera/mic hardware or real TTS is simulated as verified.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const base = process.env.HANPI_UI_URL || 'http://127.0.0.1:7860/';
const artifacts = process.env.HANPI_SCREENSHOT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'hanpi-ui-'));
fs.mkdirSync(artifacts, { recursive: true });
const python = process.env.HANPI_PYTHON || path.resolve('.venv/bin/python');
execFileSync(python, ['-c', `
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import numpy as np, soundfile as sf, os
folder=Path(${JSON.stringify(artifacts)})
font_path=os.environ.get('HANPI_TEST_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
font=ImageFont.truetype(font_path,78)
image=Image.new('RGB',(900,180),'white')
ImageDraw.Draw(image).text((35,30),'我喜欢咖啡',font=font,fill='black')
image.save(folder/'ocr.png')
sr=16000
t=np.arange(int(sr*.85))/sr
contour=np.interp(t/.85,np.linspace(0,1,5),[3,1,-1,-3,-4])
f=195*2**(contour/12)
phase=2*np.pi*np.cumsum(f)/sr
env=np.minimum(1,np.minimum(t/.07,(.85-t)/.07)).clip(0,1)
sf.write(folder/'tone4.wav',env*(.28*np.sin(phase)+.1*np.sin(2*phase)),sr)
`], { stdio: 'inherit' });

(async () => {
  for (let attempt=0; attempt<40; attempt++) {
    try { const response=await fetch(base,{signal:AbortSignal.timeout(2000)}); if(response.ok) break; } catch {}
    if(attempt===39) throw new Error('Hanpi did not become ready at '+base);
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  const browser = await chromium.launch({
    executablePath: process.env.HANPI_CHROMIUM || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  // Verify the speech callback's text/rate, without claiming audible speech works.
  await page.addInitScript(() => {
    window.__spoken = [];
    window.speechSynthesis.speak = u => window.__spoken.push({text:u.text, rate:u.rate, lang:u.lang});
  });
  const button = name => page.getByRole('button', { name, exact: true });
  const navigate = async name => {
    await page.locator('#bottom-nav').getByRole('button',{name,exact:true}).click();
  };
  const snapshot = async name => {
    await page.screenshot({ path: path.join(artifacts, name + '.png'), fullPage: true, animations: 'disabled' });
    const widths = await page.evaluate(() => ({viewport:innerWidth, page:document.documentElement.scrollWidth}));
    assert(widths.page <= widths.viewport + 1, `Horizontal overflow: ${JSON.stringify(widths)}`);
  };
  try {
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    await button('Recognize characters').waitFor();
    await snapshot('mobile-scan');
    await button('Recognize characters').click();
    await page.locator('#notice').getByRole('status').filter({hasText:'Upload a photo'}).waitFor();
    console.log('PASS empty Scan: actionable error');

    await page.locator('input[type=file][accept="image/*"]').setInputFiles(path.join(artifacts, 'ocr.png'));
    await button('Recognize characters').click();
    await button('Use verified text').waitFor();
    await button('Use verified text').click();
    await button('Listen to phrase').waitFor();
    await page.waitForFunction(() => document.querySelectorAll('#character-choices label').length === 5);
    assert.match(await page.locator('#meaning textarea').inputValue(), /coffee/);
    await page.getByText('Words in this phrase',{exact:true}).click();
    await page.locator('.vocab').first().waitFor();
    assert.equal(await page.locator('.vocab').count(), 3);
    await page.getByText('Words in this phrase',{exact:true}).click();
    const toneColors = await page.locator('#character-choices label').evaluateAll(xs => xs.map(x => getComputedStyle(x).color));
    assert.notEqual(toneColors[0], toneColors[2], 'Third and first tones need different colours');
    const clipped = await page.locator('#character-choices label').evaluateAll(xs=>xs.some(x=>{const label=x.getBoundingClientRect(),text=x.querySelector('span').getBoundingClientRect();return text.left<label.left || text.right>label.right}));
    assert(!clipped,'Pinyin must stay inside its own character button');
    await snapshot('mobile-results');
    console.log('PASS real OCR -> shared Results, pinyin, word gloss and vocabulary');

    await page.getByText('Voice & speed',{exact:true}).click();
    await page.getByText('Browser voice', {exact:true}).click();
    await page.getByText('1.25×', {exact:true}).click();
    await page.getByText('Voice & speed',{exact:true}).click();
    await button('Listen to phrase').click();
    await page.waitForFunction(() => window.__spoken.length === 1);
    assert.deepEqual(await page.evaluate(() => window.__spoken[0]), {text:'我喜欢咖啡', rate:1.25, lang:'zh-CN'});
    console.log('PASS browser speech callback text/rate; no real audio playback claim');

    await page.locator('#character-choices label').nth(3).click();
    await button('Try it').waitFor();
    await page.waitForFunction(() => document.querySelector('.focus-hanzi')?.textContent === '咖');
    const opacity = await page.locator('#character-choices label').evaluateAll(xs => xs.map(x => Number(getComputedStyle(x).opacity)));
    assert.equal(opacity[3], 1); assert(opacity[0] < 1);
    await snapshot('mobile-spotlight');
    await button('Try it').click();
    await button('Check my tone').click();
    await page.locator('#feedback').filter({hasText:'clearer sound'}).waitFor();
    await button('Try again').click();
    await page.locator('#feedback').filter({hasText:'Ready when you are'}).waitFor();
    await button('Next character').click();
    await page.waitForFunction(() => document.querySelector('.focus-hanzi')?.textContent === '啡');
    await button('Back to phrase').click();
    await button('Listen to phrase').waitFor();
    assert.match(await page.locator('#meaning textarea').inputValue(), /coffee/);
    console.log('PASS Spotlight, dimming, uncertainty feedback, retry, next, back and retained phrase');

    await navigate('Type');
    await page.getByRole('textbox', {name:'Chinese phrase', exact:true}).fill('汉'.repeat(60));
    await button('Learn this phrase').click();
    await page.waitForFunction(() => document.querySelectorAll('#character-choices label').length === 60);
    console.log('PASS all 60 typed characters retained');

    const search = page.getByRole('textbox', {name:'Search Chinese or English', exact:true});
    if(!await search.isVisible()) await button('← Back').click();
    await search.fill('coffee'); await search.press('Enter');
    await button('Translate English online').waitFor();
    await page.locator('#lookup-results').waitFor();
    assert.match(await page.locator('#lookup-tone-1 label').first().innerText(),/咖啡/);
    await page.locator('#lookup-tone-1 label').first().click();
    await button('Listen to phrase').waitFor();
    console.log('PASS English search uses offline candidates; online translation remains opt-in');

    if(!await search.isVisible()) await button('← Back').click();
    await search.fill('骂'); await search.press('Enter');
    await page.waitForFunction(() => document.querySelectorAll('#character-choices label').length === 1);
    await button('☆ Save phrase').click();
    await page.locator('#notice').getByRole('status').filter({hasText:'Saved 骂'}).waitFor();
    await page.locator('#character-choices label').first().click();
    await button('Try it').click();
    // Switch the audio component to its upload source, then upload a known synthetic falling tone.
    const recording = page.locator('#practice-recording');
    await recording.getByRole('button', {name:'Upload file', exact:true}).click();
    await recording.locator('input[type=file]').setInputFiles(path.join(artifacts, 'tone4.wav'));
    await button('Check my tone').click();
    await page.locator('#feedback').filter({hasText:'Your tone shape looks close'}).waitFor();
    await snapshot('mobile-feedback');
    await button('Next character').click();
    await page.getByText('Nice practice session!', {exact:true}).waitFor();
    await button('Done').click();
    await button('Try the whole phrase').click();
    await button('Review recording').click();
    await page.getByText('Record your attempt first. You can play it back and choose a character to practise.', {exact:true}).waitFor();
    await button('Finish practice').click();
    await page.getByText('Nice practice session!', {exact:true}).waitFor();
    console.log('PASS synthetic audio upload -> matching pitch feedback -> completion; whole-phrase review has no fake grade');

    await navigate('Saved');
    const card = page.locator('.library-card').filter({hasText:'骂'});
    await card.waitFor();
    assert.match(await card.innerText(), /1 practice\(s\)/);
    await page.reload({waitUntil:'domcontentloaded'});
    await navigate('Saved');
    await card.waitFor();
    await button('Practise again').click();
    await page.waitForFunction(() => document.querySelectorAll('#character-choices label').length === 1);
    assert.match(await page.locator('#meaning textarea').inputValue(), /scold/i);
    await navigate('Saved');
    await button('Remove star').click();
    await page.locator('.library-empty').waitFor();
    console.log('PASS save, matching practice counter, reload persistence, reopen and remove');

    await navigate('Speak');
    await button('Use my recording').click();
    await page.getByText('Record a phrase first, then transcribe it.', {exact:true}).waitFor();
    await button('Use this text').click();
    await page.locator('#notice').getByRole('status').filter({hasText:'Enter Chinese text'}).waitFor();
    console.log('PASS Speak missing recording/transcript states');

    await page.setViewportSize({width:1280,height:900});
    await navigate('Scan');
    await snapshot('desktop-scan');
    await navigate('Type');
    await page.getByRole('textbox', {name:'Chinese phrase', exact:true}).fill('我喜欢咖啡');
    await button('Learn this phrase').click();
    await button('Listen to phrase').waitFor();
    await snapshot('desktop-results');
    await page.locator('#character-choices label').nth(3).locator('input').focus();
    await page.keyboard.press('Space');
    await button('Try it').waitFor();
    await page.waitForFunction(() => document.querySelector('.focus-hanzi')?.textContent === '咖');
    console.log('PASS desktop layout and keyboard character selection');
    assert.deepEqual(errors, []);
    console.log('PASS no browser page errors. Screenshots:', artifacts);
  } catch (error) {
    await page.screenshot({path:path.join(artifacts,'failure.png'), fullPage:true, animations:'disabled'});
    console.error('Page at failure:',(await page.locator('body').innerText()).slice(-6000));
    throw error;
  } finally { await browser.close(); }
})().catch(e => {console.error(e);process.exit(1);});
