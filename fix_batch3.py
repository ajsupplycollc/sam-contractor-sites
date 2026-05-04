"""
Fix batch 3: rebuild all targets from scratch.
Phase 1: Build clean target list from all raw handles + existing targets
Phase 2: Visit IG profiles for correct display names + download logos
Phase 3: Maps enrichment for proper business names + phone/rating/reviews
Phase 4: Regenerate sites

Single process. Checkpointing after each phase.
"""
import json, os, re, sys, asyncio, urllib.request, urllib.parse, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

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
    "clermont": "Clermont, FL", "deltona": "Deltona, FL",
    "titusville": "Titusville, FL", "st augustine": "St Augustine, FL",
    "lehigh": "Lehigh Acres, FL", "port charlotte": "Port Charlotte, FL",
    "sunrise": "Sunrise, FL", "spring hill": "Spring Hill, FL",
    "panama city": "Panama City, FL", "plant city": "Plant City, FL",
    "winter park": "Winter Park, FL",
}


def guess_category(text: str) -> str:
    text = text.lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in text:
            return cat
    return "General Contractor"


def guess_location(text: str) -> str:
    text = text.lower()
    for keyword, location in LOCATION_KEYWORDS.items():
        if keyword in text:
            return location
    return "Florida"


def slugify(name: str) -> str:
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')[:50]


def get_ws_url(prefer_domain: str = '') -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    if prefer_domain:
        for tab in tabs:
            if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
                url = tab.get('url', '')
                if prefer_domain in url and 'omnibox' not in url:
                    return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if not url.startswith('chrome://') or url == 'chrome://newtab/':
                if 'omnibox' not in url:
                    return tab['webSocketDebuggerUrl']
    raise Exception("No Chrome tab found")


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def cdp_navigate(ws, url: str, msg_id: int, wait: float = 3.5) -> int:
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": url}
    }))
    msg_id += 1
    await asyncio.sleep(wait)
    await drain(ws)
    return msg_id


async def cdp_eval(ws, js: str, msg_id: int, timeout: float = 8.0):
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
                await drain(ws)
                return val, msg_id
        except (asyncio.TimeoutError, Exception):
            break
    await drain(ws)
    return '', msg_id


