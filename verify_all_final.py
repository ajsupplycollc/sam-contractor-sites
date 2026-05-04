"""Final comprehensive verification of all batch 3 sites."""
import json, re, os, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\ajsup\sam_contractor_sites'


def slugify(name: str) -> str:
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')[:50]


def main():
    with open(os.path.join(BASE, 'batch3_final.json'), 'r', encoding='utf-8') as f:
        all_targets = json.load(f)

    with open(os.path.join(BASE, 'batch3_slug_map.json'), 'r', encoding='utf-8') as f:
        slug_map = json.load(f)

    targets = [t for t in all_targets if not t.get('has_website')]
    excluded = [t for t in all_targets if t.get('has_website')]

    print(f"Total in batch3_final.json: {len(all_targets)}")
    print(f"Excluded (have website): {len(excluded)}")
    print(f"Active targets: {len(targets)}")

    ok = 0
    wrong_ig = []
    wrong_name = []
    missing_site = []
    missing_logo = []
    slug_collisions = {}

    for t in targets:
        ig = t['ig']
        name = t['name']
        slug = slug_map.get(ig)

        if not slug:
            # Fallback slug calculation
            slug = slugify(name) or slugify(ig.replace('_', ' ').replace('.', ' '))

        slug_collisions.setdefault(slug, []).append(ig)

        site_path = os.path.join(BASE, slug, 'index.html')
        logo_path = os.path.join(BASE, slug, 'logo.png')

        if not os.path.exists(site_path):
            missing_site.append(f"@{ig} slug={slug}")
            continue

        with open(site_path, 'r', encoding='utf-8') as f:
            html = f.read()

        site_ok = True

        if f'instagram.com/{ig}' not in html:
            ig_refs = list(set(re.findall(r'instagram\.com/([a-zA-Z0-9_.]+)', html)))
            wrong_ig.append(f"@{ig} slug={slug} has={ig_refs}")
            site_ok = False

        if name not in html:
            wrong_name.append(f"@{ig} name='{name}' slug={slug}")
            site_ok = False

        if not os.path.exists(logo_path):
            missing_logo.append(f"@{ig} slug={slug}")

        if site_ok:
            ok += 1

    # Check for remaining slug collisions
    collisions = {s: igs for s, igs in slug_collisions.items() if len(igs) > 1}

    print(f"\n{'='*60}")
    print(f"FINAL VERIFICATION RESULTS")
    print(f"{'='*60}")
    print(f"Sites OK (name + IG correct): {ok}/{len(targets)}")
    print(f"Wrong IG handle: {len(wrong_ig)}")
    print(f"Wrong name: {len(wrong_name)}")
    print(f"Missing site: {len(missing_site)}")
    print(f"Missing logo: {len(missing_logo)}")
    print(f"Slug collisions: {len(collisions)}")

    if wrong_ig:
        print(f"\nWRONG IG:")
        for x in wrong_ig:
            print(f"  {x}")

    if wrong_name:
        print(f"\nWRONG NAME:")
        for x in wrong_name:
            print(f"  {x}")

    if missing_site:
        print(f"\nMISSING SITE:")
        for x in missing_site:
            print(f"  {x}")

    if collisions:
        print(f"\nSLUG COLLISIONS:")
        for s, igs in collisions.items():
            print(f"  {s}: {igs}")

    if missing_logo:
        print(f"\nMISSING LOGOS:")
        for x in missing_logo:
            print(f"  {x}")

    if ok == len(targets) and not wrong_ig and not wrong_name and not missing_site and not collisions:
        print(f"\nALL {ok} SITES VERIFIED PERFECT.")
        return True
    return False


if __name__ == '__main__':
    main()
