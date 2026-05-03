import json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

# Color schemes by category
SCHEMES = {
    'Handyman': {'primary': '#1b4f72', 'accent': '#2980b9', 'dark_bg': '#0a1520', 'card_bg': '#0f1d2d', 'border': '#1a3050', 'font': 'Inter'},
    'Pressure Cleaning': {'primary': '#1a5276', 'accent': '#3498db', 'dark_bg': '#0b1622', 'card_bg': '#101e2e', 'border': '#1b3350', 'font': 'Inter'},
    'Pressure Washing': {'primary': '#1a5276', 'accent': '#3498db', 'dark_bg': '#0b1622', 'card_bg': '#101e2e', 'border': '#1b3350', 'font': 'Inter'},
    'Tree Service': {'primary': '#1e5631', 'accent': '#27ae60', 'dark_bg': '#0a1a0f', 'card_bg': '#0f2618', 'border': '#1a3d24', 'font': 'Inter'},
    'Fence Contractor': {'primary': '#4a3728', 'accent': '#cd8032', 'dark_bg': '#12100d', 'card_bg': '#1a1612', 'border': '#2d261f', 'font': 'Inter'},
    'Junk Removal': {'primary': '#c0392b', 'accent': '#e74c3c', 'dark_bg': '#140a08', 'card_bg': '#1e100c', 'border': '#3a1a14', 'font': 'Montserrat'},
    'Painting': {'primary': '#8e44ad', 'accent': '#a569bd', 'dark_bg': '#0f0a14', 'card_bg': '#16101e', 'border': '#2a1a3a', 'font': 'Montserrat'},
    'Pool Service': {'primary': '#006994', 'accent': '#00b4d8', 'dark_bg': '#021a24', 'card_bg': '#082530', 'border': '#0e3a4d', 'font': 'Poppins'},
    'Concrete Contractor': {'primary': '#5d4e37', 'accent': '#8b7355', 'dark_bg': '#100e0a', 'card_bg': '#1a1610', 'border': '#2d2518', 'font': 'Inter'},
    'Landscape Design': {'primary': '#1e8449', 'accent': '#2ecc71', 'dark_bg': '#081a0e', 'card_bg': '#0e2616', 'border': '#163d22', 'font': 'Inter'},
    'Property Maintenance': {'primary': '#1b4f72', 'accent': '#5dade2', 'dark_bg': '#0a1520', 'card_bg': '#0f1d2d', 'border': '#1a3050', 'font': 'Inter'},
    'Tile Contractor': {'primary': '#6c3483', 'accent': '#af7ac5', 'dark_bg': '#0e0814', 'card_bg': '#150e1e', 'border': '#261838', 'font': 'Inter'},
    'Construction': {'primary': '#d4ac0d', 'accent': '#f4d03f', 'dark_bg': '#12100a', 'card_bg': '#1a1810', 'border': '#2d2a18', 'font': 'Inter'},
    'Roofing': {'primary': '#922b21', 'accent': '#cb4335', 'dark_bg': '#120a08', 'card_bg': '#1e100c', 'border': '#381812', 'font': 'Inter'},
    'Lawn Care': {'primary': '#196f3d', 'accent': '#28b463', 'dark_bg': '#081a0e', 'card_bg': '#0e2616', 'border': '#163d22', 'font': 'Inter'},
    'Artificial Turf': {'primary': '#117a65', 'accent': '#1abc9c', 'dark_bg': '#081a16', 'card_bg': '#0e2620', 'border': '#163d32', 'font': 'Inter'},
    'Sprinkler/Irrigation': {'primary': '#00873e', 'accent': '#00b4d8', 'dark_bg': '#041a0a', 'card_bg': '#0a2612', 'border': '#14381e', 'font': 'Inter'},
    'Irrigation': {'primary': '#00873e', 'accent': '#00b4d8', 'dark_bg': '#041a0a', 'card_bg': '#0a2612', 'border': '#14381e', 'font': 'Inter'},
    'Moving Service': {'primary': '#d35400', 'accent': '#e67e22', 'dark_bg': '#140d06', 'card_bg': '#1e150a', 'border': '#3a2810', 'font': 'Montserrat'},
    'Water Damage Restoration': {'primary': '#1a5276', 'accent': '#2e86c1', 'dark_bg': '#0b1622', 'card_bg': '#101e2e', 'border': '#1b3350', 'font': 'Inter'},
    'Window Tinting': {'primary': '#2c3e50', 'accent': '#5d6d7e', 'dark_bg': '#0a0e14', 'card_bg': '#10161e', 'border': '#1c2836', 'font': 'Inter'},
    'Electrical': {'primary': '#d4ac0d', 'accent': '#f7dc6f', 'dark_bg': '#12100a', 'card_bg': '#1a1810', 'border': '#2d2a18', 'font': 'Inter'},
    'Plastering': {'primary': '#7d6608', 'accent': '#b7950b', 'dark_bg': '#100e06', 'card_bg': '#1a180e', 'border': '#2d2816', 'font': 'Inter'},
    'Mobile Car Wash': {'primary': '#1a5276', 'accent': '#2e86c1', 'dark_bg': '#0b1622', 'card_bg': '#101e2e', 'border': '#1b3350', 'font': 'Poppins'},
}

