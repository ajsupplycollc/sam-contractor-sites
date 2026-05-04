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
    "miami plumber instagram no website",
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
    "plumb": "Plumbing",
    "electric": "Electrical",
    "paint": "Painting",
    "handyman": "Handyman",
    "landscap": "Landscaping",
    "pool": "Pool Service",
    "roof": "Roofing",
    "pressure": "Pressure Washing",
    "fence": "Fence Contractor",
    "floor": "Flooring",
    "hvac": "HVAC",
    "drywall": "Drywall",
    "concrete": "Concrete Contractor",
    "garage": "Garage Door",
    "gutter": "Gutter Cleaning",
    "window": "Window Cleaning",
    "cabinet": "Cabinetry",
    "bathroom": "Bathroom Remodel",
    "paver": "Paver Installation",
    "appliance": "Appliance Repair",
    "deck": "Deck Building",
    "kitchen": "Kitchen Remodel",
    "stucco": "Stucco Contractor",
    "carpet": "Carpet Cleaning",
    "mold": "Mold Removal",
    "locksmith": "Locksmith",
    "screen": "Screen Enclosure",
    "epoxy": "Epoxy Flooring",
    "tree": "Tree Service",
    "lawn": "Lawn Care",
    "mov": "Moving Service",
    "junk": "Junk Removal",
    "tile": "Tile Contractor",
}


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            return tab['webSocketDebuggerUrl']
    raise Exception("No available Chrome tab found")


def guess_category(query: str, bio: str) -> str:
    text = (query + " " + bio).lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in text:
            return cat
    return "General Contractor"


def guess_location(bio: str) -> str:
    bio_lower = bio.lower()
    if "broward" in bio_lower:
        return "Broward County, FL"
    if "palm beach" in bio_lower:
        return "Palm Beach, FL"
    if "fort lauderdale" in bio_lower or "ft lauderdale" in bio_lower:
        return "Fort Lauderdale, FL"
    if "hialeah" in bio_lower:
        return "Hialeah, FL"
    if "homestead" in bio_lower:
        return "Homestead, FL"
    if "doral" in bio_lower:
        return "Doral, FL"
    return "Miami, FL"


