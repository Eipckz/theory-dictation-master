import {chromium} from '@playwright/test';
import fs from 'node:fs';
const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:1440,height:1000}});
await page.goto('http://127.0.0.1:4173');await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:'docs/media/web-today.png',fullPage:true});
await page.locator('[data-page="learn"]').click();await page.locator('#lesson-select').selectOption('6');await page.screenshot({path:'docs/media/web-learn.png',fullPage:true});
await page.locator('#lesson-guided').click();await page.locator('#duration').selectOption('12');for(const pitch of ['28','29','30','28'])await page.locator('[data-pitch="'+pitch+'"]').click();await page.screenshot({path:'docs/media/web-practice.png',fullPage:true});
await page.locator('[data-page="settings"]').click();await page.screenshot({path:'docs/media/web-settings.png',fullPage:true});
await page.setViewportSize({width:390,height:844});await page.locator('[data-page="practice"]').click();await page.screenshot({path:'docs/media/web-mobile.png',fullPage:true});await browser.close();
