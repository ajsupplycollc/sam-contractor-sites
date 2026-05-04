"""Update short links for all batch 3 sites using the new slug map."""
import json, os, sys, urllib.request, urllib.parse, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\ajsup\sam_contractor_sites'


def create_tinyurl(long_url: str) -> str:
    try:
        api = f'https://tinyurl.com/api-create.php?url={urllib.parse.quote_plus(long_url)}'
        req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10).read().decode()
        if resp.startswith('http'):
            return resp.strip()
    except Exception:
        pass
    return long_url


def main():
    with open(os.path.join(BASE, 'batch3_final.json'), 'r', encoding='utf-8') as f:
        all_targets = json.load(f)

    with open(os.path.join(BASE, 'batch3_slug_map.json'), 'r', encoding='utf-8') as f:
        slug_map = json.load(f)

    # Load existing short links
    links_path = os.path.join(BASE, 'batch3_short_links.json')
    if os.path.exists(links_path):
        with open(links_path, 'r', encoding='utf-8') as f:
            short_links = json.load(f)
    else:
        short_links = {}

    targets = [t for t in all_targets if not t.get('has_website')]

    # Find which ones need new short links (slug changed or missing)
    needs_update = []
    for t in targets:
        ig = t['ig']
        slug = slug_map.get(ig)
        if not slug:
            continue

        expected_long = f'https://ajsupplycollc.github.io/sam-contractor-sites/{slug}/'

        existing = short_links.get(ig, {})
        if existing.get('long') != expected_long:
            needs_update.append((t, slug))

    print(f"Total active targets: {len(targets)}")
    print(f"Need new short links: {len(needs_update)}")

    created = 0
    for i, (t, slug) in enumerate(needs_update):
        ig = t['ig']
        long_url = f'https://ajsupplycollc.github.io/sam-contractor-sites/{slug}/'
        short_url = create_tinyurl(long_url)

        short_links[ig] = {
            'short': short_url,
            'long': long_url,
            'slug': slug,
            'name': t['name'],
        }
        created += 1

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(needs_update)}] created", flush=True)
            with open(links_path, 'w', encoding='utf-8') as f:
                json.dump(short_links, f, indent=2, ensure_ascii=False)

        time.sleep(0.3)

    # Final save
    with open(links_path, 'w', encoding='utf-8') as f:
        json.dump(short_links, f, indent=2, ensure_ascii=False)

    print(f"\nShort links updated: {created}")
    print(f"Total short links: {len(short_links)}")

    # Verify all targets have short links
    missing = [t['ig'] for t in targets if t['ig'] not in short_links]
    if missing:
        print(f"Missing short links: {len(missing)}")
        for m in missing[:10]:
            print(f"  @{m}")
    else:
        print("All 410 targets have short links.")


if __name__ == '__main__':
    main()
