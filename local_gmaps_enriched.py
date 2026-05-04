"""
Local Google Maps scraper WITH enrichment.
Extracts business info from Google Maps, then visits each website to pull
Instagram, Facebook, email, and other social links.
Same logic as our Apify actor, runs locally for free.
"""
import json, time, re, sys, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

SEARCH_QUERIES = [
    "handyman miami FL",
    "handyman fort lauderdale FL",
    "handyman broward FL",
    "pressure washing miami FL",
    "pressure washing broward FL",
    "pressure washing fort lauderdale FL",
    "fence installer miami FL",
    "fence installer south florida",
    "landscaping miami FL",
    "lawn care miami FL",
    "tree service miami FL",
    "pool service miami FL",
    "painting contractor miami FL",
    "concrete contractor miami FL",
    "concrete contractor south florida",
    "junk removal miami FL",
    "tile installer miami FL",
    "roofing contractor miami FL",
    "plumber miami FL",
    "electrician miami FL",
    "flooring installer miami FL",
    "paver installation miami FL",
    "moving company miami FL",
    "drywall contractor miami FL",
    "stucco contractor miami FL",
    "screen enclosure miami FL",
    "epoxy flooring miami FL",
    "gutter cleaning miami FL",
    "sprinkler irrigation miami FL",
    "garage door installer miami FL",
]


def enrich_business(page, business: dict) -> dict:
    """Visit business website and extract emails, social media, lead score."""
    website = business.get('website', '')
    business['emails'] = []
    business['social_instagram'] = ''
    business['social_facebook'] = ''
    business['social_tiktok'] = ''
    business['has_email'] = False
    business['has_social_media'] = False
    business['lead_score'] = 'hot'

    if not website:
        return business

    try:
        url = website if website.startswith('http') else f'https://{website}'
        page.goto(url, wait_until='domcontentloaded', timeout=10000)
        page.wait_for_timeout(2000)
        content = page.content()

        # Extract emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = list(set(re.findall(email_pattern, content)))
        junk = ['example.com', 'domain.com', 'email.com', 'test.com', 'sample.com',
                '.png', '.jpg', '.gif', '.svg', '.css', '.js', 'wixpress', 'sentry',
                'cloudflare', 'googleapis', 'gstatic', 'squarespace', 'wordpress',
                'shopify', 'godaddy', 'wix.com', 'noreply', 'no-reply', 'mailer-daemon',
                'fontawesome', 'bootstrap', 'indiantypefoundry']
        emails = [e for e in emails if not any(x in e.lower() for x in junk)]
        business['emails'] = emails[:5]
        business['has_email'] = len(emails) > 0

        # Extract social media
        ig_match = re.search(r'(?:instagram\.com|instagr\.am)/([a-zA-Z0-9_.]+)', content)
        if ig_match:
            business['social_instagram'] = ig_match.group(1)

        fb_match = re.search(r'facebook\.com/([a-zA-Z0-9_.]+)', content)
        if fb_match:
            business['social_facebook'] = fb_match.group(1)

        tt_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', content)
        if tt_match:
            business['social_tiktok'] = tt_match.group(1)

        has_social = bool(business['social_instagram'] or business['social_facebook'] or business['social_tiktok'])
        business['has_social_media'] = has_social

        # Lead scoring
        if not has_social and not emails:
            business['lead_score'] = 'hot'
        elif not has_social or not emails:
            business['lead_score'] = 'warm'
        else:
            business['lead_score'] = 'cold'

    except Exception as e:
        pass

    return business


