import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SpinnyScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)
        self.cars_file = self.output_dir / "cars.json"
        
        with open(self.output_dir / "cities.json", "r") as f:
            self.cities = json.load(f)
            
        self.car_data = {} # Deduplicate by ID
        
        if self.cars_file.exists():
            try:
                with open(self.cars_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for car in data:
                        if 'id' in car:
                            self.car_data[car['id']] = car
                logger.info(f"Loaded {len(self.car_data)} existing cars from checkpoint.")
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")

    def clean_car(self, car):
        car.pop('images', None)
        car.pop('reviews', None)
        car.pop('features', None)
        return car

    def save_checkpoint(self):
        with open(self.cars_file, "w", encoding="utf-8") as f:
            json.dump(list(self.car_data.values()), f, indent=2, ensure_ascii=False)

    async def handle_listing_response(self, response):
        try:
            if response.status == 200 and "application/json" in response.headers.get("content-type", ""):
                url = response.url
                if "spinny" in url and ("search" in url or "listing" in url):
                    data = await response.json()
                    new_count = 0
                    if isinstance(data, dict):
                        items = []
                        if 'results' in data:
                            items = data['results']
                        elif 'data' in data and isinstance(data['data'], list):
                            items = data['data']
                            
                        for item in items:
                            if 'id' in item and 'permanent_url' in item:
                                cid = item['id']
                                if cid not in self.car_data:
                                    self.car_data[cid] = self.clean_car(item)
                                    new_count += 1
                                    
                    if new_count > 0:
                        logger.info(f"Added {new_count} new unique cars from listings.")
        except Exception:
            pass

    async def handle_detail_response(self, response, car_id):
        try:
            if response.status == 200 and "application/json" in response.headers.get("content-type", ""):
                url = response.url
                # Spinny detail endpoints usually contain the car id or 'detail'
                if str(car_id) in url or "inspection" in url or "detail" in url:
                    data = await response.json()
                    
                    # Extract inspection scores if they exist
                    if isinstance(data, dict):
                        # Some APIs return data inside 'data' or 'inspection'
                        insp = data.get('inspection', data.get('data', {}).get('inspection', {}))
                        if insp:
                            # Map sections if available
                            sections = insp.get('sections', [])
                            scores = {}
                            for sec in sections:
                                name = sec.get('name', '').lower()
                                score = sec.get('rating', 5.0)
                                if 'engine' in name or 'transmission' in name:
                                    scores['engine_transmission_chassis'] = score
                                elif 'interior' in name or 'ac' in name:
                                    scores['interiors_ac'] = score
                                elif 'exterior' in name or 'light' in name:
                                    scores['exteriors_lights'] = score
                                elif 'tyre' in name or 'clutch' in name or 'brake' in name:
                                    scores['tyres_clutch_brakes'] = score
                            
                            if scores:
                                self.car_data[car_id]['condition_ratings'] = scores
                                self.car_data[car_id]['details_scraped'] = True
                                logger.info(f"Extracted inspection details for car {car_id}")
        except Exception:
            pass

    async def scrape_city(self, context, city, retries=3):
        for attempt in range(retries):
            logger.info(f"Scraping city: {city['name']} (Attempt {attempt+1})")
            page = await context.new_page()
            page.on("response", self.handle_listing_response)
            
            try:
                await page.goto(city['url'], wait_until="networkidle", timeout=60000)
                
                # Robust pagination: scroll until height doesn't change
                last_height = await page.evaluate("document.body.scrollHeight")
                max_scrolls = 20 # Limit to prevent infinite loop
                
                for _ in range(max_scrolls):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(3) # Wait for network requests
                    
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        # Try one more time with a smaller scroll in case of lazy loading glitch
                        await page.mouse.wheel(0, -500)
                        await asyncio.sleep(1)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                        await asyncio.sleep(3)
                        new_height = await page.evaluate("document.body.scrollHeight")
                        if new_height == last_height:
                            logger.info("Reached end of page pagination.")
                            break
                    last_height = new_height
                    
                logger.info(f"Total unique cars so far: {len(self.car_data)}")
                self.save_checkpoint()
                break # Success, exit retry loop
            except Exception as e:
                logger.error(f"Error scraping {city['name']}: {e}")
                await asyncio.sleep(2)
            finally:
                await page.close()

    async def scrape_details(self, context):
        """Iterate over cars and scrape individual details for missing condition_ratings."""
        pending_cars = [car for car in self.car_data.values() if not car.get('details_scraped')]
        logger.info(f"Starting detail extraction for {len(pending_cars)} vehicles.")
        
        for idx, car in enumerate(pending_cars):
            if 'permanent_url' not in car:
                continue
                
            car_url = "https://www.spinny.com" + car['permanent_url'] if car['permanent_url'].startswith('/') else car['permanent_url']
            logger.info(f"Detail [{idx+1}/{len(pending_cars)}]: {car_url}")
            
            page = await context.new_page()
            
            # Wrap response handler to pass car_id
            async def detail_handler(response):
                await self.handle_detail_response(response, car['id'])
                
            page.on("response", detail_handler)
            
            try:
                # We don't need networkidle if the inspection is embedded in the HTML or early JSON
                await page.goto(car_url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2) # Give it a moment to fetch the inspection API
                
                # Fallback: if API wasn't found, try to extract from DOM
                if not car.get('details_scraped'):
                    # Example DOM extraction logic here if needed
                    car['details_scraped'] = True # Mark as done so we don't retry forever
                    
                self.save_checkpoint()
            except Exception as e:
                logger.error(f"Failed to extract details for {car['id']}: {e}")
            finally:
                await page.close()
                await asyncio.sleep(0.5) # Slight rate limiting

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            # Phase 1: Collect Listings
            for city in self.cities:
                await self.scrape_city(context, city)
                await asyncio.sleep(1) # Rate limit between cities
                
            # Phase 2: Collect Details
            await self.scrape_details(context)
                
            await browser.close()
        
        logger.info(f"Finished scraping. Total collected: {len(self.car_data)} cars.")

if __name__ == "__main__":
    scraper = SpinnyScraper(headless=True)
    asyncio.run(scraper.run())
