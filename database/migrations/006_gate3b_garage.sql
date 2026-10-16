-- =====================================================================
-- Migration 006 (Gate 3B, the Garage redesign): two more vehicles Rockstar names and shows in its own screenshots, the pictures
-- the Garage pages use for atmosphere, and plain editorial copy for the official vehicles.
-- NON-DESTRUCTIVE and IDEMPOTENT: inserts or refreshes rows and UPDATEs text columns only.
-- No DROP, no DELETE, no TRUNCATE. Vehicle names, slugs, categories, labels and source links are never changed.
-- Run after 001 to 005. Apply with: python -m scripts.migrate_db --plan   then   python -m scripts.migrate_db
--
--   * Dinka Enduro Motorcycle and Crest Kayak are the titles of two pictures in Rockstar's "Jason's Safehouse Vehicles" set on
--     https://www.rockstargames.com/VI/media/screenshots. The maker is the first word of Rockstar's name for each. Rockstar publishes
--     no specifications for either, so none are stored.
--   * The mod-shop, classic-car and safehouse pictures are Rockstar's own, titled as Rockstar titles them. They are not attached to a
--     vehicle: the Garage uses them as atmosphere and never names a model from them.
--   * The editorial copy only says what the official pictures show.
-- =====================================================================

INSERT INTO vehicles (vehicle_id, category_id, slug, name, manufacturer, summary, description, content_status, source_url, source_note) VALUES
(14, 6, 'dinka-enduro', 'Dinka Enduro Motorcycle', 'Dinka', 'A green trail bike against a teal garage door.',
 'Knobby tyres, a high headlight and a green tank: Rockstar shows the Dinka Enduro Motorcycle parked flat-on against a corrugated shutter, every part of it in view.',
 'official', 'https://www.rockstargames.com/VI/media/screenshots',
 'Named in Rockstar''s Jason''s Safehouse Vehicles screenshots, which show it on its own. The maker is the first word of Rockstar''s name for it. Type judged from the picture. No specifications are published.'),
(15, 5, 'crest-kayak', 'Crest Kayak', 'Crest', 'An orange kayak on calm water at sunset.',
 'A paddler in an orange Crest Kayak heads out across glowing water at sunset, a wooden pier and low houses behind.',
 'official', 'https://www.rockstargames.com/VI/media/screenshots',
 'Named in Rockstar''s Jason''s Safehouse Vehicles screenshots, which show it on the water. The maker is the first word of Rockstar''s name for it. Type judged from the picture. No specifications are published.')
AS new ON DUPLICATE KEY UPDATE
    category_id = new.category_id, name = new.name, manufacturer = new.manufacturer, summary = new.summary,
    description = new.description, content_status = new.content_status, source_url = new.source_url, source_note = new.source_note;

