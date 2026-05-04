"""
Search Instagram directly for contractor targets.
Stays on IG the whole time (no domain switching) — more reliable CDP.
Searches IG for contractor keywords, checks each profile for website.
"""
import json, time, re, sys, asyncio, urllib.request, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

IG_SEARCHES = [
    "handyman miami",
    "pressure washing miami",
    "pressure washing broward",
    "fence miami",
    "fence south florida",
    "landscaping miami",
    "lawn care miami",
    "tree service miami",
    "pool service miami",
    "painting miami contractor",
    "concrete miami",
    "junk removal miami",
    "tile miami",
    "roofing miami",
    "plumber miami",
    "electrician miami",
    "flooring miami",
    "paver miami",
    "moving miami",
    "handyman broward",
    "handyman fort lauderdale",
    "pressure washing pompano",
    "pool cleaning miami",
    "lawn mowing miami",
    "tree trimming miami",
    "drywall miami",
    "stucco miami",
    "epoxy flooring miami",
    "screen enclosure miami",
    "gutter cleaning miami",
]

CATEGORY_MAP = {
    'handyman': 'Handyman', 'pressure': 'Pressure Washing',
    'fence': 'Fence Contractor', 'landscap': 'Landscaping',
    'lawn': 'Lawn Care', 'tree': 'Tree Service', 'pool': 'Pool Service',
    'paint': 'Painting', 'concrete': 'Concrete Contractor',
    'junk': 'Junk Removal', 'tile': 'Tile Contractor',
    'roof': 'Roofing', 'plumb': 'Plumbing', 'electric': 'Electrical',
    'floor': 'Flooring', 'paver': 'Paver Installation',
    'moving': 'Moving Service', 'drywall': 'Drywall',
    'stucco': 'Stucco Contractor', 'epoxy': 'Epoxy Flooring',
    'screen': 'Screen Enclosure', 'gutter': 'Gutter Cleaning',
    'mow': 'Lawn Care', 'trim': 'Tree Service',
    'clean': 'Pressure Washing',
}


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


def guess_category(query: str, bio: str = '') -> str:
    text = (query + ' ' + bio).lower()
    for kw, cat in CATEGORY_MAP.items():
        if kw in text:
            return cat
    return 'General Contractor'


async def send_and_get(ws, msg_id: int, method: str, params: dict = None) -> tuple[dict, int]:
    """Send CDP command and wait for response."""
    cmd = {"id": msg_id, "method": method}
    if params:
        cmd["params"] = params
    await ws.send(json.dumps(cmd))
    msg_id += 1

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if data.get('id') == msg_id - 1:
                return data, msg_id
        except (asyncio.TimeoutError, Exception):
            break
    return {}, msg_id


async def evaluate(ws, js: str, msg_id: int) -> tuple[str, int]:
    """Evaluate JS and return result value."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js, "returnByValue": True}
    }))
    msg_id += 1

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=4)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                return val, msg_id
        except (asyncio.TimeoutError, Exception):
            break
    return '', msg_id


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def search_ig(ws, query: str, msg_id: int) -> tuple[list[str], int]:
    """Search Instagram and return account handles from results."""
    # Navigate to explore/search
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/explore/search/keyword/?q={query.replace(' ', '%20')}"}
    }))
    msg_id += 1
    await asyncio.sleep(4)
    await drain(ws)

    # Extract account links from search results
    js = """
    (function() {
        const handles = [];
        // Get all profile links from search results
        const links = document.querySelectorAll('a[href^="/"]');
        for (const a of links) {
            const href = a.getAttribute('href') || '';
            const match = href.match(/^\\/([a-zA-Z0-9_.]+)\\/$/);
            if (match) {
                const h = match[1].toLowerCase();
                if (!['explore','reels','stories','direct','accounts','p','reel'].includes(h) && h.length > 2) {
                    if (!handles.includes(h)) handles.push(h);
                }
            }
            if (handles.length >= 15) break;
        }
        return JSON.stringify(handles);
    })()
    """
    val, msg_id = await evaluate(ws, js, msg_id)
    await drain(ws)

    handles = []
    if val and val.startswith('['):
        handles = json.loads(val)

    # If explore search didn't work, try the search API approach
    if len(handles) < 3:
        # Use IG's top search bar
        await ws.send(json.dumps({
            "id": msg_id, "method": "Page.navigate",
            "params": {"url": "https://www.instagram.com/"}
        }))
        msg_id += 1
        await asyncio.sleep(3)
        await drain(ws)

        # Click search, type query, grab results
        search_js = f"""
        (function() {{
            // Find and click the search icon/link
            const searchLink = document.querySelector('a[href="/explore/"]') ||
                               document.querySelector('svg[aria-label="Search"]')?.closest('a') ||
                               document.querySelector('a[href*="search"]');
            if (searchLink) searchLink.click();
            return 'clicked_search';
        }})()
        """
        await evaluate(ws, search_js, msg_id)
        msg_id += 1
        await asyncio.sleep(1.5)
        await drain(ws)

        # Type in search
        type_js = f"""
        (function() {{
            const input = document.querySelector('input[placeholder="Search"]') ||
                          document.querySelector('input[aria-label="Search input"]') ||
                          document.querySelector('input[type="text"]');
            if (input) {{
                input.focus();
                input.value = '{query}';
                input.dispatchEvent(new Event('input', {{bubbles: true}}));
                return 'typed';
            }}
            return 'no_input';
        }})()
        """
        await evaluate(ws, type_js, msg_id)
        msg_id += 1
        await asyncio.sleep(3)
        await drain(ws)

        # Grab results from search dropdown
        results_js = """
        (function() {
            const handles = [];
            const links = document.querySelectorAll('a[href^="/"][role="link"], a[href^="/"]');
            for (const a of links) {
                const href = a.getAttribute('href') || '';
                const match = href.match(/^\\/([a-zA-Z0-9_.]+)\\/$/);
                if (match) {
                    const h = match[1].toLowerCase();
                    if (!['explore','reels','stories','direct','accounts','p','reel','strangeadvancedmarketing'].includes(h) && h.length > 2) {
                        if (!handles.includes(h)) handles.push(h);
                    }
                }
                if (handles.length >= 15) break;
            }
            return JSON.stringify(handles);
        })()
        """
        val, msg_id = await evaluate(ws, results_js, msg_id)
        await drain(ws)

        if val and val.startswith('['):
            new_handles = json.loads(val)
            for h in new_handles:
                if h not in handles:
                    handles.append(h)

    return handles, msg_id


async def check_profile(ws, handle: str, msg_id: int) -> tuple[dict | None, int]:
    """Visit IG profile and check if contractor without website."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/{handle}/"}
    }))
    msg_id += 1
    await asyncio.sleep(3)
    await drain(ws)

    js = """
    (function() {
        const r = {has_website: false, bio: '', name: '', not_found: false, handle: ''};
        const pageText = document.body?.innerText || '';
        if (pageText.includes("Sorry, this page") || pageText.includes("isn't available")) {
            r.not_found = true;
            return JSON.stringify(r);
        }
        // Check for external link
        const extLinks = document.querySelectorAll('a[href*="l.instagram.com"]');
        if (extLinks.length > 0) r.has_website = true;
        const allLinks = document.querySelectorAll('a');
        for (const a of allLinks) {
            const href = (a.href || '').toLowerCase();
            if (href.includes('linktr.ee') || href.includes('linkin.bio') ||
                href.includes('linkpop') || href.includes('taplink') ||
                href.includes('beacons.ai') || href.includes('stan.store')) {
                r.has_website = true;
            }
        }
        // Get header info
        const header = document.querySelector('header');
        if (header) {
            r.bio = header.innerText || '';
            const h2 = header.querySelector('h2');
            if (h2) r.handle = h2.textContent.trim();
        }
        // Get display name
        const nameSpan = document.querySelector('header span.x1lliihq');
        if (nameSpan) r.name = nameSpan.textContent.trim();
        return JSON.stringify(r);
    })()
    """
    val, msg_id = await evaluate(ws, js, msg_id)
    await drain(ws)

    if val and val.startswith('{'):
        return json.loads(val), msg_id
    return None, msg_id


