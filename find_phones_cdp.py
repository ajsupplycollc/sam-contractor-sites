import json, time, re, sys, asyncio
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

import urllib.parse, urllib.request

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
PHONE_RE = re.compile(r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}')


def get_ws_url() -> str:
    """Get the WebSocket URL for the first Chrome tab."""
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            return tab['webSocketDebuggerUrl']
    raise Exception("No available Chrome tab found")


async def search_and_extract(ws, query: str, msg_id: int) -> tuple[str, float, int]:
    """Navigate to Google search and extract phone/rating/reviews from page text."""
    url = f'https://www.google.com/search?q={urllib.parse.quote_plus(query)}'

    # Navigate
    await ws.send(json.dumps({
        "id": msg_id,
        "method": "Page.navigate",
        "params": {"url": url}
    }))
    msg_id += 1

    # Wait for load
    await asyncio.sleep(3)

    # Get page text
    await ws.send(json.dumps({
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {"expression": "document.body.innerText"}
    }))
    msg_id += 1

    # Read responses
    page_text = ''
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                val = data['result']['result'].get('value', '')
                if val and len(val) > 100:
                    page_text = val
                    break
        except asyncio.TimeoutError:
            break
        except Exception:
            break

    if not page_text:
        return '', 0, 0, msg_id

    # Extract phone
    phone = ''
    phones = PHONE_RE.findall(page_text)
    for p in phones:
        clean = re.sub(r'[^\d]', '', p)
        if len(clean) == 10 and clean[0] not in ('0', '1'):
            phone = f'({clean[:3]}) {clean[3:6]}-{clean[6:]}'
            break

    # Extract rating
    rating = 0.0
    rating_match = re.search(r'(\d\.\d)\s*(?:\(\d+\)|\n)', page_text)
    if not rating_match:
        rating_match = re.search(r'Rating[:\s]*(\d\.\d)', page_text)
    if rating_match:
        rating = float(rating_match.group(1))

    # Extract review count
    review_count = 0
    review_match = re.search(r'\((\d+)\)\s*(?:Google reviews?|reviews?)', page_text, re.IGNORECASE)
    if not review_match:
        review_match = re.search(r'(\d+)\s+(?:Google\s+)?reviews?', page_text, re.IGNORECASE)
    if review_match:
        review_count = int(review_match.group(1))

    return phone, rating, review_count, msg_id


async def main():
    with open(f'{BASE_DIR}/master_targets.json', 'r', encoding='utf-8') as f:
        targets = json.load(f)

    missing = [t for t in targets if not t.get('phone')]
    print(f"Searching for phone numbers for {len(missing)} businesses via CDP...\n")

    ws_url = get_ws_url()
    print(f"Connected to Chrome: {ws_url[:60]}...\n")

    found_count = 0
    rating_found = 0
    msg_id = 1

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        # Enable Page domain
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)

        for i, target in enumerate(missing):
            name = target['name']
            location = target.get('location', 'Miami, FL')
            query = f'{name} {location}'

            print(f"[{i+1}/{len(missing)}] {name}...", end=' ', flush=True)

            try:
                phone, rating, reviews, msg_id = await search_and_extract(ws, query, msg_id)

                if phone:
                    target['phone'] = phone
                    found_count += 1
                    print(f"FOUND: {phone}", end='')
                else:
                    print("no phone", end='')

                if rating and not target.get('rating'):
                    target['rating'] = rating
                    rating_found += 1
                    print(f" | rating={rating}", end='')
                if reviews and (not target.get('reviews') or reviews > target.get('reviews', 0)):
                    target['reviews'] = reviews
                    print(f" | reviews={reviews}", end='')

                print(flush=True)

            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                # Reconnect if needed
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            # Delay between searches
            await asyncio.sleep(3)

    # Update master_targets.json
    missing_map = {t['name']: t for t in missing}
    for t in targets:
        if t['name'] in missing_map:
            updated = missing_map[t['name']]
            if updated.get('phone') and not t.get('phone'):
                t['phone'] = updated['phone']
            if updated.get('rating') and not t.get('rating'):
                t['rating'] = updated['rating']
            if updated.get('reviews') and (not t.get('reviews') or updated.get('reviews', 0) > t.get('reviews', 0)):
                t['reviews'] = updated['reviews']

    with open(f'{BASE_DIR}/master_targets.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Found {found_count} phone numbers, {rating_found} new ratings.")
    print("Updated master_targets.json")


if __name__ == '__main__':
    asyncio.run(main())
