import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto('https://www.spinny.com/buy-used-cars/noida/hyundai/elite-i20/sportz-12-sector-4-2017/30459072/', wait_until='networkidle')
        text = await page.evaluate('document.body.innerText')
        with open('car_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        await b.close()
        
asyncio.run(run())
