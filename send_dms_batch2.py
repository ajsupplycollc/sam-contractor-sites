import json, time, random, sys, asyncio, subprocess, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'websockets', '-q'])
    import websockets

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
GOG = r'C:\Users\ajsup\gogcli\gog.exe'
SHEET_ID = '1Fdfh-s3fF32l5FwxqGm3jeKS9_6B0NF07lx1q5TFrLM'
SHEET_START_ROW = 51  # batch 2 starts at row 51

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
            if 'instagram.com' in url and 'omnibox' not in url:
                return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
            url = tab.get('url', '')
            if not url.startswith('chrome://') or url == 'chrome://newtab/':
                return tab['webSocketDebuggerUrl']
    raise Exception("No available Chrome tab found")


def update_sheet_status(row_num: int, status: str, date: str) -> None:
    subprocess.run(
        [GOG, 'sheets', 'update', SHEET_ID, f'Sheet1!J{row_num}', status],
        capture_output=True, text=True
    )
    subprocess.run(
        [GOG, 'sheets', 'update', SHEET_ID, f'Sheet1!K{row_num}', date],
        capture_output=True, text=True
    )


async def drain(ws):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.3)
    except (asyncio.TimeoutError, Exception):
        pass


async def send_dm(ws, ig_handle: str, message: str, msg_id: int) -> tuple[bool, int]:
    # Navigate to profile
    print(f"    Navigating to @{ig_handle}...", flush=True)
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/{ig_handle}/"}
    }))
    msg_id += 1
    await asyncio.sleep(4)
    await drain(ws)

    # Follow if not already following
    print(f"    Checking follow status...", flush=True)
    follow_js = """
    (function() {
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            const txt = btn.textContent.trim();
            if (txt === 'Follow') { btn.click(); return 'followed'; }
            if (txt === 'Following' || txt === 'Requested') { return 'already_following'; }
        }
        const divBtns = document.querySelectorAll('div[role="button"]');
        for (const btn of divBtns) {
            const txt = btn.textContent.trim();
            if (txt === 'Follow') { btn.click(); return 'followed'; }
            if (txt === 'Following' || txt === 'Requested') { return 'already_following'; }
        }
        return 'no_follow_btn';
    })()
    """
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": follow_js}}))
    msg_id += 1

    follow_result = ''
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                follow_result = data['result']['result'].get('value', '')
                if follow_result: break
        except (asyncio.TimeoutError, Exception):
            break

    if follow_result == 'followed':
        print(f"    Followed @{ig_handle}", flush=True)
        await asyncio.sleep(2)
    elif follow_result == 'already_following':
        print(f"    Already following @{ig_handle}", flush=True)
    else:
        print(f"    Follow button: {follow_result}", flush=True)

    await drain(ws)

    # Click Message button
    print(f"    Clicking Message...", flush=True)
    click_js = """
    (function() {
        const buttons = document.querySelectorAll('div[role="button"]');
        for (const btn of buttons) {
            if (btn.textContent.trim() === 'Message') { btn.click(); return 'clicked'; }
        }
        const allBtns = document.querySelectorAll('button');
        for (const btn of allBtns) {
            if (btn.textContent.trim() === 'Message') { btn.click(); return 'clicked'; }
        }
        return 'not_found';
    })()
    """
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": click_js}}))
    msg_id += 1

    result = ''
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                result = data['result']['result'].get('value', '')
                if result: break
        except (asyncio.TimeoutError, Exception):
            break

    if result != 'clicked':
        print(f"    WARNING: Message button not found ({result})", flush=True)
        return False, msg_id

    await asyncio.sleep(3)
    await drain(ws)

    # Focus message input
    print(f"    Typing message...", flush=True)
    type_js = """
    (function() {
        const msgBox = document.querySelector('div[role="textbox"][contenteditable="true"]');
        if (msgBox) { msgBox.focus(); return 'focused_textbox'; }
        const ta = document.querySelector('textarea[placeholder*="Message"]') || document.querySelector('textarea');
        if (ta) { ta.focus(); return 'focused_textarea'; }
        return 'no_input_found';
    })()
    """
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": type_js}}))
    msg_id += 1

    input_type = ''
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(resp)
            if 'result' in data and 'result' in data.get('result', {}):
                input_type = data['result']['result'].get('value', '')
                if input_type: break
        except (asyncio.TimeoutError, Exception):
            break

    if 'no_input' in input_type or not input_type:
        print(f"    WARNING: No message input ({input_type})", flush=True)
        return False, msg_id

    await asyncio.sleep(0.5)

    # Type message line by line
    for line in message.split('\n'):
        await ws.send(json.dumps({"id": msg_id, "method": "Input.insertText", "params": {"text": line}}))
        msg_id += 1
        await asyncio.sleep(0.1)
        await ws.send(json.dumps({"id": msg_id, "method": "Input.dispatchKeyEvent", "params": {"type": "keyDown", "key": "Enter", "code": "Enter", "modifiers": 8}}))
        msg_id += 1
        await ws.send(json.dumps({"id": msg_id, "method": "Input.dispatchKeyEvent", "params": {"type": "keyUp", "key": "Enter", "code": "Enter", "modifiers": 8}}))
        msg_id += 1
        await asyncio.sleep(0.05)

    await asyncio.sleep(1)
    await drain(ws)

    # Send (Enter without modifiers)
    print(f"    Sending...", flush=True)
    await ws.send(json.dumps({"id": msg_id, "method": "Input.dispatchKeyEvent", "params": {"type": "keyDown", "key": "Enter", "code": "Enter"}}))
    msg_id += 1
    await ws.send(json.dumps({"id": msg_id, "method": "Input.dispatchKeyEvent", "params": {"type": "keyUp", "key": "Enter", "code": "Enter"}}))
    msg_id += 1

    await asyncio.sleep(2)
    await drain(ws)

    print(f"    SENT!", flush=True)
    return True, msg_id


