"""
Scaled DM sender for overnight unattended operation.
Sends follow + DM via CDP for all targets with status 'Not Sent'.

Usage:
  python send_dms_scaled.py [targets_json] [links_json] [--offset N] [--limit N]

Requires: Chrome debug open (--remote-debugging-port=9222), logged into Instagram.
"""
import json, time, re, sys, asyncio, urllib.request, os, random, subprocess

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
GOG = r'C:\Users\ajsup\gogcli\gog.exe'
SHEET_ID = '1Fdfh-s3fF32l5FwxqGm3jeKS9_6B0NF07lx1q5TFrLM'

SCRIPTS = [
    'Hey {name}! I saw your work on here and it\'s solid. I noticed you don\'t have a website yet - I actually already built one for you as a sample. Check it out:\n\n{link}\n\nIt\'s mobile-friendly, has your phone number, reviews, services - everything a customer Googling you would want to see.\n\nIf you already have a domain, I can connect it there. If not, I can set you up with one - $500 flat, no monthly fees. Either way, the site is yours to look at. Let me know what you think.\n\n- Jereme, Strange Advanced Marketing',
    'What\'s up {name}! Your work caught my eye scrolling through. I do marketing for contractors and I went ahead and put together a sample website for your business - take a look:\n\n{link}\n\nIt\'s got your services, contact info, reviews, and it works on phones. If you\'ve got a domain already, I can link it up. If you need one, I\'ll handle that too - $500 one-time, no subscriptions. Figured it could help you land more jobs off Google. Lmk!\n\n- Jereme, SAM',
    'Hey {name} - your page is fire. I noticed you don\'t have a website so I went ahead and built you one as a free sample:\n\n{link}\n\nPhone number, services, reviews, Google Maps - all there and ready to go. If you want it on your own domain I can set that up for $500, no monthly costs. Already have a domain? Even easier. Just thought it\'d help you get more leads. Let me know!\n\n- Jereme, Strange Advanced Marketing',
    'Yo {name}! Found your page and the work speaks for itself. I build websites for contractors and I put together a free sample for you - check it:\n\n{link}\n\nIt\'s ready to go - mobile-friendly, your info, services, everything. If you want to put it on your own domain, $500 flat and it\'s done. Already own a domain? Even better, I\'ll hook it up. No monthly fees, no subscriptions. Hit me up if you\'re interested.\n\n- Jereme, SAM',
    'Hey {name}! I work with contractors on their online presence and your page stood out. I actually built a sample website for your business for free - here it is:\n\n{link}\n\nServices, phone, reviews, map - the whole thing. If you want it live on your own domain I can handle everything for $500, one-time. If you already own a domain, even simpler. Just wanted to show you what\'s possible. Let me know!\n\n- Jereme, Strange Advanced Marketing',
]


def get_friendly_name(target: dict) -> str:
    name = target['name']
    words = name.split()
    if len(words) <= 2:
        return name
    if any(w in name.lower() for w in ['llc', 'inc', 'corp', 'services']):
        return ' '.join(words[:2])
    return words[0]


def get_ws_url() -> str:
    data = urllib.request.urlopen('http://localhost:9222/json').read()
    tabs = json.loads(data)
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if 'instagram.com' in url:
                return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if not url.startswith('chrome://') or url == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    raise Exception("No available Chrome tab found")


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


async def evaluate_js(ws, js: str, msg_id: int, timeout: float = 10.0) -> tuple[str, int]:
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


async def follow_and_dm(ws, handle: str, message: str, msg_id: int) -> tuple[bool, int]:
    msg_id = await navigate_and_wait(ws, f"https://www.instagram.com/{handle}/", msg_id, wait=4.0)

    # Click follow button if present
    follow_js = """
    (function() {
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.textContent.trim() === 'Follow') {
                btn.click();
                return 'followed';
            }
        }
        return 'already_following_or_not_found';
    })()
    """
    val, msg_id = await evaluate_js(ws, follow_js, msg_id)
    await asyncio.sleep(2)

    # Click Message button
    msg_btn_js = """
    (function() {
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.textContent.trim() === 'Message') {
                btn.click();
                return 'clicked';
            }
        }
        const links = document.querySelectorAll('a');
        for (const a of links) {
            if (a.textContent.trim() === 'Message') {
                a.click();
                return 'clicked_link';
            }
        }
        return 'not_found';
    })()
    """
    val, msg_id = await evaluate_js(ws, msg_btn_js, msg_id)

    if 'not_found' in val:
        return False, msg_id

    await asyncio.sleep(3)

    # Type and send message
    escaped = message.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    type_js = f"""
    (function() {{
        const textarea = document.querySelector('textarea[placeholder*="Message"], div[contenteditable="true"][role="textbox"]');
        if (!textarea) return 'no_textarea';
        textarea.focus();
        document.execCommand('insertText', false, '{escaped}');
        textarea.dispatchEvent(new Event('input', {{bubbles: true}}));
        return 'typed';
    }})()
    """
    val, msg_id = await evaluate_js(ws, type_js, msg_id)

    if val == 'no_textarea':
        return False, msg_id

    await asyncio.sleep(1)

    send_js = """
    (function() {
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.textContent.trim() === 'Send') {
                btn.click();
                return 'sent';
            }
        }
        // Try keyboard Enter
        const textarea = document.querySelector('textarea, div[contenteditable="true"][role="textbox"]');
        if (textarea) {
            textarea.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', bubbles: true}));
            return 'enter_sent';
        }
        return 'no_send_button';
    })()
    """
    val, msg_id = await evaluate_js(ws, send_js, msg_id)
    await asyncio.sleep(2)

    return 'sent' in val or 'enter' in val, msg_id


