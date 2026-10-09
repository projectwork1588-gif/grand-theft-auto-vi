-- =====================================================================
-- GRAND THEFT AUTO VI | Team Valkyrie | deterministic seed data
-- Every row has an explicit primary key, so re-running always gives identical data.
--
-- HONESTY RULES
--   official : stated on Rockstar's own site (source_url says which page). Descriptions are our own
--              short paraphrases of what that page says. Nothing is invented.
--   fan      : community-compiled or team interpretation (none seeded at present).
--   demo     : fictional records invented by Team Valkyrie to demonstrate the schema.
--              Demo missions deliberately do NOT include official characters, so we
--              never write fake story about real GTA VI characters.
-- =====================================================================

-- ------------------------------ regions ------------------------------
-- All six names are listed on the official Leonida page.
INSERT INTO regions (region_id, slug, name, summary, description, content_status, source_url, source_note) VALUES
(1, 'vice-city', 'Vice City',
 'The neon-lit urban centre of Leonida.',
 'Vice City is the best-known setting of Grand Theft Auto VI. Rockstar''s official site presents it as the urban heart of the state of Leonida and links it to Boobie Ike''s businesses.',
 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(2, 'leonida-keys', 'Leonida Keys',
 'The island area where the official site places Jason''s work for drug runners.',
 'Rockstar''s official site presents the Leonida Keys as the area where Jason Duval and Brian Heder operate.',
 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(3, 'grassrivers', 'Grassrivers',
 'A region the official site associates with the rap duo Real Dimez.',
 'Listed as an explorable region of Leonida on Rockstar''s official site, where it is connected with Real Dimez.',
 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(4, 'port-gellhorn', 'Port Gellhorn',
 'A region the official site associates with bank robber Raul Bautista.',
 'Listed as an explorable region of Leonida on Rockstar''s official site, where it is connected with Raul Bautista''s heists.',
 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(5, 'ambrosia', 'Ambrosia',
 'A region of Leonida listed on the official site.',
 'Listed as an explorable region of Leonida on Rockstar''s official site. Further detail will be added only when it can be sourced.',
 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(6, 'mount-kalaga', 'Mount Kalaga',
 'A region of Leonida listed on the official site.',
 'Listed as an explorable region of Leonida on Rockstar''s official site. Further detail will be added only when it can be sourced.',
 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.');

-- ----------------------------- locations -----------------------------
-- All locations are fictional demo places invented by Team Valkyrie.
INSERT INTO locations (location_id, region_id, slug, name, location_type, summary, description, content_status, source_note) VALUES
(1, 1, 'sunset-pier-boardwalk', 'Sunset Pier Boardwalk', 'landmark',
 'Fictional demo boardwalk used to demonstrate location records.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(2, 1, 'neon-row-district', 'Neon Row District', 'district',
 'Fictional demo nightlife district.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(3, 1, 'bayfront-studio-lot', 'Bayfront Studio Lot', 'venue',
 'Fictional demo recording studio venue.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(4, 2, 'coral-hook-marina', 'Coral Hook Marina', 'waterfront',
 'Fictional demo marina on an island road.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(5, 3, 'heron-reach-dock', 'Heron Reach Airboat Dock', 'waterfront',
 'Fictional demo dock at the edge of a wetland.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(6, 4, 'pelican-quay-terminal', 'Pelican Quay Terminal', 'waterfront',
 'Fictional demo cargo terminal.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(7, 5, 'smokestack-row', 'Smokestack Row', 'district',
 'Fictional demo industrial strip.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.'),
(8, 6, 'kalaga-ridge-lookout', 'Kalaga Ridge Lookout', 'wilderness',
 'Fictional demo hilltop viewpoint.',
 'Fictional demo location invented by Team Valkyrie. It does not exist in the game.',
 'demo', 'Invented for database demonstration.');

-- ----------------------------- characters ----------------------------
-- Official records are verified against rockstargames.com/VI/only-in-leonida. IDs 8-10 are demo.
INSERT INTO characters (character_id, slug, full_name, alias, role_title, summary, biography, home_location_id, content_status, source_url, source_note) VALUES
(1, 'jason-duval', 'Jason Duval', NULL, 'Protagonist',
 'Playable lead who works for drug runners in the Leonida Keys.',
 'One of the two leads shown on Rockstar''s official site. He has an Army background, now works for drug runners in the Keys, and wants an easier life than the one he keeps ending up with.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(2, 'lucia-caminos', 'Lucia Caminos', NULL, 'Protagonist',
 'Playable lead, recently out of Leonida Penitentiary.',
 'The other lead shown on Rockstar''s official site. Fighting for her family landed her in Leonida Penitentiary, and now that she is out she is determined to improve her odds.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(3, 'cal-hampton', 'Cal Hampton', NULL, 'Associate',
 'Jason''s friend and an associate of Brian Heder.',
 'Described on the official site as a homebody who listens in on Coast Guard communications and spends a lot of time on conspiracy theories.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(4, 'boobie-ike', 'Boobie Ike', NULL, 'Entrepreneur',
 'Vice City figure whose street background grew into businesses.',
 'Described as a Vice City legend with real estate, a strip club and a recording studio, who is partnering with Dre''Quan Priest at Only Raw Records.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(5, 'dre-quan-priest', 'Dre''Quan Priest', NULL, 'Music executive',
 'Founder of Only Raw Records, which manages Real Dimez.',
 'Described as a former street dealer turned music entrepreneur who founded Only Raw Records and manages the group Real Dimez.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(6, 'raul-bautista', 'Raul Bautista', NULL, 'Bank robber',
 'Experienced bank robber who recruits crews for large heists.',
 'Described on the official site as a seasoned bank robber who assembles talented crews for high-reward jobs.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(7, 'brian-heder', 'Brian Heder', NULL, 'Drug runner',
 'Veteran Keys drug smuggler who runs a boat yard with his wife Lori.',
 'Described as a classic drug runner from the Keys, who gives Jason a place to live in return for his help.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
(11, 'real-dimez', 'Real Dimez', NULL, 'Rap duo',
 'Rap duo of Bae-Luxe and Roxy, signed to Only Raw Records.',
 'Described as two high school friends, Bae-Luxe and Roxy, who turned their street activity into rap tracks and a social media following.',
 NULL, 'official', 'https://www.rockstargames.com/VI/only-in-leonida', 'Verified on Rockstar''s official site on 2026-10-09.'),
-- Demo records: fictional characters invented by Team Valkyrie.
(8, 'delia-marsh', 'Delia Marsh', 'The Broker', 'Fixer',
 'Fictional demo fixer who arranges deals along the waterfront.',
 'Fictional demo character invented by Team Valkyrie to demonstrate character records, relationships and missions. Not part of the game.',
 3, 'demo', NULL, 'Invented for database demonstration.'),
(9, 'tomas-reyes-hall', 'Tomas Reyes-Hall', 'Gator', 'Airboat guide',
 'Fictional demo guide who knows every channel of the wetlands.',
 'Fictional demo character invented by Team Valkyrie to demonstrate character records, relationships and missions. Not part of the game.',
 5, 'demo', NULL, 'Invented for database demonstration.'),
(10, 'nico-brandt', 'Nico Brandt', NULL, 'Dock foreman',
 'Fictional demo foreman who runs a busy cargo terminal.',
 'Fictional demo character invented by Team Valkyrie to demonstrate character records, relationships and missions. Not part of the game.',
 6, 'demo', NULL, 'Invented for database demonstration.');

-- Relationships marked official are stated on the official Leonida page. The rest are demo.
INSERT INTO character_relationships (from_character_id, to_character_id, relationship_type, description, content_status, source_url) VALUES
(1, 2, 'partner', 'Presented on the official site as the two leads of the story.', 'official', 'https://www.rockstargames.com/VI/only-in-leonida'),
(7, 1, 'employer', 'Brian gives Jason housing in return for his help.', 'official', 'https://www.rockstargames.com/VI/only-in-leonida'),
(3, 1, 'ally', 'Cal is described as Jason''s friend.', 'official', 'https://www.rockstargames.com/VI/only-in-leonida'),
(4, 5, 'associate', 'Described as partners in the Only Raw Records venture.', 'official', 'https://www.rockstargames.com/VI/only-in-leonida'),
(8, 10, 'associate', 'Demo: Delia brokers shipping favours with Nico.', 'demo', NULL),
(8, 9,  'ally',      'Demo: Delia trusts Tomas to move quiet cargo through the wetlands.', 'demo', NULL),
(9, 10, 'rival',     'Demo: Tomas and Nico disagree over who controls the river route.', 'demo', NULL);

-- ------------------------ vehicle categories / vehicles -----------------------
INSERT INTO vehicle_categories (category_id, slug, name, description) VALUES
(1, 'sports',     'Sports',      'Fast, low-slung road cars.'),
(2, 'muscle',     'Muscle',      'Heavy, powerful rear-drive cars.'),
(3, 'sedan',      'Sedans',      'Everyday four-door cars.'),
(4, 'offroad',    'Off-road',    'Trucks and utility vehicles for rough ground.'),
(5, 'boat',       'Boats',       'Watercraft for coast and wetland.'),
(6, 'motorcycle', 'Motorcycles', 'Two-wheeled vehicles.');

-- All vehicles are fictional demo records. No performance statistics are stored.
INSERT INTO vehicles (vehicle_id, category_id, slug, name, manufacturer, summary, description, content_status, source_note) VALUES
(1, 1, 'corvina-gt',      'Corvina GT',      'Veloce Motors',    'Fictional demo sports coupe.',     'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(2, 1, 'strada-lumen',    'Strada Lumen',    'Veloce Motors',    'Fictional demo sports roadster.',  'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(3, 2, 'bruiser-v8',      'Bruiser V8',      'Halcyon Works',    'Fictional demo muscle coupe.',     'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(4, 3, 'meridian-sedan',  'Meridian Sedan',  'Halcyon Works',    'Fictional demo family sedan.',     'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(5, 4, 'ridgeback-4x4',   'Ridgeback 4x4',   'Ironwood Trucks',  'Fictional demo pickup truck.',     'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(6, 5, 'tidewalker-skiff','Tidewalker Skiff','Seabright Marine', 'Fictional demo shallow boat.',     'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(7, 5, 'swampfox-airboat','Swampfox Airboat','Seabright Marine', 'Fictional demo wetland airboat.',  'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.'),
(8, 6, 'zephyr-250',      'Zephyr 250',      'Aerolite Cycles',  'Fictional demo street bike.',      'Fictional demo vehicle invented by Team Valkyrie. It is not a confirmed GTA VI vehicle.', 'demo', 'Invented for database demonstration.');

-- ------------------------------- missions ------------------------------
-- All missions are fictional demo records.
INSERT INTO missions (mission_id, slug, title, mission_type, summary, synopsis, content_status, source_note) VALUES
(1, 'harbour-lights',          'Harbour Lights',          'story',    'Demo mission: a quiet shipment arrives after dark.',        'Fictional demo mission invented by Team Valkyrie. It is not part of the game.', 'demo', 'Invented for database demonstration.'),
(2, 'quiet-water',             'Quiet Water',             'side',     'Demo mission: a guided run through the wetlands.',          'Fictional demo mission invented by Team Valkyrie. It is not part of the game.', 'demo', 'Invented for database demonstration.'),
(3, 'last-call-smokestack-row','Last Call at Smokestack Row','heist', 'Demo mission: a planned job on an industrial strip.',        'Fictional demo mission invented by Team Valkyrie. It is not part of the game.', 'demo', 'Invented for database demonstration.'),
(4, 'ridge-run',               'Ridge Run',               'activity', 'Demo activity: a timed drive to a hilltop lookout.',        'Fictional demo mission invented by Team Valkyrie. It is not part of the game.', 'demo', 'Invented for database demonstration.'),
(5, 'ledger-of-favours',       'Ledger of Favours',       'story',    'Demo mission: a fixer calls in several debts.',             'Fictional demo mission invented by Team Valkyrie. It is not part of the game.', 'demo', 'Invented for database demonstration.');

INSERT INTO mission_characters (mission_id, character_id, role_in_mission) VALUES
(1, 8,  'Arranges the shipment'),
(1, 10, 'Controls the terminal gates'),
(2, 9,  'Guide'),
(2, 8,  'Client'),
(3, 10, 'Inside contact'),
(3, 8,  'Planner'),
(4, 9,  'Race marshal'),
(5, 8,  'Fixer'),
(5, 9,  'Courier'),
(5, 10, 'Debtor');

INSERT INTO mission_vehicles (mission_id, vehicle_id, usage_note) VALUES
(1, 3, 'Escort car'),
(1, 6, 'Water transfer'),
(2, 7, 'Primary transport'),
(3, 5, 'Getaway truck'),
(3, 4, 'Decoy sedan'),
(4, 1, 'Time-trial car'),
(4, 8, 'Alternative bike'),
(5, 2, 'Fixer''s car');

INSERT INTO mission_locations (mission_id, location_id, is_primary) VALUES
(1, 6, TRUE),
(1, 1, FALSE),
(2, 5, TRUE),
(3, 7, TRUE),
(3, 2, FALSE),
(4, 8, TRUE),
(5, 3, TRUE),
(5, 4, FALSE);

-- ------------------------------ media_assets ------------------------------
-- Records only: nothing is copied. All rows await human review before any use.
INSERT INTO media_assets (media_id, slug, title, media_type, intended_use, source_url, embed_url, local_path, attribution, usage_status, approval_status, notes) VALUES
(1, 'official-trailer-1', 'Grand Theft Auto VI Trailer 1', 'trailer',
 'Media Theatre: link to the official trailer page.',
 'https://www.rockstargames.com/VI/trailer-1', NULL, NULL,
 'Copyright Rockstar Games / Take-Two Interactive.', 'link_only', 'pending_review',
 'Official page exists (checked 2026-10-09). Embed URL not yet confirmed. Do not embed until a human approves.'),
(2, 'official-trailer-2', 'Grand Theft Auto VI Trailer 2', 'trailer',
 'Media Theatre: link to the official trailer page.',
 'https://www.rockstargames.com/VI/trailer-2', NULL, NULL,
 'Copyright Rockstar Games / Take-Two Interactive.', 'link_only', 'pending_review',
 'Official page exists (checked 2026-10-09). Embed URL not yet confirmed. Do not embed until a human approves.'),
(3, 'official-media-artwork-hub', 'Official Media and Artwork downloads', 'wallpaper',
 'Wallpaper gallery: link out to Rockstar''s own Media page. Files are never copied into this repository.',
 'https://www.rockstargames.com/VI/media', NULL, NULL,
 'Copyright Rockstar Games / Take-Two Interactive.', 'link_only', 'pending_review',
 'Official page offers videos, screenshots and artwork/wallpapers for download (checked 2026-10-09). It states no licence terms, so a human must review before any use beyond linking.');