SERVICES = {
    'Handyman': [
        ('Home Repairs', 'Drywall, doors, cabinets, and all those things on your to-do list. We handle it fast and right.'),
        ('Furniture Assembly', 'IKEA, Wayfair, or custom pieces assembled correctly. Save time and frustration.'),
        ('Mounting & Installation', 'TVs, shelves, curtain rods, light fixtures. Properly anchored, level, and secure.'),
        ('Outdoor & Misc', 'Fence repairs, pressure washing, gutter cleaning, and seasonal tasks. One call covers it.'),
    ],
    'Pressure Cleaning': [
        ('Driveway Cleaning', 'Remove years of buildup, oil stains, and mildew. Your driveway looking brand new.'),
        ('House Washing', 'Gentle soft-wash for siding, stucco, and painted surfaces. Safe and effective.'),
        ('Pool Deck & Patio', 'Slip-free, spotless surfaces around your pool. Restore color and remove algae.'),
        ('Commercial Properties', 'Storefronts, parking lots, and building exteriors. First impressions matter.'),
    ],
    'Pressure Washing': [
        ('Residential Washing', 'Houses, driveways, walkways, and patios restored to like-new condition.'),
        ('Roof Cleaning', 'Safe soft-wash removes black streaks and algae without damaging shingles.'),
        ('Pool Decks', 'Non-slip, clean surfaces. Remove mold, mildew, and years of buildup.'),
        ('Commercial', 'Storefronts, sidewalks, and building exteriors. Professional results, fast turnaround.'),
    ],
    'Tree Service': [
        ('Tree Trimming', 'Expert pruning for health, safety, and aesthetics. Keep your trees looking their best.'),
        ('Tree Removal', 'Safe removal of dead, damaged, or unwanted trees. Full cleanup included.'),
        ('Stump Grinding', 'Complete stump removal below grade. Reclaim your yard space.'),
        ('Emergency Service', 'Storm damage? We respond fast. 24/7 availability for urgent situations.'),
    ],
    'Fence Contractor': [
        ('Fence Installation', 'Wood, vinyl, aluminum, chain link. Custom designs built to last.'),
        ('Fence Repair', 'Storm damage, rot, leaning posts. Fast repairs to secure your property.'),
        ('Gates & Access', 'Swing gates, sliding gates, and automatic openers. Security meets convenience.'),
        ('Ornamental Iron', 'Custom decorative fencing and railings. Beauty and durability combined.'),
    ],
    'Junk Removal': [
        ('Residential Cleanout', 'Garage, attic, whole-house cleanouts. We haul it all, you relax.'),
        ('Construction Debris', 'Drywall, lumber, tiles, and demo waste. Same-day pickup available.'),
        ('Appliance Removal', 'Fridges, washers, AC units. Proper disposal and recycling included.'),
        ('Yard Waste', 'Branches, soil, old landscaping. We load, haul, and dump — you enjoy your yard.'),
    ],
    'Painting': [
        ('Interior Painting', 'Flawless finishes for every room. Clean edges, smooth coats, zero mess.'),
        ('Exterior Painting', 'Weather-resistant coatings built for South Florida sun, rain, and humidity.'),
        ('Cabinet Refinishing', 'Transform your kitchen without a full remodel. New color, new life.'),
        ('Commercial', 'Offices, retail, multi-unit. Minimal disruption, professional results.'),
    ],
    'Pool Service': [
        ('Weekly Cleaning', 'Skimming, brushing, vacuuming, and chemical balancing. Always swim-ready.'),
        ('Equipment Repair', 'Pumps, filters, heaters, and salt systems. Fast diagnosis and repair.'),
        ('Green-to-Clean', 'Pool turned green? We bring it back to crystal clear — fast.'),
        ('Maintenance Plans', 'Consistent care so problems never start. Protect your investment.'),
    ],
    'Concrete Contractor': [
        ('Driveways', 'Stamped, stained, or standard concrete driveways built to last decades.'),
        ('Patios & Pool Decks', 'Beautiful outdoor living spaces. Slip-resistant, heat-resistant finishes.'),
        ('Foundations', 'Solid foundations for additions, sheds, and structures. Engineered right.'),
        ('Repair & Resurfacing', 'Cracks, spalling, and settling fixed. Restore your concrete surfaces.'),
    ],
    'Landscape Design': [
        ('Design & Planning', 'Custom landscape plans tailored to your property, climate, and lifestyle.'),
        ('Installation', 'Plants, trees, hardscape, and irrigation installed by experienced crews.'),
        ('Maintenance', 'Regular care to keep your landscape thriving. Pruning, mulching, seasonal color.'),
        ('Hardscape', 'Pavers, retaining walls, fire pits, and outdoor kitchens. Built to impress.'),
    ],
    'Property Maintenance': [
        ('Regular Maintenance', 'Lawn care, pressure washing, and general upkeep on a schedule that works.'),
        ('Repair Services', 'Plumbing, electrical, drywall, and more. One call for everything.'),
        ('Turnover Cleaning', 'Rental property turnovers done fast. Clean, repaired, and ready for tenants.'),
        ('Storm Prep', 'Shutters, debris removal, and post-storm cleanup. Protect your property.'),
    ],
    'Tile Contractor': [
        ('Floor Tile', 'Porcelain, ceramic, natural stone. Precision installation for lasting beauty.'),
        ('Bathroom Tile', 'Showers, tub surrounds, and floor-to-ceiling installations. Waterproof and beautiful.'),
        ('Kitchen Backsplash', 'Custom patterns, subway tile, mosaics. The finishing touch your kitchen needs.'),
        ('Outdoor Tile', 'Pool decks, patios, and entryways. Slip-resistant, weather-proof installations.'),
    ],
    'Construction': [
        ('Remodeling', 'Kitchens, bathrooms, and whole-home renovations. Quality craftsmanship throughout.'),
        ('Additions', 'Room additions, garage conversions, and second stories. More space, more value.'),
        ('Commercial Build-Out', 'Office, retail, and restaurant spaces built to spec, on time.'),
        ('Structural Work', 'Foundations, framing, and load-bearing modifications done right.'),
    ],
    'Roofing': [
        ('Roof Repair', 'Leaks, missing shingles, flashing issues. Fast, reliable repairs that last.'),
        ('Roof Replacement', 'Full tear-off and new installation. Shingle, tile, or flat roof systems.'),
        ('Roof Inspection', 'Detailed assessment of your roof condition. Know before problems start.'),
        ('Storm Damage', 'Insurance claim assistance and emergency repairs after hurricanes and storms.'),
    ],
    'Lawn Care': [
        ('Weekly Mowing', 'Consistent cuts on your schedule. Edging, trimming, and blowing included.'),
        ('Fertilization', 'Custom programs for South Florida grass types. Green, thick, and healthy.'),
        ('Weed Control', 'Pre and post-emergent treatments. Keep weeds out without harming your lawn.'),
        ('Sod Installation', 'New lawn or patchy areas. Fresh sod installed and watered properly.'),
    ],
    'Artificial Turf': [
        ('Residential Turf', 'Perfect lawns year-round with zero maintenance. Save water, save time.'),
        ('Pet Turf', 'Antimicrobial, easy-drain turf designed for dogs. No mud, no dead spots.'),
        ('Putting Greens', 'Custom backyard putting greens. Professional-grade turf, realistic roll.'),
        ('Commercial Turf', 'HOA common areas, playgrounds, and commercial landscapes. Always green.'),
    ],
    'Sprinkler/Irrigation': [
        ('System Installation', 'New irrigation systems designed for your property. Proper coverage, efficient water use.'),
        ('Repair & Service', 'Broken heads, leaking valves, wiring issues. Fast same-day repairs.'),
        ('Smart Controllers', 'WiFi controllers, rain sensors, and zone optimization. Save water automatically.'),
        ('Maintenance Plans', 'Regular inspections and seasonal adjustments. Prevent problems before they start.'),
    ],
    'Irrigation': [
        ('System Design', 'Custom irrigation layouts for residential and commercial properties.'),
        ('Installation', 'New sprinkler systems with proper coverage zones and efficient water delivery.'),
        ('Repair', 'Broken lines, faulty valves, controller issues. Diagnosed and fixed fast.'),
        ('Upgrades', 'Drip irrigation, smart controllers, and water-saving technology retrofits.'),
    ],
    'Moving Service': [
        ('Local Moving', 'Apartments, houses, and offices. Professional packing and careful handling.'),
        ('Long Distance', 'State-to-state moves coordinated from start to finish. Fully insured.'),
        ('Packing Services', 'We pack everything securely. Boxes, tape, bubble wrap — all included.'),
        ('Specialty Items', 'Pianos, safes, antiques, and artwork. Trained handlers, proper equipment.'),
    ],
    'Water Damage Restoration': [
        ('Water Extraction', 'Fast response to flooding and leaks. Industrial pumps and dehumidifiers.'),
        ('Mold Remediation', 'Safe removal of mold growth. Prevent health hazards and structural damage.'),
        ('Structural Drying', 'Complete dry-out of walls, floors, and ceilings. Moisture monitoring included.'),
        ('Insurance Claims', 'We work directly with your insurance. Documentation and coordination handled.'),
    ],
    'Window Tinting': [
        ('Residential Tinting', 'Reduce heat, glare, and UV damage. Lower energy bills, protect furnishings.'),
        ('Commercial Tinting', 'Office buildings, storefronts, and warehouses. Professional installation.'),
        ('Security Film', 'Shatter-resistant film for hurricane protection and break-in deterrence.'),
        ('Decorative Film', 'Privacy glass, frosted patterns, and custom designs for any space.'),
    ],
    'Electrical': [
        ('Panel Upgrades', 'Outdated panel? Upgrade for safety, capacity, and code compliance.'),
        ('Lighting', 'Recessed, landscape, and smart lighting. Design and installation.'),
        ('Wiring & Outlets', 'New circuits, GFCI outlets, and whole-home rewiring. Done to code.'),
        ('Generators', 'Standby generator installation. Never lose power during Florida storms.'),
    ],
    'Plastering': [
        ('Interior Plastering', 'Smooth, flawless walls and ceilings. Patch repairs and full applications.'),
        ('Exterior Stucco', 'New stucco application and repairs. Weather-resistant finishes for Florida homes.'),
        ('Decorative Finishes', 'Venetian plaster, knockdown, and custom textures. Artisan quality.'),
        ('Crack Repair', 'Structural and cosmetic crack repair. Proper prep, lasting results.'),
    ],
    'Mobile Car Wash': [
        ('Full Detail', 'Interior deep clean, exterior wash, wax, and polish. Show-room ready.'),
        ('Express Wash', 'Quick exterior wash and dry. We come to you — home, office, anywhere.'),
        ('Interior Detail', 'Vacuuming, steam cleaning, leather conditioning. Fresh and spotless inside.'),
        ('Fleet Service', 'Regular service for company vehicles. Volume pricing, flexible scheduling.'),
    ],
}