def update_dm_status(sheet_row: int, status: str):
    from datetime import datetime
    date_str = datetime.now().strftime('%Y-%m-%d')
    subprocess.run(
        [GOG, 'sheets', 'update', SHEET_ID, f'Sheet1!J{sheet_row}:K{sheet_row}', f'{status}|{date_str}'],
        capture_output=True, text=True
    )


async def main():
    targets_file = sys.argv[1] if len(sys.argv) > 1 else 'scaled_targets.json'
    links_file = sys.argv[2] if len(sys.argv) > 2 else 'scaled_short_links.json'

    offset = 0
    limit = 9999
    for i, arg in enumerate(sys.argv):
        if arg == '--offset' and i + 1 < len(sys.argv):
            offset = int(sys.argv[i + 1])
        if arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    targets_path = os.path.join(BASE_DIR, targets_file)
    links_path = os.path.join(BASE_DIR, links_file)

    with open(targets_path, 'r', encoding='utf-8') as f:
        all_targets = json.load(f)

    short_links = {}
    if os.path.exists(links_path):
        with open(links_path, 'r', encoding='utf-8') as f:
            short_links = json.load(f)

    # Find sheet start row for these targets
    # Read sheet to find where these targets start
    result = subprocess.run(
        [GOG, 'sheets', 'get', SHEET_ID, 'Sheet1!A:J'],
        capture_output=True, text=True, encoding='utf-8'
    )
    sheet_lines = result.stdout.strip().split('\n')
    ig_to_row = {}
    for row_idx, line in enumerate(sheet_lines):
        cols = line.split('\t') if '\t' in line else re.split(r'\s{2,}', line)
        for col in cols:
            if col.strip().startswith('@'):
                ig_to_row[col.strip().lstrip('@').lower()] = row_idx + 1

    targets = all_targets[offset:offset + limit]
    print(f"=== Scaled DM Sender ===")
    print(f"Targets: {len(targets)} (offset {offset}, limit {limit})")
    print(f"Short links loaded: {len(short_links)}")
    print()

    ws_url = get_ws_url()
    msg_id = 1
    sent = 0
    failed = 0

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i, target in enumerate(targets):
            handle = target['ig']
            name = get_friendly_name(target)

            from generate_v2 import slugify
            slug = slugify(target['name'])
            link = short_links.get(slug, f"https://ajsupplycollc.github.io/sam-contractor-sites/{slug}/")

            script = random.choice(SCRIPTS).format(name=name, link=link)

            print(f"[{i+1}/{len(targets)}] @{handle} ({name})...", end=' ', flush=True)

            try:
                success, msg_id = await follow_and_dm(ws, handle, script, msg_id)
                sheet_row = ig_to_row.get(handle.lower(), 0)

                if success:
                    sent += 1
                    if sheet_row:
                        update_dm_status(sheet_row, 'Sent')
                    print(f"SENT ({sent} total)", flush=True)
                else:
                    failed += 1
                    if sheet_row:
                        update_dm_status(sheet_row, 'Failed')
                    print(f"FAILED ({failed} total)", flush=True)

            except Exception as e:
                failed += 1
                print(f"ERROR: {e}", flush=True)
                await asyncio.sleep(3)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    print("  Could not reconnect. Waiting 30s...", flush=True)
                    await asyncio.sleep(30)

            delay = random.uniform(20, 35)
            print(f"  Waiting {delay:.0f}s...", flush=True)
            await asyncio.sleep(delay)

    print(f"\n{'=' * 60}")
    print(f"DM run complete: {sent} sent, {failed} failed out of {len(targets)}")


if __name__ == '__main__':
    asyncio.run(main())
