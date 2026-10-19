-- =====================================================================
-- Migration 007 (Leonida / Regions): two region descriptions say more than Rockstar's official site does, so they are rewritten to say only what it does.
-- NON-DESTRUCTIVE and IDEMPOTENT: it UPDATEs the summary and description text of two official regions and nothing else.
-- No DROP, no DELETE, no TRUNCATE. Region names, slugs, status, source links and every relationship are never changed.
-- Run after 001 to 006. Apply with: python -m scripts.migrate_db --only 007_region_wording.sql --plan   then   python -m scripts.migrate_db --only 007_region_wording.sql
--
--   * Grassrivers and Port Gellhorn were described as the turf of Real Dimez and the heist country of Raul Bautista. Rockstar's official "Only in Leonida" page
--     names the regions with an "Explore" link each, but does not say in words which character belongs to which region; that pairing had been read from the
--     order of the links on the page, which can be read two ways. Nothing on the page, in the region postcards or in the screenshots states it.
--   * The new wording keeps to what can be shown: the region is one of the six Rockstar names, and what its own screenshots show. Grassrivers' screenshots
--     show wetlands and airboats; Port Gellhorn's show low rooftops at golden hour and a motel at night.
--   * The other four regions keep their wording: Rockstar's text places Boobie Ike in Vice City and Jason Duval and Brian Heder in the Keys, and the Ambrosia and
--     Mount Kalaga wording describes Rockstar's pictures and its own names ("Mount Kalaga National Park").
--   * character_regions, which lists only the people Rockstar's own text places in a region, is not touched.
-- =====================================================================
UPDATE regions SET summary = 'Wetlands and airboats, in Rockstar''s own screenshots.', description = 'Grassrivers is one of the six regions of Leonida named on Rockstar''s official site. Its screenshots show wetlands and airboats; Rockstar has shared few written details about it so far.' WHERE slug = 'grassrivers' AND content_status = 'official';
UPDATE regions SET summary = 'Rooftops at golden hour and a motel at night, in Rockstar''s own screenshots.', description = 'Port Gellhorn is one of the six regions of Leonida named on Rockstar''s official site. Rockstar has shared few written details about it so far.' WHERE slug = 'port-gellhorn' AND content_status = 'official';
