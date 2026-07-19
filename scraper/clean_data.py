import json

with open('data/cars_with_scores.json', 'r', encoding='utf-8') as f:
    cars = json.load(f)

cleaned_cars = []
for car in cars:
    # Keep only necessary fields
    cleaned = {
        'id': car.get('id'),
        'make': car.get('make'),
        'model': car.get('model'),
        'variant': car.get('variant'),
        'make_year': car.get('make_year'),
        'mileage': car.get('mileage'),
        'price': car.get('price'),
        'fuel_type': car.get('fuel_type'),
        'transmission': car.get('transmission'),
        'body_type': car.get('body_type'),
        'city': car.get('city'),
        'no_of_owners': car.get('no_of_owners'),
        'permanent_url': car.get('permanent_url'),
        'condition_ratings': car.get('condition_ratings', {})
    }
    cleaned_cars.append(cleaned)

with open('data/cars_clean.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned_cars, f, indent=2)
    
print("Cleaned JSON saved to data/cars_clean.json")
