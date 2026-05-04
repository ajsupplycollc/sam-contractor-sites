"""
Process a single chunk of targets for the scaled SAM pipeline.
Run by a subagent: python process_single_chunk.py chunk_N.json

For each target in the chunk:
  1. Generate site HTML (generate_v2.py)
  2. Create TinyURL short link
  3. Update Google Sheet row
  4. Write site to disk

No CDP/browser needed — this is pure generation + API calls.
"""
import json, os, sys, subprocess, re, urllib.request, urllib.parse, time, random

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GOG = r'C:\Users\ajsup\gogcli\gog.exe'

# Import site generator
sys.path.insert(0, r'C:\Users\ajsup\sam_contractor_sites')
from generate_v2 import generate_site, slugify, HERO_IMAGES, SCHEMES


def create_short_link(slug: str) -> str:
    base_url = f"https://ajsupplycollc.github.io/sam-contractor-sites/{slug}/"
    alias = f"sam-{slug}"[:30]
    try:
        api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(base_url, safe='')}&alias={alias}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        short = resp.read().decode().strip()
        if short.startswith('http'):
            return short
    except Exception:
        pass
    # Fallback: no alias
    try:
        api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(base_url, safe='')}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        short = resp.read().decode().strip()
        if short.startswith('http'):
            return short
    except Exception:
        pass
    return base_url


def update_sheet_row(sheet_id: str, row: int, target: dict, short_link: str):
    values = (
        f"{target['name']}|{target['category']}|{target['location']}|"
        f"{target.get('phone', '')}|@{target['ig']}|{target.get('rating', '')}|"
        f"{target.get('reviews', '')}|{short_link}|Live|Not Sent"
    )
    result = subprocess.run(
        [GOG, 'sheets', 'update', sheet_id, f'Sheet1!A{row}:J{row}', values],
        capture_output=True, text=True, encoding='utf-8'
    )
    return 'Updated' in result.stdout


def main():
    if len(sys.argv) < 2:
        print("Usage: python process_single_chunk.py chunk_N.json")
        sys.exit(1)

    chunk_file = sys.argv[1]
    if not os.path.isabs(chunk_file):
        chunk_file = os.path.join(r'C:\Users\ajsup\sam_contractor_sites', chunk_file)

    with open(chunk_file, 'r', encoding='utf-8') as f:
        chunk = json.load(f)

    chunk_id = chunk['chunk_id']
    targets = chunk['targets']
    sheet_start = chunk['sheet_start_row']
    sheet_id = chunk['sheet_id']
    base_dir = chunk['base_dir']

    print(f"=== Chunk {chunk_id}: Processing {len(targets)} targets ===")
    print(f"Sheet rows: {sheet_start} to {sheet_start + len(targets) - 1}")

    results = {"processed": 0, "failed": 0, "short_links": {}}

    for i, target in enumerate(targets):
        row = sheet_start + i
        slug = slugify(target['name'])
        site_dir = os.path.join(base_dir, slug)

        print(f"  [{i+1}/{len(targets)}] {target['name']} (@{target['ig']}) -> {slug}", end=' ', flush=True)

        try:
            # Generate site
            os.makedirs(site_dir, exist_ok=True)
            html = generate_site(target)
            with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)

            # Create short link
            short_link = create_short_link(slug)
            results['short_links'][slug] = short_link

            # Update sheet
            update_sheet_row(sheet_id, row, target, short_link)

            results['processed'] += 1
            print(f"OK ({short_link})", flush=True)

        except Exception as e:
            results['failed'] += 1
            print(f"FAILED: {e}", flush=True)

        time.sleep(random.uniform(0.5, 1.5))

    # Save chunk results
    results_file = os.path.join(base_dir, f'chunk_{chunk_id}_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n=== Chunk {chunk_id} complete: {results['processed']} processed, {results['failed']} failed ===")


if __name__ == '__main__':
    main()
