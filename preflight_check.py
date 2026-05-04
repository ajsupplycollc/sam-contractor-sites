"""
Preflight check for SAM DM batches.
Validates all targets BEFORE DMs fire. Blocks if critical issues found.
Run: python preflight_check.py [targets_json] [links_json]
"""
import json, os, sys, re, urllib.request, asyncio, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

CATEGORY_KEYWORDS = {
    'Pressure Washing': ['pressure', 'wash', 'soft wash', 'power wash', 'clean'],
    'Fence Contractor': ['fence'],
    'Flooring': ['floor', 'flooring'],
    'Roofing': ['roof'],
    'Painting': ['paint'],
    'Pool Service': ['pool'],
    'Plumbing': ['plumb'],
    'Electrical': ['electric'],
    'Landscaping': ['landscape', 'landscap'],
    'Lawn Care': ['lawn'],
    'Tree Service': ['tree service', 'tree trim', 'tree remov'],
    'Concrete Contractor': ['concrete'],
    'Paver Installation': ['paver'],
    'HVAC': ['hvac', 'air condition', 'cooling', 'ac '],
    'Drywall': ['drywall'],
    'Garage Door': ['garage door'],
    'Window Cleaning': ['window clean'],
    'Cabinetry': ['cabinet'],
    'Junk Removal': ['junk'],
    'Moving Service': ['moving', 'mover'],
    'Handyman': ['handyman'],
    'Tile Contractor': ['tile'],
}

CATEGORY_IMAGES = {
    'Pressure Washing': ['photo-1720478664465-4dc6c66e4f6a', 'photo-1664840951038-caf513bcc639', 'photo-1645256418914-feb28d7ec701'],
    'Pressure Cleaning': ['photo-1720478664465-4dc6c66e4f6a', 'photo-1664840951038-caf513bcc639', 'photo-1645256418914-feb28d7ec701'],
    'Painting': ['photo-1572627614522-1c56af1d9d72', 'photo-1525909002-1b05e0c869d8'],
    'Roofing': ['photo-1632178050091-f5730a7cf20b', 'photo-1635048424329-a2b1dfb93a83'],
}


def slugify(name: str) -> str:
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def check_category(target: dict, idx: int) -> list:
    issues = []
    name = target['name'].lower()
    assigned_cat = target['category']

    for correct_cat, keywords in CATEGORY_KEYWORDS.items():
        if correct_cat == assigned_cat:
            continue
        for kw in keywords:
            if kw in name:
                if assigned_cat == 'Painting' and any(pw in name for pw in ['pressure', 'wash', 'clean']):
                    issues.append(f'CRITICAL: idx={idx} "{target["name"]}" has "{kw}" in name but category is "{assigned_cat}" (should be "{correct_cat}")')
                elif correct_cat == 'Pressure Washing' and assigned_cat == 'Window Cleaning' and 'window' in name:
                    pass  # Window Cleaning with "clean" keyword is fine
                elif correct_cat != 'Pressure Washing' or not any(skip in name for skip in ['window']):
                    issues.append(f'CRITICAL: idx={idx} "{target["name"]}" has "{kw}" in name but category is "{assigned_cat}" (should be "{correct_cat}")')
                break
    return issues


def check_site_exists(target: dict, idx: int) -> list:
    issues = []
    slug = slugify(target['name'])
    site_dir = os.path.join(BASE_DIR, slug)
    index_path = os.path.join(site_dir, 'index.html')

    if not os.path.exists(index_path):
        issues.append(f'CRITICAL: idx={idx} "{target["name"]}" - no index.html at {slug}/')
        return issues

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    og_match = re.search(r'og:image.*?content="(.*?)"', html)
    if og_match:
        img_url = og_match.group(1)
        photo_match = re.search(r'photo-[a-zA-Z0-9_-]+', img_url)
        if photo_match:
            photo_id = photo_match.group(0)
            cat = target['category']
            if cat in CATEGORY_IMAGES:
                if photo_id not in CATEGORY_IMAGES[cat]:
                    for wrong_cat, wrong_imgs in CATEGORY_IMAGES.items():
                        if wrong_cat != cat and photo_id in wrong_imgs:
                            issues.append(f'WARNING: idx={idx} "{target["name"]}" - hero image belongs to "{wrong_cat}" but target is "{cat}"')
                            break

    title_match = re.search(r'<title>(.*?)</title>', html)
    if title_match:
        title = title_match.group(1).lower()
        cat_lower = target['category'].lower()
        if cat_lower not in title and slugify(target['name']) not in title.replace(' ', '-'):
            pass  # Not necessarily an issue

    return issues


