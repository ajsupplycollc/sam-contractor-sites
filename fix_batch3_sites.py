"""
Fix the 27 batch 3 site issues:
1. Replace 'Sponsored' names with humanized IG handles
2. Make all slugs unique (append IG handle suffix on collision)
3. Regenerate only the affected sites
4. Re-verify all 410 sites
"""
import json, re, os, sys, shutil, importlib.util

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\ajsup\sam_contractor_sites'


def slugify(name: str) -> str:
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')[:50]


def humanize_handle(handle: str) -> str:
    """Convert IG handle to readable business name."""
    h = handle.replace('_', ' ').replace('.', ' ')
    h = re.sub(r'\s+', ' ', h).strip()
    return h.title()


def make_unique_slug(name: str, ig: str, used_slugs: dict) -> str:
    """Generate a unique slug. If collision, append IG handle."""
    slug = slugify(name)
    if not slug:
        slug = slugify(ig.replace('_', ' ').replace('.', ' '))

    if slug in used_slugs and used_slugs[slug] != ig:
        slug = slugify(f"{name} {ig}")
    if not slug:
        slug = slugify(ig)

    return slug


def main():
    # Load targets
    with open(os.path.join(BASE, 'batch3_final.json'), 'r', encoding='utf-8') as f:
        all_targets = json.load(f)

    targets = [t for t in all_targets if not t.get('has_website')]
    print(f"Total targets to fix-check: {len(targets)}")

    # Phase 1: Fix names and compute unique slugs
    used_slugs = {}
    needs_regen = []
    old_slug_map = {}

    for t in targets:
        ig = t['ig']
        old_name = t['name']
        old_slug = slugify(old_name) or slugify(ig.replace('_', ' ').replace('.', ' '))
        old_slug_map[ig] = old_slug

        # Fix "Sponsored" names
        if old_name.startswith('Sponsored'):
            new_name = humanize_handle(ig)
            t['name'] = new_name
            print(f"  Fixed name: @{ig} '{old_name}' -> '{new_name}'")

    # Now assign unique slugs
    slug_assignments = {}
    slug_owner = {}

    for t in targets:
        ig = t['ig']
        name = t['name']
        slug = slugify(name)
        if not slug:
            slug = slugify(ig.replace('_', ' ').replace('.', ' '))

        if slug in slug_owner and slug_owner[slug] != ig:
            # Collision — make unique by appending IG handle
            slug = slugify(f"{name} {ig}")
            if not slug:
                slug = slugify(ig)

        slug_owner[slug] = ig
        slug_assignments[ig] = slug

    # Identify which sites need regeneration
    for t in targets:
        ig = t['ig']
        new_slug = slug_assignments[ig]
        old_slug = old_slug_map[ig]
        site_path = os.path.join(BASE, new_slug, 'index.html')

        regen = False
        if old_slug != new_slug:
            regen = True
        elif not os.path.exists(site_path):
            regen = True
        else:
            with open(site_path, 'r', encoding='utf-8') as f:
                html = f.read()
            if f'instagram.com/{ig}' not in html or t['name'] not in html:
                regen = True

        if regen:
            needs_regen.append((t, new_slug, old_slug))

    print(f"\nSites needing regeneration: {len(needs_regen)}")
    for t, new_slug, old_slug in needs_regen:
        print(f"  @{t['ig']}: name='{t['name']}' old_slug={old_slug} new_slug={new_slug}")

    # Phase 2: Load generator and regenerate
    spec = importlib.util.spec_from_file_location('gen', os.path.join(BASE, 'generate_v2.py'))
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    regenerated = 0
    errors = []

    for t, new_slug, old_slug in needs_regen:
        ig = t['ig']
        site_dir = os.path.join(BASE, new_slug)
        os.makedirs(site_dir, exist_ok=True)

        # Copy logo from old slug dir if it exists there but not in new
        new_logo = os.path.join(site_dir, 'logo.png')
        if not os.path.exists(new_logo):
            old_logo = os.path.join(BASE, old_slug, 'logo.png')
            if os.path.exists(old_logo):
                shutil.copy2(old_logo, new_logo)
            else:
                # Try IG handle slug
                ig_slug = slugify(ig.replace('_', ' ').replace('.', ' '))
                ig_logo = os.path.join(BASE, ig_slug, 'logo.png')
                if os.path.exists(ig_logo):
                    shutil.copy2(ig_logo, new_logo)

        try:
            html = gen.generate_site(t)
            with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            regenerated += 1
        except Exception as e:
            errors.append(f"@{ig}: {e}")
            print(f"  ERROR generating @{ig}: {e}")

    print(f"\nRegenerated: {regenerated}/{len(needs_regen)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")

    # Phase 3: Save updated final JSON and slug assignments
    with open(os.path.join(BASE, 'batch3_final.json'), 'w', encoding='utf-8') as f:
        json.dump(all_targets, f, indent=2, ensure_ascii=False)

    with open(os.path.join(BASE, 'batch3_slug_map.json'), 'w', encoding='utf-8') as f:
        json.dump(slug_assignments, f, indent=2)

    # Phase 4: Full verification
    print(f"\n{'='*60}")
    print("FULL VERIFICATION")
    print(f"{'='*60}")

    ok = 0
    issues = []

    for t in targets:
        ig = t['ig']
        name = t['name']
        slug = slug_assignments[ig]
        site_path = os.path.join(BASE, slug, 'index.html')

        if not os.path.exists(site_path):
            issues.append(f"MISSING: @{ig} slug={slug}")
            continue

        with open(site_path, 'r', encoding='utf-8') as f:
            html = f.read()

        problems = []
        if f'instagram.com/{ig}' not in html:
            ig_refs = list(set(re.findall(r'instagram\.com/([a-zA-Z0-9_.]+)', html)))
            problems.append(f"wrong IG (has {ig_refs})")
        if name not in html:
            problems.append(f"name not found")

        if problems:
            issues.append(f"@{ig} slug={slug}: {', '.join(problems)}")
        else:
            ok += 1

    # Check logos
    missing_logos = 0
    for t in targets:
        slug = slug_assignments[t['ig']]
        if not os.path.exists(os.path.join(BASE, slug, 'logo.png')):
            missing_logos += 1

    print(f"Sites verified OK: {ok}/{len(targets)}")
    print(f"Missing logos: {missing_logos}")
    print(f"Issues: {len(issues)}")

    if issues:
        for iss in issues:
            print(f"  {iss}")
    else:
        print("\nALL 410 SITES VERIFIED CLEAN.")

    return len(issues) == 0


if __name__ == '__main__':
    main()
