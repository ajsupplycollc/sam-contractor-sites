"""
Enrich IG targets with Google Maps data (phone, rating, reviews, proper name).
Takes new_targets_batch2.json handles, searches Google Maps for each, extracts business info.
Uses Chrome debug CDP.
"""
import json, time, re, sys, asyncio, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'google.com/maps' in url or url == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if not url.startswith('chrome://') or url == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    raise Exception("No Chrome tab found")


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


def clean_search_name(target: dict) -> str:
    """Build a search query from the target's name/handle."""
    name = target.get('name', '')
    handle = target.get('ig', '').lstrip('@')

    # If name is garbage (starts with "Followed by" or is another handle), use the IG handle
    if (name.startswith('Followed by') or
        name == handle or
        '.' in name and ' ' not in name or  # looks like a handle
        name.startswith('#') or
        name.startswith('•') or
        'Service areas' in name):
        # Convert handle to searchable name: underscores/dots to spaces, title case
        search = handle.replace('_', ' ').replace('.', ' ')
        search = re.sub(r'\d+$', '', search)  # remove trailing numbers
        return search.title()
    return name


async def search_gmaps(ws, query: str, msg_id: int) -> tuple[dict, int]:
    """Search Google Maps for a business and extract info from first result."""
    search_url = f'https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}'

    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": search_url}
    }))
    msg_id += 1
    await asyncio.sleep(4)
    await drain(ws)

    # Extract business info from Maps results or detail page
    js = """
    (function() {
        const r = {name: '', phone: '', rating: 0, reviews: 0, address: '', found: false};
        const text = document.body?.innerText || '';

        // Check if we landed on a business detail page (has phone/rating)
        // Or on search results page

        // Try to get rating - look for star pattern
        const ratingMatch = text.match(/(\\d\\.\\d)\\s*(?:stars?|\\()/);
        if (ratingMatch) {
            r.rating = parseFloat(ratingMatch[1]);
        }

        // Try to get review count
        const reviewMatch = text.match(/(\\d[\\d,]*)\\s*(?:reviews?|Google reviews?)/i);
        if (reviewMatch) {
            r.reviews = parseInt(reviewMatch[1].replace(',', ''));
        }

        // Try to get phone - multiple patterns
        const phonePatterns = [
            /\\(?(\\d{3})\\)?[\\s.-](\\d{3})[\\s.-](\\d{4})/g
        ];
        for (const pat of phonePatterns) {
            const matches = [...text.matchAll(pat)];
            for (const m of matches) {
                const full = m[0];
                // Skip if it looks like a zip code or year
                if (!full.startsWith('(0') && !full.startsWith('(1')) {
                    r.phone = full;
                    r.found = true;
                    break;
                }
            }
            if (r.phone) break;
        }

        // Get business name from the page title or heading
        const h1 = document.querySelector('h1');
        if (h1) {
            const h1text = h1.textContent.trim();
            if (h1text && h1text.length > 2 && h1text.length < 80) {
                r.name = h1text;
                r.found = true;
            }
        }

        // If we have rating or phone, mark as found
        if (r.rating > 0 || r.phone) r.found = true;

        return JSON.stringify(r);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and val.startswith('{'):
                    await drain(ws)
                    return json.loads(val), msg_id
        except (asyncio.TimeoutError, Exception):
            break

    await drain(ws)
    return {'found': False}, msg_id


async def click_first_result(ws, msg_id: int) -> int:
    """Click the first result in Maps search results to get detail page."""
    js = """
    (function() {
        // Click first result link in the feed
        const links = document.querySelectorAll('a[href*="/maps/place/"]');
        if (links.length > 0) {
            links[0].click();
            return 'clicked';
        }
        // Try div results
        const results = document.querySelectorAll('[role="feed"] > div');
        if (results.length > 0) {
            results[0].click();
            return 'clicked_div';
        }
        return 'no_results';
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                await drain(ws)
                return msg_id
        except (asyncio.TimeoutError, Exception):
            break

    await drain(ws)
    return msg_id


async def get_detail_info(ws, msg_id: int) -> tuple[dict, int]:
    """Extract detailed info from a Maps business detail page."""
    js = """
    (function() {
        const r = {name: '', phone: '', rating: 0, reviews: 0, address: '', has_website: false, found: false};

        // Business name from aria-label on main heading or h1
        const h1 = document.querySelector('h1');
        if (h1) {
            r.name = h1.textContent.trim();
        }

        // Rating from aria-label
        const ratingEl = document.querySelector('[role="img"][aria-label*="star"]');
        if (ratingEl) {
            const match = ratingEl.getAttribute('aria-label').match(/(\\d\\.\\d)/);
            if (match) r.rating = parseFloat(match[1]);
        }

        // Also try the text-based rating
        if (!r.rating) {
            const spans = document.querySelectorAll('span');
            for (const s of spans) {
                const ariaLabel = s.getAttribute('aria-label') || '';
                const match = ariaLabel.match(/(\\d\\.\\d)\\s*stars?/);
                if (match) {
                    r.rating = parseFloat(match[1]);
                    break;
                }
            }
        }

        // Reviews count
        const text = document.body?.innerText || '';
        const revMatch = text.match(/(\\d[\\d,]*)\\s*(?:reviews?|Google reviews?)/i);
        if (revMatch) r.reviews = parseInt(revMatch[1].replace(',', ''));

        // Phone - look for tel: links or phone pattern in buttons/info area
        const telLinks = document.querySelectorAll('a[href^="tel:"]');
        if (telLinks.length > 0) {
            const href = telLinks[0].href;
            const digits = href.replace(/\\D/g, '').slice(-10);
            if (digits.length === 10) {
                r.phone = '(' + digits.substr(0,3) + ') ' + digits.substr(3,3) + '-' + digits.substr(6,4);
            }
        }

        // Also look for phone in aria-labels (Maps shows phone in button aria-label)
        if (!r.phone) {
            const buttons = document.querySelectorAll('button[aria-label*="Phone"], button[data-tooltip*="phone"]');
            for (const btn of buttons) {
                const label = btn.getAttribute('aria-label') || btn.getAttribute('data-tooltip') || '';
                const phoneMatch = label.match(/\\(?(\\d{3})\\)?[\\s.-]?(\\d{3})[\\s.-]?(\\d{4})/);
                if (phoneMatch) {
                    r.phone = phoneMatch[0];
                    break;
                }
            }
        }

        // Phone from text (common in Maps detail)
        if (!r.phone) {
            const phoneRegex = /\\(?(\\d{3})\\)?[\\s.-](\\d{3})[\\s.-](\\d{4})/g;
            const matches = [...text.matchAll(phoneRegex)];
            for (const m of matches) {
                // Filter out obvious non-phone numbers
                if (!m[0].includes('(0') && !m[0].includes('(1')) {
                    r.phone = m[0];
                    break;
                }
            }
        }

        // Check for website
        const websiteBtn = document.querySelector('a[data-item-id="authority"], a[aria-label*="Website"]');
        if (websiteBtn) r.has_website = true;
        // Also check for website link in buttons
        const allBtns = document.querySelectorAll('a[aria-label]');
        for (const btn of allBtns) {
            const label = (btn.getAttribute('aria-label') || '').toLowerCase();
            if (label.includes('website') || label.includes('open website')) {
                r.has_website = true;
                break;
            }
        }

        if (r.name || r.phone || r.rating) r.found = true;
        return JSON.stringify(r);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js}
    }))
    msg_id += 1

    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and val.startswith('{'):
                    await drain(ws)
                    return json.loads(val), msg_id
        except (asyncio.TimeoutError, Exception):
            break

    await drain(ws)
    return {'found': False}, msg_id


async def main():
    with open(f'{BASE_DIR}/new_targets_batch2.json', 'r', encoding='utf-8') as f:
        targets = json.load(f)

    print(f"Enriching {len(targets)} targets via Google Maps...\n")

    ws_url = get_ws_url()
    msg_id = 1
    enriched = 0
    skipped_has_site = 0

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i, target in enumerate(targets):
            handle = target.get('ig', '').lstrip('@')
            search_name = clean_search_name(target)
            location = target.get('location', 'Miami FL')
            category = target.get('category', '')

            # Build search query: business name + location
            query = f"{search_name} {category} {location}"

            print(f"[{i+1}/{len(targets)}] @{handle} -> \"{query[:50]}\"...", end=' ', flush=True)

            try:
                # Search Google Maps
                info, msg_id = await search_gmaps(ws, query, msg_id)

                # If no results from initial page, try clicking first result
                if not info.get('found'):
                    msg_id = await click_first_result(ws, msg_id)
                    await asyncio.sleep(2.5)
                    await drain(ws)
                    info, msg_id = await get_detail_info(ws, msg_id)

                if info.get('found'):
                    # Check if this business has a website (skip those)
                    if info.get('has_website'):
                        skipped_has_site += 1
                        print(f"HAS WEBSITE - keeping for now", flush=True)

                    # Update target with Maps data
                    if info.get('name') and len(info['name']) > 2:
                        # Only update name if current name is garbage
                        current_name = target.get('name', '')
                        if (current_name.startswith('Followed by') or
                            current_name == handle or
                            '.' in current_name and ' ' not in current_name):
                            target['name'] = info['name']

                    if info.get('phone') and not target.get('phone'):
                        target['phone'] = info['phone']

                    if info.get('rating', 0) > 0:
                        target['rating'] = info['rating']

                    if info.get('reviews', 0) > 0:
                        target['reviews'] = info['reviews']

                    enriched += 1
                    print(f"FOUND: {info.get('name', '')[:25]} | {info.get('phone', 'no phone')} | {info.get('rating', 0)}★ ({info.get('reviews', 0)})", flush=True)
                else:
                    print(f"NOT FOUND on Maps", flush=True)

            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            await asyncio.sleep(2)

    # Save enriched data
    with open(f'{BASE_DIR}/new_targets_batch2.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    with_phone = sum(1 for t in targets if t.get('phone'))
    with_rating = sum(1 for t in targets if t.get('rating', 0) > 0)
    print(f"\n{'='*50}")
    print(f"Done! Enriched {enriched}/{len(targets)} from Google Maps")
    print(f"  With phone: {with_phone}")
    print(f"  With rating: {with_rating}")
    print(f"  Had website on Maps: {skipped_has_site}")


if __name__ == '__main__':
    asyncio.run(main())
