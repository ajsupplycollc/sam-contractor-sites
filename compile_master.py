import json, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

original_valid = [
    {'name': 'Pro Painting And Sons', 'ig': 'propaintingandsons', 'phone': '(786) 554-3438', 'category': 'Painting & Pressure Cleaning', 'location': 'Miami, FL', 'rating': 4.9, 'reviews': 113, 'has_site': False},
    {'name': 'Veloz Contractors Inc', 'ig': 'velozcontractors', 'phone': '(786) 506-1891', 'category': 'General Contractor', 'location': 'Hialeah, FL', 'rating': 4.8, 'reviews': 103, 'has_site': False},
    {'name': 'Mobile Car Wash Miami LLC', 'ig': '', 'fb': 'mycarwashmiami', 'phone': '(786) 795-9334', 'category': 'Mobile Car Wash', 'location': 'Miami, FL', 'rating': 5.0, 'reviews': 220, 'has_site': False},
    {'name': 'Palm Atlantic Handyman Services', 'ig': '', 'phone': '(954) 607-0846', 'category': 'Handyman', 'location': 'South Florida', 'rating': 5.0, 'reviews': 95, 'has_site': False},
    {'name': 'Water Damage Clean', 'ig': '', 'phone': '', 'category': 'Water Damage Restoration', 'location': 'South Florida', 'rating': 4.8, 'reviews': 96, 'has_site': False},
    {'name': 'Boca Raton Blue Pool Service', 'ig': '', 'phone': '(561) 781-7444', 'category': 'Pool Cleaning', 'location': 'Boca Raton, FL', 'rating': 4.7, 'reviews': 39, 'has_site': False},
    {'name': 'El Valle Sprinkler Systems', 'ig': 'elvallesprinklersystems', 'phone': '(305) 205-9314', 'category': 'Sprinkler Contractor', 'location': 'Pompano Beach, FL', 'rating': 4.9, 'reviews': 19, 'has_site': False},
    {'name': 'Plastering and Stucco Pros', 'ig': '', 'phone': '', 'category': 'Plastering', 'location': 'Miami, FL', 'rating': 5.0, 'reviews': 23, 'has_site': False},
    {'name': 'South Florida Window Tinting', 'ig': '', 'phone': '', 'category': 'Window Tinting', 'location': 'Palm Beach Gardens, FL', 'rating': 4.0, 'reviews': 21, 'has_site': False},
    {'name': 'Masters Electrical Contractors', 'ig': '', 'phone': '', 'category': 'Electrical', 'location': 'Pembroke Pines, FL', 'rating': 5.0, 'reviews': 18, 'has_site': False},
    {'name': 'MVP Synthetic Turf LLC', 'ig': '', 'phone': '(561) 255-5998', 'category': 'Artificial Turf', 'location': 'West Palm Beach, FL', 'rating': 5.0, 'reviews': 14, 'has_site': False},
    {'name': 'New Life Landscaping & Lawn Care', 'ig': '', 'phone': '', 'category': 'Landscaping', 'location': 'South Florida', 'rating': 4.7, 'reviews': 0, 'has_site': False},
    {'name': 'Golden Stucco & Plastering', 'ig': '', 'phone': '', 'category': 'Plastering', 'location': 'South Florida', 'rating': 5.0, 'reviews': 0, 'has_site': False},
    {'name': 'ROOFING REPAIR SERVICE CORP', 'ig': '', 'phone': '', 'category': 'Roofing', 'location': 'Homestead, FL', 'rating': 5.0, 'reviews': 0, 'has_site': False},
    {'name': 'South Florida Pressure Cleaning', 'ig': '', 'phone': '', 'category': 'Pressure Cleaning', 'location': 'Hialeah, FL', 'rating': 5.0, 'reviews': 0, 'has_site': False},
    {'name': 'Leonel International Tile Corporation', 'ig': '', 'phone': '', 'category': 'Tile Contractor', 'location': 'Hialeah, FL', 'rating': 4.9, 'reviews': 0, 'has_site': True, 'notes': 'has bad com-place site'},
    {'name': 'The Home Tiles', 'ig': '', 'phone': '', 'category': 'Tile Store', 'location': 'Hialeah, FL', 'rating': 4.8, 'reviews': 0, 'has_site': True, 'notes': 'thehometiles.com exists but bad'},
]