async def search_google_for_ig(ws, query: str, msg_id: int) -> tuple[list[str], int]:
    """Search Google and extract instagram.com URLs from results."""
    import urllib.parse
    url = f'https://www.google.com/search?q={urllib.parse.quote_plus(query + " site:instagram.com")}&num=20'

    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": url}
    }))
    msg_id += 1
    await asyncio.sleep(4)

    # Get page HTML for links
    js = """
    (function() {
        const links = document.querySelectorAll('a[href*="instagram.com"]');
        const handles = [];
        for (const link of links) {
            const href = link.href;
            const match = href.match(/instagram\\.com\\/([a-zA-Z0-9_.]+)/);
            if (match && match[1] && !['p','explore','reel','stories','accounts','about','developer'].includes(match[1])) {
                handles.push(match[1].toLowerCase());
            }
        }
        return JSON.stringify([...new Set(handles)]);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    handles = []
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and val.startswith('['):
                    handles = json.loads(val)
                    break
        except (asyncio.TimeoutError, Exception):
            break

    # Drain
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass

    return handles, msg_id


async def check_ig_profile(ws, handle: str, msg_id: int) -> tuple[dict | None, int]:
    """Visit an IG profile and check if they have a website. Extract bio info."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/{handle}/"}
    }))
    msg_id += 1
    await asyncio.sleep(3)

    js = """
    (function() {
        const result = {has_website: false, name: '', bio: '', followers: 0, is_business: false};

        // Check for external link (website)
        const extLinks = document.querySelectorAll('a[href*="l.instagram.com"]');
        if (extLinks.length > 0) {
            result.has_website = true;
        }
        // Also check for linktr.ee or linkinbio type links
        const allLinks = document.querySelectorAll('a');
        for (const a of allLinks) {
            const href = (a.href || '').toLowerCase();
            if (href.includes('linktr.ee') || href.includes('linkin.bio') || href.includes('linkpop') || href.includes('taplink')) {
                result.has_website = true;
            }
        }

        // Get name from header
        const header = document.querySelector('header');
        if (header) {
            const nameEl = header.querySelector('span[class*="x1lliihq"]') || header.querySelector('h2');
            if (nameEl) result.name = nameEl.textContent.trim();
        }

        // Get full page text for bio
        const mainContent = document.querySelector('header');
        if (mainContent) {
            result.bio = mainContent.innerText || '';
        }

        // Check for business category indicator
        const categoryEl = document.querySelector('[class*="x1lliihq"][class*="x193iq5w"]');
        if (categoryEl && categoryEl.textContent.match(/(contractor|service|business|company|cleaning|repair|install)/i)) {
            result.is_business = true;
        }

        // Check follower count
        const stats = document.querySelectorAll('header li span, header ul li span');
        for (const s of stats) {
            const txt = s.getAttribute('title') || s.textContent || '';
            const num = txt.replace(/,/g, '');
            if (!isNaN(num) && parseInt(num) > 0) {
                result.followers = parseInt(num);
                break;
            }
        }

        // Check if page is available
        const pageText = document.body.innerText || '';
        if (pageText.includes("Sorry, this page") || pageText.includes("isn't available")) {
            result.not_found = true;
        }

        return JSON.stringify(result);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    profile_data = None
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and val.startswith('{'):
                    profile_data = json.loads(val)
                    break
        except (asyncio.TimeoutError, Exception):
            break

    # Drain
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass

    return profile_data, msg_id


async def main():
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    # Load existing targets to avoid duplicates
    with open(f'{BASE_DIR}/master_targets.json', 'r', encoding='utf-8') as f:
        existing = json.load(f)
    existing_igs = {t.get('ig', '').lower() for t in existing if t.get('ig')}

    print(f"Finding {target_count} new IG targets (have {len(existing_igs)} existing)...\n")

    ws_url = get_ws_url()
    msg_id = 1
    new_targets = []
    checked = set()

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)

        for qi, query in enumerate(SEARCH_QUERIES):
            if len(new_targets) >= target_count:
                break

            print(f"\n[Search {qi+1}/{len(SEARCH_QUERIES)}] {query}", flush=True)

            try:
                handles, msg_id = await search_google_for_ig(ws, query, msg_id)
                print(f"  Found {len(handles)} handles: {handles[:5]}...", flush=True)

                for handle in handles:
                    if len(new_targets) >= target_count:
                        break
                    if handle in existing_igs or handle in checked:
                        continue
                    checked.add(handle)

                    # Check the profile
                    await asyncio.sleep(2)
                    profile, msg_id = await check_ig_profile(ws, handle, msg_id)

                    if not profile:
                        print(f"    @{handle}: couldn't load", flush=True)
                        continue
                    if profile.get('not_found'):
                        print(f"    @{handle}: page not found", flush=True)
                        continue
                    if profile.get('has_website'):
                        print(f"    @{handle}: HAS WEBSITE - skip", flush=True)
                        continue

                    # Good target - no website!
                    bio = profile.get('bio', '')
                    name = profile.get('name', '') or handle
                    category = guess_category(query, bio)
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
                        "notes": f"Found via IG search: {query[:30]}"
                    }
                    new_targets.append(target)
                    print(f"    @{handle}: NO WEBSITE - ADDED ({category}) [{len(new_targets)}/{target_count}]", flush=True)

            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            await asyncio.sleep(3)

    # Save new targets
    output_path = f'{BASE_DIR}/new_targets_batch2.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_targets, f, indent=2, ensure_ascii=False)

    print(f"\n\nDone! Found {len(new_targets)} new targets without websites.")
    print(f"Saved to: {output_path}")
    print(f"Categories: {dict((t['category'], sum(1 for x in new_targets if x['category']==t['category'])) for t in new_targets)}")


if __name__ == '__main__':
    asyncio.run(main())
