import json, time, re, subprocess, urllib.parse, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

# Load targets missing phone numbers
with open(f'{BASE_DIR}/master_targets.json', 'r', encoding='utf-8') as f:
    targets = json.load(f)

missing = [t for t in targets if not t.get('phone')]
print(f"Searching for phone numbers for {len(missing)} businesses...\n")

# US phone regex patterns
PHONE_RE = re.compile(r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}')

def search_google_for_phone(business_name: str, location: str) -> tuple[str, float, int]:
    """Search Google via curl and extract phone, rating, review count from results."""
    query = urllib.parse.quote_plus(f'{business_name} {location} phone')
    url = f'https://www.google.com/search?q={query}'

    try:
        result = subprocess.run(
            ['curl', '-s', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', url],
            capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace'
        )
        html = result.stdout

        # Extract phone numbers
        phones = PHONE_RE.findall(html)
        phone = ''
        if phones:
            # Filter out unlikely numbers (e.g., years like 2024)
            for p in phones:
                clean = re.sub(r'[^\d]', '', p)
                if len(clean) == 10 and clean[0] not in ('0', '1'):
                    phone = f'({clean[:3]}) {clean[3:6]}-{clean[6:]}'
                    break

        # Try to extract rating
        rating = 0
        rating_match = re.search(r'(\d\.\d)\s*(?:out of 5|/5|stars?)', html)
        if rating_match:
            rating = float(rating_match.group(1))

        # Try to extract review count
        review_count = 0
        review_match = re.search(r'(\d+)\s*(?:reviews?|Google reviews?)', html)
        if review_match:
            review_count = int(review_match.group(1))

        return phone, rating, review_count
    except Exception as e:
        print(f"  Error: {e}")
        return '', 0, 0


found_count = 0
updated_targets = []

for i, target in enumerate(missing):
    name = target['name']
    location = target.get('location', 'Miami, FL')

    print(f"[{i+1}/{len(missing)}] {name}...", end=' ')

    phone, rating, reviews = search_google_for_phone(name, location)

    if phone:
        target['phone'] = phone
        found_count += 1
        print(f"FOUND: {phone}", end='')
    else:
        print("no phone found", end='')

    # Update rating/reviews if we found better data
    if rating and not target.get('rating'):
        target['rating'] = rating
        print(f" | rating={rating}", end='')
    if reviews and (not target.get('reviews') or reviews > target.get('reviews', 0)):
        target['reviews'] = reviews
        print(f" | reviews={reviews}", end='')

    print()

    # Small delay to avoid rate limiting
    time.sleep(2)

# Update master_targets.json with found phones
all_targets = []
with open(f'{BASE_DIR}/master_targets.json', 'r', encoding='utf-8') as f:
    all_targets = json.load(f)

# Map updates back
missing_map = {t['name']: t for t in missing}
for t in all_targets:
    if t['name'] in missing_map:
        updated = missing_map[t['name']]
        if updated.get('phone'):
            t['phone'] = updated['phone']
        if updated.get('rating') and not t.get('rating'):
            t['rating'] = updated['rating']
        if updated.get('reviews') and (not t.get('reviews') or updated['reviews'] > t.get('reviews', 0)):
            t['reviews'] = updated['reviews']

with open(f'{BASE_DIR}/master_targets.json', 'w', encoding='utf-8') as f:
    json.dump(all_targets, f, indent=2, ensure_ascii=False)

print(f"\nDone! Found phone numbers for {found_count}/{len(missing)} businesses.")
print(f"Updated master_targets.json")
