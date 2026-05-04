"""
Local Google Maps scraper for contractor leads.
Runs Playwright headless — no Apify credits needed.
Searches multiple categories, filters for no-website + has-phone businesses.
"""
import json, time, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

SEARCH_QUERIES = [
    "handyman miami FL",
    "handyman fort lauderdale FL",
    "pressure washing miami FL",
    "pressure washing broward FL",
    "fence installer south florida",
    "landscaping miami dade FL",
    "lawn care miami FL",
    "tree service miami FL",
    "pool service miami FL",
    "painting contractor miami FL",
    "concrete contractor south florida",
    "junk removal miami FL",
    "tile installer miami FL",
    "roofing contractor miami FL",
    "plumber miami FL",
    "electrician miami FL",
    "flooring installer miami FL",
    "paver installation south florida",
    "moving company miami FL",
    "pressure cleaning fort lauderdale FL",
]


def scrape_query(page, query: str, max_results: int = 20) -> list:
    """Search Google Maps for a query and extract business info."""
    results = []
    search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)

        # Wait for results feed
        try:
            page.wait_for_selector('div[role="feed"]', timeout=8000)
        except Exception:
            print("    No results feed found", flush=True)
            return results

        # Scroll to load results
        prev_count = 0
        scroll_attempts = 0
        while scroll_attempts < 10:
            listings = page.query_selector_all('a[href*="/maps/place/"]')
            if len(listings) >= max_results:
                break
            if len(listings) == prev_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            prev_count = len(listings)
            page.evaluate('const f=document.querySelector(\'div[role="feed"]\');if(f)f.scrollTop+=1000;')
            page.wait_for_timeout(1500)

        listings = page.query_selector_all('a[href*="/maps/place/"]')

        for i, listing in enumerate(listings[:max_results]):
            try:
                listing.click()
                page.wait_for_timeout(2000)

                biz = {}

                name_el = page.query_selector('h1.DUwDvf')
                if name_el:
                    biz['name'] = name_el.inner_text()

                rating_el = page.query_selector('div.F7nice span[aria-hidden="true"]')
                if rating_el:
                    try:
                        biz['rating'] = float(rating_el.inner_text())
                    except ValueError:
                        biz['rating'] = 0

                review_el = page.query_selector('div.F7nice span[aria-label*="review"]')
                if review_el:
                    label = review_el.get_attribute('aria-label') or ''
                    match = re.search(r'(\d[\d,]*)', label)
                    if match:
                        biz['reviews'] = int(match.group(1).replace(',', ''))

                cat_el = page.query_selector('button.DkEaL')
                if cat_el:
                    biz['category'] = cat_el.inner_text()

                addr_els = page.query_selector_all('button[data-item-id="address"] div.fontBodyMedium')
                if addr_els:
                    biz['address'] = addr_els[0].inner_text()

                phone_els = page.query_selector_all('button[data-item-id*="phone"] div.fontBodyMedium')
                if phone_els:
                    biz['phone'] = phone_els[0].inner_text()

                website_els = page.query_selector_all('a[data-item-id="authority"] div.fontBodyMedium')
                if website_els:
                    biz['website'] = website_els[0].inner_text()
                else:
                    biz['website'] = ''

                biz['maps_url'] = page.url

                if biz.get('name'):
                    results.append(biz)

            except Exception as e:
                continue

    except Exception as e:
        print(f"    Page error: {e}", flush=True)

    return results


def main():
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 60

    # Load existing targets
    existing_path = f'{BASE_DIR}/master_targets.json'
    if os.path.exists(existing_path):
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        existing_phones = {re.sub(r'\D', '', t.get('phone', ''))[-10:] for t in existing if t.get('phone')}
        existing_names = {t.get('name', '').lower().strip() for t in existing if t.get('name')}
    else:
        existing_phones = set()
        existing_names = set()

    print(f"Local Google Maps scraper — {len(SEARCH_QUERIES)} queries, target {target_count} leads")
    print(f"Skipping {len(existing_names)} existing targets\n")

    all_businesses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for qi, query in enumerate(SEARCH_QUERIES):
            print(f"[{qi+1}/{len(SEARCH_QUERIES)}] {query}...", end=' ', flush=True)
            results = scrape_query(page, query, max_results=20)
            print(f"{len(results)} businesses", flush=True)

            for r in results:
                r['_source_query'] = query
            all_businesses.extend(results)

            time.sleep(2)

        browser.close()

    print(f"\nTotal raw: {len(all_businesses)}")

    # Dedup by name
    seen = set()
    unique = []
    for biz in all_businesses:
        name = (biz.get('name') or '').lower().strip()
        if name and name not in seen:
            seen.add(name)
            unique.append(biz)
    print(f"After dedup: {len(unique)}")

    # Filter: no website + has phone
    no_website = [b for b in unique if not b.get('website') and b.get('phone')]
    print(f"No website + has phone: {len(no_website)}")

    # Remove existing
    new_leads = []
    for biz in no_website:
        name = (biz.get('name') or '').lower().strip()
        phone = re.sub(r'\D', '', biz.get('phone', ''))[-10:]
        if name in existing_names or (phone and phone in existing_phones):
            continue
        new_leads.append(biz)
    print(f"New leads (not in existing): {len(new_leads)}")

    # Format targets
    targets = []
    for biz in new_leads[:target_count]:
        category = biz.get('category', '')
        if not category:
            query = biz.get('_source_query', '').lower()
            if 'handyman' in query: category = 'Handyman'
            elif 'pressure' in query: category = 'Pressure Washing'
            elif 'fence' in query: category = 'Fence Contractor'
            elif 'landscap' in query: category = 'Landscaping'
            elif 'lawn' in query: category = 'Lawn Care'
            elif 'tree' in query: category = 'Tree Service'
            elif 'pool' in query: category = 'Pool Service'
            elif 'paint' in query: category = 'Painting'
            elif 'concrete' in query: category = 'Concrete Contractor'
            elif 'junk' in query: category = 'Junk Removal'
            elif 'tile' in query: category = 'Tile Contractor'
            elif 'roof' in query: category = 'Roofing'
            elif 'plumb' in query: category = 'Plumbing'
            elif 'electric' in query: category = 'Electrical'
            elif 'floor' in query: category = 'Flooring'
            elif 'paver' in query: category = 'Paver Installation'
            elif 'moving' in query: category = 'Moving Service'
            else: category = 'General Contractor'

        location = biz.get('address', 'Miami, FL')
        if ',' in location:
            parts = [p.strip() for p in location.split(',')]
            if len(parts) >= 2:
                location = f"{parts[-2]}, FL"

        targets.append({
            "name": biz.get('name', ''),
            "ig": "",
            "phone": biz.get('phone', ''),
            "category": category,
            "location": location,
            "rating": biz.get('rating', 0),
            "reviews": biz.get('reviews', 0),
            "has_site": False,
            "notes": f"GMaps: {biz.get('_source_query', '')[:30]}",
            "maps_url": biz.get('maps_url', ''),
        })

    # Save
    output_path = f'{BASE_DIR}/gmaps_targets_batch.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    raw_path = f'{BASE_DIR}/gmaps_raw_results.json'
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(all_businesses, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {len(targets)} new contractor targets without websites.")
    print(f"Saved to: {output_path}")

    if targets:
        cats = {}
        for t in targets:
            cats[t['category']] = cats.get(t['category'], 0) + 1
        print("\nCategories:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
