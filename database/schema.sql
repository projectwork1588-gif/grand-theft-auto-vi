-- =====================================================================
-- GRAND THEFT AUTO VI  |  Team Valkyrie  |  Unofficial educational fan project
-- Schema for MySQL 8.x (InnoDB, utf8mb4)
--
-- Run order: schema.sql -> seed.sql   (python -m scripts.init_db does both)
-- The database itself is created by scripts/setup_db.py (needs an admin account).
--
-- content_status used on core tables:
--   official = named/confirmed by Rockstar Games (source_url REQUIRED)
--   fan      = community or team interpretation, not confirmed
--   demo     = fictional record invented by Team Valkyrie to demonstrate the database
-- NOTE: scripts/sqlfile.py splits this file into statements (it understands quotes
-- and comments). Avoid DELIMITER blocks, stored procedures and triggers here.
-- =====================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS media_vehicles;
DROP TABLE IF EXISTS media_regions;
DROP TABLE IF EXISTS media_locations;
DROP TABLE IF EXISTS media_characters;
DROP TABLE IF EXISTS media_assets;
DROP TABLE IF EXISTS favourite_locations;
DROP TABLE IF EXISTS favourite_missions;
DROP TABLE IF EXISTS favourite_vehicles;
DROP TABLE IF EXISTS favourite_characters;
DROP TABLE IF EXISTS mission_locations;
DROP TABLE IF EXISTS mission_vehicles;
DROP TABLE IF EXISTS mission_characters;
DROP TABLE IF EXISTS missions;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS vehicle_categories;
DROP TABLE IF EXISTS character_relationships;
DROP TABLE IF EXISTS characters;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- users: accounts (registration/login arrive in Phase 3)
-- ---------------------------------------------------------------------
CREATE TABLE users (
    user_id        INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    username       VARCHAR(30)   NOT NULL,
    email          VARCHAR(254)  NOT NULL,
    password_hash  VARCHAR(255)  NOT NULL,
    role           ENUM('user','admin') NOT NULL DEFAULT 'user',
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- regions: the large areas of the state of Leonida (1) -> (N) locations
-- ---------------------------------------------------------------------
CREATE TABLE regions (
    region_id       SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    slug            VARCHAR(60)   NOT NULL,
    name            VARCHAR(80)   NOT NULL,
    summary         VARCHAR(255)  NOT NULL,
    description     TEXT          NOT NULL,
    content_status  ENUM('official','fan','demo') NOT NULL,
    source_url      VARCHAR(500)  NULL,
    source_note     VARCHAR(500)  NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (region_id),
    UNIQUE KEY uq_regions_slug (slug),
    UNIQUE KEY uq_regions_name (name),
    CONSTRAINT ck_regions_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- locations: places inside a region.  region (1) -> (N) location
-- ---------------------------------------------------------------------
CREATE TABLE locations (
    location_id     INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    region_id       SMALLINT UNSIGNED NOT NULL,
    slug            VARCHAR(80)   NOT NULL,
    name            VARCHAR(100)  NOT NULL,
    location_type   ENUM('city','district','landmark','venue','wilderness','waterfront') NOT NULL,
    summary         VARCHAR(255)  NOT NULL,
    description     TEXT          NOT NULL,
    content_status  ENUM('official','fan','demo') NOT NULL,
    source_url      VARCHAR(500)  NULL,
    source_note     VARCHAR(500)  NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (location_id),
    UNIQUE KEY uq_locations_slug (slug),
    UNIQUE KEY uq_locations_region_name (region_id, name),
    CONSTRAINT fk_locations_region FOREIGN KEY (region_id)
        REFERENCES regions (region_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_locations_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- characters.  location (1) -> (N) characters via optional home_location_id
-- ---------------------------------------------------------------------
CREATE TABLE characters (
    character_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    slug              VARCHAR(80)   NOT NULL,
    full_name         VARCHAR(100)  NOT NULL,
    alias             VARCHAR(60)   NULL,
    role_title        VARCHAR(80)   NOT NULL,
    summary           VARCHAR(255)  NOT NULL,
    biography         TEXT          NOT NULL,
    home_location_id  INT UNSIGNED  NULL,
    content_status    ENUM('official','fan','demo') NOT NULL,
    source_url        VARCHAR(500)  NULL,
    source_note       VARCHAR(500)  NULL,
    created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (character_id),
    UNIQUE KEY uq_characters_slug (slug),
    KEY ix_characters_full_name (full_name),
    KEY ix_characters_status (content_status),
    CONSTRAINT fk_characters_home_location FOREIGN KEY (home_location_id)
        REFERENCES locations (location_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT ck_characters_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- character_relationships: character (M) <-> (N) character (directed).
-- One row = "from_character is <relationship_type> of to_character".
-- Composite PK stops duplicates, CHECK stops self-relationships.
-- ---------------------------------------------------------------------
CREATE TABLE character_relationships (
    from_character_id  INT UNSIGNED NOT NULL,
    to_character_id    INT UNSIGNED NOT NULL,
    relationship_type  ENUM('partner','ally','employer','associate','rival','family','other') NOT NULL,
    description        VARCHAR(255) NOT NULL,
    content_status     ENUM('official','fan','demo') NOT NULL,
    source_url         VARCHAR(500) NULL,
    PRIMARY KEY (from_character_id, to_character_id),
    KEY ix_char_rel_to (to_character_id),
    -- MySQL forbids ON UPDATE CASCADE on columns used in a CHECK (error 3823).
    -- Primary keys never change, so the default ON UPDATE RESTRICT loses nothing.
    CONSTRAINT fk_char_rel_from FOREIGN KEY (from_character_id)
        REFERENCES characters (character_id) ON DELETE CASCADE,
    CONSTRAINT fk_char_rel_to FOREIGN KEY (to_character_id)
        REFERENCES characters (character_id) ON DELETE CASCADE,
    CONSTRAINT ck_char_rel_not_self CHECK (from_character_id <> to_character_id),
    CONSTRAINT ck_char_rel_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- vehicle_categories: lookup table.  category (1) -> (N) vehicles
-- ---------------------------------------------------------------------
CREATE TABLE vehicle_categories (
    category_id  TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    slug         VARCHAR(40)  NOT NULL,
    name         VARCHAR(60)  NOT NULL,
    description  VARCHAR(255) NOT NULL,
    PRIMARY KEY (category_id),
    UNIQUE KEY uq_vehicle_categories_slug (slug),
    UNIQUE KEY uq_vehicle_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- vehicles.  No performance statistics are stored on purpose: none are confirmed.
-- ---------------------------------------------------------------------
CREATE TABLE vehicles (
    vehicle_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    category_id     TINYINT UNSIGNED NOT NULL,
    slug            VARCHAR(80)   NOT NULL,
    name            VARCHAR(100)  NOT NULL,
    manufacturer    VARCHAR(80)   NULL,
    summary         VARCHAR(255)  NOT NULL,
    description     TEXT          NOT NULL,
    content_status  ENUM('official','fan','demo') NOT NULL,
    source_url      VARCHAR(500)  NULL,
    source_note     VARCHAR(500)  NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (vehicle_id),
    UNIQUE KEY uq_vehicles_slug (slug),
    UNIQUE KEY uq_vehicles_name (name),
    KEY ix_vehicles_category (category_id),
    CONSTRAINT fk_vehicles_category FOREIGN KEY (category_id)
        REFERENCES vehicle_categories (category_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_vehicles_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- missions: story / side content records
-- ---------------------------------------------------------------------
CREATE TABLE missions (
    mission_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    slug            VARCHAR(80)   NOT NULL,
    title           VARCHAR(120)  NOT NULL,
    mission_type    ENUM('story','side','heist','activity') NOT NULL,
    summary         VARCHAR(255)  NOT NULL,
    synopsis        TEXT          NOT NULL,
    content_status  ENUM('official','fan','demo') NOT NULL,
    source_url      VARCHAR(500)  NULL,
    source_note     VARCHAR(500)  NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mission_id),
    UNIQUE KEY uq_missions_slug (slug),
    UNIQUE KEY uq_missions_title (title),
    KEY ix_missions_type (mission_type),
    CONSTRAINT ck_missions_official_source
        CHECK (content_status <> 'official' OR source_url IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- Junction tables (many-to-many) with composite primary keys
-- ---------------------------------------------------------------------
CREATE TABLE mission_characters (
    mission_id         INT UNSIGNED NOT NULL,
    character_id       INT UNSIGNED NOT NULL,
    role_in_mission    VARCHAR(80)  NOT NULL,
    PRIMARY KEY (mission_id, character_id),
    KEY ix_mission_characters_character (character_id),
    CONSTRAINT fk_mc_mission FOREIGN KEY (mission_id)
        REFERENCES missions (mission_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_mc_character FOREIGN KEY (character_id)
        REFERENCES characters (character_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE mission_vehicles (
    mission_id   INT UNSIGNED NOT NULL,
    vehicle_id   INT UNSIGNED NOT NULL,
    usage_note   VARCHAR(160) NOT NULL,
    PRIMARY KEY (mission_id, vehicle_id),
    KEY ix_mission_vehicles_vehicle (vehicle_id),
    CONSTRAINT fk_mv_mission FOREIGN KEY (mission_id)
        REFERENCES missions (mission_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_mv_vehicle FOREIGN KEY (vehicle_id)
        REFERENCES vehicles (vehicle_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE mission_locations (
    mission_id    INT UNSIGNED NOT NULL,
    location_id   INT UNSIGNED NOT NULL,
    is_primary    BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (mission_id, location_id),
    KEY ix_mission_locations_location (location_id),
    CONSTRAINT fk_ml_mission FOREIGN KEY (mission_id)
        REFERENCES missions (mission_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ml_location FOREIGN KEY (location_id)
        REFERENCES locations (location_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- Favourites: user (M) <-> (N) entity.  One table per entity keeps real
-- foreign keys (a single polymorphic table cannot).
-- ---------------------------------------------------------------------
CREATE TABLE favourite_characters (
    user_id       INT UNSIGNED NOT NULL,
    character_id  INT UNSIGNED NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, character_id),
    KEY ix_fav_characters_entity (character_id),
    CONSTRAINT fk_favc_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_favc_entity FOREIGN KEY (character_id)
        REFERENCES characters (character_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE favourite_vehicles (
    user_id     INT UNSIGNED NOT NULL,
    vehicle_id  INT UNSIGNED NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, vehicle_id),
    KEY ix_fav_vehicles_entity (vehicle_id),
    CONSTRAINT fk_favv_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_favv_entity FOREIGN KEY (vehicle_id)
        REFERENCES vehicles (vehicle_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE favourite_missions (
    user_id     INT UNSIGNED NOT NULL,
    mission_id  INT UNSIGNED NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, mission_id),
    KEY ix_fav_missions_entity (mission_id),
    CONSTRAINT fk_favm_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_favm_entity FOREIGN KEY (mission_id)
        REFERENCES missions (mission_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE favourite_locations (
    user_id      INT UNSIGNED NOT NULL,
    location_id  INT UNSIGNED NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, location_id),
    KEY ix_fav_locations_entity (location_id),
    CONSTRAINT fk_favl_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_favl_entity FOREIGN KEY (location_id)
        REFERENCES locations (location_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- media_assets: the database half of the media inventory.
-- Nothing here is a copy of Rockstar media - rows only RECORD where an asset
-- lives (official link / permitted embed / our own file) and its permission state.
-- ---------------------------------------------------------------------
CREATE TABLE media_assets (
    media_id         INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    slug             VARCHAR(80)   NOT NULL,
    title            VARCHAR(150)  NOT NULL,
    media_type       ENUM('trailer','video','screenshot','wallpaper','artwork') NOT NULL,
    intended_use     VARCHAR(255)  NOT NULL,
    source_url       VARCHAR(500)  NULL,
    embed_url        VARCHAR(500)  NULL,
    local_path       VARCHAR(255)  NULL,
    attribution      VARCHAR(255)  NOT NULL,
    usage_status     ENUM('link_only','embed_permitted','original','licensed','permission_required') NOT NULL,
    approval_status  ENUM('pending_review','approved','rejected') NOT NULL DEFAULT 'pending_review',
    notes            VARCHAR(500)  NULL,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (media_id),
    UNIQUE KEY uq_media_assets_slug (slug),
    KEY ix_media_assets_type (media_type),
    CONSTRAINT ck_media_has_location
        CHECK (source_url IS NOT NULL OR embed_url IS NOT NULL OR local_path IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE media_characters (
    media_id      INT UNSIGNED NOT NULL,
    character_id  INT UNSIGNED NOT NULL,
    PRIMARY KEY (media_id, character_id),
    KEY ix_media_characters_character (character_id),
    CONSTRAINT fk_medc_media FOREIGN KEY (media_id)
        REFERENCES media_assets (media_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_medc_character FOREIGN KEY (character_id)
        REFERENCES characters (character_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE media_locations (
    media_id     INT UNSIGNED NOT NULL,
    location_id  INT UNSIGNED NOT NULL,
    PRIMARY KEY (media_id, location_id),
    KEY ix_media_locations_location (location_id),
    CONSTRAINT fk_medl_media FOREIGN KEY (media_id)
        REFERENCES media_assets (media_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_medl_location FOREIGN KEY (location_id)
        REFERENCES locations (location_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Added in Phase 2 (see database/migrations/001_phase2_media.sql): official region imagery
-- belongs to REGIONS, not to the fictional demo locations, so it needs its own junction.
CREATE TABLE media_regions (
    media_id   INT UNSIGNED      NOT NULL,
    region_id  SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (media_id, region_id),
    KEY ix_media_regions_region (region_id),
    CONSTRAINT fk_medr_media FOREIGN KEY (media_id)
        REFERENCES media_assets (media_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_medr_region FOREIGN KEY (region_id)
        REFERENCES regions (region_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Added in the Phase 2 refinement (see database/migrations/002_phase2_garage.sql): official vehicle screenshots
-- belong to the vehicles Rockstar names, never to the fictional demo vehicles.
CREATE TABLE media_vehicles (
    media_id    INT UNSIGNED NOT NULL,
    vehicle_id  INT UNSIGNED NOT NULL,
    PRIMARY KEY (media_id, vehicle_id),
    KEY ix_media_vehicles_vehicle (vehicle_id),
    CONSTRAINT fk_medv_media FOREIGN KEY (media_id)
        REFERENCES media_assets (media_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_medv_vehicle FOREIGN KEY (vehicle_id)
        REFERENCES vehicles (vehicle_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