def scrape_query(page, query: str, max_results: int = 15) -> list:
    """Search Google Maps and extract business listings."""
    results = []
    search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)

        try:
            page.wait_for_selector('div[role="feed"]', timeout=8000)
        except Exception:
            return results

        # Scroll to load
        prev_count = 0
        scroll_attempts = 0
        while scroll_attempts < 8:
            listings = page.query_selector_all('a[href*="/maps/place/"]')
            if len(listings) >= max_results:
                break
            if len(listings) == prev_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            prev_count = len(listings)
            page.evaluate('const f=document.querySelector(\'div[role="feed"]\');if(f)f.scrollTop+=1000;')
            page.wait_for_timeout(1500)

        listings = page.query_selector_all('a[href*="/maps/place/"]')

        for i, listing in enumerate(listings[:max_results]):
            try:
                listing.click()
                page.wait_for_timeout(2000)

                biz = {}
                name_el = page.query_selector('h1.DUwDvf')
                if name_el:
                    biz['name'] = name_el.inner_text()

                rating_el = page.query_selector('div.F7nice span[aria-hidden="true"]')
                if rating_el:
                    try:
                        biz['rating'] = float(rating_el.inner_text())
                    except ValueError:
                        biz['rating'] = 0

                review_el = page.query_selector('div.F7nice span[aria-label*="review"]')
                if review_el:
                    label = review_el.get_attribute('aria-label') or ''
                    match = re.search(r'(\d[\d,]*)', label)
                    if match:
                        biz['reviews'] = int(match.group(1).replace(',', ''))

                cat_el = page.query_selector('button.DkEaL')
                if cat_el:
                    biz['category'] = cat_el.inner_text()

                addr_els = page.query_selector_all('button[data-item-id="address"] div.fontBodyMedium')
                if addr_els:
                    biz['address'] = addr_els[0].inner_text()

                phone_els = page.query_selector_all('button[data-item-id*="phone"] div.fontBodyMedium')
                if phone_els:
                    biz['phone'] = phone_els[0].inner_text()

                website_els = page.query_selector_all('a[data-item-id="authority"] div.fontBodyMedium')
                if website_els:
                    biz['website'] = website_els[0].inner_text()
                else:
                    biz['website'] = ''

                if biz.get('name'):
                    results.append(biz)

            except Exception:
                continue

    except Exception as e:
        print(f"    Page error: {e}", flush=True)

    return results


