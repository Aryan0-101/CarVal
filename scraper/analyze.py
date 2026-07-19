import json
from bs4 import BeautifulSoup

def analyze_html():
    with open("sample_page.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Check scripts for JSON data
    print("Script tags:")
    for script in soup.find_all("script"):
        content = script.string
        if content and len(content) > 1000: # Probably embedded JSON data
            print(f"- Large script found. Starts with: {content[:100]}...")
            
    # 2. Check for car cards
    print("\nLooking for car cards...")
    # Typically Spinny has links like /buy-used-cars/...
    links = soup.find_all("a", href=True)
    car_links = set([link['href'] for link in links if '/buy-used-cars/' in link['href']])
    print(f"Found {len(car_links)} car links")
    for link in list(car_links)[:5]:
        print(link)

if __name__ == "__main__":
    analyze_html()
