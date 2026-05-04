import json, time, sys, asyncio, urllib.request, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
OUT_DIR = os.path.join(BASE_DIR, 'hero_candidates')
os.makedirs(OUT_DIR, exist_ok=True)

CATEGORIES = {
    'Handyman': 'handyman tools workbench repair',
    'Pressure Washing': 'pressure washing driveway cleaning',
    'Pressure Cleaning': 'pressure washing concrete cleaning',
    'Tree Service': 'tree trimming arborist service',
    'Fence Contractor': 'wooden privacy fence backyard installed',
    'Junk Removal': 'junk removal hauling truck dumpster',
    'Painting': 'house painting contractor roller wall',
    'Pool Service': 'swimming pool blue water backyard',
    'Pool Cleaning': 'pool cleaning service maintenance',
    'Concrete Contractor': 'concrete pouring driveway sidewalk',
    'Landscape Design': 'landscaping garden design backyard',
    'Landscaping': 'professional landscaping lawn garden',
    'Property Maintenance': 'property maintenance building repair',
    'Tile Contractor': 'tile installation floor ceramic',
    'Tile Store': 'tile showroom floor samples',
    'Construction': 'construction site building framing',
    'Roofing': 'roof shingles installation contractor',
    'Lawn Care': 'lawn mowing freshly cut grass yard',
    'Artificial Turf': 'artificial turf grass installation green',
    'Sprinkler/Irrigation': 'lawn sprinkler irrigation system watering',
    'Irrigation': 'irrigation sprinkler system yard',
    'Sprinkler Contractor': 'sprinkler system installation lawn',
    'Moving Service': 'moving truck boxes movers loading',
    'Water Damage Restoration': 'water damage restoration flood repair',
    'Window Tinting': 'window tinting film glass building',
    'Electrical': 'electrician electrical panel wiring',
    'Plastering': 'stucco plastering wall exterior',
    'Mobile Car Wash': 'car wash detailing mobile',
    'General Contractor': 'general contractor renovation home',
    'Painting & Pressure Cleaning': 'house painting exterior contractor',
    # New categories for future targets
    'Plumbing': 'plumber plumbing pipes repair',
    'HVAC': 'hvac air conditioning unit repair',
    'Flooring': 'hardwood flooring installation contractor',
    'Drywall': 'drywall installation finishing taping',
    'Garage Door': 'garage door installation repair',
    'Gutter Cleaning': 'gutter cleaning maintenance roof',
    'Cabinetry': 'kitchen cabinet installation custom',
    'Bathroom Remodel': 'bathroom remodel renovation tile',
    'Paver Installation': 'paver patio driveway installation',
    'Appliance Repair': 'appliance repair technician kitchen',
    'Deck Building': 'wood deck building backyard outdoor',
    'Kitchen Remodel': 'kitchen remodel renovation modern',
    'Stucco Contractor': 'stucco exterior wall finish',
    'Carpet Cleaning': 'carpet cleaning steam professional',
    'Mold Removal': 'mold removal remediation professional',
    'Locksmith': 'locksmith door lock key service',
    'Screen Enclosure': 'screen enclosure patio pool lanai',
    'Epoxy Flooring': 'epoxy floor garage coating',
}


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'instagram.com' in url or 'unsplash.com' in url:
                return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            if not tab.get('url', '').startswith('chrome://'):
                return tab['webSocketDebuggerUrl']
    raise Exception("No Chrome tab found")


async def search_unsplash(ws, query: str, msg_id: int) -> tuple[list[str], int]:
    """Search Unsplash and extract photo IDs from results."""
    import urllib.parse
    url = f'https://unsplash.com/s/photos/{urllib.parse.quote_plus(query)}'

    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": url}
    }))
    msg_id += 1
    await asyncio.sleep(4)

    # Extract photo IDs from the page
    js = """
    (function() {
        const imgs = document.querySelectorAll('img[src*="images.unsplash.com/photo-"]');
        const ids = [];
        for (const img of imgs) {
            const match = img.src.match(/(photo-[a-f0-9-]+)/);
            if (match && !ids.includes(match[1])) {
                ids.push(match[1]);
            }
            if (ids.length >= 6) break;
        }
        // Also check srcset
        if (ids.length < 3) {
            const allImgs = document.querySelectorAll('img[srcset*="images.unsplash.com"]');
            for (const img of allImgs) {
                const srcset = img.srcset || '';
                const match = srcset.match(/(photo-[a-f0-9-]+)/);
                if (match && !ids.includes(match[1])) {
                    ids.push(match[1]);
                }
                if (ids.length >= 6) break;
            }
        }
        // Also try figure/a links
        if (ids.length < 3) {
            const links = document.querySelectorAll('a[href*="/photos/"]');
            for (const a of links) {
                const href = a.href;
                const match = href.match(/photos\\/([a-zA-Z0-9_-]+)/);
                if (match) {
                    ids.push('lookup:' + match[1]);
                }
                if (ids.length >= 6) break;
            }
        }
        return JSON.stringify(ids);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    ids = []
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and val.startswith('['):
                    ids = json.loads(val)
                    break
        except (asyncio.TimeoutError, Exception):
            break

    # Drain
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass

    return ids, msg_id


async def main():
    print(f"Finding hero images for {len(CATEGORIES)} categories...\n")

    ws_url = get_ws_url()
    msg_id = 1
    results = {}

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)

        for cat, query in CATEGORIES.items():
            print(f"[{cat}] Searching: {query}...", end=' ', flush=True)

            try:
                ids, msg_id = await search_unsplash(ws, query, msg_id)
                print(f"found {len(ids)} candidates", flush=True)

                # Download first 3 candidates as thumbnails
                for i, pid in enumerate(ids[:3]):
                    if pid.startswith('lookup:'):
                        continue
                    img_url = f'https://images.unsplash.com/{pid}?w=400&h=200&fit=crop&crop=center'
                    safe_cat = cat.replace('/', '-').replace(' ', '_')
                    path = os.path.join(OUT_DIR, f'{safe_cat}_{i+1}_{pid}.jpg')
                    try:
                        urllib.request.urlretrieve(img_url, path)
                    except Exception:
                        pass

                results[cat] = ids[:3]

            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                results[cat] = []
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            await asyncio.sleep(2)

    # Save results
    with open(os.path.join(BASE_DIR, 'hero_image_candidates.json'), 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDone! Saved candidates for {len(results)} categories.")
    print(f"Thumbnails in: {OUT_DIR}")
    print(f"Results in: hero_image_candidates.json")


if __name__ == '__main__':
    asyncio.run(main())
