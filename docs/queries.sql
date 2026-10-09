-- =====================================================================
-- Example queries for the viva. Every statement here is executed by
-- tests/test_example_queries.py against the seeded test database.
-- =====================================================================

-- 1. JOIN: every location with the region it belongs to (one-to-many)
SELECT r.name AS region, l.name AS location, l.location_type
FROM locations l
JOIN regions r ON r.region_id = l.region_id
ORDER BY r.name, l.name;

-- 2. WHERE + ORDER BY: only fictional demo characters, alphabetically
SELECT full_name, alias, role_title
FROM characters
WHERE content_status = 'demo'
ORDER BY full_name;

-- 3. GROUP BY + COUNT: vehicles per category (LEFT JOIN keeps empty categories)
SELECT vc.name AS category, COUNT(v.vehicle_id) AS vehicles
FROM vehicle_categories vc
LEFT JOIN vehicles v ON v.category_id = vc.category_id
GROUP BY vc.category_id, vc.name
ORDER BY vehicles DESC, vc.name;

-- 4. HAVING: categories that contain more than one vehicle
SELECT vc.name AS category, COUNT(*) AS vehicles
FROM vehicle_categories vc
JOIN vehicles v ON v.category_id = vc.category_id
GROUP BY vc.category_id, vc.name
HAVING COUNT(*) > 1;

-- 5. Many-to-many: each mission with its cast (junction table + GROUP_CONCAT)
SELECT m.title, COUNT(mc.character_id) AS cast_size,
       GROUP_CONCAT(c.full_name ORDER BY c.full_name SEPARATOR ', ') AS cast_names
FROM missions m
JOIN mission_characters mc ON mc.mission_id = m.mission_id
JOIN characters c ON c.character_id = mc.character_id
GROUP BY m.mission_id, m.title
ORDER BY m.title;

-- 6. Three-table path: missions that happen in a given region, with their vehicles
SELECT DISTINCT m.title, v.name AS vehicle, r.name AS region
FROM missions m
JOIN mission_locations ml ON ml.mission_id = m.mission_id
JOIN locations l ON l.location_id = ml.location_id
JOIN regions r ON r.region_id = l.region_id
JOIN mission_vehicles mv ON mv.mission_id = m.mission_id
JOIN vehicles v ON v.vehicle_id = mv.vehicle_id
WHERE r.slug = 'port-gellhorn'
ORDER BY m.title, v.name;

-- 7. NOT EXISTS: characters who appear in no mission
SELECT c.full_name, c.content_status
FROM characters c
WHERE NOT EXISTS (SELECT 1 FROM mission_characters mc WHERE mc.character_id = c.character_id)
ORDER BY c.full_name;

-- 8. Search + pagination: page 1 (3 rows per page) of a name search
SELECT slug, full_name
FROM characters
WHERE full_name LIKE '%a%'
ORDER BY full_name
LIMIT 3 OFFSET 0;

-- 9. Both directions of a directed relationship table (UNION ALL)
SELECT 'outgoing' AS direction, a.full_name AS this_character, b.full_name AS other_character, cr.relationship_type
FROM character_relationships cr
JOIN characters a ON a.character_id = cr.from_character_id
JOIN characters b ON b.character_id = cr.to_character_id
UNION ALL
SELECT 'incoming', b.full_name, a.full_name, cr.relationship_type
FROM character_relationships cr
JOIN characters a ON a.character_id = cr.from_character_id
JOIN characters b ON b.character_id = cr.to_character_id
ORDER BY this_character, other_character;

-- 10. Most favourited vehicles (the Terminal "TOP FAVOURITED VEHICLES" command will use this shape)
SELECT v.name, COUNT(f.user_id) AS favourites
FROM vehicles v
LEFT JOIN favourite_vehicles f ON f.vehicle_id = v.vehicle_id
GROUP BY v.vehicle_id, v.name
ORDER BY favourites DESC, v.name
LIMIT 5;

-- 11. Honesty report: how much of the content is official, fan or demo, per table
SELECT 'characters' AS entity, content_status, COUNT(*) AS records FROM characters GROUP BY content_status
UNION ALL
SELECT 'regions', content_status, COUNT(*) FROM regions GROUP BY content_status
UNION ALL
SELECT 'vehicles', content_status, COUNT(*) FROM vehicles GROUP BY content_status
UNION ALL
SELECT 'missions', content_status, COUNT(*) FROM missions GROUP BY content_status
ORDER BY entity, content_status;

-- 12. Media inventory: official media by type and permission state (GROUP BY on two columns)
SELECT media_type, usage_status, approval_status, COUNT(*) AS items
FROM media_assets
GROUP BY media_type, usage_status, approval_status
ORDER BY media_type, usage_status;

-- 13. Many-to-many with the Phase 2 junction: official images attached to each region
SELECT r.name AS region, COUNT(mr.media_id) AS images, MIN(m.slug) AS first_image
FROM regions r
JOIN media_regions mr ON mr.region_id = r.region_id
JOIN media_assets m ON m.media_id = mr.media_id AND m.approval_status = 'approved'
GROUP BY r.region_id, r.name
ORDER BY r.name;

-- 14. Official vehicles and how many official images each has (media_vehicles junction, LEFT JOIN + HAVING)
SELECT v.name, vc.name AS category, COUNT(mv.media_id) AS images
FROM vehicles v
JOIN vehicle_categories vc ON vc.category_id = v.category_id
LEFT JOIN media_vehicles mv ON mv.vehicle_id = v.vehicle_id
WHERE v.content_status = 'official'
GROUP BY v.vehicle_id, v.name, vc.name
HAVING COUNT(mv.media_id) >= 1
ORDER BY images DESC, v.name;
