import asyncio
import json
from playwright.async_api import async_playwright

async def test_city():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Visit Delhi as an example
        await page.goto("https://www.spinny.com/used-cars-in-delhi-ncr/s/", wait_until="networkidle")
        
        # Look for script tags with JSON data
        script_content = await page.evaluate('''() => {
            const scripts = document.querySelectorAll('script#__NEXT_DATA__');
            return scripts.length > 0 ? scripts[0].textContent : null;
        }''')
        
        if script_content:
            data = json.loads(script_content)
            with open("sample_next_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("Successfully extracted __NEXT_DATA__")
        else:
            print("__NEXT_DATA__ not found. They might be using something else.")
            # fallback: dump full html
            html = await page.content()
            with open("sample_page.html", "w", encoding="utf-8") as f:
                f.write(html)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_city())
