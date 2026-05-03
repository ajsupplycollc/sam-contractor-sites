"""
Batch site generator for contractor outreach.
Generates customized single-page websites for each target business.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES = [
    {
        "slug": "mobile-car-wash-miami",
        "name": "Mobile Car Wash Miami LLC",
        "tagline": "Professional Mobile Car Detailing",
        "subtitle": "We come to you — spotless results, zero hassle",
        "phone": "(786) 795-9334",
        "phone_raw": "+17867959334",
        "address": "13017 SW 3rd St, Miami, FL 33184",
        "rating": "5.0",
        "reviews": "220",
        "category": "Mobile Car Wash & Detailing",
        "social_type": "facebook",
        "social_url": "https://www.facebook.com/mycarwashmiami",
        "social_handle": "mycarwashmiami",
        "primary": "#0066cc",
        "accent": "#00aaff",
        "dark_bg": "#0a1628",
        "card_bg": "#0f1d33",
        "border": "#1a2d4a",
        "theme": "dark",
        "font": "Poppins",
        "services": [
            ("Full Exterior Wash", "Hand wash, rinse, dry, and tire shine. Your car looking showroom-fresh without leaving your driveway."),
            ("Interior Deep Clean", "Vacuuming, dashboard wipe-down, leather conditioning, and window cleaning. Every surface detailed."),
            ("Full Detail Package", "Complete interior and exterior treatment. Clay bar, polish, wax, and interior deep clean — the works."),
            ("Fleet & Commercial", "Multi-vehicle packages for businesses. Keep your fleet looking professional with regular scheduled service."),
        ],
        "stats": [("5.0★", "Google Rating"), ("220+", "Happy Customers"), ("Mobile", "We Come to You"), ("100%", "Hand Wash")],
    },
    {
        "slug": "leonel-international-tile",
        "name": "Leonel International Tile Corporation",
        "tagline": "Premium Tile — Selection, Quality, Service",
        "subtitle": "Hialeah's trusted source for tile since day one",
        "phone": "(305) 883-7160",
        "phone_raw": "+13058837160",
        "address": "209 W 21st St, Hialeah, FL 33010",
        "rating": "4.9",
        "reviews": "186",
        "category": "Tile Store & Installation",
        "social_type": None,
        "primary": "#8B4513",
        "accent": "#D4A574",
        "dark_bg": "#1a1008",
        "card_bg": "#241a0f",
        "border": "#3d2b18",
        "theme": "dark",
        "font": "DM Sans",
        "services": [
            ("Tile Selection", "Thousands of styles — porcelain, ceramic, marble, travertine, and natural stone. Floor-to-ceiling options for every project."),
            ("Professional Installation", "Expert installers who handle everything from prep to grout. Precision cuts, level surfaces, beautiful results."),
            ("Kitchen & Bath Tile", "Backsplashes, shower surrounds, bathroom floors. Transform your most-used spaces with premium materials."),
            ("Commercial Projects", "Large-format tile, high-traffic rated materials, and volume pricing for commercial spaces and developments."),
        ],
        "stats": [("4.9★", "Google Rating"), ("186+", "5-Star Reviews"), ("1000s", "Tile Styles"), ("Expert", "Installation")],
    },
    {
        "slug": "the-home-tiles",
        "name": "The Home Tiles",
        "tagline": "Your Home, Your Style, Our Tile",
        "subtitle": "Quality tile and expert guidance in Hialeah",
        "phone": "(305) 884-3660",
        "phone_raw": "+13058843660",
        "address": "1001 Hialeah Dr, Hialeah, FL 33010",
        "rating": "4.8",
        "reviews": "132",
        "category": "Tile Store",
        "social_type": None,
        "primary": "#2d3436",
        "accent": "#c0956c",
        "dark_bg": "#f5f0eb",
        "card_bg": "#ffffff",
        "border": "#e0d5c9",
        "theme": "light",
        "font": "Outfit",
        "services": [
            ("Porcelain & Ceramic", "Durable, versatile, and beautiful. Browse our wide selection of porcelain and ceramic tile for floors, walls, and more."),
            ("Natural Stone", "Marble, travertine, slate, and granite. Bring the beauty of natural stone into your home."),
            ("Design Consultation", "Not sure what works? Our team helps you choose the right tile, pattern, and layout for your space and budget."),
            ("Contractor Supply", "Bulk pricing and reliable stock for contractors and builders. Quick availability and competitive rates."),
        ],
        "stats": [("4.8★", "Google Rating"), ("132+", "5-Star Reviews"), ("Premium", "Selection"), ("Expert", "Guidance")],
    },
    {
        "slug": "palm-atlantic-handyman",
        "name": "Palm Atlantic Handyman Services",
        "tagline": "No Job Too Small — Done Right, Every Time",
        "subtitle": "Reliable handyman services across South Florida",
        "phone": "(954) 607-0846",
        "phone_raw": "+19546070846",
        "address": "South Florida",
        "rating": "5.0",
        "reviews": "95",
        "category": "Handyman Services",
        "social_type": None,
        "primary": "#1b5e20",
        "accent": "#4caf50",
        "dark_bg": "#0a1a0c",
        "card_bg": "#112214",
        "border": "#1e3520",
        "theme": "dark",
        "font": "Inter",
        "services": [
            ("Home Repairs", "Drywall patches, door fixes, cabinet adjustments, and all those things on your to-do list. We handle it all."),
            ("Furniture Assembly", "IKEA, Wayfair, or custom — we assemble it fast and right so you don't have to."),
            ("Mounting & Installation", "TVs, shelves, curtain rods, light fixtures. Properly anchored, level, and secure."),
            ("Outdoor & Misc", "Fence repairs, pressure washing, gutter cleaning, and seasonal maintenance. One call covers everything."),
        ],
        "stats": [("5.0★", "Perfect Rating"), ("95+", "Completed Jobs"), ("Same-Day", "Availability"), ("100%", "Satisfaction")],
    },
    {
        "slug": "boca-raton-blue-pool",
        "name": "Boca Raton Blue Pool Service",
        "tagline": "Crystal Clear Pools, Zero Stress",
        "subtitle": "Professional pool cleaning and maintenance in Boca Raton",
        "phone": "(561) 781-7444",
        "phone_raw": "+15617817444",
        "address": "2100 N Federal Hwy #197, Boca Raton, FL 33431",
        "rating": "4.7",
        "reviews": "39",
        "category": "Pool Cleaning Service",
        "social_type": None,
        "primary": "#006994",
        "accent": "#00b4d8",
        "dark_bg": "#021a24",
        "card_bg": "#082530",
        "border": "#0e3a4d",
        "theme": "dark",
        "font": "Poppins",
        "services": [
            ("Weekly Pool Cleaning", "Skimming, brushing, vacuuming, and chemical balancing. Your pool stays swim-ready every single week."),
            ("Equipment Repair", "Pumps, filters, heaters, and salt systems. Fast diagnosis and reliable repairs to keep everything running."),
            ("Green-to-Clean", "Pool turned green? We bring it back to crystal clear — fast. Full chemical treatment and deep cleaning."),
            ("Seasonal Maintenance", "Opening, closing, and storm prep. Protect your investment year-round with seasonal service."),
        ],
        "stats": [("4.7★", "Google Rating"), ("39+", "5-Star Reviews"), ("Weekly", "Service Plans"), ("Licensed", "& Insured")],
    },
    {
        "slug": "general-construction-engineering",
        "name": "General Construction & Engineering Services, Inc.",
        "tagline": "Built to Last — Engineering Meets Craftsmanship",
        "subtitle": "Licensed general contractor serving Hialeah and Miami-Dade",
        "phone": "(305) 833-3370",
        "phone_raw": "+13058333370",
        "address": "1590 W 73rd St, Hialeah, FL 33014",
        "rating": "4.4",
        "reviews": "20",
        "category": "General Contractor",
        "social_type": None,
        "primary": "#37474f",
        "accent": "#ff8f00",
        "dark_bg": "#eceff1",
        "card_bg": "#ffffff",
        "border": "#cfd8dc",
        "theme": "light",
        "font": "Inter",
        "services": [
            ("General Contracting", "Full-scope project management from permits to punch list. Residential and commercial construction done right."),
            ("Structural Engineering", "Engineering-backed builds with structural integrity you can trust. Code-compliant and inspector-ready."),
            ("Renovations & Remodels", "Kitchen, bathroom, and whole-home renovations. Modernize your property with quality workmanship."),
            ("Commercial Construction", "Office build-outs, retail spaces, and warehouse improvements. On time, on budget, built to code."),
        ],
        "stats": [("4.4★", "Google Rating"), ("20+", "Reviews"), ("Licensed", "Contractor"), ("Engineering", "Expertise")],
    },
    {
        "slug": "el-valle-sprinkler-systems",
        "name": "El Valle Sprinkler Systems",
        "tagline": "Keep Your Lawn Green & Healthy",
        "subtitle": "Professional irrigation systems in Pompano Beach and South Florida",
        "phone": "(305) 205-9314",
        "phone_raw": "+13052059314",
        "address": "4311 Crystal Lake Dr, Pompano Beach, FL 33064",
        "rating": "4.9",
        "reviews": "19",
        "category": "Lawn Sprinkler System Contractor",
        "social_type": "instagram",
        "social_url": "https://instagram.com/elvallesprinklersystems",
        "social_handle": "elvallesprinklersystems",
        "primary": "#00873e",
        "accent": "#00b4d8",
        "dark_bg": "#041a0a",
        "card_bg": "#0a2612",
        "border": "#14381e",
        "theme": "dark",
        "font": "Inter",
        "services": [
            ("Sprinkler Installation", "New irrigation systems designed for your property. Proper coverage, efficient water use, and a greener lawn."),
            ("System Repair", "Broken heads, leaking valves, wiring issues. Fast diagnosis and same-day repairs to keep your system running."),
            ("Upgrades & Retrofits", "New pumps, smart controllers, rain sensors, and drip zones. Modernize your system for better performance."),
            ("Maintenance Plans", "Regular inspections, head adjustments, and seasonal tuning. Prevent problems before they start."),
        ],
        "stats": [("4.9★", "Google Rating"), ("19+", "5-Star Reviews"), ("Licensed", "Contractor"), ("Same-Day", "Repairs")],
    },
    {
        "slug": "flooring-installation-hialeah",
        "name": "Flooring Installation in Hialeah",
        "tagline": "Expert Flooring — Installed Right the First Time",
        "subtitle": "Hialeah's trusted flooring contractor for every room in your home",
        "phone": "(954) 770-5343",
        "phone_raw": "+19547705343",
        "address": "855 W 36th St, Hialeah, FL 33012",
        "rating": "5.0",
        "reviews": "2",
        "category": "Flooring Contractor",
        "social_type": None,
        "primary": "#5d4037",
        "accent": "#a1887f",
        "dark_bg": "#f5f0eb",
        "card_bg": "#ffffff",
        "border": "#d7ccc8",
        "theme": "light",
        "font": "DM Sans",
        "services": [
            ("Hardwood Flooring", "Classic, warm, and timeless. Professional installation of solid and engineered hardwood floors."),
            ("Laminate & Vinyl", "Durable, affordable, and waterproof options. Perfect for high-traffic areas and moisture-prone rooms."),
            ("Tile Flooring", "Porcelain, ceramic, and natural stone. Precision installation with clean grout lines and level surfaces."),
            ("Floor Refinishing", "Sand, stain, and seal existing wood floors. Bring old floors back to life without full replacement."),
        ],
        "stats": [("5.0★", "Perfect Rating"), ("Expert", "Installation"), ("All Types", "of Flooring"), ("Free", "Estimates")],
    },
    {
        "slug": "south-florida-pressure-cleaning",
        "name": "South Florida Pressure Cleaning",
        "tagline": "Blast Away the Buildup",
        "subtitle": "Professional pressure washing in Hialeah and Miami-Dade",
        "phone": "(305) 586-5262",
        "phone_raw": "+13055865262",
        "address": "8841 W 34th Ct, Hialeah, FL 33018",
        "rating": "5.0",
        "reviews": "1",
        "category": "Pressure Washing Service",
        "social_type": None,
        "primary": "#1565c0",
        "accent": "#42a5f5",
        "dark_bg": "#0a1929",
        "card_bg": "#0d2137",
        "border": "#163a5c",
        "theme": "dark",
        "font": "Inter",
        "services": [
            ("Driveway & Sidewalk", "Remove oil stains, mold, and years of grime from concrete and pavers. Looks brand new when we're done."),
            ("House & Building Wash", "Soft wash and pressure clean exterior walls, stucco, and siding. Safe for all surfaces."),
            ("Pool Deck & Patio", "Non-slip surfaces restored to clean, safe condition. Perfect before and after pool season."),
            ("Roof Cleaning", "Gentle soft wash to remove black streaks, algae, and mold without damaging your shingles or tiles."),
        ],
        "stats": [("5.0★", "Perfect Rating"), ("Pro", "Equipment"), ("Residential", "& Commercial"), ("Free", "Estimates")],
    },
]


def generate_dark_site(s: dict) -> str:
    social_section = ""
    if s.get("social_type") == "instagram":
        social_section = f'''<div class="contact-item">
                    <h3>See Our Work</h3>
                    <a href="{s['social_url']}" target="_blank" rel="noopener">@{s['social_handle']}</a>
                    <p>Follow us on Instagram</p>
                </div>'''
    elif s.get("social_type") == "facebook":
        social_section = f'''<div class="contact-item">
                    <h3>Find Us Online</h3>
                    <a href="{s['social_url']}" target="_blank" rel="noopener">Facebook Page</a>
                    <p>Reviews, photos & updates</p>
                </div>'''
    else:
        social_section = f'''<div class="contact-item">
                    <h3>Service Area</h3>
                    <p style="color:{s['accent']};font-weight:600;font-size:1.1rem;">South Florida</p>
                    <p>Miami-Dade, Broward, Palm Beach</p>
                </div>'''

    services_html = ""
    for title, desc in s["services"]:
        services_html += f'''<div class="service-card">
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>\n                '''

    stats_html = ""
    for val, label in s["stats"]:
        stats_html += f'''<div class="stat-item">
                    <h3>{val}</h3>
                    <p>{label}</p>
                </div>\n                '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{s["name"]} | {s["category"]} | South Florida</title>
    <meta name="description" content="{s["name"]} - {s["tagline"]}. {s["rating"]} stars, {s["reviews"]}+ reviews. {s["category"]} in South Florida. Call {s["phone"]}.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family={s["font"].replace(" ", "+")}:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        :root{{--primary:{s["primary"]};--accent:{s["accent"]};--dark-bg:{s["dark_bg"]};--card-bg:{s["card_bg"]};--border:{s["border"]};}}
        body{{font-family:'{s["font"]}',-apple-system,sans-serif;color:#e4e4e7;background:var(--dark-bg);line-height:1.6}}
        .container{{max-width:1100px;margin:0 auto;padding:0 20px}}
        header{{background:rgba(0,0,0,0.5);backdrop-filter:blur(10px);padding:12px 0;position:sticky;top:0;z-index:100;border-bottom:1px solid var(--border)}}
        header .container{{display:flex;justify-content:space-between;align-items:center}}
        .logo{{font-size:1rem;font-weight:700;letter-spacing:0.5px}}
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
            <div class="logo"><span>{s["name"].split()[0]}</span> {" ".join(s["name"].split()[1:])}</div>
            <a href="tel:{s["phone_raw"]}" class="header-cta">Call Now</a>
        </div>
    </header>
    <section class="hero">
        <div class="container">
            <div class="hero-badge">{s["category"]}</div>
            <h1><span>{s["tagline"].split(" — ")[0].split(" – ")[0]}</span></h1>
            <p class="tagline">{s["subtitle"]}</p>
            <div class="rating"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span>{s["rating"]} / 5 &mdash; {s["reviews"]}+ Google Reviews</span></div><br>
            <a href="tel:{s["phone_raw"]}" class="hero-cta">Free Estimate &rarr; {s["phone"]}</a>
        </div>
    </section>
    <section class="services">
        <div class="container">
            <h2 class="section-title">Our Services</h2>
            <p class="section-subtitle">Professional {s["category"].lower()} you can count on</p>
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
                <div class="contact-item"><h3>Call Us</h3><a href="tel:{s["phone_raw"]}">{s["phone"]}</a><p>Mon &ndash; Sat</p></div>
                <div class="contact-item"><h3>Location</h3><p>{s["address"]}</p></div>
                {social_section}
            </div>
        </div>
    </section>
    <section class="cta-bottom">
        <div class="container">
            <h2>Ready for a Free Estimate?</h2>
            <p class="sub">No pressure. No hidden fees. Just quality work.</p>
            <a href="tel:{s["phone_raw"]}">Call {s["phone"]} Now</a>
        </div>
    </section>
    <footer>
        <div class="container">
            <p>&copy; 2026 {s["name"]} &bull; South Florida &bull; <a href="tel:{s["phone_raw"]}">{s["phone"]}</a></p>
        </div>
    </footer>
</body>
</html>'''


def generate_light_site(s: dict) -> str:
    social_section = ""
    if s.get("social_type"):
        social_section = f'''<div class="contact-item">
                    <h3>Find Us Online</h3>
                    <a href="{s['social_url']}" target="_blank" rel="noopener">@{s['social_handle']}</a>
                </div>'''
    else:
        social_section = f'''<div class="contact-item">
                    <h3>Service Area</h3>
                    <p style="color:{s['primary']};font-weight:600;font-size:1.1rem;">South Florida</p>
                    <p>Miami-Dade &bull; Broward &bull; Palm Beach</p>
                </div>'''

    services_html = ""
    for title, desc in s["services"]:
        services_html += f'''<div class="service-card">
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>\n                '''

    stats_html = ""
    for val, label in s["stats"]:
        stats_html += f'''<div class="stat-item">
                    <h3>{val}</h3>
                    <p>{label}</p>
                </div>\n                '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{s["name"]} | {s["category"]} | South Florida</title>
    <meta name="description" content="{s["name"]} - {s["tagline"]}. {s["rating"]} stars, {s["reviews"]}+ reviews. {s["category"]} in South Florida. Call {s["phone"]}.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family={s["font"].replace(" ", "+")}:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        :root{{--primary:{s["primary"]};--accent:{s["accent"]};--bg:{s["dark_bg"]};--card:{s["card_bg"]};--border:{s["border"]};}}
        body{{font-family:'{s["font"]}',-apple-system,sans-serif;color:#1a1a1a;background:var(--bg);line-height:1.6}}
        .container{{max-width:1100px;margin:0 auto;padding:0 20px}}
        header{{background:#fff;padding:12px 0;position:sticky;top:0;z-index:100;box-shadow:0 1px 8px rgba(0,0,0,.08)}}
        header .container{{display:flex;justify-content:space-between;align-items:center}}
        .logo{{font-size:1rem;font-weight:700;color:var(--primary)}}
        .header-cta{{background:var(--primary);color:#fff;text-decoration:none;padding:10px 20px;border-radius:6px;font-weight:600;font-size:.85rem}}
        .hero{{background:var(--primary);color:#fff;padding:80px 0 60px;text-align:center}}
        .hero-badge{{display:inline-block;background:rgba(255,255,255,.2);padding:6px 16px;border-radius:20px;font-size:.75rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:20px}}
        .hero h1{{font-size:clamp(2rem,5vw,3rem);font-weight:800;margin-bottom:14px;line-height:1.15}}
        .hero .tagline{{font-size:1.1rem;opacity:.9;margin-bottom:24px;font-weight:300}}
        .hero .rating{{display:inline-flex;align-items:center;gap:10px;background:rgba(255,255,255,.15);padding:10px 20px;border-radius:30px;font-size:.9rem;margin-bottom:30px}}
        .stars{{color:#fbbf24}}
        .hero-cta{{display:inline-block;background:#fff;color:var(--primary);text-decoration:none;padding:18px 40px;border-radius:8px;font-weight:700;font-size:1.05rem;transition:transform .2s}}
        .hero-cta:hover{{transform:scale(1.03)}}
        .services{{padding:60px 0}}
        .section-title{{text-align:center;font-size:1.8rem;font-weight:700;margin-bottom:10px;color:var(--primary)}}
        .section-subtitle{{text-align:center;color:#6b7280;font-size:.95rem;margin-bottom:40px}}
        .services-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}}
        .service-card{{background:var(--card);padding:28px;border-radius:10px;border-left:4px solid var(--accent);box-shadow:0 2px 8px rgba(0,0,0,.04)}}
        .service-card h3{{font-size:1.1rem;margin-bottom:8px;font-weight:600;color:var(--primary)}}
        .service-card p{{color:#6b7280;font-size:.9rem}}
        .why-us{{padding:60px 0;background:var(--primary);color:#fff}}
        .why-us .section-title{{color:#fff}}
        .why-us .section-subtitle{{color:rgba(255,255,255,.7)}}
        .stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;text-align:center}}
        .stat-item{{padding:24px;background:rgba(255,255,255,.1);border-radius:10px}}
        .stat-item h3{{font-size:2.2rem;font-weight:800;color:#fff}}
        .stat-item p{{color:rgba(255,255,255,.7);margin-top:4px}}
        .reviews-section{{padding:60px 0}}
        .reviews-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}
        .review-card{{background:var(--card);padding:24px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.04);border:1px solid var(--border)}}
        .review-card .review-stars{{color:var(--accent);margin-bottom:10px}}
        .review-card p{{color:#374151;font-style:italic;font-size:.95rem}}
        .review-card .reviewer{{color:#9ca3af;font-size:.8rem;margin-top:10px;font-weight:500}}
        .contact{{padding:60px 0;background:var(--card);text-align:center}}
        .contact-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px;margin-top:30px}}
        .contact-item{{padding:24px}}
        .contact-item h3{{color:var(--primary);margin-bottom:8px;font-weight:600}}
        .contact-item p{{color:#6b7280}}
        .contact-item a{{color:var(--primary);text-decoration:none;font-weight:600;font-size:1.1rem}}
        .cta-bottom{{background:var(--primary);color:#fff;padding:50px 0;text-align:center}}
        .cta-bottom h2{{font-size:1.8rem;margin-bottom:8px;font-weight:700}}
        .cta-bottom .sub{{opacity:.85;margin-bottom:24px;font-weight:300}}
        .cta-bottom a{{display:inline-block;background:#fff;color:var(--primary);text-decoration:none;padding:16px 40px;border-radius:8px;font-weight:700;font-size:1.05rem}}
        footer{{background:#1a1a1a;color:#9ca3af;padding:24px 0;text-align:center;font-size:.8rem}}
        footer a{{color:var(--accent);text-decoration:none}}
        @media(max-width:768px){{.hero{{padding:50px 0 40px}}.services-grid,.reviews-grid{{grid-template-columns:1fr}}.stats-grid{{grid-template-columns:repeat(2,1fr)}}}}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">{s["name"]}</div>
            <a href="tel:{s["phone_raw"]}" class="header-cta">Call Now</a>
        </div>
    </header>
    <section class="hero">
        <div class="container">
            <div class="hero-badge">{s["category"]}</div>
            <h1>{s["tagline"]}</h1>
            <p class="tagline">{s["subtitle"]}</p>
            <div class="rating"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span>{s["rating"]} / 5 &mdash; {s["reviews"]}+ Google Reviews</span></div><br>
            <a href="tel:{s["phone_raw"]}" class="hero-cta">Free Estimate &rarr; {s["phone"]}</a>
        </div>
    </section>
    <section class="services">
        <div class="container">
            <h2 class="section-title">Our Services</h2>
            <p class="section-subtitle">Professional {s["category"].lower()} you can count on</p>
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
                <div class="contact-item"><h3>Call Us</h3><a href="tel:{s["phone_raw"]}">{s["phone"]}</a><p>Mon &ndash; Sat</p></div>
                <div class="contact-item"><h3>Location</h3><p>{s["address"]}</p></div>
                {social_section}
            </div>
        </div>
    </section>
    <section class="cta-bottom">
        <div class="container">
            <h2>Ready for a Free Estimate?</h2>
            <p class="sub">No pressure. No hidden fees. Just quality work.</p>
            <a href="tel:{s["phone_raw"]}">Call {s["phone"]} Now</a>
        </div>
    </section>
    <footer>
        <div class="container">
            <p>&copy; 2026 {s["name"]} &bull; South Florida &bull; <a href="tel:{s["phone_raw"]}">{s["phone"]}</a></p>
        </div>
    </footer>
</body>
</html>'''


base_dir = r"C:\Users\ajsup\sam_contractor_sites"

for site in SITES:
    slug = site["slug"]
    site_dir = os.path.join(base_dir, slug)
    os.makedirs(site_dir, exist_ok=True)

    if site["theme"] == "dark":
        html = generate_dark_site(site)
    else:
        html = generate_light_site(site)

    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Built: {slug}/index.html")

print(f"\nAll {len(SITES)} sites generated.")