def check_short_link(link: dict, idx: int) -> list:
    issues = []
    url = link.get('short_link', '')
    if not url:
        issues.append(f'CRITICAL: idx={idx} "{link.get("name","")}" - no short_link')
        return issues

    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        resp = urllib.request.urlopen(req, timeout=10)
        if resp.status >= 400:
            issues.append(f'WARNING: idx={idx} short link {url} returned status {resp.status}')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            issues.append(f'CRITICAL: idx={idx} short link {url} returned 404')
        else:
            issues.append(f'WARNING: idx={idx} short link {url} returned {e.code}')
    except Exception as e:
        issues.append(f'WARNING: idx={idx} short link {url} failed: {str(e)[:50]}')

    return issues


def check_logo(target: dict, idx: int) -> list:
    issues = []
    slug = slugify(target['name'])
    logo_path = os.path.join(BASE_DIR, slug, 'logo.png')
    if not os.path.exists(logo_path):
        issues.append(f'WARNING: idx={idx} "{target["name"]}" - no logo.png at {slug}/')
    return issues


async def check_ig_websites(targets: list) -> list:
    """Re-verify IG profiles for website links. Requires Chrome debug active."""
    issues = []
    try:
        import websockets
        data = urllib.request.urlopen('http://localhost:9222/json').read()
        tabs = json.loads(data)
        ws_url = None
        for tab in tabs:
            if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
                url = tab.get('url', '')
                if 'instagram.com' in url:
                    ws_url = tab['webSocketDebuggerUrl']
                    break
        if not ws_url:
            for tab in tabs:
                if tab.get('type') == 'page' and 'webSocketDebuggerUrl' in tab:
                    url = tab.get('url', '')
                    if not url.startswith('chrome://') or url == 'chrome://newtab/':
                        ws_url = tab['webSocketDebuggerUrl']
                        break

        if not ws_url:
            issues.append('SKIP: No Chrome tab available for IG website check')
            return issues

        msg_id = 1
        async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
            for idx, t in enumerate(targets):
                ig = t.get('ig', '').lstrip('@')
                if not ig:
                    continue

                await ws.send(json.dumps({
                    "id": msg_id, "method": "Page.navigate",
                    "params": {"url": f"https://www.instagram.com/{ig}/"}
                }))
                msg_id += 1
                await asyncio.sleep(3)

                check_js = """
                (function() {
                    const links = document.querySelectorAll('a[href]');
                    for (const a of links) {
                        const href = a.href || '';
                        const text = (a.textContent || '').trim().toLowerCase();
                        if (href.includes('l.instagram.com/') ||
                            (a.closest && a.closest('[class*="bio"]')) ||
                            text.match(/\\.com|\\.net|\\.org|\\.io|www\\.|http/)) {
                            const display = a.textContent.trim();
                            if (display && !display.includes('instagram') &&
                                !display.includes('facebook') && display.length > 3) {
                                return 'HAS_WEBSITE:' + display;
                            }
                        }
                    }
                    const extLink = document.querySelector('a[rel*="nofollow"][target="_blank"]');
                    if (extLink) {
                        const t = extLink.textContent.trim();
                        if (t && !t.includes('instagram') && !t.includes('facebook')) {
                            return 'HAS_WEBSITE:' + t;
                        }
                    }
                    return 'NO_WEBSITE';
                })()
                """
                await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": check_js}}))
                msg_id += 1

                result = ''
                deadline = time.time() + 5
                while time.time() < deadline:
                    try:
                        resp = await asyncio.wait_for(ws.recv(), timeout=2)
                        data = json.loads(resp)
                        if 'result' in data and 'result' in data.get('result', {}):
                            result = data['result']['result'].get('value', '')
                            if result:
                                break
                    except (asyncio.TimeoutError, Exception):
                        break

                if result.startswith('HAS_WEBSITE:'):
                    website = result.replace('HAS_WEBSITE:', '')
                    issues.append(f'CRITICAL: idx={idx} @{ig} "{t["name"]}" HAS WEBSITE: {website}')

                await asyncio.sleep(1.5)

    except ImportError:
        issues.append('SKIP: websockets not installed for IG check')
    except Exception as e:
        issues.append(f'SKIP: IG website check failed: {str(e)[:80]}')

    return issues


