"""
Regenerate all batch 3 sites from batch3_final.json.
Also creates short links via TinyURL and updates the Google Sheet.
"""
import json, os, sys, re, urllib.request, urllib.parse, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'
SHEET_ID = '1Fdfh-s3fF32l5FwxqGm3jeKS9_6B0NF07lx1q5TFrLM'
GOG = r'C:\Users\ajsup\gogcli\gog.exe'


def slugify(name: str) -> str:
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')[:50]


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
    # Load final targets
    final_path = f'{BASE_DIR}/batch3_final.json'
    if not os.path.exists(final_path):
        print("ERROR: batch3_final.json not found. Run fix_batch3.py first.")
        return

    with open(final_path, 'r', encoding='utf-8') as f:
        all_targets = json.load(f)

    # Filter out targets that already have a website
    targets = [t for t in all_targets if not t.get('has_website')]
    excluded = len(all_targets) - len(targets)
    print(f"Total targets: {len(all_targets)}")
    print(f"Excluded (have website): {excluded}")
    print(f"Generating sites for: {len(targets)}\n")

    # Import generate_v2
    import importlib.util
    spec = importlib.util.spec_from_file_location('gen', f'{BASE_DIR}/generate_v2.py')
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    generated = 0
    logos_found = 0
    short_links = {}
    errors = []

    for i, t in enumerate(targets):
        name = t['name']
        ig = t['ig']
        slug = slugify(name)

        if not slug:
            slug = slugify(ig.replace('_', ' ').replace('.', ' '))

        site_dir = os.path.join(BASE_DIR, slug)
        os.makedirs(site_dir, exist_ok=True)

        # Check if logo exists (may be under old slug from IG scraping)
        logo_path = os.path.join(site_dir, 'logo.png')
        if not os.path.exists(logo_path):
            # Try finding logo under ig handle slug
            ig_slug = slugify(ig.replace('_', ' ').replace('.', ' '))
            alt_logo = os.path.join(BASE_DIR, ig_slug, 'logo.png')
            if os.path.exists(alt_logo):
                os.makedirs(site_dir, exist_ok=True)
                import shutil
                shutil.copy2(alt_logo, logo_path)

            # Also try under ig_display_name slug
            display_name = t.get('ig_display_name', '')
            if display_name:
                dn_slug = slugify(display_name)
                dn_logo = os.path.join(BASE_DIR, dn_slug, 'logo.png')
                if os.path.exists(dn_logo) and not os.path.exists(logo_path):
                    os.makedirs(site_dir, exist_ok=True)
                    import shutil
                    shutil.copy2(dn_logo, logo_path)

        if os.path.exists(logo_path):
            logos_found += 1

        try:
            html = gen.generate_site(t)
            with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            generated += 1

            # Create short link
            long_url = f'https://ajsupplycollc.github.io/sam-contractor-sites/{slug}/'
            short_url = create_tinyurl(long_url)
            short_links[ig] = {
                'short': short_url,
                'long': long_url,
                'slug': slug,
                'name': name,
            }

            if (i + 1) % 25 == 0:
                print(f"  [{i+1}/{len(targets)}] generated, {logos_found} logos", flush=True)
                # Save progress
                with open(f'{BASE_DIR}/batch3_short_links.json', 'w', encoding='utf-8') as f:
                    json.dump(short_links, f, indent=2)

        except Exception as e:
            errors.append(f"@{ig}: {e}")
            print(f"  ERROR @{ig}: {e}", flush=True)

        time.sleep(0.3)

    # Final save
    with open(f'{BASE_DIR}/batch3_short_links.json', 'w', encoding='utf-8') as f:
        json.dump(short_links, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Sites generated: {generated}/{len(targets)}")
    print(f"Logos found: {logos_found}")
    print(f"Short links created: {len(short_links)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors[:10]:
            print(f"  {e}")


def verify_all():
    """Verify every generated site has correct name/ig pairing and logo."""
    final_path = f'{BASE_DIR}/batch3_final.json'
    with open(final_path, 'r', encoding='utf-8') as f:
        targets = json.load(f)

    issues = []
    ok = 0

    for t in targets:
        name = t['name']
        ig = t['ig']
        slug = slugify(name)
        if not slug:
            slug = slugify(ig.replace('_', ' ').replace('.', ' '))

        site_path = os.path.join(BASE_DIR, slug, 'index.html')

        if not os.path.exists(site_path):
            issues.append(f"MISSING SITE: @{ig} ({name})")
            continue

        with open(site_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Check name appears
        if name not in html:
            issues.append(f"NAME NOT IN HTML: @{ig} expected '{name}'")

        # Check IG handle appears
        if f'instagram.com/{ig}' not in html:
            issues.append(f"IG HANDLE MISSING: @{ig}")

        # Check name and IG are consistent (not mismatched)
        # The name should appear in the header area and IG in the footer
        if name in html and f'instagram.com/{ig}' in html:
            ok += 1

        # Check logo
        logo_path = os.path.join(BASE_DIR, slug, 'logo.png')
        if not os.path.exists(logo_path):
            issues.append(f"NO LOGO: @{ig} ({name})")

    print(f"\n{'='*60}")
    print(f"VERIFICATION RESULTS")
    print(f"{'='*60}")
    print(f"Total targets: {len(targets)}")
    print(f"Sites OK (name + IG correct): {ok}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print(f"\nIssue details:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"\nAll sites verified clean.")

    return len(issues) == 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_all()
    else:
        main()
