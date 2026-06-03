import math

# GPS coordinates for each location (lat, lng)
LOCATION_COORDS = {
    "times_square":          (40.7580, -73.9855),
    "washington_square_park": (40.7308, -73.9973),
    "high_line":              (40.7480, -74.0048),
    "grand_central":          (40.7527, -73.9772),
    "wall_street":            (40.7069, -74.0089),
    "chelsea_market":         (40.7424, -74.0044),
}

# Display names for greetings
LOCATION_DISPLAY = {
    "times_square":           "Times Square",
    "washington_square_park": "Washington Square Park",
    "high_line":              "the High Line",
    "grand_central":          "Grand Central Terminal",
    "wall_street":            "Wall Street",
    "chelsea_market":         "Chelsea Market",
}

# Max distance (km) to still claim a known location
LOCATION_RADIUS_KM = 1.0


def haversine(lat1, lng1, lat2, lng2):
    """Distance in km between two GPS points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def nearest_location(lat: float, lng: float) -> dict | None:
    """Return nearest known location if within LOCATION_RADIUS_KM, else None."""
    best_key, best_dist = None, float("inf")
    for key, (clat, clng) in LOCATION_COORDS.items():
        d = haversine(lat, lng, clat, clng)
        if d < best_dist:
            best_dist = d
            best_key = key
    if best_dist <= LOCATION_RADIUS_KM:
        return {"key": best_key, "name": LOCATION_DISPLAY[best_key], "distance_km": round(best_dist, 3)}
    return None


NYC_KNOWLEDGE = {
    "times_square": {
        "aliases": ["times square", "42nd", "8th ave and 42nd", "7th ave and 42nd", "broadway and 42nd"],
        "college_student": {
            "hook": "The TKTS red stairs in the middle of the plaza sell same-day Broadway tickets at up to 50% off — most students have no idea that's what those steps actually are.",
            "hack": "Come back here at 3am on a weekend — the place is still packed, the street vendors are out, and you'll see a version of NYC that tour groups never get.",
            "locals_only": "That military recruiting station in the middle of the square used to be a public bathroom in the 1900s. Also the reason 42nd Street was called 'the Deuce' — it was legitimately the sketchiest block in Manhattan through the 80s.",
        },
        "family_kids": {
            "hook": "All those cartoon characters and superheroes posing for photos? Completely legal and self-employed — it's an official street performer zone. Your kids can take a photo, just know a tip is expected.",
            "hack": "The best view of all the billboards — the one your kids will actually remember — is from the red TKTS stairs right in the center. Free to climb, best photo op in Times Square.",
            "locals_only": "M&M's World and Hershey's on this block were specifically designed to be massive tourist attractions, but the actual NYC candy institution is Economy Candy on Rivington Street on the Lower East Side. Worth the detour.",
        },
        "adult_explorer": {
            "hook": "Before all the neon, this was Longacre Square — the center of NYC's carriage industry. When cars took over, the New York Times moved its headquarters here in 1904 and threw the first New Year's Eve party to promote it. The ball drop has been happening ever since.",
            "hack": "The old subway station at City Hall — closed since 1945 — is accessible as a bonus loop at the end of the 6 train. Stay on when everyone else gets off at Brooklyn Bridge and you'll glide through it without buying a ticket.",
            "locals_only": "Studio 54 was two blocks from here on 54th Street. The building is now a Broadway theater — Broadway Shubert — and the basement where Bianca Jagger rode a horse on her birthday is now the green room.",
        },
    },
    "washington_square_park": {
        "aliases": ["washington square", "wsp", "washington sq"],
        "college_student": {
            "hook": "Every April 20th, this park becomes the largest public 4/20 gathering in New York City. NYPD basically stands back and watches — it's an open secret that's been going on for decades.",
            "hack": "The chess tables on the southwest corner have hustlers who'll play you for $5 a game. They'll let you win the first one. Don't play a second.",
            "locals_only": "The fountain in the center isn't actually aligned with the arch — it was moved six feet during a 2009 renovation to finally line up with Fifth Avenue. Before that, it was slightly off for a hundred years and nobody fixed it.",
        },
        "family_kids": {
            "hook": "In summer, the fountain becomes an unofficial splash pad — kids strip down and run through it and nobody cares. It's a total New York moment.",
            "hack": "The dog run on the southwest side is one of the best in the city and it's free to walk through even without a dog. Kids love watching the chaos. The southwest corner also has free puppet shows some weekend afternoons — check the park's Instagram.",
            "locals_only": "There are free outdoor chess sets you can borrow from the parks department attendant near the chess tables. Great way to kill an hour if the kids are old enough.",
        },
        "adult_explorer": {
            "hook": "The arch was designed by Stanford White — same architect who was later shot dead by a jealous husband at Madison Square Garden in one of the most scandalous murders of the Gilded Age. This was his last major work before that.",
            "hack": "The marble arch has a staircase hidden inside the north leg. It used to be accessible — artists including Marcel Duchamp and John Sloan famously broke in in 1917 and declared the park an independent republic from the top.",
            "locals_only": "Before it was a park, this was a potter's field — a mass burial ground for the poor and the executed. There are an estimated 20,000 bodies still under it. And Bob Dylan used to busk at the fountain in the early 60s before he was famous.",
        },
    },
    "high_line": {
        "aliases": ["high line", "highline", "west side"],
        "college_student": {
            "hook": "The High Line was saved from demolition in 1999 by two neighborhood guys who had zero experience in city planning. They just started a nonprofit and fought for it for a decade. Now it generates $2 billion a year for the neighborhood.",
            "hack": "The best section is the Radial Benchway between 24th and 25th — the tiered wooden seating that faces a huge window overlooking 10th Avenue traffic. It's like street theater and most people walk right past it.",
            "locals_only": "Chelsea Market directly below you used to be the Nabisco factory where the Oreo cookie was invented in 1912. The brick structure you can see from the High Line is original factory architecture.",
        },
        "family_kids": {
            "hook": "The original rail tracks and wild grasses are preserved intentionally — the designers wanted it to feel like nature reclaiming the city. Kids usually notice the plants growing through the steel before adults do.",
            "hack": "There's a water feature and spray ground at the 14th Street entrance in summer. It's free and uncrowded compared to the crowded central fountain areas elsewhere in the city.",
            "locals_only": "The Whitney Museum at the southern end of the High Line has a free viewing deck on the 5th floor that's open to the public even if you don't buy a museum ticket. Best elevated view of the Hudson in the neighborhood.",
        },
        "adult_explorer": {
            "hook": "The last train ran on these tracks in 1980, carrying a load of frozen turkeys. For 19 years it sat completely abandoned until a grassroots campaign — started over a dinner party bet — turned it into what's now the most visited tourist attraction in New York.",
            "hack": "Come at dawn. The High Line opens at 7am and for the first hour it's almost entirely locals walking dogs or commuting. The light on the Hudson is extraordinary and you'll have the benches to yourself.",
            "locals_only": "The stretch between 18th and 20th Street passes through what was the Meatpacking District's old slaughterhouse zone — the cobblestone streets below still have the original drainage channels cut into them for exactly the reason you're imagining.",
        },
    },
    "grand_central": {
        "aliases": ["grand central", "grand central terminal", "42nd and park", "vanderbilt"],
        "college_student": {
            "hook": "The whispering gallery in the lower dining concourse is a legit physics trick — stand in one corner of the vaulted archway and whisper into the wall, someone in the diagonal corner can hear you perfectly. It's acoustics, not magic.",
            "hack": "The secret bar on Track 61 — the old train platform that FDR used to sneak into the Waldorf Astoria — is now a bar called Campbell Apartment. It's one of the most stunning rooms in the city and most New Yorkers don't know it exists.",
            "locals_only": "That famous green ceiling with the constellations has the stars backward — mirror image of the sky. The original painter either worked from a medieval manuscript that got it wrong, or deliberately made it 'God's view looking down.' Nobody knows for sure.",
        },
        "family_kids": {
            "hook": "Look up at the main concourse ceiling — that blue-green sky with gold constellations is the most photographed ceiling in New York. Ask your kids to find the spot where there's a small dark patch in the upper left corner — that's the only original section left showing how dirty it was before the 1990s restoration.",
            "hack": "The lower level food market (Grand Central Market) has some of the best cheap lunch options in Midtown — Murray's Cheese, Li-Lac Chocolates, Dishes — and it's dramatically less crowded than the main concourse.",
            "locals_only": "The terminal has 44 platforms on two underground levels and 67 tracks — more than any other terminal in the world. Kids who are into trains will lose their minds in the lower level.",
        },
        "adult_explorer": {
            "hook": "Jackie Kennedy saved this building. When Penn Station was demolished in 1963, the public outcry was so intense that she personally lobbied to save Grand Central from the same fate — testifying before Congress and threatening to handcuff herself to the building.",
            "hack": "The Oyster Bar in the lower level has been here since 1913. Get the pan roast — it's a cream-based shellfish stew that's been on the menu continuously for over a century. One of the most legitimately historic meals in New York.",
            "locals_only": "Cornelius Vanderbilt's statue faces south on 42nd Street — looking toward the original Vanderbilt family properties downtown, not toward the station he built. That's either an oversight or a power move, depending on who you ask.",
        },
    },
    "wall_street": {
        "aliases": ["wall street", "bowling green", "financial district", "fidi", "charging bull", "broadway and wall"],
        "college_student": {
            "hook": "The Charging Bull sculpture was installed illegally in 1989 — the artist Arturo Di Modica trucked it in himself at 1am and bolted it to the sidewalk outside the NYSE as a 'gift to New York' after the 1987 crash. The city tried to remove it, public outcry kept it.",
            "hack": "The Stone Street block one block south of here is a pedestrian alley packed with outdoor bar seating — it's where finance workers actually drink after work. Way more interesting than the tourist spots, and happy hour starts at 4pm.",
            "locals_only": "The wall that Wall Street is named after was a literal defensive wall built by Dutch settlers in 1653 to keep out the English and the Lenape. It ran exactly along this street. It didn't work.",
        },
        "family_kids": {
            "hook": "The Fearless Girl statue facing the Charging Bull was added in 2017 by an investment firm — there's actually a controversy about it that's a great conversation starter about public art and corporate messaging if your kids are old enough.",
            "hack": "The National Museum of the American Indian at the Alexander Hamilton Custom House right on Bowling Green is completely free. It's in one of the most beautiful Beaux-Arts buildings in the city and the kids' programming is excellent.",
            "locals_only": "Bowling Green — the small park behind the bull — is the oldest public park in New York City, used as an actual bowling green by Dutch settlers in the 1600s. The fence around it is original 1771 ironwork.",
        },
        "adult_explorer": {
            "hook": "The entire financial system of the United States was essentially created within two blocks of where you're standing. The first Bank of the United States, Alexander Hamilton's Treasury building, the first stock exchange — all happened here in the 1790s.",
            "hack": "The Federal Hall National Memorial at 26 Wall Street is free to enter and completely ignored by tourists. This is the exact site where George Washington was inaugurated as the first president. The bronze statue marks the spot. You can stand on it.",
            "locals_only": "Trinity Church at the end of Wall Street has a graveyard where Alexander Hamilton is actually buried — not in DC, not in Virginia, right here. His grave gets flowers and $10 bills left on it constantly since the musical.",
        },
    },
    "chelsea_market": {
        "aliases": ["chelsea market", "chelsea", "9th ave and 15th", "15th street"],
        "college_student": {
            "hook": "The entire building was the Nabisco factory from 1898 to 1958 — the Oreo, the Fig Newton, and the Animal Cracker were all invented and first manufactured here. The lobby has original factory machinery still hanging from the ceiling.",
            "hack": "The taco place at the far west end (Los Tacos No. 1) regularly tops best-of-NYC lists and has a line out the door — but if you go right when they open at 11am you can walk straight in. The al pastor is the move.",
            "locals_only": "The building floods on the ground floor during major storms — the architects intentionally preserved the slope of the original factory floor that drained toward the Hudson. There's actual artwork down near the far west entrance dedicated to water.",
        },
        "family_kids": {
            "hook": "The building's architect kept deliberately weird design elements throughout — random pipes, exposed brick, a lobster hanging from the ceiling, a stream running along the floor in the main corridor. Ask your kids to count how many strange things they can spot.",
            "hack": "The Fat Witch Bakery inside sells brownies by the pound and always has samples out. The Lobster Place seafood market at the west end has a small oyster bar but also sells fish and chips that kids universally love.",
            "locals_only": "The High Line runs directly above the western end of Chelsea Market — you can take the stairs from inside the market up to the elevated park without going back outside. Most people don't realize they're connected.",
        },
        "adult_explorer": {
            "hook": "When the Food Network launched in 1993, they set up their original studios inside this building — the converted factory aesthetic was the whole brand identity. Chelsea Market became a food destination partly because food TV was being filmed here.",
            "hack": "Anthropologie, Cire Trudon candles, Artists & Fleas — the retail on the upper mezzanine level is dramatically less crowded than the food hall below and has some genuinely interesting stuff if you're willing to take the stairs.",
            "locals_only": "Before Nabisco, this block was a cluster of row houses that were demolished for the factory. One of the residents displaced was a young woman named Emma Goldman — the famous anarchist — who was living here in the 1890s when she was already organizing labor movements in the garment district.",
        },
    },
}

PROFILE_LABELS = {
    "college_student": "College Student",
    "family_kids": "Family with Young Kids",
    "adult_explorer": "Adult Explorer",
}


def get_knowledge(location_text: str, profile: str) -> dict | None:
    location_lower = location_text.lower()
    for loc_key, loc_data in NYC_KNOWLEDGE.items():
        for alias in loc_data["aliases"]:
            if alias in location_lower:
                profile_data = loc_data.get(profile)
                if profile_data:
                    return {
                        "location_name": loc_key.replace("_", " ").title(),
                        **profile_data,
                    }
    return None
