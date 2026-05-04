"""
Quick pass through IG profiles to extract display names, phone numbers, and bios.
Uses Chrome debug CDP.
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


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'instagram.com' in url or url == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            if not tab.get('url', '').startswith('chrome://') or tab.get('url') == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    raise Exception("No Chrome tab found")


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def get_profile_info(ws, handle: str, msg_id: int) -> tuple[dict, int]:
    """Visit IG profile and extract display name, phone, bio."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/{handle}/"}
    }))
    msg_id += 1
    await asyncio.sleep(3)
    await drain(ws)

    js = """
    (function() {
        const r = {name: '', phone: '', bio: '', location: ''};

        // Get header text (contains name, bio, everything)
        const header = document.querySelector('header');
        if (header) {
            r.bio = header.innerText || '';
        }

        // Get display name - try multiple selectors
        // The display name is usually in a span within the header section
        const headerSpans = document.querySelectorAll('header section span');
        for (const s of headerSpans) {
            const text = s.textContent.trim();
            // Display name is typically not a number and not the handle
            if (text.length > 2 && text.length < 60 &&
                !text.match(/^\\d/) && !text.includes('follower') &&
                !text.includes('following') && !text.includes('post') &&
                text !== handle) {
                // First non-handle, non-stat span is likely the display name
                if (!r.name || text.length > r.name.length) {
                    r.name = text;
                }
            }
        }

        // Try meta title for name
        if (!r.name) {
            const title = document.title || '';
            const match = title.match(/^(.+?)\\s*[(@|•]/);
            if (match) r.name = match[1].trim();
        }

        // Extract phone from bio text
        const bioText = r.bio;
        // US phone patterns
        const phonePatterns = [
            /\\(?(\\d{3})\\)?[\\s.-]?(\\d{3})[\\s.-]?(\\d{4})/,
            /(\\d{3})[\\s.-](\\d{3})[\\s.-](\\d{4})/,
        ];
        for (const pat of phonePatterns) {
            const match = bioText.match(pat);
            if (match) {
                r.phone = match[0].trim();
                break;
            }
        }

        // Also check for phone in link buttons
        const buttons = document.querySelectorAll('a[href*="tel:"], a[href*="wa.me"], a[href*="whatsapp"]');
        for (const btn of buttons) {
            const href = btn.href || '';
            const telMatch = href.match(/tel:[+]?1?(\\d{10})/);
            if (telMatch) {
                const d = telMatch[1];
                r.phone = '(' + d.substr(0,3) + ') ' + d.substr(3,3) + '-' + d.substr(6,4);
                break;
            }
            const waMatch = href.match(/wa\\.me\\/1?(\\d{10})/);
            if (waMatch) {
                const d = waMatch[1];
                r.phone = '(' + d.substr(0,3) + ') ' + d.substr(3,3) + '-' + d.substr(6,4);
                break;
            }
        }

        return JSON.stringify(r);
    })()
    """
    await ws.send(json.dumps({
        "id": msg_id, "method": "Runtime.evaluate",
        "params": {"expression": js.replace('handle', f'"{handle}"')}
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
    return {}, msg_id


async def main():
    with open(f'{BASE_DIR}/new_targets_batch2.json', 'r', encoding='utf-8') as f:
        targets = json.load(f)

    print(f"Enriching {len(targets)} IG profiles with names & phones...\n")

    ws_url = get_ws_url()
    msg_id = 1

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i, target in enumerate(targets):
            handle = target['ig'].lstrip('@')
            print(f"[{i+1}/{len(targets)}] @{handle}...", end=' ', flush=True)

            try:
                info, msg_id = await get_profile_info(ws, handle, msg_id)

                if info.get('name') and info['name'] != handle:
                    target['name'] = info['name']

                if info.get('phone'):
                    target['phone'] = info['phone']

                name_display = target['name'][:30] if target['name'] != handle else '(no name)'
                phone_display = target.get('phone', '') or 'no phone'
                print(f"{name_display} | {phone_display}", flush=True)

            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            await asyncio.sleep(1.5)

    # Save
    with open(f'{BASE_DIR}/new_targets_batch2.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    with_phone = sum(1 for t in targets if t.get('phone'))
    with_name = sum(1 for t in targets if t.get('name') and t['name'] != t['ig'].lstrip('@'))
    print(f"\nDone! {with_name} with display names, {with_phone} with phone numbers.")


if __name__ == '__main__':
    asyncio.run(main())
