import json, time, re, sys, asyncio, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

CONTRACTOR_KEYWORDS = [
    'contractor', 'contracting', 'construction', 'remodel', 'renovation',
    'handyman', 'plumb', 'electric', 'hvac', 'a/c', 'air condition',
    'roof', 'paint', 'pressure wash', 'pressure clean', 'power wash',
    'landscap', 'lawn', 'tree service', 'tree trim', 'arborist',
    'fence', 'fencing', 'pool', 'tile', 'floor', 'carpet', 'clean',
    'junk removal', 'haul', 'moving', 'mover', 'concrete', 'paver',
    'stucco', 'plaster', 'drywall', 'garage door', 'gutter',
    'sprinkler', 'irrigation', 'window tint', 'screen enclosure',
    'epoxy', 'cabinet', 'kitchen', 'bathroom', 'deck', 'locksmith',
    'mold', 'water damage', 'restoration', 'repair', 'install',
    'maintenance', 'property', 'turf', 'sod', 'car wash', 'detail',
    'welding', 'welder', 'mason', 'masonry', 'demolition', 'demo',
    'insulation', 'solar', 'glass', 'mirror', 'shutters', 'blinds',
    'pest control', 'exterminator', 'general contractor', 'gc',
    'home improvement', 'remodeling', 'build', 'builder',
    'licensed', 'insured', 'free estimate', 'commercial', 'residential',
    'llc', 'inc', 'corp', 'services', 'solutions', 'pros',
]

CATEGORY_MAP = {
    'plumb': 'Plumbing', 'electric': 'Electrical', 'paint': 'Painting',
    'handyman': 'Handyman', 'landscap': 'Landscaping', 'lawn': 'Lawn Care',
    'pool': 'Pool Service', 'roof': 'Roofing', 'pressure': 'Pressure Washing',
    'fence': 'Fence Contractor', 'fencing': 'Fence Contractor',
    'floor': 'Flooring', 'hvac': 'HVAC', 'a/c': 'HVAC',
    'air condition': 'HVAC', 'drywall': 'Drywall',
    'concrete': 'Concrete Contractor', 'paver': 'Paver Installation',
    'garage door': 'Garage Door', 'gutter': 'Gutter Cleaning',
    'cabinet': 'Cabinetry', 'bathroom': 'Bathroom Remodel',
    'deck': 'Deck Building', 'kitchen': 'Kitchen Remodel',
    'stucco': 'Stucco Contractor', 'plaster': 'Plastering',
    'carpet': 'Carpet Cleaning', 'mold': 'Mold Removal',
    'locksmith': 'Locksmith', 'screen': 'Screen Enclosure',
    'epoxy': 'Epoxy Flooring', 'tree': 'Tree Service',
    'junk': 'Junk Removal', 'haul': 'Junk Removal',
    'moving': 'Moving Service', 'mover': 'Moving Service',
    'tile': 'Tile Contractor', 'sprinkler': 'Sprinkler/Irrigation',
    'irrigation': 'Irrigation', 'car wash': 'Mobile Car Wash',
    'detail': 'Auto Detailing', 'window tint': 'Window Tinting',
    'water damage': 'Water Damage Restoration', 'restoration': 'Water Damage Restoration',
    'solar': 'Solar', 'pest': 'Pest Control', 'welding': 'Welding',
    'welder': 'Welding', 'mason': 'Masonry', 'demolition': 'Demolition',
    'insulation': 'Insulation', 'turf': 'Artificial Turf', 'sod': 'Lawn Care',
    'glass': 'Glass & Mirror', 'shutter': 'Shutters & Blinds',
    'build': 'Construction', 'remodel': 'General Contractor',
    'renovation': 'General Contractor', 'construct': 'Construction',
    'repair': 'Handyman', 'maintenance': 'Property Maintenance',
}

SOUTH_FL_INDICATORS = [
    'miami', 'dade', 'broward', 'palm beach', 'fort lauderdale',
    'ft lauderdale', 'hialeah', 'homestead', 'doral', 'kendall',
    'coral gables', 'boca raton', 'pompano', 'hollywood', 'davie',
    'pembroke', 'plantation', 'sunrise', 'weston', 'miramar',
    'south florida', 'so fla', 'soflo', 'sfla', '305', '786', '954',
    '561', 'fl', 'florida',
]


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'instagram.com' in url and 'omnibox' not in url:
                return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            if not tab.get('url', '').startswith('chrome://'):
                return tab['webSocketDebuggerUrl']
    raise Exception("No Chrome tab found")


def guess_category(bio: str) -> str:
    bio_lower = bio.lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in bio_lower:
            return cat
    return "General Contractor"


