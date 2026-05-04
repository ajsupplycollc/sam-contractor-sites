"""
Find Florida contractor IG targets via Chrome Debug Protocol — SCALED version.
Covers ALL major Florida metros, 30+ categories, generates 200+ targets.
Phase 1: Google searches to collect IG handles (stays on Google)
Phase 2: Check each IG profile for website/bio (stays on IG)
Requires: Chrome debug open (--remote-debugging-port=9222)
"""
import json, time, re, sys, asyncio, urllib.request, os, random

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

CITIES = [
    # South Florida
    "Miami", "Fort Lauderdale", "Hialeah", "Hollywood", "Pembroke Pines",
    "Miramar", "Coral Springs", "Pompano Beach", "West Palm Beach", "Boca Raton",
    "Deerfield Beach", "Homestead", "Davie", "Plantation", "Sunrise", "Doral",
    "Boynton Beach", "Delray Beach", "Jupiter", "Palm Beach Gardens",
    # Central Florida
    "Orlando", "Tampa", "St Petersburg", "Kissimmee", "Lakeland",
    "Clearwater", "Brandon", "Palm Bay", "Melbourne", "Daytona Beach",
    "Deltona", "Sanford", "Ocala", "Gainesville", "Winter Park",
    "Altamonte Springs", "Clermont", "Apopka",
    # North Florida
    "Jacksonville", "Tallahassee", "Pensacola", "Panama City",
    "St Augustine", "Fernandina Beach", "Orange Park",
    # Southwest Florida
    "Naples", "Fort Myers", "Cape Coral", "Sarasota", "Bradenton",
    "Bonita Springs", "Lehigh Acres", "Port Charlotte",
    # Treasure Coast / Space Coast
    "Port St Lucie", "Stuart", "Vero Beach", "Titusville", "Cocoa Beach",
]

CATEGORIES = [
    "plumber", "electrician", "painter contractor", "handyman",
    "landscaper", "pool service", "roofing contractor", "pressure washing",
    "fence installer", "flooring contractor", "HVAC", "drywall contractor",
    "concrete contractor", "garage door installer", "gutter cleaning",
    "window cleaning", "cabinet installer", "bathroom remodel",
    "paver installer", "appliance repair", "deck builder",
    "kitchen remodel", "stucco contractor", "carpet cleaning",
    "mold removal", "locksmith", "screen enclosure",
    "epoxy flooring", "tree trimming", "lawn care",
    "moving service", "junk removal", "tile contractor",
]

CATEGORY_MAP = {
    "plumb": "Plumbing", "electric": "Electrical", "paint": "Painting",
    "handyman": "Handyman", "landscap": "Landscaping", "pool": "Pool Service",
    "roof": "Roofing", "pressure": "Pressure Washing", "fence": "Fence Contractor",
    "floor": "Flooring", "hvac": "HVAC", "drywall": "Drywall",
    "concrete": "Concrete Contractor", "garage": "Garage Door",
    "gutter": "Gutter Cleaning", "window": "Window Cleaning",
    "cabinet": "Cabinetry", "bathroom": "Bathroom Remodel",
    "paver": "Paver Installation", "appliance": "Appliance Repair",
    "deck": "Deck Building", "kitchen": "Kitchen Remodel",
    "stucco": "Stucco Contractor", "carpet": "Carpet Cleaning",
    "mold": "Mold Removal", "locksmith": "Locksmith",
    "screen": "Screen Enclosure", "epoxy": "Epoxy Flooring",
    "tree": "Tree Service", "lawn": "Lawn Care",
    "mov": "Moving Service", "junk": "Junk Removal", "tile": "Tile Contractor",
}

LOCATION_KEYWORDS = {
    "miami": "Miami, FL", "fort lauderdale": "Fort Lauderdale, FL",
    "hialeah": "Hialeah, FL", "hollywood": "Hollywood, FL",
    "pembroke": "Pembroke Pines, FL", "miramar": "Miramar, FL",
    "coral springs": "Coral Springs, FL", "pompano": "Pompano Beach, FL",
    "west palm": "West Palm Beach, FL", "boca": "Boca Raton, FL",
    "homestead": "Homestead, FL", "doral": "Doral, FL",
    "orlando": "Orlando, FL", "tampa": "Tampa, FL",
    "st pete": "St Petersburg, FL", "kissimmee": "Kissimmee, FL",
    "lakeland": "Lakeland, FL", "clearwater": "Clearwater, FL",
    "daytona": "Daytona Beach, FL", "jacksonville": "Jacksonville, FL",
    "tallahassee": "Tallahassee, FL", "pensacola": "Pensacola, FL",
    "naples": "Naples, FL", "fort myers": "Fort Myers, FL",
    "cape coral": "Cape Coral, FL", "sarasota": "Sarasota, FL",
    "bradenton": "Bradenton, FL", "port st lucie": "Port St Lucie, FL",
    "gainesville": "Gainesville, FL", "ocala": "Ocala, FL",
    "melbourne": "Melbourne, FL", "palm bay": "Palm Bay, FL",
    "broward": "Broward County, FL", "palm beach": "Palm Beach County, FL",
}

