import json
import logging
import re
import asyncio
import aiohttp
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def fetch_score(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                
                headings = {
                    "engine_transmission_chassis": "Engine, transmission &amp; chassis",
                    "fuel_ignition_other": "Fuel supply, ignition &amp; other systems",
                    "interiors_ac": "Seats, AC, audio &amp; other features",
                    "exteriors_lights": "Panels, glasses, lights &amp; fixtures",
                    "tyres_clutch_brakes": "Tyres, clutch, brakes &amp; more"
                }
                
                scores = {}
                for key, h in headings.items():
                    idx = html.find(h)
                    if idx != -1:
                        snippet = html[idx:idx+500]
                        clean = re.sub(r'<[^>]+>', ' ', snippet)
                        match = re.search(r'(\d\.\d)', clean)
                        if match:
                            scores[key] = float(match.group(1))
                return scores
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
    return {}

async def process_cars():
    input_file = Path("data/cars.json")
    if not input_file.exists():
        logger.error("No cars.json found")
        return
        
    with open(input_file, "r", encoding="utf-8") as f:
        cars = json.load(f)
        
    # filter valid cars
    cars = [c for c in cars if 'permanent_url' in c]
    logger.info(f"Processing {len(cars)} cars...")
    
    # Process in batches to avoid rate limiting
    batch_size = 10
    
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(cars), batch_size):
            batch = cars[i:i+batch_size]
            tasks = []
            for car in batch:
                url = "https://www.spinny.com" + car['permanent_url']
                tasks.append(fetch_score(session, url))
                
            results = await asyncio.gather(*tasks)
            
            for j, scores in enumerate(results):
                batch[j]['condition_ratings'] = scores
                logger.info(f"Car {batch[j]['id']} scores: {scores}")
                
            await asyncio.sleep(1) # Be nice to the server
            
    with open("data/cars_with_scores.json", "w", encoding="utf-8") as f:
        json.dump(cars, f, indent=2, ensure_ascii=False)
        
    logger.info("Saved cars_with_scores.json")

if __name__ == "__main__":
    asyncio.run(process_cars())
