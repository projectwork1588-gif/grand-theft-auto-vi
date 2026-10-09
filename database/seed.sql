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
-- Records only: nothing is copied. Images and players are REMOTE references to Rockstar's own published media.
-- Generated from one manifest (see docs/MEDIA_INVENTORY.md). Mirrors database/migrations/001_phase2_media.sql.
INSERT INTO media_assets (media_id, slug, title, media_type, intended_use, source_url, embed_url, local_path, attribution, usage_status, approval_status, notes) VALUES
(1, 'official-trailer-1', 'Grand Theft Auto VI Trailer 1', 'trailer', 'Trailer preview on the homepage: opens Rockstar''s player on demand.', 'https://www.rockstargames.com/VI/trailer-1', 'https://www.rockstargames.com/videoplayer?id=rkoCtr1r&embed&autoplay=false&locale=en_us', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Official embed: Rockstar''s own player page, built to be framed, with no framing restriction (checked 2026-10-09). Nothing is downloaded. Loaded only when a visitor presses play.'),
(2, 'official-trailer-2', 'Grand Theft Auto VI Trailer 2', 'trailer', 'Trailer preview on the homepage: opens Rockstar''s player on demand.', 'https://www.rockstargames.com/VI/trailer-2', 'https://www.rockstargames.com/videoplayer?id=cpys7u21&embed&autoplay=false&locale=en_us', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Official embed: Rockstar''s own player page, built to be framed, with no framing restriction (checked 2026-10-09). Nothing is downloaded. Loaded only when a visitor presses play.'),
(3, 'official-media-artwork-hub', 'Official Media and Artwork downloads', 'wallpaper', 'Link out to Rockstar''s own Media page. Files are never copied into this repository.', 'https://www.rockstargames.com/VI/media', NULL, NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'link_only', 'approved', 'Plain link to the official Media page, which offers videos, screenshots and artwork for download. No licence terms are stated there.'),
(4, 'official-an-extended-look', 'Grand Theft Auto VI: An Extended Look', 'video', 'Video preview on the homepage: opens Rockstar''s player on demand.', 'https://www.rockstargames.com/VI/an-extended-look', 'https://www.rockstargames.com/videoplayer?id=rk721912&embed&autoplay=false&locale=en_us', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Official embed: Rockstar''s own player page, built to be framed, with no framing restriction (checked 2026-10-09). Nothing is downloaded. Loaded only when a visitor presses play.'),
(5, 'art-jason-lucia-beach', 'Jason and Lucia on the beach (official artwork)', 'artwork', 'Hero background and character galleries.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_Beach_landscape.0419q._86ukpt.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(6, 'art-jason-lucia-01', 'Jason and Lucia, artwork 1 (official artwork)', 'artwork', 'Hero background and character galleries.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_01_landscape.12x2gvspcm_3m.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(7, 'art-jason-lucia-02', 'Jason and Lucia, artwork 2 (official artwork)', 'artwork', 'Hero background and character galleries.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_02_landscape.0cosv-uzbpt91.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(8, 'art-jason-lucia-robbery', 'Jason and Lucia, the robbery (official artwork)', 'artwork', 'Hero background and character galleries.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_Robbery_landscape.09c8a~do21h4p.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(9, 'art-jason-lucia-motel', 'Jason and Lucia at the motel (official artwork)', 'artwork', 'Hero background and character galleries.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_Motel_landscape.08edvuwtm-20v.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(10, 'art-cal-hampton', 'Cal Hampton (official artwork)', 'artwork', 'Character portrait on the catalogue, profile and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Cal_Hampton_landscape.17k7bnt3myg.2.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(11, 'art-boobie-ike', 'Boobie Ike (official artwork)', 'artwork', 'Character portrait on the catalogue, profile and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Boobie_Ike_landscape.0ldnbn87k-8mq.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(12, 'art-dequan-priest', 'Dre''Quan Priest (official artwork)', 'artwork', 'Character portrait on the catalogue, profile and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/DreQuan_Priest_landscape.0_b7hszyze6cy.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(13, 'art-real-dimez', 'Real Dimez (official artwork)', 'artwork', 'Character portrait on the catalogue, profile and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Real_Dimez_landscape.0637akp_a5a_q.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(14, 'art-raul-bautista', 'Raul Bautista (official artwork)', 'artwork', 'Character portrait on the catalogue, profile and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Raul_Bautista_landscape.11_3hd0fr69~j.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(15, 'art-brian-heder', 'Brian Heder (official artwork)', 'artwork', 'Character portrait on the catalogue, profile and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Brian_Heder_landscape.0a-egj5b8yo1q.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(16, 'postcard-vice-city', 'Vice City postcard (official artwork)', 'artwork', 'Region cover image on the regions pages and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Vice_City_Postcard_landscape.0v2njmlk2n-qm.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(17, 'postcard-leonida-keys', 'Leonida Keys postcard (official artwork)', 'artwork', 'Region cover image on the regions pages and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Leonida_Keys_Postcard_landscape.05oezf2h--~ed.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(18, 'postcard-grassrivers', 'Grassrivers postcard (official artwork)', 'artwork', 'Region cover image on the regions pages and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Grassrivers_Postcard_landscape.15-10i39nhex2.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(19, 'postcard-port-gellhorn', 'Port Gellhorn postcard (official artwork)', 'artwork', 'Region cover image on the regions pages and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Port_Gellhorn_Postcard_landscape.176c2o75nmcr8.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(20, 'postcard-ambrosia', 'Ambrosia postcard (official artwork)', 'artwork', 'Region cover image on the regions pages and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Ambrosia_Postcard_landscape.0gd~9a41ia-rt.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(21, 'postcard-mount-kalaga', 'Mount Kalaga National Park postcard (official artwork)', 'artwork', 'Region cover image on the regions pages and homepage.', 'https://www.rockstargames.com/VI/media/artwork-wallpapers', 'https://www.rockstargames.com/VI/_next/static/media/Mount_Kalaga_National_Park_Postcard_landscape.0c1cb4ocq16n3.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(22, 'shot-jason-duval-01', 'Jason Duval, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_Duval_01.07m377xeb6jhq.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(23, 'shot-jason-duval-02', 'Jason Duval, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_Duval_02.1486~7_v40cn..jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(24, 'shot-jason-duval-03', 'Jason Duval, official screenshot 3', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_Duval_03.0-1vum7x-3vtp.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(25, 'shot-lucia-caminos-01', 'Lucia Caminos, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Lucia_Caminos_01.0a7yqvewctkfp.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(26, 'shot-lucia-caminos-02', 'Lucia Caminos, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Lucia_Caminos_02.16n.5umvlu_48.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(27, 'shot-lucia-caminos-03', 'Lucia Caminos, official screenshot 3', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Lucia_Caminos_03.14xgd2y_ymmeg.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(28, 'shot-jason-and-lucia-01', 'Jason and Lucia, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_01.0naeahss9-1x6.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(29, 'shot-jason-and-lucia-02', 'Jason and Lucia, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_02.0uig00eojlokf.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(30, 'shot-jason-and-lucia-03', 'Jason and Lucia, official screenshot 3', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_03.15z-.c0tptrzs.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(31, 'shot-jason-and-lucia-04', 'Jason and Lucia, official screenshot 4', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_04.0m7i~huzhskdw.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(32, 'shot-cal-hampton-01', 'Cal Hampton, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Cal_Hampton_01.0xlil231_osh4.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(33, 'shot-cal-hampton-02', 'Cal Hampton, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Cal_Hampton_02.05r2t_mck65fe.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(34, 'shot-boobie-ike-01', 'Boobie Ike, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Boobie_Ike_01.0-wji2pg5anfs.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(35, 'shot-boobie-ike-02', 'Boobie Ike, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Boobie_Ike_02.0sp9mtc.1cdzs.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(36, 'shot-dequan-priest-01', 'Dre''Quan Priest, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/DreQuan_Priest_01.0_0~wi-ipdj35.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(37, 'shot-dequan-priest-02', 'Dre''Quan Priest, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/DreQuan_Priest_02.02u69e~nkk3eo.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(38, 'shot-real-dimez-01', 'Real Dimez, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Real_Dimez_01.0djwwboo8-glx.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(39, 'shot-real-dimez-02', 'Real Dimez, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Real_Dimez_02.1366u9.x.yp0_.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(40, 'shot-raul-bautista-01', 'Raul Bautista, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Raul_Bautista_01.0md1ii-yrn96r.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(41, 'shot-raul-bautista-02', 'Raul Bautista, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Raul_Bautista_02.10ddy6ogywu-t.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(42, 'shot-brian-heder-01', 'Brian Heder, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Brian_Heder_01.0r.ute88os9k-.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(43, 'shot-brian-heder-02', 'Brian Heder, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Brian_Heder_02.0kmg6iw38f-9o.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(44, 'shot-vice-city-01', 'Vice City, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Vice_City_01.135x56yoeu.6t.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(45, 'shot-vice-city-02', 'Vice City, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Vice_City_02.0c5.7qx17u9kl.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(46, 'shot-vice-city-03', 'Vice City, official screenshot 3', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Vice_City_03.0nqz~lrqdmlze.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(47, 'shot-vice-city-04', 'Vice City, official screenshot 4', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Vice_City_04.06evqutgh7624.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(48, 'shot-leonida-keys-01', 'Leonida Keys, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Leonida_Keys_01.0zgz7tveur6y8.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(49, 'shot-leonida-keys-02', 'Leonida Keys, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Leonida_Keys_02.0~ptk-53gl0lq.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(50, 'shot-grassrivers-01', 'Grassrivers, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Grassrivers_01.1096rw4lbjur_.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(51, 'shot-grassrivers-02', 'Grassrivers, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Grassrivers_02.0teqs5xe2pem1.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(52, 'shot-port-gellhorn-01', 'Port Gellhorn, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Port_Gellhorn_01.0fmisvza-5-cq.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(53, 'shot-port-gellhorn-02', 'Port Gellhorn, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Port_Gellhorn_02.00e7cz6lwrup-.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(54, 'shot-ambrosia-01', 'Ambrosia, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Ambrosia_01.0rqphs0gazkm..jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(55, 'shot-ambrosia-02', 'Ambrosia, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Ambrosia_02.0wtqs05ozl.ym.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(56, 'shot-mount-kalaga-01', 'Mount Kalaga National Park, official screenshot 1', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Mount_Kalaga_National_Park_01.0v5fl0f83hjv_.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(57, 'shot-mount-kalaga-02', 'Mount Kalaga National Park, official screenshot 2', 'screenshot', 'Gallery image on the related profile page and the homepage media preview.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/Mount_Kalaga_National_Park_02.0f24dhopdprvx.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Approved for display by the Team Valkyrie Phase 2 media brief (2026-10-09). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.');

INSERT INTO media_characters (media_id, character_id) VALUES
(1, 1),
(1, 2),
(2, 1),
(2, 2),
(5, 1),
(5, 2),
(6, 1),
(6, 2),
(7, 1),
(7, 2),
(8, 1),
(8, 2),
(9, 1),
(9, 2),
(10, 3),
(11, 4),
(12, 5),
(13, 11),
(14, 6),
(15, 7),
(22, 1),
(23, 1),
(24, 1),
(25, 2),
(26, 2),
(27, 2),
(28, 1),
(28, 2),
(29, 1),
(29, 2),
(30, 1),
(30, 2),
(31, 1),
(31, 2),
(32, 3),
(33, 3),
(34, 4),
(35, 4),
(36, 5),
(37, 5),
(38, 11),
(39, 11),
(40, 6),
(41, 6),
(42, 7),
(43, 7);

INSERT INTO media_regions (media_id, region_id) VALUES
(16, 1),
(17, 2),
(18, 3),
(19, 4),
(20, 5),
(21, 6),
(44, 1),
(45, 1),
(46, 1),
(47, 1),
(48, 2),
(49, 2),
(50, 3),
(51, 3),
(52, 4),
(53, 4),
(54, 5),
(55, 5),
(56, 6),
(57, 6);
