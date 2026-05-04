"""
Find contractor targets via Apify Google Maps Lead Generator.
Searches multiple categories, filters for no-website businesses, then checks IG.
"""
import json, time, sys, asyncio, urllib.request, urllib.parse, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
APIFY_TOKEN = os.environ.get('APIFY_TOKEN', '')
ACTOR_ID = 'Ea3kaZU7JKxxVRHnb'

SEARCH_QUERIES = [
    "handyman miami FL",
    "pressure washing miami FL",
    "pressure washing fort lauderdale FL",
    "fence installer miami FL",
    "landscaping miami FL",
    "lawn care broward county FL",
    "tree service miami FL",
    "pool service miami FL",
    "painting contractor miami FL",
    "concrete contractor miami FL",
    "junk removal miami FL",
    "tile contractor miami FL",
    "roofing contractor hialeah FL",
    "plumber miami FL no website",
    "electrician broward FL",
    "flooring installer miami FL",
    "paver installation miami dade FL",
    "pressure cleaning pompano beach FL",
    "handyman fort lauderdale FL",
    "moving service miami FL",
]


def api_call(method: str, url: str, data: dict = None) -> dict:
    """Make Apify API call."""
    full_url = f"{url}?token={APIFY_TOKEN}"
    if data:
        body = json.dumps(data).encode()
        req = urllib.request.Request(full_url, data=body, method=method,
                                     headers={'Content-Type': 'application/json'})
    else:
        req = urllib.request.Request(full_url, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def start_actor_run(query: str, max_results: int = 20) -> str:
    """Start an actor run, return run ID."""
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    input_data = {
        "searchQuery": query,
        "maxResults": max_results,
        "enrichLeads": False,
    }
    result = api_call('POST', url, input_data)
    run_id = result['data']['id']
    return run_id


def wait_for_run(run_id: str, timeout: int = 300) -> str:
    """Wait for actor run to complete. Returns status."""
    url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    start = time.time()
    while time.time() - start < timeout:
        result = api_call('GET', url)
        status = result['data']['status']
        if status in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
            return status
        time.sleep(5)
    return 'TIMEOUT'


def get_run_results(run_id: str) -> list:
    """Get dataset items from a completed run."""
    url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"
    result = api_call('GET', url)
    if isinstance(result, list):
        return result
    return result.get('data', result) if isinstance(result, dict) else []


def main():
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    # Load existing to avoid dupes
    existing_path = f'{BASE_DIR}/master_targets.json'
    if os.path.exists(existing_path):
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        existing_phones = {t.get('phone', '').replace('-', '').replace(' ', '')[-10:] for t in existing if t.get('phone')}
        existing_names = {t.get('name', '').lower().strip() for t in existing if t.get('name')}
    else:
        existing_phones = set()
        existing_names = set()

    print(f"Starting Apify Google Maps scrape for {len(SEARCH_QUERIES)} queries...")
    print(f"Existing targets to skip: {len(existing_names)} names, {len(existing_phones)} phones\n")

    # Start all runs (Apify allows 25 concurrent)
    runs = {}
    for i, query in enumerate(SEARCH_QUERIES):
        try:
            run_id = start_actor_run(query, max_results=20)
            runs[run_id] = query
            print(f"  [{i+1}/{len(SEARCH_QUERIES)}] Started: {query} (run: {run_id[:8]}...)")
            time.sleep(1)
        except Exception as e:
            print(f"  [{i+1}] FAILED to start {query}: {e}")

    print(f"\n{len(runs)} runs started. Waiting for completion...\n")

    # Wait for all runs
    all_businesses = []
    for run_id, query in runs.items():
        print(f"  Waiting: {query[:40]}...", end=' ', flush=True)
        status = wait_for_run(run_id, timeout=300)
        if status == 'SUCCEEDED':
            items = get_run_results(run_id)
            print(f"OK - {len(items)} results")
            for item in items:
                item['_source_query'] = query
            all_businesses.extend(items)
        else:
            print(f"FAILED ({status})")

    print(f"\nTotal raw results: {len(all_businesses)}")

    # Deduplicate by name
    seen_names = set()
    unique = []
    for biz in all_businesses:
        name = (biz.get('name') or '').lower().strip()
        if name and name not in seen_names:
            seen_names.add(name)
            unique.append(biz)
    print(f"After dedup: {len(unique)}")

    # Filter: no website
    no_website = [b for b in unique if not b.get('website')]
    print(f"Without website: {len(no_website)}")

    # Filter out existing targets
    new_leads = []
    for biz in no_website:
        name = (biz.get('name') or '').lower().strip()
        phone = (biz.get('phone') or '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')[-10:]
        if name in existing_names:
            continue
        if phone and phone in existing_phones:
            continue
        new_leads.append(biz)
    print(f"New (not in master_targets): {len(new_leads)}")

    # Format as targets
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
        if len(location) > 50:
            location = location.split(',')[-2].strip() + ', FL' if ',' in location else 'Miami, FL'

        target = {
            "name": biz.get('name', ''),
            "ig": "",
            "phone": biz.get('phone', ''),
            "category": category,
            "location": location,
            "rating": float(biz.get('rating', 0) or 0),
            "reviews": int(biz.get('review_count', 0) or 0),
            "has_site": False,
            "notes": f"Google Maps - {biz.get('_source_query', '')[:30]}",
            "maps_url": biz.get('maps_url', ''),
        }
        targets.append(target)

    # Save
    output_path = f'{BASE_DIR}/apify_targets_batch.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    # Also save full raw data
    raw_path = f'{BASE_DIR}/apify_raw_results.json'
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(all_businesses, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Found {len(targets)} new targets without websites.")
    print(f"Targets saved to: {output_path}")
    print(f"Raw data saved to: {raw_path}")

    if targets:
        cats = {}
        for t in targets:
            cats[t['category']] = cats.get(t['category'], 0) + 1
        print("\nCategories:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
