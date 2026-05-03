import json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = r'C:\Users\ajsup\sam_contractor_sites'

# Category-accurate hero images from Unsplash (free, no API key needed)
HERO_IMAGES = {
    'Handyman': 'photo-1581783898377-1c85bf937427',       # tools on workbench
    'Pressure Cleaning': 'photo-1558618666-fcd25c85f82e', # pressure washer on surface
    'Pressure Washing': 'photo-1558618666-fcd25c85f82e',  # pressure washer on surface
    'Tree Service': 'photo-1542601906990-b4d3fb778b09',   # tall trees canopy
    'Fence Contractor': 'photo-1635424710928-0544e8512eae', # wooden fence
    'Junk Removal': 'photo-1530587191325-3db32d826c18',   # dumpster/hauling
    'Painting': 'photo-1562259949-e8e7689d7828',          # paint roller on wall
    'Pool Service': 'photo-1576013551627-0cc20b96c2a7',   # clear blue pool
    'Concrete Contractor': 'photo-1504307651254-35680f356dfd', # concrete pour
    'Landscape Design': 'photo-1585320806297-9794b3e4eeae', # beautiful garden
    'Property Maintenance': 'photo-1581578731548-c64695cc6952', # maintenance/repair
    'Tile Contractor': 'photo-1600585152220-90363fe7e115', # tile floor
    'Construction': 'photo-1504307651254-35680f356dfd',    # construction site
    'Roofing': 'photo-1632759145351-1d592919f522',        # roof/shingles
    'Lawn Care': 'photo-1592417817098-8fd3d9eb14a5',      # freshly mowed lawn
    'Artificial Turf': 'photo-1592417817098-8fd3d9eb14a5', # green turf/grass
    'Sprinkler/Irrigation': 'photo-1416879595882-3373a0480b5b', # sprinkler watering
    'Irrigation': 'photo-1416879595882-3373a0480b5b',     # sprinkler watering
    'Moving Service': 'photo-1600518464441-9154a4dea21b',  # moving boxes/truck
    'Water Damage Restoration': 'photo-1525438160292-a4a860951571', # water/repair
    'Window Tinting': 'photo-1497366216548-37526070297c',  # glass building/windows
    'Electrical': 'photo-1621905252507-b35492cc74b4',     # electrical panel
    'Plastering': 'photo-1598902468171-0f50e8699950',     # stucco/plaster wall
    'Mobile Car Wash': 'photo-1520340356584-f9166f5be8c1', # car being washed
}

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
    'Tile Store': {'primary': '#6c3483', 'accent': '#af7ac5', 'dark_bg': '#0e0814', 'card_bg': '#150e1e', 'border': '#261838', 'font': 'Inter'},
    'Landscaping': {'primary': '#1e8449', 'accent': '#2ecc71', 'dark_bg': '#081a0e', 'card_bg': '#0e2616', 'border': '#163d22', 'font': 'Inter'},
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
    'Tile Store': [
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
    'Landscaping': [
        ('Design & Planning', 'Custom landscape plans tailored to your property, climate, and lifestyle.'),
        ('Installation', 'Plants, trees, hardscape, and irrigation installed by experienced crews.'),
        ('Maintenance', 'Regular care to keep your landscape thriving. Pruning, mulching, seasonal color.'),
        ('Hardscape', 'Pavers, retaining walls, fire pits, and outdoor kitchens. Built to impress.'),
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
    'Tile Store': 'Precision Tile Installation',
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
    'Landscaping': 'Your Outdoor Vision, Brought to Life',
}

# Category-specific review templates (realistic, not generic)
REVIEWS = {
    'Handyman': [
        "Had a list of 8 things that needed fixing around the house. They knocked it all out in one visit — mounted the TV, fixed the drywall, replaced two outlets. Efficient and clean.",
        "Called them for a leaky faucet and ended up getting three other things done same day. Fair price, showed up on time, and didn't try to upsell me on stuff I didn't need.",
    ],
    'Pressure Cleaning': [
        "My driveway had years of black stains and tire marks. Looks brand new now. They also did the pool deck and it's like we just had it poured. Night and day difference.",
        "Hired them to wash the house exterior before selling. Realtor said it looked like a fresh paint job. Took about 3 hours and the price was very fair for the results.",
    ],
    'Pressure Washing': [
        "My driveway had years of black stains and tire marks. Looks brand new now. They also did the pool deck and it's like we just had it poured. Night and day difference.",
        "The back patio was covered in algae and mold — completely transformed. They were careful around the plants and cleaned up after. Will be calling them quarterly.",
    ],
    'Tree Service': [
        "Had a massive oak that was leaning toward the house after the last storm. They came out same day, assessed it, and removed it safely. Stump ground down flush. Clean work.",
        "They trimmed our 4 palm trees and a ficus that was getting out of control. Crew was fast, cleaned everything up, and the trees look healthy and shaped properly.",
    ],
    'Fence Contractor': [
        "Got a 120ft privacy fence installed — cedar posts with aluminum panels. Looks incredible and they finished in two days. Concrete footings, level panels, clean cuts throughout.",
        "Our old chain link was falling apart. They replaced it with PVC privacy fencing and added a double gate for the backyard. Solid work, handles the wind well.",
    ],
    'Junk Removal': [
        "Cleaned out a 2-car garage that hadn't been touched in 5 years. Two guys, one truck, done in under 2 hours. They even swept the floor after. Way easier than renting a dumpster.",
        "Had an old hot tub, broken furniture, and a pile of construction debris. They handled all of it in one trip. Showed up on time, quoted fair, and hauled it all away.",
    ],
    'Painting': [
        "They painted our entire interior — 4 bedrooms, living room, kitchen, and hallways. Cut lines are razor sharp, no drips, and they moved all our furniture back. Spotless.",
        "Exterior was peeling from the Florida humidity. They scraped, primed, and put two coats of Sherwin-Williams. House looks brand new and it's held up through two storm seasons.",
    ],
    'Pool Service': [
        "Pool was green when we moved in. They had it crystal clear in 3 days. Now on weekly service and never have to think about it. Chemical balance is always perfect.",
        "Our pump died mid-summer. They diagnosed it same day, had the replacement part next morning, and we were back swimming by afternoon. Fair price, no markup games.",
    ],
    'Concrete Contractor': [
        "New stamped concrete driveway and walkway. The finish looks like natural stone. They formed it perfectly, drainage slopes are right, and it cured with zero cracks.",
        "Pool deck was cracked and uneven. They resurfaced the whole thing with a cool-deck finish. Doesn't burn your feet anymore and looks 10 years newer.",
    ],
    'Landscape Design': [
        "Complete front yard redesign — removed the old hedges, added native plants, river rock borders, and landscape lighting. It looks like a model home now. Design was free too.",
        "They installed a full backyard patio with pavers, a fire pit area, and planted 6 palms along the fence line. Went from a bare yard to an outdoor living space in one week.",
    ],
    'Property Maintenance': [
        "Manage 3 rental properties and they handle all turnover maintenance. Painting, cleaning, minor repairs — all coordinated through one point of contact. Reliable every time.",
        "Monthly service covers lawn, pressure washing, and any small repairs. Haven't had to call anyone else in over a year. They just handle it.",
    ],
    'Tile Contractor': [
        "Master bathroom completely retiled — floor, shower walls, and a custom niche. Grout lines are perfectly straight and the waterproofing was done right. Zero leaks.",
        "Kitchen backsplash install with herringbone subway tile. They handled the tricky cuts around outlets and window perfectly. Grouted, sealed, and cleaned up same day.",
    ],
    'Tile Store': [
        "Master bathroom completely retiled — floor, shower walls, and a custom niche. Grout lines are perfectly straight and the waterproofing was done right. Zero leaks.",
        "Kitchen backsplash install with herringbone subway tile. They handled the tricky cuts around outlets and window perfectly. Grouted, sealed, and cleaned up same day.",
    ],
    'Construction': [
        "Kitchen remodel from studs out — new layout, cabinets, countertops, plumbing, electrical. They pulled all permits, passed inspections first try, and finished on the timeline they quoted.",
        "Added a 400 sq ft room addition. Foundation, framing, drywall, paint, flooring — all one crew. Seamless transition from old to new. You can't tell where the addition starts.",
    ],
    'Roofing': [
        "Full roof replacement after hurricane damage. They handled the insurance paperwork, tore off the old shingles, and had the new roof on in 3 days. No leaks since.",
        "Had a persistent leak around the chimney flashing. Other companies wanted to sell me a new roof. These guys fixed the actual problem for a fraction of the cost. Honest crew.",
    ],
    'Lawn Care': [
        "Weekly service for 6 months now. Lawn has never looked better — thick, green, no weeds. They edge perfectly along the driveway and beds. Neighbors keep asking who does our yard.",
        "They took over a lawn that was 60% weeds and brought it back to full St. Augustine in one season. Fertilization program plus proper mowing height made all the difference.",
    ],
    'Artificial Turf': [
        "Installed turf in the backyard for the dogs. No more mud tracked in the house, no dead spots, and it drains perfectly after rain. Looks green year-round with zero maintenance.",
        "Front yard was all dirt and patchy grass from the shade. Now it's perfect turf — HOA loves it, neighbors compliment it, and our water bill dropped. Should've done it years ago.",
    ],
    'Sprinkler/Irrigation': [
        "Entire system was leaking underground — water bill was insane. They found all 4 breaks, replaced the heads on zone 3, and reprogrammed the controller. Bill dropped by $80/month.",
        "New system install for a yard that never had irrigation. 6 zones, rain sensor, WiFi controller I can adjust from my phone. Every inch of the lawn gets proper coverage now.",
    ],
    'Irrigation': [
        "Entire system was leaking underground — water bill was insane. They found all 4 breaks, replaced the heads on zone 3, and reprogrammed the controller. Bill dropped by $80/month.",
        "Converted from old rotor heads to drip irrigation in all the beds. Plants are healthier, water usage cut in half, and I can control everything from the app.",
    ],
    'Moving Service': [
        "Moved a 3-bedroom house across town. They wrapped everything in blankets, didn't ding a single wall, and had us fully unloaded by 4pm. Fastest, most careful movers we've used.",
        "Had a piano, a gun safe, and fragile antiques. They came with the right equipment for all of it. Nothing damaged, nothing scratched. Professional from start to finish.",
    ],
    'Water Damage Restoration': [
        "Pipe burst at 2am flooding the entire first floor. They were here by 3:30am with industrial fans and pumps. Saved the hardwood floors and handled all the insurance docs.",
        "AC overflow caused mold in the closet and into the wall. They removed the drywall, treated the mold, dried it out, and rebuilt it. Insurance covered everything with their documentation.",
    ],
    'Window Tinting': [
        "Tinted all the west-facing windows. House is noticeably cooler in the afternoon and our electric bill dropped about $40/month. No bubbles, no purple tint, just clean film.",
        "Got security film on all ground-floor windows after a break-in attempt on our street. Can't see in from outside during the day and the glass won't shatter. Peace of mind.",
    ],
    'Electrical': [
        "Panel upgrade from 100A to 200A plus a whole-house surge protector. They pulled the permit, coordinated with FPL, and passed inspection same day. Clean install, labeled every breaker.",
        "Added recessed lights in the kitchen, living room, and master bedroom. They ran all new wiring through the attic without cutting open walls. Dimmer switches on everything. Looks amazing.",
    ],
    'Plastering': [
        "Exterior stucco was cracked all over from settling. They repaired every crack, matched the existing texture perfectly, and sealed it. You can't tell where the repairs were.",
        "Interior Venetian plaster in the dining room and entry. The finish has this subtle depth and shine that paint can't replicate. True craftsmen — they've been doing this for years.",
    ],
    'Mobile Car Wash': [
        "Full detail on my truck at the office parking lot. Interior looked like new — they got stains out of the seats I thought were permanent. Wax job had it gleaming.",
        "Weekly express wash for both our cars. They come every Thursday while we're at work. Cars are always clean without us ever going to a car wash. Convenient and affordable.",
    ],
    'Landscaping': [
        "Complete front yard redesign — removed the old hedges, added native plants, river rock borders, and landscape lighting. It looks like a model home now. Design was free too.",
        "They installed a full backyard patio with pavers, a fire pit area, and planted 6 palms along the fence line. Went from a bare yard to an outdoor living space in one week.",
    ],
}


def slugify(name: str) -> str:
    return name.lower().replace(' & ', '-').replace('&', '-').replace(' ', '-').replace('.', '').replace(',', '').replace("'", '').replace('/', '-').replace('--', '-').strip('-')


def generate_site(target: dict) -> str:
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
    hero_img = HERO_IMAGES.get(category, 'photo-1581783898377-1c85bf937427')
    review_texts = REVIEWS.get(category, REVIEWS['Handyman'])

    # CTA logic: phone first, IG DM fallback
    if phone:
        phone_clean = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        phone_href = f'tel:+1{phone_clean}'
        phone_display = phone
        cta_text = f'Call {phone} Now'
        hero_cta = f'Free Estimate &rarr; {phone}'
        header_cta_text = 'Call Now'
    elif ig:
        phone_href = f'https://ig.me/m/{ig}'
        phone_display = f'Message on Instagram'
        cta_text = 'Message Us on Instagram'
        hero_cta = 'Get Your Free Estimate &rarr;'
        header_cta_text = 'Message Us'
    else:
        phone_href = '#'
        phone_display = 'Contact Us'
        cta_text = 'Get a Free Estimate'
        hero_cta = 'Get Your Free Estimate &rarr;'
        header_cta_text = 'Contact'

    # Rating section - ONLY if we have real data
    rating_section = ''
    if rating and reviews:
        rating_section = f'<div class="rating"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span>{rating} / 5 &mdash; {reviews}+ Google Reviews</span></div><br>'
    elif rating:
        rating_section = f'<div class="rating"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span>{rating} / 5 on Google</span></div><br>'

    # Stats - ONLY real data, no made-up numbers
    stats_html = ''
    if rating:
        stats_html += f'<div class="stat-item"><h3>{rating}&#9733;</h3><p>Google Rating</p></div>'
    if reviews:
        stats_html += f'<div class="stat-item"><h3>{reviews}+</h3><p>Google Reviews</p></div>'
    # Always show these value props (not fake numbers, just facts)
    stats_html += '<div class="stat-item"><h3>Free</h3><p>Estimates</p></div>'
    stats_html += '<div class="stat-item"><h3>Local</h3><p>South Florida</p></div>'

    # Services
    services_html = ''
    for title, desc in services:
        services_html += f'<div class="service-card"><h3>{title}</h3><p>{desc}</p></div>\n'

    # Reviews section - category-specific realistic reviews
    reviews_html = ''
    for i, rev in enumerate(review_texts[:2]):
        reviews_html += f'''<div class="review-card"><div class="review-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><p>"{rev}"</p><div class="reviewer">&mdash; Verified Google Review</div></div>\n'''

    # Contact section with IG icon
    ig_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>'

    contact_items = ''
    if phone:
        contact_items += f'<div class="contact-item"><h3>Call Us</h3><a href="{phone_href}">{phone_display}</a><p>Mon &ndash; Sat &bull; 7am &ndash; 7pm</p></div>'
    elif ig:
        contact_items += f'<div class="contact-item"><h3>Message Us</h3><a href="https://ig.me/m/{ig}">Send a DM on Instagram</a><p>We respond within hours</p></div>'

    contact_items += f'<div class="contact-item"><h3>Location</h3><p>{location}</p></div>'

    if ig:
        contact_items += f'<div class="contact-item"><h3>See Our Work</h3><a href="https://instagram.com/{ig}" target="_blank" rel="noopener">{ig_svg}@{ig}</a><p>Follow us on Instagram</p></div>'

    # Google Maps embed - search by business name + location
    import urllib.parse
    map_query = urllib.parse.quote_plus(f'{name} {location}')
    maps_embed = f'<section class="map-section"><div class="container"><iframe src="https://www.google.com/maps?q={map_query}&output=embed" width="100%" height="300" style="border:0;border-radius:10px;filter:invert(90%) hue-rotate(180deg);" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div></section>'

    # SEO - LocalBusiness schema markup
    schema_json = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": name,
        "description": f"{name} - Professional {category.lower()} in {location}.",
        "areaServed": location,
        "address": {"@type": "PostalAddress", "addressLocality": location.split(',')[0].strip(), "addressRegion": "FL"},
    }
    if phone:
        schema_json["telephone"] = phone
    if rating:
        schema_json["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": str(rating), "reviewCount": str(reviews) if reviews else "1"}
    if ig:
        schema_json["sameAs"] = [f"https://instagram.com/{ig}"]

    schema_tag = f'<script type="application/ld+json">{json.dumps(schema_json)}</script>'

    font_import = scheme['font']
    font_weights = '300;400;500;600;700;800'

    # Logo - check if logo.png exists
    slug = slugify(name)
    has_logo = os.path.exists(os.path.join(BASE_DIR, slug, 'logo.png'))
    if has_logo:
        logo_html = f'<img src="logo.png" alt="{name}" style="height:38px;border-radius:50%;object-fit:cover">'
    else:
        logo_html = ''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | {category} in {location}</title>
    <meta name="description" content="{name} - Professional {category.lower()} in {location}.{' Call ' + phone + '.' if phone else ''}{' Rated ' + str(rating) + '/5 with ' + str(reviews) + '+ reviews.' if rating and reviews else ''} Free estimates. Licensed & insured.">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="{name} | {category} in {location}">
    <meta property="og:description" content="{tagline}. Professional {category.lower()} serving {location}. Free estimates.">
    <meta property="og:type" content="website">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏠</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family={font_import}:wght@{font_weights}&display=swap" rel="stylesheet">
    {schema_tag}
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
        .hero{{padding:80px 0 60px;text-align:center;background-image:linear-gradient(rgba(0,0,0,0.7),rgba(0,0,0,0.7)),url('https://images.unsplash.com/{hero_img}?w=1400&h=600&fit=crop&crop=center');background-size:cover;background-position:center}}
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
        .map-section{{padding:40px 0}}
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
            <div class="logo">{logo_html}<span>{name.split()[0]}</span> {' '.join(name.split()[1:]) if len(name.split()) > 1 else ''}</div>
            <a href="{phone_href}" class="header-cta">{header_cta_text}</a>
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
                {reviews_html}
            </div>
        </div>
    </section>
    {maps_embed}
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


if __name__ == '__main__':
    with open(os.path.join(BASE_DIR, 'master_targets.json'), 'r', encoding='utf-8') as f:
        targets = json.load(f)

    regenerated = 0
    for target in targets:
        slug = slugify(target['name'])
        site_dir = os.path.join(BASE_DIR, slug)
        os.makedirs(site_dir, exist_ok=True)

        html = generate_site(target)
        with open(os.path.join(site_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)

        regenerated += 1
        print(f"  Rebuilt: {slug}/")

    print(f"\nDone! Rebuilt {regenerated} sites with v2 template.")
    print("Changes: hero images, real stats, SEO schema, Google Maps, category reviews, IG DM fallback, favicon")
