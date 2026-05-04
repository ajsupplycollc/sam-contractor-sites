"""
Find South Florida contractor IG targets via Chrome Debug Protocol.
Phase 1: Google searches to collect IG handles (stays on Google)
Phase 2: Check each IG profile for website/bio (stays on IG)
Requires: Chrome debug open (--remote-debugging-port=9222)
"""
import json, time, re, sys, asyncio, urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

SEARCH_QUERIES = [
    "miami plumber instagram",
    "miami electrician instagram",
    "south florida painter contractor instagram",
    "miami dade handyman instagram",
    "broward contractor instagram",
    "miami landscaper instagram",
    "south florida pool service instagram",
    "miami roofing contractor instagram",
    "miami pressure washing instagram",
    "south florida fence installer instagram",
    "miami flooring contractor instagram",
    "south florida HVAC instagram",
    "miami drywall contractor instagram",
    "south florida concrete contractor instagram",
    "miami garage door installer instagram",
    "south florida gutter cleaning instagram",
    "miami window cleaning instagram",
    "south florida cabinet installer instagram",
    "miami bathroom remodel contractor instagram",
    "south florida paver installer instagram",
    "miami appliance repair instagram",
    "south florida deck builder instagram",
    "miami kitchen remodel contractor instagram",
    "south florida stucco contractor instagram",
    "miami carpet cleaning instagram",
    "south florida mold removal instagram",
    "miami locksmith instagram",
    "south florida screen enclosure instagram",
    "miami epoxy flooring instagram",
    "south florida tree trimming instagram",
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

SKIP_HANDLES = {
    'p', 'explore', 'reel', 'reels', 'stories', 'accounts', 'about',
    'developer', 'direct', 'instagram', 'strangeadvancedmarketing',
}


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'instagram.com' in url or 'google.com' in url:
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


def guess_location(bio: str) -> str:
    bio_lower = bio.lower()
    if "broward" in bio_lower: return "Broward County, FL"
    if "palm beach" in bio_lower: return "Palm Beach, FL"
    if "fort lauderdale" in bio_lower or "ft lauderdale" in bio_lower: return "Fort Lauderdale, FL"
    if "hialeah" in bio_lower: return "Hialeah, FL"
    if "homestead" in bio_lower: return "Homestead, FL"
    if "doral" in bio_lower: return "Doral, FL"
    return "Miami, FL"


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def navigate_and_wait(ws, url: str, msg_id: int, wait: float = 4.0) -> int:
    """Navigate and wait, draining messages."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": url}
    }))
    msg_id += 1
    await asyncio.sleep(wait)
    await drain(ws)
    return msg_id


async def evaluate_js(ws, js: str, msg_id: int, timeout: float = 8.0) -> tuple[str, int]:
    """Evaluate JS and return value string."""
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


async def search_google_for_ig(ws, query: str, msg_id: int) -> tuple[list[str], int]:
    """Search Google and extract instagram.com handles from results."""
    import urllib.parse
    url = f'https://www.google.com/search?q={urllib.parse.quote_plus(query + " site:instagram.com")}&num=20'

    msg_id = await navigate_and_wait(ws, url, msg_id, wait=4.0)

    js = """
    (function() {
        const handles = [];
        const links = document.querySelectorAll('a[href*="instagram.com"]');
        for (const link of links) {
            const href = link.href;
            const match = href.match(/instagram\\.com\\/([a-zA-Z0-9_.]+)/);
            if (match && match[1]) {
                const h = match[1].toLowerCase();
                if (!['p','explore','reel','reels','stories','accounts','about','developer','direct','instagram'].includes(h)) {
                    if (!handles.includes(h)) handles.push(h);
                }
            }
        }
        // Also check cite elements (Bing/Google show URLs there)
        const cites = document.querySelectorAll('cite');
        for (const cite of cites) {
            const text = cite.textContent || '';
            const match = text.match(/instagram\\.com\\/([a-zA-Z0-9_.]+)/);
            if (match && match[1]) {
                const h = match[1].toLowerCase();
                if (!handles.includes(h)) handles.push(h);
            }
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
    """Visit an IG profile and check if they have a website."""
    msg_id = await navigate_and_wait(ws, f"https://www.instagram.com/{handle}/", msg_id, wait=3.0)

    js = """
    (function() {
        const result = {has_website: false, name: '', bio: '', not_found: false};
        const pageText = document.body?.innerText || '';

        if (pageText.includes("Sorry, this page") || pageText.includes("isn't available")) {
            result.not_found = true;
            return JSON.stringify(result);
        }

        // External link = has website
        const extLinks = document.querySelectorAll('a[href*="l.instagram.com"]');
        if (extLinks.length > 0) result.has_website = true;

        // Check for link aggregators
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

        // Get bio/name from header
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
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    # Load existing targets
    existing_igs = set()
    for fname in ['master_targets.json', 'new_targets_batch2.json', 'network_targets.json']:
        p = f'{BASE_DIR}/{fname}'
        if __import__('os').path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for t in json.load(f):
                    if t.get('ig'):
                        existing_igs.add(t['ig'].lower())

    print(f"Finding {target_count} new IG targets...")
    print(f"Existing to skip: {len(existing_igs)}\n")

    ws_url = get_ws_url()
    msg_id = 1
    all_handles = {}  # handle -> source query

    # ========== PHASE 1: Google searches (stay on Google) ==========
    print("=" * 50)
    print("PHASE 1: Collecting handles from Google")
    print("=" * 50)

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for qi, query in enumerate(SEARCH_QUERIES):
            print(f"[{qi+1}/{len(SEARCH_QUERIES)}] {query}...", end=' ', flush=True)

            try:
                handles, msg_id = await search_google_for_ig(ws, query, msg_id)
                new_handles = [h for h in handles
                              if h.lower() not in existing_igs
                              and h.lower() not in SKIP_HANDLES
                              and h.lower() not in all_handles]
                for h in new_handles:
                    all_handles[h.lower()] = query
                print(f"{len(handles)} found, {len(new_handles)} new (total: {len(all_handles)})", flush=True)
            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            await asyncio.sleep(3)

    print(f"\nPhase 1 complete: {len(all_handles)} unique handles to check\n")

    if not all_handles:
        print("No handles found. Make sure Chrome debug is on Google.")
        return

    # ========== PHASE 2: Check IG profiles (stay on IG) ==========
    print("=" * 50)
    print("PHASE 2: Checking IG profiles")
    print("=" * 50)

    # Reconnect (may need to pick up a different/same tab)
    await asyncio.sleep(2)
    ws_url = get_ws_url()
    new_targets = []

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i, (handle, source_query) in enumerate(all_handles.items()):
            if len(new_targets) >= target_count:
                break

            try:
                profile, msg_id = await check_ig_profile(ws, handle, msg_id)
            except Exception as e:
                print(f"  [{i+1}] @{handle}: connection error, reconnecting...", flush=True)
                await asyncio.sleep(2)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                    profile, msg_id = await check_ig_profile(ws, handle, msg_id)
                except Exception:
                    print(f"  [{i+1}] @{handle}: SKIP", flush=True)
                    continue

            if not profile or profile.get('not_found'):
                continue

            if profile.get('has_website'):
                print(f"  [{i+1}] @{handle}: HAS WEBSITE - skip", flush=True)
                continue

            bio = profile.get('bio', '')
            name = profile.get('name', '') or handle
            category = guess_category(source_query, bio)
            location = guess_location(bio)

            target = {
                "name": name,
                "ig": handle,
                "phone": "",
                "category": category,
                "location": location,
                "rating": 0,
                "reviews": 0,
                "has_site": False,
                "notes": f"Found via: {source_query[:30]}"
            }
            new_targets.append(target)
            print(f"  [{i+1}] @{handle}: NO WEBSITE - TARGET [{len(new_targets)}/{target_count}]", flush=True)

            await asyncio.sleep(2)

    # Save
    output_path = f'{BASE_DIR}/new_targets_batch2.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_targets, f, indent=2, ensure_ascii=False)

    print(f"\n\nDone! Found {len(new_targets)} new targets without websites.")
    print(f"Saved to: {output_path}")

    if new_targets:
        cats = {}
        for t in new_targets:
            cats[t['category']] = cats.get(t['category'], 0) + 1
        print("\nCategories:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")


if __name__ == '__main__':
    asyncio.run(main())