async def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    with open(f'{BASE_DIR}/new_targets_batch2.json', 'r', encoding='utf-8') as f:
        targets = json.load(f)
    with open(f'{BASE_DIR}/short_links_batch2.json', 'r', encoding='utf-8') as f:
        links = json.load(f)

    ig_targets = [(t, l, i) for i, (t, l) in enumerate(zip(targets, links)) if t.get('ig')]
    ig_targets = ig_targets[start:]

    print(f"Sending {count} DMs (batch 2, starting from offset {start})...\n")
    print(f"Using 5 rotating scripts to avoid bot detection.\n")

    ws_url = get_ws_url()
    msg_id = 1
    sent = 0
    today = time.strftime('%Y-%m-%d')

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)

        for idx in range(min(count, len(ig_targets))):
            target, link, batch_idx = ig_targets[idx]
            ig = target['ig'].lstrip('@')
            friendly_name = get_friendly_name(target)
            script_num = idx % 5
            message = SCRIPTS[script_num].format(name=friendly_name, link=link['short_link'])
            sheet_row = SHEET_START_ROW + batch_idx

            print(f"[{idx+1}/{count}] @{ig} (Script {script_num+1})...", flush=True)

            try:
                success, msg_id = await send_dm(ws, ig, message, msg_id)

                if success:
                    sent += 1
                    update_sheet_status(sheet_row, 'Sent', today)
                    print(f"    Sheet updated: row {sheet_row} -> Sent\n", flush=True)
                else:
                    update_sheet_status(sheet_row, 'Failed', today)
                    print(f"    Sheet updated: row {sheet_row} -> Failed\n", flush=True)

            except Exception as e:
                print(f"    ERROR: {e}\n", flush=True)
                update_sheet_status(sheet_row, 'Error', today)
                try:
                    ws_url = get_ws_url()
                    ws = await websockets.connect(ws_url, max_size=5*1024*1024)
                    await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
                    msg_id += 1
                except Exception:
                    pass

            if idx < count - 1:
                delay = random.randint(20, 35)
                print(f"    Waiting {delay}s before next DM...\n", flush=True)
                await asyncio.sleep(delay)

    print(f"\nDone! Sent {sent}/{count} DMs successfully.")


if __name__ == '__main__':
    asyncio.run(main())