def guess_location(bio: str) -> str:
    bio_lower = bio.lower()
    locations = {
        'broward': 'Broward County, FL', 'palm beach': 'Palm Beach, FL',
        'fort lauderdale': 'Fort Lauderdale, FL', 'ft lauderdale': 'Fort Lauderdale, FL',
        'hialeah': 'Hialeah, FL', 'homestead': 'Homestead, FL',
        'doral': 'Doral, FL', 'kendall': 'Kendall, FL',
        'coral gables': 'Coral Gables, FL', 'boca raton': 'Boca Raton, FL',
        'pompano': 'Pompano Beach, FL', 'hollywood': 'Hollywood, FL',
        'pembroke': 'Pembroke Pines, FL', 'plantation': 'Plantation, FL',
        'weston': 'Weston, FL', 'miramar': 'Miramar, FL',
    }
    for key, loc in locations.items():
        if key in bio_lower:
            return loc
    return "Miami, FL"


def is_contractor(bio: str) -> bool:
    bio_lower = bio.lower()
    matches = sum(1 for kw in CONTRACTOR_KEYWORDS if kw in bio_lower)
    return matches >= 2


def is_south_florida(bio: str) -> bool:
    bio_lower = bio.lower()
    return any(ind in bio_lower for ind in SOUTH_FL_INDICATORS)


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def get_follow_list(ws, list_type: str, msg_id: int) -> tuple[list[str], int]:
    """Open following/followers dialog and scroll to extract handles."""
    # Click the following/followers link
    click_js = f"""
    (function() {{
        const links = document.querySelectorAll('a[href*="/{list_type}/"]');
        for (const a of links) {{
            a.click();
            return 'clicked';
        }}
        // Try the header stats
        const headers = document.querySelectorAll('header a, header li');
        for (const el of headers) {{
            if (el.textContent.toLowerCase().includes('{list_type.replace("_", " ")}')) {{
                el.click();
                return 'clicked_text';
            }}
        }}
        return 'not_found';
    }})()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": click_js}
    }))
    msg_id += 1
    await asyncio.sleep(3)
    await drain(ws)

    all_handles = set()
    scroll_attempts = 0
    max_scrolls = 40

    while scroll_attempts < max_scrolls:
        # Extract handles from the dialog
        extract_js = """
        (function() {
            const handles = [];
            // Look for the dialog/modal with the list
            const dialog = document.querySelector('div[role="dialog"]');
            const container = dialog || document;
            const links = container.querySelectorAll('a[href^="/"]');
            for (const a of links) {
                const href = a.getAttribute('href');
                if (href && href.match(/^\\/[a-zA-Z0-9_.]+\\/$/) && !href.includes('/explore/') && !href.includes('/p/')) {
                    const handle = href.replace(/\\//g, '');
                    if (handle && handle.length > 1 && !['explore','reels','stories','direct'].includes(handle)) {
                        handles.push(handle);
                    }
                }
            }
            return JSON.stringify([...new Set(handles)]);
        })()
        """
        await ws.send(json.dumps({
            "id": msg_id, "method": "Runtime.evaluate",
            "params": {"expression": extract_js}
        }))
        msg_id += 1

        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(resp)
                if 'result' in data and 'result' in data.get('result', {}):
                    val = data['result']['result'].get('value', '')
                    if val and val.startswith('['):
                        batch = json.loads(val)
                        prev_count = len(all_handles)
                        all_handles.update(batch)
                        new_count = len(all_handles) - prev_count
                        if new_count == 0:
                            scroll_attempts += 5
                        break
            except (asyncio.TimeoutError, Exception):
                break

        # Scroll down in the dialog
        scroll_js = """
        (function() {
            const dialog = document.querySelector('div[role="dialog"]');
            if (dialog) {
                const scrollable = dialog.querySelector('div[style*="overflow"]') ||
                                   dialog.querySelector('ul')?.parentElement ||
                                   dialog.querySelector('div > div > div');
                if (scrollable) {
                    scrollable.scrollTop = scrollable.scrollTop + 800;
                    return 'scrolled_dialog';
                }
            }
            // Try scrolling any scrollable div in dialog
            const dialogs = document.querySelectorAll('div[role="dialog"] div');
            for (const d of dialogs) {
                if (d.scrollHeight > d.clientHeight + 50) {
                    d.scrollTop = d.scrollTop + 800;
                    return 'scrolled_inner';
                }
            }
            return 'no_scroll';
        })()
        """
        await ws.send(json.dumps({
            "id": msg_id, "method": "Runtime.evaluate",
            "params": {"expression": scroll_js}
        }))
        msg_id += 1
        await asyncio.sleep(1.5)
        await drain(ws)

        scroll_attempts += 1
        if scroll_attempts % 10 == 0:
            print(f"      ... {len(all_handles)} handles so far (scroll {scroll_attempts})", flush=True)

    # Close dialog
    close_js = """
    (function() {
        const close = document.querySelector('div[role="dialog"] button svg[aria-label="Close"]') ||
                       document.querySelector('div[role="dialog"] [aria-label="Close"]');
        if (close) { close.closest('button')?.click() || close.click(); return 'closed'; }
        // Press Escape
        document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', code: 'Escape', bubbles: true}));
        return 'escaped';
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": close_js}
    }))
    msg_id += 1
    await asyncio.sleep(1)
    await drain(ws)

    return list(all_handles), msg_id


