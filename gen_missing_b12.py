"""Generate missing contractor sites for batch 1 and batch 2 targets."""
import importlib.util
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

# ---------- Category normalization ----------
# Batch JSON files use varied category names (e.g. "Plumber", "Mover",
# "Pressure washing service"). Map them to the canonical categories that
# generate_v2.py knows so that hero images / colour schemes / services match.
CATEGORY_MAP: dict[str, str] = {
    # Pressure cleaning variants
    'Pressure washing service': 'Pressure Washing',
    'Pressure Cleaning': 'Pressure Cleaning',
    'Pressure Washing': 'Pressure Washing',
    # Fence variants
    'Fence contractor': 'Fence Contractor',
    'Fence supply store': 'Fence Contractor',
    'Fence Contractor': 'Fence Contractor',
    # Landscape variants
    'Landscape designer': 'Landscape Design',
    'Landscaper': 'Landscaping',
    'Landscaping': 'Landscaping',
    'Landscape Design': 'Landscape Design',
    # Lawn
    'Lawn care service': 'Lawn Care',
    'Lawn Care': 'Lawn Care',
    # Tree
    'Tree service': 'Tree Service',
    'Tree Service': 'Tree Service',
    # Pool
    'Pool cleaning service': 'Pool Service',
    'Pool Service': 'Pool Service',
    'Pool Cleaning': 'Pool Cleaning',
    # Painting
    'Painter': 'Painting',
    'Painting': 'Painting',
    'Painting & Pressure Cleaning': 'Painting & Pressure Cleaning',
    # Concrete
    'Concrete contractor': 'Concrete Contractor',
    'Concrete Contractor': 'Concrete Contractor',
    # Junk
    'Junk removal service': 'Junk Removal',
    'Debris removal service': 'Junk Removal',
    'Waste management service': 'Junk Removal',
    'Junk Removal': 'Junk Removal',
    # Moving
    'Mover': 'Moving Service',
    'Moving Service': 'Moving Service',
    # Natural stone / tile
    'Natural stone supplier': 'Tile Contractor',
    'Stone supplier': 'Tile Contractor',
    'Tile contractor': 'Tile Contractor',
    'Tile Contractor': 'Tile Contractor',
    'Tile Store': 'Tile Store',
    # Roofing
    'Roofing contractor': 'Roofing',
    'Roofing': 'Roofing',
    # Plumbing
    'Plumber': 'Plumbing',
    'Plumbing': 'Plumbing',
    # Electrical
    'Electrician': 'Electrical',
    'Electrical': 'Electrical',
    # Flooring
    'Flooring contractor': 'Flooring',
    'Flooring store': 'Flooring',
    'Floor sanding and polishing service': 'Epoxy Flooring',
    'Flooring': 'Flooring',
    # Epoxy
    'Epoxy Flooring': 'Epoxy Flooring',
    # Stucco
    'Stucco contractor': 'Stucco Contractor',
    'Stucco Contractor': 'Stucco Contractor',
    # Drywall
    'Dry wall contractor': 'Drywall',
    'Drywall': 'Drywall',
    # Plastering
    'Plastering': 'Plastering',
    # Construction
    'Construction company': 'Construction',
    'Construction': 'Construction',
    'General contractor': 'General Contractor',
    'General Contractor': 'General Contractor',
    # Screen Enclosure
    'Building materials supplier': 'Screen Enclosure',
    'Screen repair service': 'Screen Enclosure',
    'Screen Enclosure': 'Screen Enclosure',
    # Gutter (not in generate_v2 explicitly - falls back to Handyman)
    'Gutter service': 'Handyman',
    # Garage Door
    'Garage door supplier': 'Garage Door',
    'Garage Door': 'Garage Door',
    # Awning (not in generate_v2 - falls back to Handyman)
    'Awning supplier': 'Handyman',
    # Window
    'Window Tinting': 'Window Tinting',
    'Window Cleaning': 'Window Cleaning',
    # Car Wash
    'Mobile Car Wash': 'Mobile Car Wash',
    # Water Damage
    'Water Damage Restoration': 'Water Damage Restoration',
    # HVAC
    'HVAC': 'HVAC',
    # Cabinetry
    'Cabinetry': 'Cabinetry',
    # Sprinkler/Irrigation
    'Sprinkler/Irrigation': 'Sprinkler/Irrigation',
    'Irrigation': 'Irrigation',
    'Sprinkler Contractor': 'Sprinkler Contractor',
    # Artificial Turf
    'Artificial Turf': 'Artificial Turf',
    # Property Maintenance
    'Property Maintenance': 'Property Maintenance',
    # Handyman
    'Handyman/Handywoman/Handyperson': 'Handyman',
    'Handyman': 'Handyman',
}


