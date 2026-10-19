-- =====================================================================
-- Migration 008 (Music): the radio stations, the score and the album Rockstar shows on its own Music page, https://www.rockstargames.com/VI/music
-- NON-DESTRUCTIVE and IDEMPOTENT: creates four new tables if they are missing and inserts or refreshes their rows.
-- No DROP, no DELETE, no TRUNCATE; the locations, stories, characters and every other table are not touched.
-- Run after 001 to 007. Apply with: python -m scripts.migrate_db --only 008_music.sql --plan   then   python -m scripts.migrate_db --only 008_music.sql
--
--   * Every row is Rockstar's own information (content_status 'official', source_url and verified_on set), copied as written on its Music page on 2026-10-19.
--   * station_preview_tracks are the songs that page lists for each station's preview. They are what the preview plays, not a claim about a station's full playlist.
--   * The singles are the nine that page lists under The Album. Two of Rockstar's links start http:// and are stored as https:// (the same address; the http one redirects).
--   * Nothing here is audio. Previews and full tracks play on Rockstar's own page and the labels' own links, which the site only links to.
-- =====================================================================

CREATE TABLE IF NOT EXISTS radio_stations (
    station_id      SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    slug            VARCHAR(60)   NOT NULL,
    name            VARCHAR(80)   NOT NULL,
    hosts           VARCHAR(120)  NULL,
    description     VARCHAR(500)  NOT NULL,
    logo_url        VARCHAR(500)  NULL,
    background_url  VARCHAR(500)  NULL,
    sort_order      TINYINT UNSIGNED NOT NULL,
    content_status  ENUM('official','fan','demo') NOT NULL,
    source_url      VARCHAR(500)  NULL,
    source_note     VARCHAR(500)  NULL,
    verified_on     DATE          NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (station_id),
    UNIQUE KEY uq_radio_stations_slug (slug),
    UNIQUE KEY uq_radio_stations_name (name),
    KEY ix_radio_stations_order (sort_order),
    CONSTRAINT ck_radio_stations_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS station_preview_tracks (
    station_id   SMALLINT UNSIGNED NOT NULL,
    sort_order   TINYINT UNSIGNED  NOT NULL,
    title        VARCHAR(160)      NOT NULL,
    artists      VARCHAR(200)      NOT NULL,
    PRIMARY KEY (station_id, sort_order),
    CONSTRAINT fk_station_preview_station FOREIGN KEY (station_id)
        REFERENCES radio_stations (station_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS music_releases (
    release_id       SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    slug             VARCHAR(60)   NOT NULL,
    kind             ENUM('score','album') NOT NULL,
    title            VARCHAR(160)  NOT NULL,
    byline           VARCHAR(160)  NULL,
    description      TEXT          NOT NULL,
    release_note     VARCHAR(120)  NULL,
    track_count      SMALLINT UNSIGNED NULL,
    label            VARCHAR(80)   NULL,
    artwork_url      VARCHAR(500)  NULL,
    primary_url      VARCHAR(500)  NULL,
    primary_label    VARCHAR(80)   NULL,
    secondary_url    VARCHAR(500)  NULL,
    secondary_label  VARCHAR(80)   NULL,
    content_status   ENUM('official','fan','demo') NOT NULL,
    source_url       VARCHAR(500)  NULL,
    source_note      VARCHAR(500)  NULL,
    verified_on      DATE          NULL,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (release_id),
    UNIQUE KEY uq_music_releases_slug (slug),
    CONSTRAINT ck_music_releases_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS music_tracks (
    track_id    INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    release_id  SMALLINT UNSIGNED NOT NULL,
    sort_order  TINYINT UNSIGNED  NOT NULL,
    title       VARCHAR(200)      NOT NULL,
    artists     VARCHAR(200)      NOT NULL,
    listen_url  VARCHAR(500)      NULL,
    is_score    TINYINT(1)        NOT NULL DEFAULT 0,
    PRIMARY KEY (track_id),
    UNIQUE KEY uq_music_tracks_order (release_id, sort_order),
    CONSTRAINT fk_music_tracks_release FOREIGN KEY (release_id)
        REFERENCES music_releases (release_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO radio_stations (slug, name, hosts, description, logo_url, background_url, sort_order, content_status, source_url, source_note, verified_on) VALUES
('cocoteo-fm', 'Cocoteo FM', 'El Martillo and La Gata', 'Modern Latin from El Martillo and La Gata. El party que nunca se apaga.', 'https://www.rockstargames.com/VI/_next/static/media/cocoteo-logo.0f_q~~9u45zf5.png', 'https://www.rockstargames.com/VI/_next/static/media/cocoteo-background.0~6dq9w0~ac7f.jpg', 1, 'official', 'https://www.rockstargames.com/VI/music', 'Name, description and the names beside it as written on Rockstar''s Music page; the logo and banner are the images that page shows for the station. Checked on 2026-10-19.', '2026-10-19'),
('back-country-radio', 'Back Country Radio', 'MW and Delta Dawne', 'Airboat-ready renegade country from MW and Delta Dawne.', 'https://www.rockstargames.com/VI/_next/static/media/country-logo.0_u9b8toxgaqe.png', 'https://www.rockstargames.com/VI/_next/static/media/country-background.0dgx5dx.44v.x.jpg', 2, 'official', 'https://www.rockstargames.com/VI/music', 'Name, description and the names beside it as written on Rockstar''s Music page; the logo and banner are the images that page shows for the station. Checked on 2026-10-19.', '2026-10-19'),
('afrobank-fm', 'AfroBank FM', 'Burna and Palmsy', 'Amapiano, African classics, 3-step, and more from Burna and Palmsy. Turn up the gbedu.', 'https://www.rockstargames.com/VI/_next/static/media/afrobank-logo.0r-.t_v9b~9l_.png', 'https://www.rockstargames.com/VI/_next/static/media/afrobank-background.140-_kytq55lt.jpg', 3, 'official', 'https://www.rockstargames.com/VI/music', 'Name, description and the names beside it as written on Rockstar''s Music page; the logo and banner are the images that page shows for the station. Checked on 2026-10-19.', '2026-10-19'),
('the-chamber', 'The Chamber', 'DJ Tom and DJ Kerry', 'Crushing metal has landed in Leonida. Jump in the pit with DJ Kerry and DJ Tom.', 'https://www.rockstargames.com/VI/_next/static/media/chamber-logo.039x21cy5jsiv.png', 'https://www.rockstargames.com/VI/_next/static/media/chamber-background.0bdn5.jnvwos2.jpg', 4, 'official', 'https://www.rockstargames.com/VI/music', 'Name, description and the names beside it as written on Rockstar''s Music page; the logo and banner are the images that page shows for the station. Checked on 2026-10-19.', '2026-10-19'),
('flash-fm', 'Flash FM', 'Robyn and Alex', 'The Vice City institution that delivers the best in pop music and guaranteed grooves with Robyn and Alex.', 'https://www.rockstargames.com/VI/_next/static/media/flash-logo.04o~oki.8dgm0.png', 'https://www.rockstargames.com/VI/_next/static/media/flash-background.0tc3kakjq4vi6.jpg', 5, 'official', 'https://www.rockstargames.com/VI/music', 'Name, description and the names beside it as written on Rockstar''s Music page; the logo and banner are the images that page shows for the station. Checked on 2026-10-19.', '2026-10-19'),
('dirty-south-classics', 'Dirty South Classics', 'Trick and Trina', 'A little southern hospitality from Trick and Trina, blasting regional rap and hip-hop classics.', 'https://www.rockstargames.com/VI/_next/static/media/dirty-south-logo.0oparlmygi1zd.png', 'https://www.rockstargames.com/VI/_next/static/media/dirty-south-background.05~e07omgorbi.jpg', 6, 'official', 'https://www.rockstargames.com/VI/music', 'Name, description and the names beside it as written on Rockstar''s Music page; the logo and banner are the images that page shows for the station. Checked on 2026-10-19.', '2026-10-19')
AS new ON DUPLICATE KEY UPDATE name = new.name, hosts = new.hosts, description = new.description, logo_url = new.logo_url, background_url = new.background_url,
    sort_order = new.sort_order, content_status = new.content_status, source_url = new.source_url, source_note = new.source_note, verified_on = new.verified_on;

INSERT INTO station_preview_tracks (station_id, sort_order, title, artists) VALUES
((SELECT station_id FROM radio_stations WHERE slug = 'cocoteo-fm'), 1, 'EoO', 'Bad Bunny'),
((SELECT station_id FROM radio_stations WHERE slug = 'cocoteo-fm'), 2, 'Si Es Trucho Es Trucho (Remix)', 'Axel Rulay ft. Farruko & El Alfa'),
((SELECT station_id FROM radio_stations WHERE slug = 'cocoteo-fm'), 3, 'Canalla', 'Romeo Santos & El Chaval de la Bachata'),
((SELECT station_id FROM radio_stations WHERE slug = 'back-country-radio'), 1, 'Need a Little Time Off for Bad Behavior', 'David Allan Coe'),
((SELECT station_id FROM radio_stations WHERE slug = 'back-country-radio'), 2, 'Don''t Come Home A-Drinkin'' (With Lovin'' On Your Mind)', 'Loretta Lynn'),
((SELECT station_id FROM radio_stations WHERE slug = 'back-country-radio'), 3, 'The Conversation', 'Hank Williams, Jr. & Waylon Jennings'),
((SELECT station_id FROM radio_stations WHERE slug = 'afrobank-fm'), 1, 'Joha', 'Asake'),
((SELECT station_id FROM radio_stations WHERE slug = 'afrobank-fm'), 2, 'Gye Wani', 'Pat Thomas ft. Ebo Taylor'),
((SELECT station_id FROM radio_stations WHERE slug = 'afrobank-fm'), 3, 'Shay''sana', 'DJ Lag & Robot Boii ft. Kamo Mphela'),
((SELECT station_id FROM radio_stations WHERE slug = 'the-chamber'), 1, 'I', 'Black Sabbath'),
((SELECT station_id FROM radio_stations WHERE slug = 'the-chamber'), 2, 'I''m Broken', 'Pantera'),
((SELECT station_id FROM radio_stations WHERE slug = 'the-chamber'), 3, 'Raining Blood', 'Slayer'),
((SELECT station_id FROM radio_stations WHERE slug = 'flash-fm'), 1, 'Good Ones', 'Charli xcx'),
((SELECT station_id FROM radio_stations WHERE slug = 'flash-fm'), 2, 'Electric Feel', 'MGMT'),
((SELECT station_id FROM radio_stations WHERE slug = 'flash-fm'), 3, 'Midnight Sun (Girls Trip)', 'Zara Larsson & PinkPantheress'),
((SELECT station_id FROM radio_stations WHERE slug = 'dirty-south-classics'), 1, 'Like A Pimp', 'David Banner ft. Lil'' Flip'),
((SELECT station_id FROM radio_stations WHERE slug = 'dirty-south-classics'), 2, 'Who Dat', 'JT Money ft. Solé'),
((SELECT station_id FROM radio_stations WHERE slug = 'dirty-south-classics'), 3, 'Born N Raised', 'DJ Khaled ft. Trick Daddy, Rick Ross & Pitbull')
AS new ON DUPLICATE KEY UPDATE title = new.title, artists = new.artists;

INSERT INTO music_releases (slug, kind, title, byline, description, release_note, track_count, label, artwork_url, primary_url, primary_label, secondary_url, secondary_label, content_status, source_url, source_note, verified_on) VALUES
('justice-score', 'score', 'Original Score Spotlight', 'Justice', 'Listen to the new standalone single “Flower in a Hurricane” from original score composers Justice feat. Tame Impala, SZA, and King Gizzard & The Lizard Wizard.', NULL, NULL, NULL, 'https://www.rockstargames.com/VI/_next/static/media/score-background-desktop.00160ew9j.7ha.jpg', 'https://justice.lnk.to/flowerinahurricane', 'Listen now', NULL, NULL, 'official', 'https://www.rockstargames.com/VI/music', 'Description and Listen Now link as written on Rockstar''s Music page, checked on 2026-10-19. The heading is this site''s own wording: Rockstar''s page heads the block "Official Score by Justice", but its text describes one standalone single from the original score composers, not the whole game''s score.', '2026-10-19'),
('gta-vi-the-album', 'album', 'Grand Theft Auto VI: The Album', NULL, 'With 34 original tracks that capture the electric energy of Grand Theft Auto VI’s world of Vice City and Leonida, Grand Theft Auto VI: The Album features a genre-defying roster of the most exciting artists in the world.', 'Coming November 19', 34, 'Atlantic Records', 'https://www.rockstargames.com/VI/_next/static/media/GTAVI_MusicPage_AlbumArt.05qucexa8vzgb.jpg', 'https://gtavi-thealbum.lnk.to/gtavithealbum', 'Pre-save digital album', 'https://gtavithealbum.lnk.to/store', 'Pre-order vinyl or CD', 'official', 'https://www.rockstargames.com/VI/music', 'Title, description, track count and the words ''Coming November 19'' as written on Rockstar''s Music page (it gives no year there); the label is named on the album''s own site, https://www.gtavi-thealbum.com. Checked on 2026-10-19.', '2026-10-19')
AS new ON DUPLICATE KEY UPDATE kind = new.kind, title = new.title, byline = new.byline, description = new.description, release_note = new.release_note, track_count = new.track_count, label = new.label,
    artwork_url = new.artwork_url, primary_url = new.primary_url, primary_label = new.primary_label, secondary_url = new.secondary_url, secondary_label = new.secondary_label,
    content_status = new.content_status, source_url = new.source_url, source_note = new.source_note, verified_on = new.verified_on;

INSERT INTO music_tracks (release_id, sort_order, title, artists, listen_url, is_score) VALUES
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 1, 'That''s It (feat. Future & Metro Boomin)', 'Yung Lean', 'https://gtavi-thealbum.lnk.to/thatsit', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 2, 'RHYNO', 'Travis Scott', 'https://gtavi-thealbum.lnk.to/rhyno', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 3, 'Sexy Magic', 'CA7RIEL & Paco Amoroso, Pink Pantheress, Fred again.. & Etienne de Crécy', 'https://gtavi-thealbum.lnk.to/sexymagic', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 4, 'Flower in a Hurricane (feat. Tame Impala, SZA, King Gizzard & The Lizard Wizard)', 'Justice', 'https://gtavi-thealbum.lnk.to/FIAH', 1),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 5, 'Last Thing You Need', 'Morgan Wallen', 'https://gtavi-thealbum.lnk.to/lastthingyouneed', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 6, 'Suzuki', 'Fuerza Regida', 'https://gtavi-thealbum.lnk.to/suzuki', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 7, 'Macacoa 2000', 'Rauw Alejandro', 'https://gtavi-thealbum.lnk.to/macacoa2000', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 8, 'Don''t Chart', 'Cardi B', 'https://gtavi-thealbum.lnk.to/dontchart', 0),
((SELECT release_id FROM music_releases WHERE slug = 'gta-vi-the-album'), 9, 'Bright Lights, Big City', 'Keith Richards', 'https://gtavi-thealbum.lnk.to/brightlightsbigcity', 0)
AS new ON DUPLICATE KEY UPDATE title = new.title, artists = new.artists, listen_url = new.listen_url, is_score = new.is_score;