def main():
    targets_file = sys.argv[1] if len(sys.argv) > 1 else f'{BASE_DIR}/new_targets_batch2.json'
    links_file = sys.argv[2] if len(sys.argv) > 2 else f'{BASE_DIR}/short_links_batch2.json'
    skip_ig = '--skip-ig' in sys.argv
    skip_links = '--skip-links' in sys.argv

    with open(targets_file, 'r', encoding='utf-8') as f:
        targets = json.load(f)
    with open(links_file, 'r', encoding='utf-8') as f:
        links = json.load(f)

    print(f"{'='*60}")
    print(f"  SAM PREFLIGHT CHECK")
    print(f"  Targets: {len(targets)} | Links: {len(links)}")
    print(f"{'='*60}\n")

    all_issues = []

    # 1. Category validation
    print("[1/5] Checking categories...", flush=True)
    for i, t in enumerate(targets):
        all_issues.extend(check_category(t, i))
    cat_issues = [x for x in all_issues if 'category' in x.lower() or 'CRITICAL' in x]
    print(f"      {len(cat_issues)} issues found\n")

    # 2. Site existence + image validation
    print("[2/5] Checking sites exist + correct images...", flush=True)
    site_issues_start = len(all_issues)
    for i, t in enumerate(targets):
        all_issues.extend(check_site_exists(t, i))
    site_issues = len(all_issues) - site_issues_start
    print(f"      {site_issues} issues found\n")

    # 3. Logo check
    print("[3/5] Checking logos...", flush=True)
    logo_start = len(all_issues)
    for i, t in enumerate(targets):
        all_issues.extend(check_logo(t, i))
    logo_issues = len(all_issues) - logo_start
    print(f"      {logo_issues} issues found\n")

    # 4. Short link validation
    if not skip_links:
        print("[4/5] Checking short links (HTTP)...", flush=True)
        link_start = len(all_issues)
        for i, l in enumerate(links[:len(targets)]):
            all_issues.extend(check_short_link(l, i))
            if (i + 1) % 10 == 0:
                print(f"      {i+1}/{len(targets)} checked...", flush=True)
        link_issues = len(all_issues) - link_start
        print(f"      {link_issues} issues found\n")
    else:
        print("[4/5] Short link check SKIPPED\n")

    # 5. IG website re-verification
    if not skip_ig:
        print("[5/5] Re-verifying IG profiles for websites (CDP)...", flush=True)
        ig_issues = asyncio.run(check_ig_websites(targets))
        all_issues.extend(ig_issues)
        ig_count = len([x for x in ig_issues if 'CRITICAL' in x])
        print(f"      {ig_count} targets now have websites\n")
    else:
        print("[5/5] IG website check SKIPPED\n")

    # Summary
    critical = [x for x in all_issues if 'CRITICAL' in x]
    warnings = [x for x in all_issues if 'WARNING' in x]
    skipped = [x for x in all_issues if 'SKIP' in x]

    print(f"{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  CRITICAL: {len(critical)}")
    print(f"  WARNING:  {len(warnings)}")
    print(f"  SKIPPED:  {len(skipped)}")
    print()

    if critical:
        print("CRITICAL ISSUES (must fix before DMs):")
        for issue in critical:
            print(f"  {issue}")
        print()

    if warnings:
        print("WARNINGS (review but non-blocking):")
        for issue in warnings:
            print(f"  {issue}")
        print()

    if skipped:
        print("SKIPPED CHECKS:")
        for issue in skipped:
            print(f"  {issue}")
        print()

    if critical:
        print(f"\n*** PREFLIGHT FAILED — {len(critical)} critical issues must be resolved ***")
        print("DMs should NOT fire until these are fixed.")
        return 1
    else:
        print("\n*** PREFLIGHT PASSED — clear to send DMs ***")
        return 0


if __name__ == '__main__':
    sys.exit(main())
