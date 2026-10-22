-- =====================================================================
-- Migration 010 (Accounts): users.email may be NULL.
-- Registration asks for a username and a password only, so there is no email to store. The column and its UNIQUE index stay (MySQL allows many NULLs
-- under a UNIQUE index, and every non-empty email must still be different), so a later email feature needs no further change.
-- NON-DESTRUCTIVE and IDEMPOTENT: one ALTER that relaxes a constraint. It cannot lose or change a stored value, and running it again changes nothing.
-- Apply with: python -m scripts.migrate_db --only 010_account_email_optional.sql --plan   then   python -m scripts.migrate_db --only 010_account_email_optional.sql
-- (add --test to run it on the pytest database; the production database is changed only by a separately approved rollout).
-- =====================================================================

ALTER TABLE users MODIFY email VARCHAR(254) NULL;