SKIP_HANDLES = {
    'p', 'explore', 'reel', 'reels', 'stories', 'accounts', 'about',
    'developer', 'direct', 'instagram', 'strangeadvancedmarketing',
}


def build_search_queries(max_queries: int = 0) -> list[str]:
    queries = []
    for cat in CATEGORIES:
        for city in CITIES:
            queries.append(f"{city} {cat} instagram")
    random.shuffle(queries)
    if max_queries > 0:
        queries = queries[:max_queries]
    return queries


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'instagram.com' in url or 'google.com' in url or 'bing.com' in url or 'duckduckgo.com' in url:
                if 'omnibox' not in url:
                    return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if not url.startswith('chrome://') or url == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    raise Exception("No available Chrome tab found")


def guess_category(query: str, bio: str = '') -> str:
    text = (query + " " + bio).lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in text:
            return cat
    return "General Contractor"


def guess_location(query: str, bio: str = '') -> str:
    text = (query + " " + bio).lower()
    for keyword, location in LOCATION_KEYWORDS.items():
        if keyword in text:
            return location
    return "Florida"


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def navigate_and_wait(ws, url: str, msg_id: int, wait: float = 4.0) -> int:
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": url}
    }))
    msg_id += 1
    await asyncio.sleep(wait)
    await drain(ws)
    return msg_id


async def evaluate_js(ws, js: str, msg_id: int, timeout: float = 8.0) -> tuple[str, int]:
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                return val, msg_id
        except (asyncio.TimeoutError, Exception):
            break

    await drain(ws)
    return '', msg_id


async def search_for_ig(ws, query: str, msg_id: int) -> tuple[list[str], int]:
    import urllib.parse
    url = f'https://duckduckgo.com/?q={urllib.parse.quote_plus(query + " instagram.com")}&ia=web'

    msg_id = await navigate_and_wait(ws, url, msg_id, wait=4.0)

    js = """
    (function() {
        var handles = [];
        var skip = ['p','explore','reel','reels','stories','accounts','about','developer','direct','instagram','tv','tags','popular','_n','_u','legal','privacy','help','press'];
        var all = document.body.innerHTML;
        var re = /instagram\\.com\\/([a-zA-Z0-9_.]+)/g;
        var m;
        while ((m = re.exec(all)) !== null) {
            var h = m[1].toLowerCase();
            if (skip.indexOf(h) === -1 && handles.indexOf(h) === -1 && h.length > 2) handles.push(h);
        }
        return JSON.stringify(handles);
    })()
    """
    val, msg_id = await evaluate_js(ws, js, msg_id)
    await drain(ws)

    if val and val.startswith('['):
        return json.loads(val), msg_id
    return [], msg_id


async def check_ig_profile(ws, handle: str, msg_id: int) -> tuple[dict | None, int]:
    msg_id = await navigate_and_wait(ws, f"https://www.instagram.com/{handle}/", msg_id, wait=3.0)

    js = """
    (function() {
        const result = {has_website: false, name: '', bio: '', not_found: false};
        const pageText = document.body?.innerText || '';

        if (pageText.includes("Sorry, this page") || pageText.includes("isn't available")) {
            result.not_found = true;
            return JSON.stringify(result);
        }

        const extLinks = document.querySelectorAll('a[href*="l.instagram.com"]');
        if (extLinks.length > 0) result.has_website = true;

        const allLinks = document.querySelectorAll('a');
        for (const a of allLinks) {
            const href = (a.href || '').toLowerCase();
            if (href.includes('linktr.ee') || href.includes('linkin.bio') ||
                href.includes('linkpop') || href.includes('taplink') ||
                href.includes('beacons.ai') || href.includes('stan.store') ||
                href.includes('hoo.be') || href.includes('bio.link')) {
                result.has_website = true;
            }
        }

        const header = document.querySelector('header');
        if (header) {
            result.bio = header.innerText || '';
            const h2 = header.querySelector('h2');
            if (h2) result.name = h2.textContent.trim();
        }

        return JSON.stringify(result);
    })()
    """
    val, msg_id = await evaluate_js(ws, js, msg_id)
    await drain(ws)

    if val and val.startswith('{'):
        return json.loads(val), msg_id
    return None, msg_id


