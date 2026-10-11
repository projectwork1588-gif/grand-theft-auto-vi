-- =====================================================================
-- Migration 005 (Gate 3A, the Characters page): one official relationship and the character_regions table.
-- NON-DESTRUCTIVE and IDEMPOTENT: creates a table if it is missing and inserts rows only when they are absent.
-- No DROP, no DELETE, no TRUNCATE; nothing existing is changed.
-- 1. Dre'Quan Priest -> Real Dimez. Rockstar's People and Places page says Dre'Quan "signed the Real Dimez" and that the
--    duo are "signed to Only Raw Records".
-- 2. character_regions: where Rockstar's own text places an official character in a region: Jason in the Keys, Brian's
--    smuggling in the Keys, and Boobie as a local Vice City legend. Nothing is inferred.
-- Run after 001 to 004. Apply with: python -m scripts.migrate_db --plan   then   python -m scripts.migrate_db
-- =====================================================================

CREATE TABLE IF NOT EXISTS character_regions (
    character_id  INT UNSIGNED NOT NULL,
    region_id     SMALLINT UNSIGNED NOT NULL,
    note          VARCHAR(255) NOT NULL,
    source_url    VARCHAR(500) NOT NULL,
    PRIMARY KEY (character_id, region_id),
    KEY ix_char_regions_region (region_id),
    CONSTRAINT fk_char_regions_character FOREIGN KEY (character_id)
        REFERENCES characters (character_id) ON DELETE CASCADE,
    CONSTRAINT fk_char_regions_region FOREIGN KEY (region_id)
        REFERENCES regions (region_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO character_relationships (from_character_id, to_character_id, relationship_type, description, content_status, source_url)
SELECT a.character_id, b.character_id, 'associate', 'Dre''Quan signed Real Dimez to Only Raw Records.', 'official',
       'https://www.rockstargames.com/VI/only-in-leonida'
FROM characters a JOIN characters b ON b.slug = 'real-dimez'
WHERE a.slug = 'dre-quan-priest'
  AND NOT EXISTS (SELECT 1 FROM character_relationships x
                  WHERE x.from_character_id = a.character_id AND x.to_character_id = b.character_id);

INSERT INTO character_regions (character_id, region_id, note, source_url)
SELECT c.character_id, r.region_id, x.note, 'https://www.rockstargames.com/VI/only-in-leonida'
FROM (SELECT 'jason-duval' AS cs, 'leonida-keys' AS rs, 'Works for local drug runners in the Keys.' AS note
      UNION ALL SELECT 'brian-heder', 'leonida-keys', 'A drug runner from the golden age of smuggling in the Keys.'
      UNION ALL SELECT 'boobie-ike', 'vice-city', 'A local Vice City legend.') x
JOIN characters c ON c.slug = x.cs
JOIN regions r ON r.slug = x.rs
WHERE NOT EXISTS (SELECT 1 FROM character_regions y WHERE y.character_id = c.character_id AND y.region_id = r.region_id);
