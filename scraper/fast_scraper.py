import os
import json
import time
import logging
from pathlib import Path
import urllib.request
from urllib.error import HTTPError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SpinnyFastScraper:
    def __init__(self):
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)
        self.cars_file = self.output_dir / "cars_fast.json"
        
        with open(self.output_dir / "cities.json", "r") as f:
            self.cities = json.load(f)
            
        self.car_data = {}
        
    def extract_city_slug(self, url: str) -> str:
        """Extracts 'delhi-ncr' from 'https://www.spinny.com/used-cars-in-delhi-ncr/s/'"""
        try:
            return url.split('/used-cars-in-')[1].split('/')[0]
        except:
            return "delhi-ncr"
            
    def fetch_page(self, city_slug: str, page: int) -> dict:
        url = f"https://api.spinny.com/v3/api/listing/v6/?city={city_slug}&product_type=cars&category=used&page={page}&size=50"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': f'https://www.spinny.com/used-cars-in-{city_slug}/s/'
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            logger.error(f"HTTP Error {e.code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def clean_car(self, car):
        car.pop('images', None)
        car.pop('reviews', None)
        car.pop('features', None)
        return car

    def run(self):
        total_scraped = 0
        seen_slugs = set()
        
        for city_obj in self.cities:
            city_slug = self.extract_city_slug(city_obj['url'])
            if city_slug in seen_slugs:
                continue
            seen_slugs.add(city_slug)
            
            logger.info(f"Mining API for {city_slug.upper()}...")
            
            page = 1
            while True:
                data = self.fetch_page(city_slug, page)
                if not data:
                    break
                    
                items = data.get('results', data.get('data', []))
                
                if not items or len(items) == 0:
                    logger.info(f"Reached end of {city_slug} at page {page-1}")
                    break
                    
                new_count = 0
                for item in items:
                    if 'id' in item:
                        cid = item['id']
                        if cid not in self.car_data:
                            self.car_data[cid] = self.clean_car(item)
                            new_count += 1
                            total_scraped += 1
                            
                logger.info(f"[{city_slug}] Page {page}: Found {new_count} new cars. (Total: {total_scraped})")
                
                if len(items) < 50:
                    break
                    
                page += 1
                time.sleep(0.5) # Be polite to their API
                
        # Save results
        with open(self.cars_file, "w", encoding="utf-8") as f:
            json.dump(list(self.car_data.values()), f, indent=2, ensure_ascii=False)
            
        logger.info(f"DONE! Mined {len(self.car_data)} total vehicles from the raw JSON API.")
        logger.info(f"Saved to {self.cars_file.absolute()}")

if __name__ == "__main__":
    scraper = SpinnyFastScraper()
    scraper.run()