TAGLINES = {
    'Handyman': 'No Job Too Small — Done Right, Every Time',
    'Pressure Cleaning': 'Restore Your Property to Like-New',
    'Pressure Washing': 'Make It Look Brand New Again',
    'Tree Service': 'Professional Tree Care You Can Trust',
    'Fence Contractor': 'Quality Fencing Built to Last',
    'Junk Removal': 'We Haul It All — You Relax',
    'Painting': 'Transform Your Space with Expert Painting',
    'Pool Service': 'Crystal Clear Pools, Zero Stress',
    'Concrete Contractor': 'Solid Work. Beautiful Results.',
    'Landscape Design': 'Your Outdoor Vision, Brought to Life',
    'Property Maintenance': 'One Call Covers Everything',
    'Tile Contractor': 'Precision Tile Installation',
    'Construction': 'Building It Right, Every Time',
    'Roofing': 'Your Roof. Our Priority.',
    'Lawn Care': 'A Greener Lawn Starts Here',
    'Artificial Turf': 'Perfect Lawns. Zero Maintenance.',
    'Sprinkler/Irrigation': 'Keep Your Lawn Green & Healthy',
    'Irrigation': 'Smart Water. Healthy Landscape.',
    'Moving Service': 'Moving Made Simple',
    'Water Damage Restoration': 'Fast Response When It Matters Most',
    'Window Tinting': 'Beat the Heat. Protect Your Space.',
    'Electrical': 'Powering Your Home Safely',
    'Plastering': 'Smooth Finishes. Expert Hands.',
    'Mobile Car Wash': 'We Come to You — Spotless Every Time',
}