async def main():
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    # Load existing
    existing_path = f'{BASE_DIR}/master_targets.json'
    if os.path.exists(existing_path):
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        existing_igs = {t.get('ig', '').lower() for t in existing if t.get('ig')}
    else:
        existing_igs = set()

    # Also load any batch2 targets
    for extra in ['new_targets_batch2.json', 'network_targets.json']:
        p = f'{BASE_DIR}/{extra}'
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for t in json.load(f):
                    if t.get('ig'):
                        existing_igs.add(t['ig'].lower())

    print(f"Searching IG for contractor targets ({target_count} goal)...")
    print(f"Existing to skip: {len(existing_igs)}\n")

    ws_url = get_ws_url()
    msg_id = 1
    new_targets = []
    checked = set()

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for qi, query in enumerate(IG_SEARCHES):
            if len(new_targets) >= target_count:
                break

            print(f"\n[{qi+1}/{len(IG_SEARCHES)}] Searching: {query}", flush=True)

            try:
                handles, msg_id = await search_ig(ws, query, msg_id)
                print(f"  Found {len(handles)} accounts: {handles[:5]}", flush=True)

                for handle in handles:
                    if len(new_targets) >= target_count:
                        break
                    handle_lower = handle.lower()
                    if handle_lower in existing_igs or handle_lower in checked:
                        continue
                    checked.add(handle_lower)

                    await asyncio.sleep(2)

                    try:
                        profile, msg_id = await check_profile(ws, handle, msg_id)
                    except Exception as e:
                        print(f"    @{handle}: connection error, reconnecting...", flush=True)
                        await asyncio.sleep(2)
                        try:
                            ws_url = get_ws_url()
                            ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                            await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                            msg_id += 1
                            await asyncio.sleep(1)
                            profile, msg_id = await check_profile(ws, handle, msg_id)
                        except Exception:
                            print(f"    @{handle}: SKIP (reconnect failed)", flush=True)
                            continue

                    if not profile or profile.get('not_found'):
                        continue

                    if profile.get('has_website'):
                        print(f"    @{handle}: has website - skip", flush=True)
                        continue

                    bio = profile.get('bio', '')
                    name = profile.get('name', '') or handle
                    category = guess_category(query, bio)

                    target = {
                        "name": name,
                        "ig": handle,
                        "phone": "",
                        "category": category,
                        "location": "Miami, FL",
                        "rating": 0,
                        "reviews": 0,
                        "has_site": False,
                        "notes": f"IG search: {query}"
                    }
                    new_targets.append(target)
                    print(f"    @{handle}: NO WEBSITE - TARGET [{len(new_targets)}/{target_count}]", flush=True)

            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                try:
                    await asyncio.sleep(3)
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    print("  Failed to reconnect, trying next query...", flush=True)

            await asyncio.sleep(2)

    # Save
    output_path = f'{BASE_DIR}/ig_search_targets.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_targets, f, indent=2, ensure_ascii=False)

    print(f"\n\nDone! Found {len(new_targets)} IG targets without websites.")
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