async def check_profile(ws, handle: str, msg_id: int) -> tuple[dict | None, int]:
    """Visit profile, check if contractor without website."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/{handle}/"}
    }))
    msg_id += 1
    await asyncio.sleep(3)

    js = """
    (function() {
        const r = {has_website: false, bio: '', name: '', not_found: false};
        const pageText = document.body.innerText || '';
        if (pageText.includes("Sorry, this page") || pageText.includes("isn't available")) {
            r.not_found = true;
            return JSON.stringify(r);
        }
        // External link = has website
        const extLinks = document.querySelectorAll('a[href*="l.instagram.com"]');
        if (extLinks.length > 0) r.has_website = true;
        const allLinks = document.querySelectorAll('a');
        for (const a of allLinks) {
            const href = (a.href || '').toLowerCase();
            if (href.includes('linktr.ee') || href.includes('linkin.bio') || href.includes('linkpop') || href.includes('taplink')) {
                r.has_website = true;
            }
        }
        // Get bio and name from header
        const header = document.querySelector('header');
        if (header) {
            r.bio = header.innerText || '';
            const h = header.querySelector('h2');
            if (h) r.name = h.textContent.trim();
        }
        return JSON.stringify(r);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    profile = None
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and val.startswith('{'):
                    profile = json.loads(val)
                    break
        except (asyncio.TimeoutError, Exception):
            break
    await drain(ws)
    return profile, msg_id


async def main():
    with open(f'{BASE_DIR}/master_targets.json', 'r', encoding='utf-8') as f:
        existing = json.load(f)
    existing_igs = {t.get('ig', '').lower() for t in existing if t.get('ig')}

    print(f"Scanning your IG network for contractor targets...\n")
    print(f"Existing targets to skip: {len(existing_igs)}\n")

    ws_url = get_ws_url()
    msg_id = 1
    new_targets = []

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)

        # Navigate to own profile
        print("Navigating to your profile...", flush=True)
        await ws.send(json.dumps({
            "id": msg_id, "method": "Page.navigate",
            "params": {"url": "https://www.instagram.com/strangeadvancedmarketing/"}
        }))
        msg_id += 1
        await asyncio.sleep(4)
        await drain(ws)

        # Get following list
        print("\nScanning FOLLOWING list...", flush=True)
        following, msg_id = await get_follow_list(ws, 'following', msg_id)
        print(f"  Found {len(following)} accounts in Following\n", flush=True)

        await asyncio.sleep(2)

        # Navigate back to profile for followers
        await ws.send(json.dumps({
            "id": msg_id, "method": "Page.navigate",
            "params": {"url": "https://www.instagram.com/strangeadvancedmarketing/"}
        }))
        msg_id += 1
        await asyncio.sleep(4)
        await drain(ws)

        # Get followers list
        print("Scanning FOLLOWERS list...", flush=True)
        followers, msg_id = await get_follow_list(ws, 'followers', msg_id)
        print(f"  Found {len(followers)} accounts in Followers\n", flush=True)

        # Combine and deduplicate
        all_handles = list(set(following + followers))
        # Remove own handle and existing targets
        all_handles = [h for h in all_handles if h.lower() not in existing_igs and h.lower() != 'strangeadvancedmarketing']
        print(f"Total unique handles to check: {len(all_handles)} (after removing {len(existing_igs)} existing)\n")

        # Check each profile
        checked = 0
        for handle in all_handles:
            checked += 1
            if checked % 20 == 0:
                print(f"\n--- Progress: {checked}/{len(all_handles)}, found {len(new_targets)} targets ---\n", flush=True)

            try:
                profile, msg_id = await check_profile(ws, handle, msg_id)
                if not profile or profile.get('not_found'):
                    continue

                bio = profile.get('bio', '')

                if not is_contractor(bio):
                    continue

                if profile.get('has_website'):
                    print(f"  @{handle}: contractor but HAS WEBSITE - skip", flush=True)
                    continue

                # Check if South Florida
                if not is_south_florida(bio):
                    print(f"  @{handle}: contractor, no website, but NOT South FL - skip", flush=True)
                    continue

                category = guess_category(bio)
                location = guess_location(bio)
                name = profile.get('name', '') or handle

                target = {
                    "name": name,
                    "ig": handle,
                    "phone": "",
                    "category": category,
                    "location": location,
                    "rating": 0,
                    "reviews": 0,
                    "has_site": False,
                    "notes": "From IG network"
                }
                new_targets.append(target)
                print(f"  @{handle}: TARGET FOUND - {category} in {location} [{len(new_targets)}]", flush=True)

            except Exception as e:
                print(f"  @{handle}: ERROR - {e}", flush=True)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            await asyncio.sleep(1.5)

    # Save
    output_path = f'{BASE_DIR}/network_targets.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_targets, f, indent=2, ensure_ascii=False)

    print(f"\n\nDone! Found {len(new_targets)} contractor targets from your IG network.")
    print(f"Saved to: {output_path}")
    if new_targets:
        cats = {}
        for t in new_targets:
            cats[t['category']] = cats.get(t['category'], 0) + 1
        print("Categories:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")


if __name__ == '__main__':
    asyncio.run(main())