async def main():
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    max_queries = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    output_file = sys.argv[3] if len(sys.argv) > 3 else f'{BASE_DIR}/scaled_targets.json'

    # Load ALL existing targets to deduplicate
    existing_igs = set()
    for fname in os.listdir(BASE_DIR):
        if fname.endswith('.json') and 'target' in fname.lower():
            p = os.path.join(BASE_DIR, fname)
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for t in data:
                            if isinstance(t, dict) and t.get('ig'):
                                existing_igs.add(t['ig'].lower())
            except Exception:
                pass

    queries = build_search_queries(max_queries)

    log_path = f'{BASE_DIR}/discovery_log.txt'
    def log(msg):
        with open(log_path, 'a', encoding='utf-8') as lf:
            lf.write(msg + '\n')
        print(msg, flush=True)

    log(f"=== SCALED DISCOVERY: All of Florida ===")
    log(f"Target count: {target_count}")
    log(f"Search queries: {len(queries)} (from {len(CITIES)} cities x {len(CATEGORIES)} categories)")
    log(f"Existing handles to skip: {len(existing_igs)}")

    ws_url = get_ws_url()
    msg_id = 1
    all_handles = {}

    # Resume from checkpoint if exists
    checkpoint_path = f'{BASE_DIR}/scaled_raw_handles.json'
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            all_handles = json.load(f)
        log(f"Resumed from checkpoint: {len(all_handles)} handles already collected")

    log("=" * 60)
    log("PHASE 1: Collecting handles from DuckDuckGo")
    log("=" * 60)

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for qi, query in enumerate(queries):
            if len(all_handles) >= target_count * 3:
                log(f"\n  Reached {len(all_handles)} handles (3x target), stopping search early.")
                break

            try:
                handles, msg_id = await search_for_ig(ws, query, msg_id)
                new_handles = [h for h in handles
                              if h.lower() not in existing_igs
                              and h.lower() not in SKIP_HANDLES
                              and h.lower() not in all_handles]
                for h in new_handles:
                    all_handles[h.lower()] = query
                log(f"[{qi+1}/{len(queries)}] {query}... {len(handles)} found, {len(new_handles)} new (total: {len(all_handles)})")
            except Exception as e:
                log(f"[{qi+1}/{len(queries)}] {query}... ERROR: {e}")
                try:
                    await asyncio.sleep(3)
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception as e2:
                    log(f"  Reconnect failed: {e2}")

            # Save checkpoint every 10 queries
            if (qi + 1) % 10 == 0:
                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(all_handles, f, indent=2)

            await asyncio.sleep(random.uniform(2.5, 4.5))

    log(f"\nPhase 1 complete: {len(all_handles)} unique handles to check")

    if not all_handles:
        log("No handles found. Make sure Chrome debug port is open.")
        return

    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(all_handles, f, indent=2)
    log(f"Checkpoint saved: {checkpoint_path}")

    # ========== PHASE 2: Check IG profiles ==========
    log("\n" + "=" * 60)
    log("PHASE 2: Checking IG profiles for websites")
    log("=" * 60)

    await asyncio.sleep(2)
    ws_url = get_ws_url()
    new_targets = []

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        handles_list = list(all_handles.items())
        for i, (handle, source_query) in enumerate(handles_list):
            if len(new_targets) >= target_count:
                break

            try:
                profile, msg_id = await check_ig_profile(ws, handle, msg_id)
            except Exception as e:
                log(f"  [{i+1}] @{handle}: connection error, reconnecting...")
                await asyncio.sleep(3)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                    profile, msg_id = await check_ig_profile(ws, handle, msg_id)
                except Exception:
                    log(f"  [{i+1}] @{handle}: SKIP")
                    continue

            if not profile or profile.get('not_found'):
                continue

            if profile.get('has_website'):
                log(f"  [{i+1}] @{handle}: HAS WEBSITE - skip")
                continue

            bio = profile.get('bio', '')
            name = profile.get('name', '') or handle
            category = guess_category(source_query, bio)
            location = guess_location(source_query, bio)

            target = {
                "name": name,
                "ig": handle,
                "phone": "",
                "category": category,
                "location": location,
                "rating": 0,
                "reviews": 0,
                "has_site": False,
                "notes": f"Found via: {source_query[:40]}"
            }
            new_targets.append(target)
            log(f"  [{i+1}] @{handle}: NO WEBSITE - TARGET [{len(new_targets)}/{target_count}] ({category}, {location})")

            # Save progress every 10 targets
            if len(new_targets) % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(new_targets, f, indent=2, ensure_ascii=False)
                log(f"  >> Progress saved: {len(new_targets)} targets")

            await asyncio.sleep(random.uniform(1.5, 3.0))

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_targets, f, indent=2, ensure_ascii=False)

    log(f"\n{'=' * 60}")
    log(f"Done! Found {len(new_targets)} new targets without websites.")
    log(f"Saved to: {output_file}")

    if new_targets:
        cats = {}
        locs = {}
        for t in new_targets:
            cats[t['category']] = cats.get(t['category'], 0) + 1
            locs[t['location']] = locs.get(t['location'], 0) + 1
        log("\nBy Category:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            log(f"  {cat}: {count}")
        log("\nBy Location:")
        for loc, count in sorted(locs.items(), key=lambda x: -x[1])[:15]:
            log(f"  {loc}: {count}")


if __name__ == '__main__':
    asyncio.run(main())