def slugify(name: str) -> str:
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def main() -> None:
    # Load the generator module
    spec = importlib.util.spec_from_file_location('gen', os.path.join(BASE_DIR, 'generate_v2.py'))
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    # Load both target files
    with open(os.path.join(BASE_DIR, 'gmaps_ig_targets.json'), 'r', encoding='utf-8') as f:
        batch1 = json.load(f)
    with open(os.path.join(BASE_DIR, 'new_targets_batch2.json'), 'r', encoding='utf-8') as f:
        batch2 = json.load(f)

    all_targets = batch1 + batch2
    print(f"Total targets loaded: {len(batch1)} batch1 + {len(batch2)} batch2 = {len(all_targets)}")

    already_exist = 0
    generated = 0
    gen_errors: list[str] = []

    for target in all_targets:
        slug = slugify(target['name'])
        index_path = os.path.join(BASE_DIR, slug, 'index.html')

        if os.path.isfile(index_path):
            already_exist += 1
            continue

        # Normalize category so generator picks the right theme
        raw_cat = target.get('category', 'Handyman')
        normalized = CATEGORY_MAP.get(raw_cat, raw_cat)
        target_copy = dict(target)
        target_copy['category'] = normalized

        try:
            html = gen.generate_site(target_copy)
            site_dir = os.path.join(BASE_DIR, slug)
            os.makedirs(site_dir, exist_ok=True)
            with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            generated += 1
            print(f"  Generated: {slug}/")
        except Exception as exc:
            gen_errors.append(f"{target['name']} ({slug}): {exc}")
            print(f"  ERROR: {slug} - {exc}")

    print(f"\n--- Generation Summary ---")
    print(f"Already existed: {already_exist}")
    print(f"Newly generated: {generated}")
    print(f"Errors: {len(gen_errors)}")
    for e in gen_errors:
        print(f"  {e}")

    # ---------- Verification pass ----------
    print(f"\n--- Verification (all {len(all_targets)} targets) ---")
    ok = 0
    issues: list[str] = []

    for target in all_targets:
        slug = slugify(target['name'])
        index_path = os.path.join(BASE_DIR, slug, 'index.html')
        problems: list[str] = []

        if not os.path.isfile(index_path):
            issues.append(f"{target['name']} ({slug}): index.html MISSING")
            continue

        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Business name in HTML
        if target['name'] not in html:
            problems.append('name not found in HTML')

        # 2. Instagram link
        ig = target.get('ig', '')
        if ig and f'instagram.com/{ig}' not in html:
            problems.append(f'instagram.com/{ig} link missing')

        # 3. Phone number
        phone = target.get('phone', '')
        if phone and phone not in html:
            problems.append(f'phone {phone} missing')

        if problems:
            issues.append(f"{target['name']} ({slug}): {'; '.join(problems)}")
        else:
            ok += 1

    print(f"Verified OK: {ok}/{len(all_targets)}")
    print(f"Issues: {len(issues)}")
    for iss in issues:
        print(f"  {iss}")


if __name__ == '__main__':
    main()
