import asyncio
from playwright.async_api import async_playwright

async def get_cities():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to Spinny...")
        await page.goto("https://www.spinny.com/used-cars/", wait_until="networkidle")
        
        # We need to extract the cities from the page.
        # Let's dump all links on the page to identify city links.
        links = await page.eval_on_selector_all("a", "elements => elements.map(e => ({text: e.innerText, href: e.href}))")
        
        print("Found links. Filtering cities...")
        cities = {}
        for link in links:
            href = link['href']
            text = link['text'].strip()
            # Spinny city links typically look like: https://www.spinny.com/used-cars-in-delhi/ 
            # or https://www.spinny.com/used-cars-in-mumbai/s/
            if "used-cars-in-" in href and text:
                cities[text] = href
                
        import json
        import os
        os.makedirs("data", exist_ok=True)
        city_list = [{"name": city, "url": url} for city, url in cities.items()]
        with open("data/cities.json", "w") as f:
            json.dump(city_list, f, indent=2)
            
        for city, url in cities.items():
            print(f"City: {city}, URL: {url}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_cities())