INSERT INTO media_assets (media_id, slug, title, media_type, intended_use, source_url, embed_url, local_path, attribution, usage_status, approval_status, notes) VALUES
(108, 'vehicle-dinka-enduro-01', 'Dinka Enduro Motorcycle, official screenshot', 'screenshot', 'Garage opening, card and vehicle page.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_02.0-2n5rm9n8.rq.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Rockstar''s title: Dinka Enduro Motorcycle. Added for Gate 3B (2026-10-16). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(109, 'vehicle-crest-kayak-01', 'Crest Kayak, official screenshot', 'screenshot', 'Garage opening, card and vehicle page.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_03.0c9.qtpdi.tf..jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image (their Media page invites visitors to download and share). Not copied into this repository. Rockstar''s title: Crest Kayak. Added for Gate 3B (2026-10-16). Rockstar states no licence terms, so a human should re-confirm. File names are build-hashed and may change, so the site falls back to original artwork if an image stops loading.'),
(110, 'garage-jasons-safehouse', 'Jason''s Safehouse Vehicles, official screenshot', 'screenshot', 'Garage: the scene beside the Dinka Enduro Motorcycle and Crest Kayak.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_01.0wv6pw3t-mky3.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image. Not copied into this repository. Rockstar''s title: Jason''s Safehouse Vehicles (the set that also holds the Dinka Enduro Motorcycle and Crest Kayak). It shows a stilt house with a pickup, a motorcycle and a kayak: no vehicle in it is named here. Added for Gate 3B (2026-10-16).'),
(111, 'garage-rideout-customs-01', 'Rideout Customs Mod Shop, official screenshot 1', 'screenshot', 'Garage: customs and classics.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_RIDEOUT_CUSTOMS_01.065-ms8~k8vbq.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image. Not copied into this repository. Rockstar''s title: Rideout Customs Mod Shop 01. The car is not named by Rockstar in this set, so the Garage names none. Added for Gate 3B (2026-10-16).'),
(112, 'garage-one-eyed-willies-01', 'One-Eyed Willie''s Mod Shop, official screenshot 1', 'screenshot', 'Garage: customs and classics.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_ONE_EYED_WILLIE_01.0n7-__or5f.b6.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image. Not copied into this repository. Rockstar''s title: One-Eyed Willie''s Mod Shop 01. The truck is not named by Rockstar in this set, so the Garage names none. Added for Gate 3B (2026-10-16).'),
(113, 'garage-classic-cars-02', 'Classic Car Collection, official screenshot 2', 'screenshot', 'Garage: customs and classics.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_02.0_biiqjqkpg2b.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image. Not copied into this repository. Rockstar''s title: Classic Car Collection 02. The car is not named by Rockstar in this set, so the Garage names none. Added for Gate 3B (2026-10-16).'),
(114, 'garage-classic-cars-04', 'Classic Car Collection, official screenshot 4', 'screenshot', 'Garage: customs and classics.', 'https://www.rockstargames.com/VI/media/screenshots', 'https://www.rockstargames.com/VI/_next/static/media/ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_04.05ku1csui.4h6.jpg', NULL, 'Copyright Rockstar Games / Take-Two Interactive.', 'embed_permitted', 'approved', 'Remote reference to Rockstar''s own published image. Not copied into this repository. Rockstar''s title: Classic Car Collection 04. The car is not named by Rockstar in this set, so the Garage names none. Added for Gate 3B (2026-10-16).')
AS new ON DUPLICATE KEY UPDATE
    title = new.title, media_type = new.media_type, intended_use = new.intended_use,
    source_url = new.source_url, embed_url = new.embed_url, local_path = new.local_path,
    attribution = new.attribution, usage_status = new.usage_status, approval_status = new.approval_status,
    notes = new.notes;

INSERT IGNORE INTO media_vehicles (media_id, vehicle_id) VALUES
(108, 14),
(109, 15),
(110, 14),
(110, 15);

UPDATE vehicles SET summary = 'A white coupe with red racing stripes, caught at golden hour.', description = 'White bodywork, red stripes and a red leather cabin: the ''95 Grotti Cheetah glows in the evening light outside a curved car park, then up close, door open on its red interior.' WHERE slug = 'grotti-cheetah' AND content_status = 'official';
UPDATE vehicles SET summary = 'A Dominator rebuilt for mud and dirt.', description = 'Oversized tyres, a steel bumper and a roof of driving lights: the ''67 Vapid Dominator Buggy ploughs along a wet trail, then waits outside a workshop.' WHERE slug = 'vapid-dominator-buggy' AND content_status = 'official';
UPDATE vehicles SET summary = 'A white speedboat on the bay at dusk.', description = 'The Shitzu Squalo cuts across the water with the skyline lit behind it, then appears from above and up close, its name in black lettering on the white hull.' WHERE slug = 'shitzu-squalo' AND content_status = 'official';
UPDATE vehicles SET summary = 'A yellow-and-white cruiser under the neon.', description = 'Chrome, tail fins and two-tone paint: the Vapid Stanier idles on a neon-lit street, then glows red at the tail light under a moonlit sky.' WHERE slug = 'vapid-stanier' AND content_status = 'official';
UPDATE vehicles SET summary = 'A retro pickup with racing stripes on the coast road.', description = 'A low-slung pickup with red stripes and a hood scoop, photographed on a seaside road with the water behind it. Rockstar titles the picture Vapid Ganado Retro Build.' WHERE slug = 'vapid-ganado' AND content_status = 'official';