def main():
    # Load existing
    existing_igs = set()
    existing_names = set()
    existing_phones = set()
    for fname in ['master_targets.json', 'new_targets_batch2.json']:
        p = os.path.join(BASE_DIR, fname)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for t in json.load(f):
                    if t.get('ig'):
                        existing_igs.add(t['ig'].lower())
                    if t.get('name'):
                        existing_names.add(t['name'].lower().strip())
                    if t.get('phone'):
                        existing_phones.add(re.sub(r'\D', '', t['phone'])[-10:])

    print(f"Google Maps Lead Generator — LOCAL (enrichment ON)")
    print(f"{len(SEARCH_QUERIES)} queries, existing: {len(existing_names)} names, {len(existing_igs)} IGs")
    print()

    all_businesses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        maps_page = context.new_page()
        enrich_page = context.new_page()

        # Phase 1: Scrape Google Maps
        print("=" * 50)
        print("PHASE 1: Google Maps scraping")
        print("=" * 50)

        for qi, query in enumerate(SEARCH_QUERIES):
            print(f"[{qi+1}/{len(SEARCH_QUERIES)}] {query}...", end=' ', flush=True)
            results = scrape_query(maps_page, query, max_results=15)
            print(f"{len(results)} businesses", flush=True)
            for r in results:
                r['_source_query'] = query
            all_businesses.extend(results)
            time.sleep(1.5)

        # Dedup
        seen = set()
        unique = []
        for biz in all_businesses:
            name = (biz.get('name') or '').lower().strip()
            if name and name not in seen and name not in existing_names:
                seen.add(name)
                unique.append(biz)

        print(f"\nTotal raw: {len(all_businesses)}, unique new: {len(unique)}")

        # Phase 2: Enrich (visit websites for social/email)
        print("\n" + "=" * 50)
        print("PHASE 2: Enriching leads (visiting websites)")
        print("=" * 50)

        with_ig = []
        without_website = []

        for i, biz in enumerate(unique):
            website = biz.get('website', '')
            name = biz.get('name', '?')

            if not website:
                without_website.append(biz)
                continue

            print(f"  [{i+1}/{len(unique)}] {name[:35]}...", end=' ', flush=True)
            enrich_business(enrich_page, biz)

            ig = biz.get('social_instagram', '')
            if ig and ig.lower() not in existing_igs:
                with_ig.append(biz)
                print(f"IG: @{ig}", flush=True)
            else:
                status = []
                if biz.get('has_email'):
                    status.append(f"email: {biz['emails'][0]}")
                if biz.get('social_facebook'):
                    status.append(f"FB: {biz['social_facebook']}")
                print(f"{', '.join(status) if status else 'no socials'}", flush=True)

            time.sleep(0.5)

        browser.close()

    # Build target lists
    print(f"\n{'=' * 50}")
    print(f"RESULTS")
    print(f"{'=' * 50}")
    print(f"Businesses with Instagram: {len(with_ig)}")
    print(f"Businesses without website: {len(without_website)}")

    # IG targets (have IG handle, from website enrichment)
    ig_targets = []
    for biz in with_ig:
        ig = biz.get('social_instagram', '')
        phone = biz.get('phone', '')
        phone_clean = re.sub(r'\D', '', phone)[-10:]
        if phone_clean in existing_phones:
            continue

        category = biz.get('category', biz.get('_source_query', 'General Contractor'))
        ig_targets.append({
            "name": biz.get('name', ''),
            "ig": ig,
            "phone": phone,
            "category": category,
            "location": biz.get('address', 'Miami, FL'),
            "rating": biz.get('rating', 0),
            "reviews": biz.get('reviews', 0),
            "has_site": True,
            "notes": f"GMaps enriched, website: {biz.get('website','')}",
        })

    # Phone-only targets (no website at all)
    phone_targets = []
    for biz in without_website:
        phone = biz.get('phone', '')
        if not phone:
            continue
        phone_clean = re.sub(r'\D', '', phone)[-10:]
        if phone_clean in existing_phones:
            continue

        category = biz.get('category', biz.get('_source_query', 'General Contractor'))
        phone_targets.append({
            "name": biz.get('name', ''),
            "ig": "",
            "phone": phone,
            "category": category,
            "location": biz.get('address', 'Miami, FL'),
            "rating": biz.get('rating', 0),
            "reviews": biz.get('reviews', 0),
            "has_site": False,
            "notes": "GMaps, no website",
        })

    # Save
    ig_path = os.path.join(BASE_DIR, 'gmaps_ig_targets.json')
    with open(ig_path, 'w', encoding='utf-8') as f:
        json.dump(ig_targets, f, indent=2, ensure_ascii=False)

    phone_path = os.path.join(BASE_DIR, 'gmaps_phone_targets.json')
    with open(phone_path, 'w', encoding='utf-8') as f:
        json.dump(phone_targets, f, indent=2, ensure_ascii=False)

    # Also save full enriched data
    raw_path = os.path.join(BASE_DIR, 'gmaps_enriched_full.json')
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    print(f"\nIG targets (have IG handle): {len(ig_targets)} → {ig_path}")
    print(f"Phone targets (no website): {len(phone_targets)} → {phone_path}")
    print(f"Full enriched data: {len(unique)} → {raw_path}")

    if ig_targets:
        print(f"\nIG targets:")
        for t in ig_targets[:20]:
            print(f"  @{t['ig']:<25} {t['name'][:30]:<32} {t['phone']}")

    if phone_targets:
        print(f"\nPhone-only targets:")
        for t in phone_targets[:20]:
            print(f"  {t['name'][:35]:<37} {t['phone']:<16} {t['category']}")


if __name__ == '__main__':
    main()
