"""
Find contractor IG targets via Google search + headless IG profile check.
No Chrome debug needed — runs fully in Playwright headless.
Phase 1: Google search for "site:instagram.com [contractor] [area]"
Phase 2: Visit each IG profile to check for website/bio
"""
import json, time, re, sys, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

SEARCH_QUERIES = [
    "site:instagram.com miami handyman no website",
    "site:instagram.com miami pressure washing",
    "site:instagram.com south florida pressure cleaning",
    "site:instagram.com miami fence contractor",
    "site:instagram.com miami landscaping service",
    "site:instagram.com miami lawn care",
    "site:instagram.com miami tree service",
    "site:instagram.com miami pool service",
    "site:instagram.com south florida painting contractor",
    "site:instagram.com miami concrete contractor",
    "site:instagram.com miami junk removal",
    "site:instagram.com miami tile installer",
    "site:instagram.com miami roofing",
    "site:instagram.com south florida plumber",
    "site:instagram.com miami electrician",
    "site:instagram.com south florida flooring",
    "site:instagram.com miami paver installer",
    "site:instagram.com miami moving company",
    "site:instagram.com broward handyman",
    "site:instagram.com fort lauderdale pressure washing",
    "site:instagram.com miami drywall",
    "site:instagram.com miami stucco",
    "site:instagram.com south florida epoxy flooring",
    "site:instagram.com miami screen enclosure",
    "site:instagram.com miami gutter cleaning",
    "site:instagram.com hialeah contractor",
    "site:instagram.com homestead contractor",
    "site:instagram.com miami gardens handyman",
    "site:instagram.com pembroke pines contractor",
    "site:instagram.com miami sprinkler irrigation",
]

CATEGORY_MAP = {
    'handyman': 'Handyman', 'pressure': 'Pressure Washing',
    'fence': 'Fence Contractor', 'landscap': 'Landscaping',
    'lawn': 'Lawn Care', 'tree': 'Tree Service', 'pool': 'Pool Service',
    'paint': 'Painting', 'concrete': 'Concrete Contractor',
    'junk': 'Junk Removal', 'tile': 'Tile Contractor',
    'roof': 'Roofing', 'plumb': 'Plumbing', 'electric': 'Electrical',
    'floor': 'Flooring', 'paver': 'Paver Installation',
    'moving': 'Moving Service', 'drywall': 'Drywall',
    'stucco': 'Stucco Contractor', 'epoxy': 'Epoxy Flooring',
    'screen': 'Screen Enclosure', 'gutter': 'Gutter Cleaning',
    'sprinkler': 'Sprinkler/Irrigation', 'irrigat': 'Sprinkler/Irrigation',
    'contractor': 'General Contractor',
}

SKIP_HANDLES = {
    'p', 'explore', 'reel', 'reels', 'stories', 'accounts', 'about',
    'developer', 'direct', 'instagram', 'strangeadvancedmarketing',
}


def guess_category(query: str, bio: str = '') -> str:
    text = (query + ' ' + bio).lower()
    for kw, cat in CATEGORY_MAP.items():
        if kw in text:
            return cat
    return 'General Contractor'


def extract_handles_from_search(page, query: str) -> list[str]:
    """Search DuckDuckGo and extract IG handles from results."""
    import urllib.parse
    url = f"https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"    Search nav error: {e}", flush=True)
        return []

    # Extract instagram.com links from results
    handles = page.evaluate("""
    () => {
        const handles = [];
        const allText = document.body.innerHTML || '';
        // Find instagram.com/username patterns in page HTML
        const regex = /instagram\\.com\\/([a-zA-Z0-9_.]{3,30})/g;
        let match;
        while ((match = regex.exec(allText)) !== null) {
            const h = match[1].toLowerCase();
            if (!['p','explore','reel','reels','stories','accounts','about','developer','direct','tags','locations'].includes(h)) {
                if (!handles.includes(h)) handles.push(h);
            }
            if (handles.length >= 20) break;
        }
        return handles;
    }
    """)

    return handles or []


def check_ig_profile(page, handle: str) -> dict | None:
    """Visit IG profile and extract bio/website info."""
    try:
        page.goto(f"https://www.instagram.com/{handle}/",
                  wait_until="domcontentloaded", timeout=12000)
        page.wait_for_timeout(2500)
    except Exception as e:
        return None

    try:
        result = page.evaluate("""
        () => {
            const r = {has_website: false, bio: '', name: '', not_found: false};
            const text = document.body?.innerText || '';

            // Page not found
            if (text.includes("Sorry, this page") || text.includes("isn't available") || text.includes("Page Not Found")) {
                r.not_found = true;
                return r;
            }

            // Login wall check
            if (text.includes("Log in") && text.includes("Sign up") && !text.includes("followers")) {
                r.not_found = true;
                return r;
            }

            // Check for external website link
            const extLinks = document.querySelectorAll('a[href*="l.instagram.com"]');
            if (extLinks.length > 0) r.has_website = true;

            const allLinks = document.querySelectorAll('a');
            for (const a of allLinks) {
                const href = (a.href || '').toLowerCase();
                if (href.includes('linktr.ee') || href.includes('linkin.bio') ||
                    href.includes('linkpop') || href.includes('taplink') ||
                    href.includes('beacons.ai') || href.includes('stan.store') ||
                    href.includes('hoo.be') || href.includes('bio.link')) {
                    r.has_website = true;
                }
            }

            // Get bio from meta description (works without login)
            const metaDesc = document.querySelector('meta[name="description"]');
            if (metaDesc) {
                r.bio = metaDesc.getAttribute('content') || '';
            }

            // Also try header
            const header = document.querySelector('header');
            if (header) {
                const headerText = header.innerText || '';
                if (headerText.length > r.bio.length) r.bio = headerText;
            }

            // Get name from title
            const title = document.title || '';
            const nameMatch = title.match(/^(.+?)\\s*[(@]/);
            if (nameMatch) r.name = nameMatch[1].trim();

            return r;
        }
        """)
        return result
    except Exception:
        return None