def download_image(url: str, save_path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        data = urllib.request.urlopen(req, timeout=10).read()
        if len(data) > 1000:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        pass
    return False


# ── Phase 1: Build clean target list ──��───────────────────────────

def phase1_build_targets() -> list[dict]:
    checkpoint = f'{BASE_DIR}/batch3_phase1.json'
    if os.path.exists(checkpoint):
        with open(checkpoint, 'r', encoding='utf-8') as f:
            targets = json.load(f)
        print(f"Phase 1: Loaded {len(targets)} targets from checkpoint")
        return targets

    print("Phase 1: Building clean target list...")

    # Load batch 1/2 handles to exclude
    b1 = json.load(open(f'{BASE_DIR}/gmaps_ig_targets.json', 'r', encoding='utf-8'))
    b2 = json.load(open(f'{BASE_DIR}/new_targets_batch2.json', 'r', encoding='utf-8'))
    existing_handles = set(t['ig'].lower().lstrip('@') for t in b1 + b2)

    # Load raw handles (handle -> search_query)
    raw = json.load(open(f'{BASE_DIR}/scaled_raw_handles.json', 'r', encoding='utf-8'))

    # Load existing targets for additional handles + category info
    old_targets = json.load(open(f'{BASE_DIR}/scaled_targets.json', 'r', encoding='utf-8'))
    old_target_map = {}
    for t in old_targets:
        h = t['ig'].lower().lstrip('@')
        if h not in old_target_map:
            old_target_map[h] = t

    # Build combined handle set with category/location
    handle_data = {}

    # First: raw handles (search query gives reliable category/location)
    for handle, query in raw.items():
        h = handle.lower().lstrip('@')
        if h in existing_handles or len(h) < 3:
            continue
        handle_data[h] = {
            'ig': h,
            'name': h,
            'category': guess_category(query),
            'location': guess_location(query),
        }

    # Second: handles only in old targets (use their category/location)
    for h, t in old_target_map.items():
        if h in existing_handles or h in handle_data or len(h) < 3:
            continue
        handle_data[h] = {
            'ig': h,
            'name': h,
            'category': t.get('category', 'General Contractor'),
            'location': t.get('location', 'Florida'),
        }

    targets = list(handle_data.values())
    print(f"Phase 1: Built {len(targets)} clean targets")

    with open(checkpoint, 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    return targets


# ── Phase 2: IG profile scraping ──────────────────────────────────

IG_JS = """
(function() {
    const r = {name: '', phone: '', bio: '', pic_url: ''};

    // Profile picture
    const imgs = document.querySelectorAll('header img, img[alt*="profile picture"]');
    for (const img of imgs) {
        const src = img.src || '';
        if (src.includes('cdninstagram') || src.includes('fbcdn') || src.includes('scontent')) {
            if (!r.pic_url || img.width > 100) {
                r.pic_url = src;
            }
        }
    }
    if (!r.pic_url) {
        const allImgs = document.querySelectorAll('img');
        for (const img of allImgs) {
            const alt = (img.alt || '').toLowerCase();
            if (alt.includes('profile') && img.src && img.src.includes('cdn')) {
                r.pic_url = img.src;
                break;
            }
        }
    }

    // Display name from meta description
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
        const content = metaDesc.getAttribute('content') || '';
        // Format: "X Followers, Y Following, Z Posts - Business Name (@handle)"
        const dashMatch = content.match(/Posts\\s*-\\s*(.+?)\\s*\\(@/);
        if (dashMatch) {
            r.name = dashMatch[1].trim();
        }
        // Fallback: "from Business Name (@handle)"
        if (!r.name) {
            const fromMatch = content.match(/from\\s+(.+?)\\s*\\(@/);
            if (fromMatch) {
                r.name = fromMatch[1].trim();
            }
        }
    }

    // Fallback: title tag
    if (!r.name) {
        const title = document.title || '';
        const titleMatch = title.match(/^(.+?)\\s*[(@|•]/);
        if (titleMatch && titleMatch[1].trim() !== 'Instagram') {
            r.name = titleMatch[1].trim();
        }
    }

    // Bio text
    const header = document.querySelector('header');
    if (header) {
        r.bio = header.innerText || '';
    }

    // Phone from bio or tel: links
    const bioText = r.bio || document.body?.innerText || '';
    const phoneMatch = bioText.match(/\\(?(\\d{3})\\)?[\\s.-]?(\\d{3})[\\s.-]?(\\d{4})/);
    if (phoneMatch) {
        r.phone = phoneMatch[0].trim();
    }
    const telLinks = document.querySelectorAll('a[href*="tel:"]');
    if (telLinks.length > 0 && !r.phone) {
        const href = telLinks[0].href;
        const digits = href.replace(/\\D/g, '').slice(-10);
        if (digits.length === 10) {
            r.phone = '(' + digits.substr(0,3) + ') ' + digits.substr(3,3) + '-' + digits.substr(6,4);
        }
    }

    return JSON.stringify(r);
})()
"""


async def phase2_ig_scrape(targets: list[dict], start_idx: int = 0) -> list[dict]:
    checkpoint = f'{BASE_DIR}/batch3_phase2.json'
    progress_file = f'{BASE_DIR}/batch3_ig_progress.txt'

    if os.path.exists(checkpoint) and start_idx == 0:
        with open(checkpoint, 'r', encoding='utf-8') as f:
            targets = json.load(f)
        # Check if phase 2 completed
        done = sum(1 for t in targets if t.get('ig_scraped'))
        if done >= len(targets):
            print(f"Phase 2: Already completed ({done}/{len(targets)} scraped)")
            return targets
        start_idx = done
        print(f"Phase 2: Resuming from {start_idx}/{len(targets)}")

    print(f"Phase 2: Scraping IG profiles ({len(targets)} targets, starting at {start_idx})...")

    ws_url = get_ws_url('instagram.com')
    msg_id = 1
    logos_ok = 0
    names_ok = 0

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i in range(start_idx, len(targets)):
            t = targets[i]
            handle = t['ig']

            print(f"[{i+1}/{len(targets)}] @{handle}...", end=' ', flush=True)

            try:
                msg_id = await cdp_navigate(ws, f'https://www.instagram.com/{handle}/', msg_id, wait=3.5)
                val, msg_id = await cdp_eval(ws, IG_JS, msg_id)

                if val and val.startswith('{'):
                    info = json.loads(val)

                    # Update name if we got one
                    if info.get('name') and len(info['name']) > 2:
                        t['ig_display_name'] = info['name']
                        names_ok += 1

                    # Update phone
                    if info.get('phone') and not t.get('phone'):
                        t['phone'] = info['phone']

                    # Download logo
                    display = t.get('ig_display_name', handle.replace('_', ' ').replace('.', ' ').title())
                    slug = slugify(display)
                    logo_dir = os.path.join(BASE_DIR, slug)
                    logo_path = os.path.join(logo_dir, 'logo.png')

                    if info.get('pic_url') and not os.path.exists(logo_path):
                        if download_image(info['pic_url'], logo_path):
                            logos_ok += 1
                            print(f"logo OK", end=' ')
                        else:
                            print(f"logo FAIL", end=' ')

                    display_short = (t.get('ig_display_name') or handle)[:35]
                    print(f"| {display_short}", flush=True)
                else:
                    print(f"no data (page may not exist)", flush=True)

                t['ig_scraped'] = True

            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                t['ig_scraped'] = True
                try:
                    ws_url = get_ws_url('instagram.com')
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            # Save every 10
            if (i + 1) % 10 == 0:
                with open(checkpoint, 'w', encoding='utf-8') as f:
                    json.dump(targets, f, indent=2, ensure_ascii=False)
                with open(progress_file, 'w') as f:
                    f.write(f"{i+1}/{len(targets)} | names: {names_ok} | logos: {logos_ok}\n")

            await asyncio.sleep(2)

    # Final save
    with open(checkpoint, 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 2 done: {names_ok} names, {logos_ok} logos from {len(targets)} profiles")
    return targets


# ── Phase 3: Maps enrichment ───────��─────────────────────────────

MAPS_SEARCH_JS = """
(function() {
    const r = {name: '', phone: '', rating: 0, reviews: 0, address: '', found: false, has_website: false};
    const text = document.body?.innerText || '';

    const ratingMatch = text.match(/(\\d\\.\\d)\\s*(?:stars?|\\()/);
    if (ratingMatch) r.rating = parseFloat(ratingMatch[1]);

    const reviewMatch = text.match(/(\\d[\\d,]*)\\s*(?:reviews?|Google reviews?)/i);
    if (reviewMatch) r.reviews = parseInt(reviewMatch[1].replace(',', ''));

    const phonePatterns = [/\\(?(\\d{3})\\)?[\\s.-](\\d{3})[\\s.-](\\d{4})/g];
    for (const pat of phonePatterns) {
        const matches = [...text.matchAll(pat)];
        for (const m of matches) {
            if (!m[0].startsWith('(0') && !m[0].startsWith('(1')) {
                r.phone = m[0];
                r.found = true;
                break;
            }
        }
        if (r.phone) break;
    }

    const h1 = document.querySelector('h1');
    if (h1) {
        const h1text = h1.textContent.trim();
        const generic = ['results', 'google maps', 'search', 'map'];
        if (h1text && h1text.length > 2 && h1text.length < 80 && !generic.includes(h1text.toLowerCase())) {
            r.name = h1text;
            r.found = true;
        }
    }

    if (r.rating > 0 || r.phone) r.found = true;

    const websiteBtn = document.querySelector('a[data-item-id="authority"], a[aria-label*="Website"]');
    if (websiteBtn) r.has_website = true;

    return JSON.stringify(r);
})()
"""

MAPS_DETAIL_JS = """
(function() {
    const r = {name: '', phone: '', rating: 0, reviews: 0, address: '', has_website: false, found: false};

    const h1 = document.querySelector('h1');
    if (h1) r.name = h1.textContent.trim();

    const ratingEl = document.querySelector('[role="img"][aria-label*="star"]');
    if (ratingEl) {
        const match = ratingEl.getAttribute('aria-label').match(/(\\d\\.\\d)/);
        if (match) r.rating = parseFloat(match[1]);
    }
    if (!r.rating) {
        const spans = document.querySelectorAll('span');
        for (const s of spans) {
            const ariaLabel = s.getAttribute('aria-label') || '';
            const match = ariaLabel.match(/(\\d\\.\\d)\\s*stars?/);
            if (match) { r.rating = parseFloat(match[1]); break; }
        }
    }

    const text = document.body?.innerText || '';
    const revMatch = text.match(/(\\d[\\d,]*)\\s*(?:reviews?|Google reviews?)/i);
    if (revMatch) r.reviews = parseInt(revMatch[1].replace(',', ''));

    const telLinks = document.querySelectorAll('a[href^="tel:"]');
    if (telLinks.length > 0) {
        const href = telLinks[0].href;
        const digits = href.replace(/\\D/g, '').slice(-10);
        if (digits.length === 10) {
            r.phone = '(' + digits.substr(0,3) + ') ' + digits.substr(3,3) + '-' + digits.substr(6,4);
        }
    }
    if (!r.phone) {
        const buttons = document.querySelectorAll('button[aria-label*="Phone"], button[data-tooltip*="phone"]');
        for (const btn of buttons) {
            const label = btn.getAttribute('aria-label') || btn.getAttribute('data-tooltip') || '';
            const phoneMatch = label.match(/\\(?(\\d{3})\\)?[\\s.-]?(\\d{3})[\\s.-]?(\\d{4})/);
            if (phoneMatch) { r.phone = phoneMatch[0]; break; }
        }
    }

    const websiteBtn = document.querySelector('a[data-item-id="authority"], a[aria-label*="Website"]');
    if (websiteBtn) r.has_website = true;

    if (r.name || r.phone || r.rating) r.found = true;
    return JSON.stringify(r);
})()
"""

MAPS_CLICK_JS = """
(function() {
    const links = document.querySelectorAll('a[href*="/maps/place/"]');
    if (links.length > 0) { links[0].click(); return 'clicked'; }
    const results = document.querySelectorAll('[role="feed"] > div');
    if (results.length > 0) { results[0].click(); return 'clicked_div'; }
    return 'no_results';
})()
"""


def clean_search_name(handle: str) -> str:
    search = handle.replace('_', ' ').replace('.', ' ')
    search = re.sub(r'\d+$', '', search)
    return search.title()


async def phase3_maps_enrich(targets: list[dict], start_idx: int = 0) -> list[dict]:
    checkpoint = f'{BASE_DIR}/batch3_phase3.json'
    progress_file = f'{BASE_DIR}/batch3_maps_progress.txt'

    if os.path.exists(checkpoint) and start_idx == 0:
        with open(checkpoint, 'r', encoding='utf-8') as f:
            targets = json.load(f)
        done = sum(1 for t in targets if t.get('maps_checked'))
        if done >= len(targets):
            print(f"Phase 3: Already completed ({done}/{len(targets)} checked)")
            return targets
        start_idx = done
        print(f"Phase 3: Resuming from {start_idx}/{len(targets)}")

    print(f"Phase 3: Maps enrichment ({len(targets)} targets, starting at {start_idx})...")

    ws_url = get_ws_url()
    msg_id = 1
    enriched = 0
    captcha_count = 0

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i in range(start_idx, len(targets)):
            t = targets[i]
            handle = t['ig']
            display = t.get('ig_display_name', clean_search_name(handle))
            location = t.get('location', 'Florida')
            category = t.get('category', '')

            query = f"{display} {category} {location}"
            search_url = f'https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}'

            print(f"[{i+1}/{len(targets)}] @{handle} -> \"{query[:50]}\"...", end=' ', flush=True)

            try:
                msg_id = await cdp_navigate(ws, search_url, msg_id, wait=4.0)

                # Check for CAPTCHA
                captcha_val, msg_id = await cdp_eval(ws, "document.title || ''", msg_id, timeout=3)
                if captcha_val and ('sorry' in captcha_val.lower() or 'unusual traffic' in captcha_val.lower()):
                    captcha_count += 1
                    print(f"CAPTCHA (#{captcha_count})", flush=True)
                    if captcha_count >= 3:
                        print(f"\n  Too many CAPTCHAs, stopping Maps enrichment at {i}")
                        break
                    t['maps_checked'] = True
                    await asyncio.sleep(5)
                    continue

                # Try initial page
                val, msg_id = await cdp_eval(ws, MAPS_SEARCH_JS, msg_id)
                info = json.loads(val) if val and val.startswith('{') else {'found': False}

                # If no results, click first result for detail page
                if not info.get('found'):
                    click_val, msg_id = await cdp_eval(ws, MAPS_CLICK_JS, msg_id)
                    if click_val and 'click' in str(click_val):
                        await asyncio.sleep(3.5)
                        await drain(ws)
                        val2, msg_id = await cdp_eval(ws, MAPS_DETAIL_JS, msg_id)
                        if val2 and val2.startswith('{'):
                            info = json.loads(val2)

                if info.get('found'):
                    if info.get('name') and len(info['name']) > 2:
                        t['maps_name'] = info['name']
                    if info.get('phone') and not t.get('phone'):
                        t['phone'] = info['phone']
                    if info.get('rating', 0) > 0:
                        t['rating'] = info['rating']
                    if info.get('reviews', 0) > 0:
                        t['reviews'] = info['reviews']
                    if info.get('has_website'):
                        t['has_website'] = True
                    enriched += 1
                    print(f"FOUND: {info.get('name', '')[:25]} | {info.get('phone', 'no phone')} | {info.get('rating', 0)}*", flush=True)
                else:
                    print(f"NOT FOUND", flush=True)

                t['maps_checked'] = True

            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                t['maps_checked'] = True
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            # Save every 10
            if (i + 1) % 10 == 0:
                with open(checkpoint, 'w', encoding='utf-8') as f:
                    json.dump(targets, f, indent=2, ensure_ascii=False)
                with open(progress_file, 'w') as f:
                    f.write(f"{i+1}/{len(targets)} | enriched: {enriched} | captchas: {captcha_count}\n")

            await asyncio.sleep(2)

    # Final save
    with open(checkpoint, 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 3 done: {enriched}/{len(targets)} enriched from Maps")
    return targets


# ── Phase 4: Finalize names ──────────────────────────────────────

def phase4_finalize_names(targets: list[dict]) -> list[dict]:
    """Set the final display name for each target using best available data."""
    for t in targets:
        handle = t['ig']
        maps_name = t.get('maps_name', '')
        ig_name = t.get('ig_display_name', '')
        humanized = handle.replace('_', ' ').replace('.', ' ').title()
        humanized = re.sub(r'\d+$', '', humanized).strip()

        # Priority: Maps name (most professional) > IG display name > humanized handle
        # But only use Maps name if it looks like a business name (not generic)
        generic_maps = {'results', 'google maps', 'search', 'map', 'florida'}
        if maps_name and len(maps_name) > 2 and maps_name.lower() not in generic_maps:
            t['name'] = maps_name
        elif ig_name and len(ig_name) > 2:
            t['name'] = ig_name
        else:
            t['name'] = humanized

    # Save final targets
    with open(f'{BASE_DIR}/batch3_final.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    names_proper = sum(1 for t in targets if t['name'] != t['ig'])
    phones = sum(1 for t in targets if t.get('phone'))
    ratings = sum(1 for t in targets if t.get('rating', 0) > 0)
    print(f"\nFinal target stats:")
    print(f"  Total: {len(targets)}")
    print(f"  Proper names: {names_proper}")
    print(f"  With phone: {phones}")
    print(f"  With rating: {ratings}")

    return targets


# ── Single target test mode ──────────────────────────────────────

async def test_single(handle: str):
    """Test the full pipeline on a single handle."""
    print(f"=== Testing single target: @{handle} ===\n")

    # Build target
    raw = json.load(open(f'{BASE_DIR}/scaled_raw_handles.json', 'r', encoding='utf-8'))
    query = raw.get(handle, '')
    target = {
        'ig': handle,
        'name': handle,
        'category': guess_category(query) if query else 'General Contractor',
        'location': guess_location(query) if query else 'Florida',
    }
    print(f"Category: {target['category']}, Location: {target['location']}")

    # IG scrape
    print("\n--- IG Profile Scrape ---")
    targets = await phase2_ig_scrape([target], start_idx=0)
    target = targets[0]

    # Maps enrich
    print("\n--- Maps Enrichment ---")
    targets = await phase3_maps_enrich([target], start_idx=0)
    target = targets[0]

    # Finalize name
    targets = phase4_finalize_names([target])
    target = targets[0]

    print(f"\n--- Final target ---")
    print(json.dumps(target, indent=2, ensure_ascii=False))

    return target


# ── Main ──────────────────────────────────────────────────────────

async def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        handle = sys.argv[2] if len(sys.argv) > 2 else None
        if not handle:
            raw = json.load(open(f'{BASE_DIR}/scaled_raw_handles.json', 'r', encoding='utf-8'))
            handle = list(raw.keys())[0]
        await test_single(handle)
        return

    # Full pipeline
    targets = phase1_build_targets()
    targets = await phase2_ig_scrape(targets)
    targets = await phase3_maps_enrich(targets)
    targets = phase4_finalize_names(targets)

    print(f"\n{'='*60}")
    print(f"All phases complete. {len(targets)} targets ready for site generation.")
    print(f"Run generate_v2.py with batch3_final.json to regenerate sites.")


if __name__ == '__main__':
    asyncio.run(main())