new_ig_targets = [
    {'name': 'Handyman Jamal', 'ig': 'handymanjamal', 'category': 'Handyman', 'location': 'Miami, FL'},
    {'name': 'Handyman Miami', 'ig': 'handyman_miami1', 'category': 'Handyman', 'location': 'Miami, FL'},
    {'name': 'Handyman Jonathan', 'ig': 'handyman_jonathan', 'category': 'Handyman', 'location': 'Miami, FL'},
    {'name': 'Rickys Pressure Cleaning LLC', 'ig': 'rickyspressurecleaningllc', 'category': 'Pressure Cleaning', 'location': 'South Florida'},
    {'name': 'Nathans Pressure Washing', 'ig': 'nathanspressurewashing', 'category': 'Pressure Washing', 'location': 'Fort Lauderdale, FL'},
    {'name': 'Ronin Pressure Washing', 'ig': 'roninpressurewashing', 'category': 'Pressure Washing', 'location': 'South Florida'},
    {'name': 'Angel Tree Service 305', 'ig': 'angeltreeservice305', 'category': 'Tree Service', 'location': 'Miami, FL'},
    {'name': 'Osuna Ornamental Fences', 'ig': 'osuna_ornamental_fences', 'category': 'Fence Contractor', 'location': 'Miami, FL'},
    {'name': 'Yuri Fencing LLC', 'ig': 'yuri_fencing_llc', 'category': 'Fence Contractor', 'location': 'Miami, FL'},
    {'name': 'Miami Fence Medina', 'ig': 'miami_fence_medina', 'category': 'Fence Contractor', 'location': 'Miami, FL'},
    {'name': 'Evelio Fence', 'ig': 'eveliofence', 'category': 'Fence Contractor', 'location': 'Miami, FL'},
    {'name': 'Miami Muscle Junk Removal', 'ig': 'miamimusclejunkremoval', 'category': 'Junk Removal', 'location': 'Miami, FL'},
    {'name': 'Miami Vice Junk Removal', 'ig': 'miamivice_junkremoval', 'category': 'Junk Removal', 'location': 'Miami, FL'},
    {'name': 'Mia Haul Away', 'ig': 'miahaulaway', 'category': 'Junk Removal', 'location': 'Miami, FL'},
    {'name': 'Paolo Services Paint', 'ig': 'paoloservicespaint', 'category': 'Painting', 'location': 'Miami, FL'},
    {'name': 'AM Painting Contractors LLC', 'ig': 'ampaintingcontractorsllc', 'category': 'Painting', 'location': 'Miami, FL'},
    {'name': 'Beluga Pool Service', 'ig': 'belugapoolservice', 'category': 'Pool Service', 'location': 'Miami, FL'},
    {'name': 'Green Leaf Pool', 'ig': 'greenleafpool', 'category': 'Pool Service', 'location': 'Miami, FL'},
    {'name': 'Miami Concrete Designs', 'ig': 'miami_concrete_designs', 'category': 'Concrete Contractor', 'location': 'Miami, FL'},
    {'name': 'SFF Landscape Design', 'ig': 'sfflandscape_design', 'category': 'Landscape Design', 'location': 'South Florida'},
    {'name': 'Pastor Property Maintenance', 'ig': 'pastorpropertymaintenance', 'category': 'Property Maintenance', 'location': 'Miami, FL'},
    {'name': 'Miami Tile', 'ig': 'miami_tile', 'category': 'Tile Contractor', 'location': 'Miami, FL'},
    {'name': 'Fence Services', 'ig': 'fence_services', 'category': 'Fence Contractor', 'location': 'Miami, FL'},
    {'name': 'King Tower Inc', 'ig': 'kingtowerinc', 'category': 'Construction', 'location': 'Miami, FL'},
    {'name': 'MIBE Roofing', 'ig': 'miberoofing', 'category': 'Roofing', 'location': 'Miami, FL'},
    {'name': 'Rausa Roofing', 'ig': 'rausaroofing', 'category': 'Roofing', 'location': 'Miami, FL'},
    {'name': 'Lawncierge', 'ig': 'lawncierge', 'category': 'Lawn Care', 'location': 'Broward County, FL'},
    {'name': 'Smiths PLC', 'ig': 'smiths.plc', 'category': 'Lawn Care', 'location': 'Broward County, FL'},
    {'name': 'The Grass Lady', 'ig': 'the.grass.lady', 'category': 'Artificial Turf', 'location': 'South Florida'},
    {'name': 'Aleman Sprinklers', 'ig': 'alemansprinklers', 'category': 'Sprinkler/Irrigation', 'location': 'Miami, FL'},
    {'name': 'AP Irrigations', 'ig': 'apirrigations', 'category': 'Irrigation', 'location': 'South Florida'},
    {'name': 'Green Team Sprinklers', 'ig': 'greenteamsprinklers', 'category': 'Sprinkler/Irrigation', 'location': 'South Florida'},
    {'name': 'Benny and the Moving', 'ig': 'bennyandthemoving', 'category': 'Moving Service', 'location': 'Miami, FL'},
]

# Combine
for t in new_ig_targets:
    t['phone'] = t.get('phone', '')
    t['rating'] = t.get('rating', 0)
    t['reviews'] = t.get('reviews', 0)
    t['has_site'] = False
    t['notes'] = 'IG-only, confirmed no website'

master = original_valid + new_ig_targets
print(f"Original targets: {len(original_valid)}")
print(f"New IG targets: {len(new_ig_targets)}")
print(f"GRAND TOTAL: {len(master)}")

with open('C:/Users/ajsup/sam_contractor_sites/master_targets.json', 'w', encoding='utf-8') as f:
    json.dump(master, f, indent=2, ensure_ascii=False)

print(f"\nSaved master_targets.json")
print("\n=== ALL TARGETS WITH INSTAGRAM (DM-able) ===")
dm_targets = [t for t in master if t.get('ig')]
for i, t in enumerate(dm_targets, 1):
    print(f"{i:2d}. {t['name']} | @{t['ig']} | {t['category']} | {t['location']}")
print(f"\nDM-able targets: {len(dm_targets)}")
print(f"Phone/other outreach targets: {len(master) - len(dm_targets)}")