def main():
    target_count = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    # Load existing
    existing_igs = set()
    for fname in ['master_targets.json', 'new_targets_batch2.json', 'network_targets.json']:
        p = os.path.join(BASE_DIR, fname)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for t in json.load(f):
                    if t.get('ig'):
                        existing_igs.add(t['ig'].lower())

    print(f"Finding {target_count} contractor IG targets (Playwright headless)")
    print(f"Existing to skip: {len(existing_igs)}")
    print(f"Queries: {len(SEARCH_QUERIES)}\n")

    new_targets = []
    all_handles_found = {}  # handle -> source query

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Phase 1: Google searches to collect handles
        print("=" * 50)
        print("PHASE 1: Google search for IG profiles")
        print("=" * 50)

        for qi, query in enumerate(SEARCH_QUERIES):
            print(f"[{qi+1}/{len(SEARCH_QUERIES)}] {query.replace('site:instagram.com ','')}...", end=' ', flush=True)
            handles = extract_handles_from_search(page, query)
            new_handles = [h for h in handles if h.lower() not in existing_igs and h not in SKIP_HANDLES]
            print(f"{len(handles)} found, {len(new_handles)} new", flush=True)

            for h in new_handles:
                if h.lower() not in all_handles_found:
                    all_handles_found[h.lower()] = query

            time.sleep(2)

            # Check if Google is blocking us
            if len(handles) == 0 and qi > 3:
                page.wait_for_timeout(5000)

        print(f"\nPhase 1 complete: {len(all_handles_found)} unique handles to check\n")

        # Phase 2: Check each IG profile
        print("=" * 50)
        print("PHASE 2: Checking IG profiles")
        print("=" * 50)

        checked = 0
        for handle, source_query in list(all_handles_found.items()):
            if len(new_targets) >= target_count:
                break

            checked += 1
            profile = check_ig_profile(page, handle)

            if not profile:
                print(f"  [{checked}] @{handle}: couldn't load", flush=True)
                continue
            if profile.get('not_found'):
                print(f"  [{checked}] @{handle}: login wall/not found", flush=True)
                # If we hit login wall, we can't check more profiles
                if checked > 3 and all(
                    check_ig_profile(page, list(all_handles_found.keys())[i]) is None or
                    check_ig_profile(page, list(all_handles_found.keys())[i]).get('not_found')
                    for i in range(checked, min(checked+2, len(all_handles_found)))
                ):
                    print("\n  IG login wall detected. Can't check profiles without login.", flush=True)
                    print("  Using Google snippet data instead...\n", flush=True)
                    break
                continue
            if profile.get('has_website'):
                print(f"  [{checked}] @{handle}: HAS WEBSITE - skip", flush=True)
                continue

            bio = profile.get('bio', '')
            name = profile.get('name', '') or handle
            category = guess_category(source_query, bio)

            target = {
                "name": name,
                "ig": handle,
                "phone": "",
                "category": category,
                "location": "Miami, FL",
                "rating": 0,
                "reviews": 0,
                "has_site": False,
                "notes": f"IG: {source_query.replace('site:instagram.com ','')[:30]}"
            }
            new_targets.append(target)
            print(f"  [{checked}] @{handle}: NO WEBSITE - TARGET [{len(new_targets)}/{target_count}]", flush=True)

            time.sleep(1.5)

        # If IG blocked us, fall back to using Google snippet descriptions
        if len(new_targets) < target_count and checked < len(all_handles_found):
            print("\nFallback: adding remaining handles from Google results (unverified)...")
            remaining = [(h, q) for h, q in all_handles_found.items()
                        if h not in {t['ig'] for t in new_targets}
                        and h.lower() not in existing_igs]

            for handle, source_query in remaining:
                if len(new_targets) >= target_count:
                    break
                category = guess_category(source_query)
                target = {
                    "name": handle,
                    "ig": handle,
                    "phone": "",
                    "category": category,
                    "location": "Miami, FL",
                    "rating": 0,
                    "reviews": 0,
                    "has_site": False,
                    "notes": f"Google found, unverified: {source_query.replace('site:instagram.com ','')[:25]}"
                }
                new_targets.append(target)

        browser.close()

    # Save
    output_path = os.path.join(BASE_DIR, 'new_ig_targets.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_targets, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Found {len(new_targets)} targets.")
    print(f"Saved to: {output_path}")

    if new_targets:
        cats = {}
        for t in new_targets:
            cats[t['category']] = cats.get(t['category'], 0) + 1
        print("\nCategories:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