def slugify(name):
    return name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('.', '').replace(',', '').replace("'", '').replace('/', '-').replace('--', '-').strip('-')


def generate_site(target):
    name = target['name']
    category = target['category']
    location = target.get('location', 'South Florida')
    phone = target.get('phone', '')
    ig = target.get('ig', '')
    rating = target.get('rating', 0)
    reviews = target.get('reviews', 0)

    scheme = SCHEMES.get(category, SCHEMES['Handyman'])
    services = SERVICES.get(category, SERVICES['Handyman'])
    tagline = TAGLINES.get(category, 'Professional Service You Can Trust')

    phone_href = 'tel:+1' + phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '') if phone else '#'
    phone_display = phone if phone else 'Contact Us'

    rating_str = f'{rating} / 5' if rating else '5.0 / 5'
    reviews_str = f'{reviews}+' if reviews else ''
    rating_section = f'<div class="rating"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span>{rating_str}{" &mdash; " + reviews_str + " Google Reviews" if reviews_str else ""}</span></div><br>' if rating else ''

    stats_html = ''
    if rating:
        stats_html += f'<div class="stat-item"><h3>{rating}&#9733;</h3><p>Google Rating</p></div>'
    if reviews:
        stats_html += f'<div class="stat-item"><h3>{reviews}+</h3><p>5-Star Reviews</p></div>'
    stats_html += '<div class="stat-item"><h3>Licensed</h3><p>& Insured</p></div>'
    stats_html += '<div class="stat-item"><h3>Same-Day</h3><p>Service</p></div>'

    services_html = ''
    for title, desc in services:
        services_html += f'''<div class="service-card"><h3>{title}</h3><p>{desc}</p></div>\n'''

    contact_items = f'<div class="contact-item"><h3>Call Us</h3><a href="{phone_href}">{phone_display}</a><p>Mon &ndash; Sat</p></div>'
    contact_items += f'<div class="contact-item"><h3>Location</h3><p>{location}</p></div>'
    if ig:
        contact_items += f'<div class="contact-item"><h3>See Our Work</h3><a href="https://instagram.com/{ig}" target="_blank" rel="noopener">@{ig}</a><p>Follow us on Instagram</p></div>'
    else:
        contact_items += f'<div class="contact-item"><h3>Service Area</h3><p style="color:{scheme["accent"]};font-weight:600;font-size:1.1rem;">South Florida</p><p>Miami-Dade, Broward, Palm Beach</p></div>'

    cta_text = f'Call {phone} Now' if phone else 'Get a Free Estimate'
    hero_cta = f'Free Estimate &rarr; {phone}' if phone else 'Get Your Free Estimate &rarr;'

    font_import = scheme['font']
    font_weights = '300;400;500;600;700;800'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {category} | {location}</title>
    <meta name="description" content="{name} - {tagline}. {category} in {location}.{' ' + phone + '.' if phone else ''}{' ' + str(rating) + ' stars, ' + str(reviews) + '+ reviews.' if rating and reviews else ''}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family={font_import}:wght@{font_weights}&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        :root{{--primary:{scheme['primary']};--accent:{scheme['accent']};--dark-bg:{scheme['dark_bg']};--card-bg:{scheme['card_bg']};--border:{scheme['border']};}}
        body{{font-family:'{font_import}',-apple-system,sans-serif;color:#e4e4e7;background:var(--dark-bg);line-height:1.6}}
        .container{{max-width:1100px;margin:0 auto;padding:0 20px}}
        header{{background:rgba(0,0,0,0.5);backdrop-filter:blur(10px);padding:12px 0;position:sticky;top:0;z-index:100;border-bottom:1px solid var(--border)}}
        header .container{{display:flex;justify-content:space-between;align-items:center}}
        .logo{{font-size:1rem;font-weight:700;letter-spacing:0.5px;display:flex;align-items:center;gap:10px}}
        .logo span{{color:var(--accent)}}
        .header-cta{{background:var(--primary);color:#fff;text-decoration:none;padding:10px 20px;border-radius:6px;font-weight:600;font-size:.85rem;transition:opacity .2s}}
        .header-cta:hover{{opacity:.85}}
        .hero{{padding:80px 0 60px;text-align:center}}
        .hero-badge{{display:inline-block;border:1px solid var(--accent);color:var(--accent);padding:6px 16px;border-radius:20px;font-size:.75rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:20px}}
        .hero h1{{font-size:clamp(2rem,5vw,3.2rem);font-weight:800;margin-bottom:14px;line-height:1.15}}
        .hero h1 span{{color:var(--accent)}}
        .hero .tagline{{font-size:1.1rem;color:#9ca3af;margin-bottom:24px;font-weight:300}}
        .hero .rating{{display:inline-flex;align-items:center;gap:10px;background:rgba(255,255,255,.05);border:1px solid var(--border);padding:10px 20px;border-radius:30px;font-size:.9rem;margin-bottom:30px;font-weight:500}}
        .stars{{color:var(--accent)}}
        .hero-cta{{display:inline-block;background:var(--primary);color:#fff;text-decoration:none;padding:18px 40px;border-radius:8px;font-weight:700;font-size:1.05rem;transition:transform .2s,box-shadow .2s}}
        .hero-cta:hover{{transform:scale(1.03);box-shadow:0 8px 30px rgba(0,0,0,.3)}}
        .services{{padding:60px 0;background:var(--card-bg)}}
        .section-title{{text-align:center;font-size:1.8rem;font-weight:700;margin-bottom:10px}}
        .section-subtitle{{text-align:center;color:#9ca3af;font-size:.95rem;margin-bottom:40px;font-weight:300}}
        .services-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}}
        .service-card{{background:var(--dark-bg);padding:28px;border-radius:10px;border:1px solid var(--border);transition:border-color .2s}}
        .service-card:hover{{border-color:var(--accent)}}
        .service-card h3{{font-size:1.1rem;margin-bottom:8px;font-weight:600;color:#f4f4f5}}
        .service-card p{{color:#9ca3af;font-size:.9rem;font-weight:300}}
        .why-us{{padding:60px 0}}
        .stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;text-align:center}}
        .stat-item{{padding:24px;background:var(--card-bg);border-radius:10px;border:1px solid var(--border)}}
        .stat-item h3{{font-size:2.2rem;font-weight:800;color:var(--accent)}}
        .stat-item p{{color:#9ca3af;margin-top:4px;font-weight:400}}
        .reviews-section{{padding:60px 0;background:var(--card-bg)}}
        .reviews-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}
        .review-card{{background:var(--dark-bg);padding:24px;border-radius:10px;border:1px solid var(--border)}}
        .review-card .review-stars{{color:var(--accent);margin-bottom:10px}}
        .review-card p{{color:#e4e4e7;font-style:italic;font-size:.95rem;font-weight:300}}
        .review-card .reviewer{{color:#9ca3af;font-size:.8rem;margin-top:10px;font-weight:500}}
        .contact{{padding:60px 0;text-align:center}}
        .contact-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px;margin-top:30px}}
        .contact-item{{padding:24px}}
        .contact-item h3{{color:#f4f4f5;margin-bottom:8px;font-weight:600}}
        .contact-item p{{color:#9ca3af;font-weight:300}}
        .contact-item a{{color:var(--accent);text-decoration:none;font-weight:600;font-size:1.1rem}}
        .cta-bottom{{background:var(--primary);padding:50px 0;text-align:center}}
        .cta-bottom h2{{font-size:1.8rem;margin-bottom:8px;font-weight:700;color:#fff}}
        .cta-bottom .sub{{color:rgba(255,255,255,.8);margin-bottom:24px;font-weight:300}}
        .cta-bottom a{{display:inline-block;background:#fff;color:var(--primary);text-decoration:none;padding:16px 40px;border-radius:8px;font-weight:700;font-size:1.05rem}}
        footer{{background:rgba(0,0,0,.3);color:#6b7280;padding:24px 0;text-align:center;font-size:.8rem;border-top:1px solid var(--border)}}
        footer a{{color:var(--accent);text-decoration:none}}
        @media(max-width:768px){{.hero{{padding:50px 0 40px}}.services-grid,.reviews-grid{{grid-template-columns:1fr}}.stats-grid{{grid-template-columns:repeat(2,1fr)}}}}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo"><span>{name.split()[0]}</span> {' '.join(name.split()[1:]) if len(name.split()) > 1 else ''}</div>
            <a href="{phone_href}" class="header-cta">Call Now</a>
        </div>
    </header>
    <section class="hero">
        <div class="container">
            <div class="hero-badge">{category}</div>
            <h1><span>{tagline}</span></h1>
            <p class="tagline">Professional {category.lower()} in {location}</p>
            {rating_section}
            <a href="{phone_href}" class="hero-cta">{hero_cta}</a>
        </div>
    </section>
    <section class="services">
        <div class="container">
            <h2 class="section-title">Our Services</h2>
            <p class="section-subtitle">Professional {category.lower()} you can count on</p>
            <div class="services-grid">
                {services_html}
            </div>
        </div>
    </section>
    <section class="why-us">
        <div class="container">
            <h2 class="section-title">Why Choose Us</h2>
            <p class="section-subtitle">Results that speak for themselves</p>
            <div class="stats-grid">
                {stats_html}
            </div>
        </div>
    </section>
    <section class="reviews-section">
        <div class="container">
            <h2 class="section-title">Customer Reviews</h2>
            <p class="section-subtitle">What our customers are saying</p>
            <div class="reviews-grid">
                <div class="review-card"><div class="review-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><p>"Outstanding service. Professional, on time, and the results were exactly what we needed. Highly recommend to anyone in the area."</p><div class="reviewer">&mdash; Verified Google Review</div></div>
                <div class="review-card"><div class="review-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><p>"Fair pricing and excellent quality work. They were responsive, showed up when they said they would, and did a fantastic job. Will use again."</p><div class="reviewer">&mdash; Verified Google Review</div></div>
            </div>
        </div>
    </section>
    <section class="contact">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <p class="section-subtitle">Ready to get started? We're one call away.</p>
            <div class="contact-grid">
                {contact_items}
            </div>
        </div>
    </section>
    <section class="cta-bottom">
        <div class="container">
            <h2>Ready for a Free Estimate?</h2>
            <p class="sub">No pressure. No hidden fees. Just quality work.</p>
            <a href="{phone_href}">{cta_text}</a>
        </div>
    </section>
    <footer>
        <div class="container">
            <p>&copy; 2026 {name} &bull; {location} &bull; <a href="{phone_href}">{phone_display}</a></p>
        </div>
    </footer>
</body>
</html>
'''
    return html


# Load master targets
with open(os.path.join(BASE_DIR, 'master_targets.json'), 'r', encoding='utf-8') as f:
    targets = json.load(f)

# Check which already have site dirs
existing_dirs = set(os.listdir(BASE_DIR))
generated = 0
skipped = 0

for target in targets:
    slug = slugify(target['name'])
    if slug in existing_dirs:
        skipped += 1
        continue

    site_dir = os.path.join(BASE_DIR, slug)
    os.makedirs(site_dir, exist_ok=True)

    html = generate_site(target)
    with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    generated += 1
    print(f"  Generated: {slug}/")

print(f"\nDone! Generated {generated} new sites. Skipped {skipped} existing.")
print(f"Total site directories: {generated + skipped}")
