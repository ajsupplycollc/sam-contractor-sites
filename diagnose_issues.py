"""Diagnose all batch 3 site issues: slug collisions, wrong IG, missing names."""
import json, re, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\ajsup\sam_contractor_sites'

def slugify(name):
    s = name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9\-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')[:50]

with open(os.path.join(BASE, 'batch3_final.json'), 'r', encoding='utf-8') as f:
    all_targets = json.load(f)

targets = [t for t in all_targets if not t.get('has_website')]

issues = []
slug_map = {}

for t in targets:
    name = t['name']
    ig = t['ig']
    slug = slugify(name)
    if not slug:
        slug = slugify(ig.replace('_', ' ').replace('.', ' '))

    slug_map.setdefault(slug, []).append(ig)

    site_path = os.path.join(BASE, slug, 'index.html')
    if not os.path.exists(site_path):
        issues.append(('MISSING', ig, repr(name), slug, []))
        continue

    with open(site_path, 'r', encoding='utf-8') as f:
        html = f.read()

    wrong_ig = f'instagram.com/{ig}' not in html
    wrong_name = name not in html

    if wrong_ig or wrong_name:
        ig_refs = list(set(re.findall(r'instagram\.com/([a-zA-Z0-9_.]+)', html)))
        issues.append(('WRONG' if wrong_ig else 'NAME_ONLY', ig, repr(name), slug, ig_refs))

print('=== SLUG COLLISIONS ===')
for slug, igs in slug_map.items():
    if len(igs) > 1:
        print(f'  slug={slug}: {igs}')

print(f'\n=== ALL ISSUES ({len(issues)}) ===')
for typ, ig, name, slug, refs in issues:
    print(f'  [{typ}] @{ig} name={name} slug={slug} html_ig={refs}')
