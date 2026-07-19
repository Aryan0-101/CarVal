import asyncio
import json
from playwright.async_api import async_playwright

async def test_car():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def handle_resp(resp):
            if "api.spinny.com" in resp.url or "api" in resp.url:
                print(f"API: {resp.url}")
        
        page.on("response", handle_resp)
        url = "https://www.spinny.com/buy-used-cars/noida/hyundai/elite-i20/sportz-12-sector-4-2017/30459072/"
        print(f"Visiting {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Scroll to bottom to trigger any lazy loading
        for i in range(5):
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(1)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_car())
