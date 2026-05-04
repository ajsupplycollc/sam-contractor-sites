"""
Visit each IG profile via CDP to:
1. Download profile picture as logo.png
2. Extract proper display name
3. Extract phone from bio if present
Saves logos to each target's site directory.
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


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')[:50]


async def scrape_ig_profile(ws, handle: str, msg_id: int) -> tuple[dict, int]:
    """Visit IG profile and extract name, phone, profile pic URL."""
    await ws.send(json.dumps({
        "id": msg_id, "method": "Page.navigate",
        "params": {"url": f"https://www.instagram.com/{handle}/"}
    }))
    msg_id += 1
    await asyncio.sleep(3.5)
    await drain(ws)

    js = """
    (function() {
        const r = {name: '', phone: '', bio: '', pic_url: ''};

        // Get profile picture URL - it's in an img tag within header
        const imgs = document.querySelectorAll('header img, img[alt*="profile picture"]');
        for (const img of imgs) {
            const alt = (img.alt || '').toLowerCase();
            const src = img.src || '';
            if (src.includes('cdninstagram') || src.includes('fbcdn') || src.includes('scontent')) {
                // Get the highest res version
                if (!r.pic_url || img.width > 100) {
                    r.pic_url = src;
                }
            }
        }

        // Also check for profile pic in any img with profile-related alt text
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

        // Get display name from meta title
        const title = document.title || '';
        const titleMatch = title.match(/^(.+?)\\s*[(@|•]/);
        if (titleMatch) {
            r.name = titleMatch[1].trim();
        }

        // Also try the header section for name
        const header = document.querySelector('header');
        if (header) {
            const headerText = header.innerText || '';
            r.bio = headerText;

            // Name is usually in a specific span - try meta description too
            const metaDesc = document.querySelector('meta[name="description"]');
            if (metaDesc) {
                const content = metaDesc.getAttribute('content') || '';
                // Format: "123 Followers, 456 Following, 789 Posts - See Instagram photos and videos from Business Name (@handle)"
                const descMatch = content.match(/from\\s+(.+?)\\s*\\(@/);
                if (descMatch) {
                    r.name = descMatch[1].trim();
                }
            }
        }

        // Extract phone from bio
        const bioText = r.bio || document.body?.innerText || '';
        const phonePatterns = [
            /\\(?(\\d{3})\\)?[\\s.-]?(\\d{3})[\\s.-]?(\\d{4})/
        ];
        for (const pat of phonePatterns) {
            const match = bioText.match(pat);
            if (match) {
                r.phone = match[0].trim();
                break;
            }
        }

        // Check tel: links
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
    return {}, msg_id


def download_image(url: str, save_path: str) -> bool:
    """Download an image URL to local path."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        data = urllib.request.urlopen(req, timeout=10).read()
        if len(data) > 1000:  # sanity check - at least 1KB
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        pass
    return False


async def main():
    with open(f'{BASE_DIR}/new_targets_batch2.json', 'r', encoding='utf-8') as f:
        targets = json.load(f)

    print(f"Scraping IG profiles for {len(targets)} targets (logos + names + phones)...\n")

    ws_url = get_ws_url()
    msg_id = 1
    logos_downloaded = 0
    names_fixed = 0
    phones_found = 0

    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": msg_id, "method": "Page.enable"}))
        msg_id += 1
        await asyncio.sleep(0.5)
        await drain(ws)

        for i, target in enumerate(targets):
            handle = target.get('ig', '').lstrip('@')
            name = target.get('name', handle)
            slug = slugify(name if name != handle else handle.replace('_', ' ').replace('.', ' '))

            print(f"[{i+1}/{len(targets)}] @{handle}...", end=' ', flush=True)

            try:
                info, msg_id = await scrape_ig_profile(ws, handle, msg_id)

                # Update name if we got a better one
                if info.get('name') and len(info['name']) > 2:
                    current_name = target.get('name', '')
                    if (current_name.startswith('Followed by') or
                        current_name == handle or
                        len(info['name']) > len(current_name)):
                        target['name'] = info['name']
                        names_fixed += 1
                        # Recalculate slug with new name
                        slug = slugify(info['name'])

                # Update phone
                if info.get('phone') and not target.get('phone'):
                    target['phone'] = info['phone']
                    phones_found += 1

                # Download logo
                logo_dir = os.path.join(BASE_DIR, slug)
                logo_path = os.path.join(logo_dir, 'logo.png')

                if info.get('pic_url') and not os.path.exists(logo_path):
                    if download_image(info['pic_url'], logo_path):
                        logos_downloaded += 1
                        print(f"✓ logo", end=' ')
                    else:
                        print(f"x logo", end=' ')

                display_name = target.get('name', handle)[:30]
                phone_display = target.get('phone', '') or 'no phone'
                print(f"| {display_name} | {phone_display}", flush=True)

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

    # Save updated targets
    with open(f'{BASE_DIR}/new_targets_batch2.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Done!")
    print(f"  Logos downloaded: {logos_downloaded}")
    print(f"  Names fixed: {names_fixed}")
    print(f"  Phones found: {phones_found}")


if __name__ == '__main__':
    asyncio.run(main())
