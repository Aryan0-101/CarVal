import re

def extract():
    with open("raw_car.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    headings = [
        "Engine, transmission &amp; chassis", # HTML escaped
        "Engine, transmission & chassis",
        "Fuel supply, ignition &amp; other systems",
        "Fuel supply, ignition & other systems",
        "Seats, AC, audio &amp; other features",
        "Seats, AC, audio & other features",
        "Panels, glasses, lights &amp; fixtures",
        "Panels, glasses, lights & fixtures",
        "Tyres, clutch, brakes &amp; more",
        "Tyres, clutch, brakes & more"
    ]
    
    # We will search for the heading, and then find the first \d\.\d within the next 200 characters
    results = {}
    for h in headings:
        idx = html.find(h)
        if idx != -1:
            snippet = html[idx:idx+500]
            # Strip tags to make it cleaner
            clean = re.sub(r'<[^>]+>', ' ', snippet)
            match = re.search(r'(\d\.\d)', clean)
            if match:
                results[h] = match.group(1)
            else:
                results[h] = "No score found"
                
    print(results)

if __name__ == "__main__":
    extract()
