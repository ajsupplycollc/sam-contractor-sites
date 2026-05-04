"""Polish the humanized handle names to be more readable."""
import json, re, os, sys, importlib.util

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\ajsup\sam_contractor_sites'

HANDLE_NAME_MAP = {
    'stpeteplumbing': 'St Pete Plumbing',
    'everydayplumber': 'Everyday Plumber',
    'theb12storesprings': 'The B12 Store Springs',
    'epoxy_flooring': 'Epoxy Flooring',
    'treecofl': 'Treeco FL',
    'hollywoodfencellc': 'Hollywood Fence LLC',
    'flpressurekings': 'FL Pressure Kings',
    'palm.plumberair': 'Palm Plumber Air',
    'letsgetmovinghialeah': 'Lets Get Moving Hialeah',
    'opdhialeah': 'OPD Hialeah',
    'locksmithhialeah': 'Locksmith Hialeah',
    'fastactlocksmith': 'Fast Act Locksmith',
    'daytona.pressure': 'Daytona Pressure',
    'doubledlocksmith': 'Double D Locksmith',
    'verdigrishomesfl': 'Verdigris Homes FL',
    'coralspringsfl': 'Coral Springs FL',
    'zieglerdrywallpainting': 'Ziegler Drywall Painting',
    'hvacwithbrandon': 'HVAC With Brandon',
    'palmatlantichms': 'Palm Atlantic HMS',
    'alldayfence': 'All Day Fence',
    'motolandscapingllc': 'Moto Landscaping LLC',
}


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

    spec = importlib.util.spec_from_file_location('gen', os.path.join(BASE, 'generate_v2.py'))
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    updated = 0
    for t in all_targets:
        ig = t['ig']
        if ig in HANDLE_NAME_MAP:
            old_name = t['name']
            new_name = HANDLE_NAME_MAP[ig]
            if old_name != new_name:
                t['name'] = new_name
                slug = slug_map.get(ig)
                if slug:
                    site_dir = os.path.join(BASE, slug)
                    html = gen.generate_site(t)
                    with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
                        f.write(html)
                    updated += 1
                    print(f"  @{ig}: '{old_name}' -> '{new_name}' (slug={slug})")

    with open(os.path.join(BASE, 'batch3_final.json'), 'w', encoding='utf-8') as f:
        json.dump(all_targets, f, indent=2, ensure_ascii=False)

    print(f"\nPolished {updated} names")

    # Quick re-verify the updated ones
    ok = 0
    for ig, new_name in HANDLE_NAME_MAP.items():
        slug = slug_map.get(ig)
        if not slug:
            continue
        site_path = os.path.join(BASE, slug, 'index.html')
        if not os.path.exists(site_path):
            print(f"  MISSING: @{ig} slug={slug}")
            continue
        with open(site_path, 'r', encoding='utf-8') as f:
            html = f.read()
        if f'instagram.com/{ig}' in html and new_name in html:
            ok += 1
        else:
            print(f"  FAIL: @{ig} slug={slug}")

    print(f"Verified polished names: {ok}/{len(HANDLE_NAME_MAP)}")


if __name__ == '__main__':
    main()
