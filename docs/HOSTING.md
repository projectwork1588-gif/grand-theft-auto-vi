# Hosting guide (draft, Stage 5)

**Status: a guide and an assessment. Nothing has been deployed, no provider has been chosen, no production migration has been run and the live database was never opened.**
Read it with `docs/ACCOUNTS.md` ("Production settings", "Migration safety"), which stays the authority on security settings.

## 1. What this site needs from a host

| Need | Why | Where it comes from |
|------|-----|---------------------|
| Python 3.11 or newer (developed on 3.14) | `README.md` | the host's runtime setting |
| **MySQL 8.0 (not MariaDB)** | the schema uses the collation `utf8mb4_0900_ai_ci` 27 times over, which MariaDB does not have; also CHECK constraints, `FIELD()`, `ON DUPLICATE KEY UPDATE` | `database/schema.sql` |
| A production WSGI server pointed at `wsgi:app` | `flask run` is for a developer's machine; `wsgi.py` refuses to start without `FLASK_ENV` | gunicorn on Linux hosts, waitress on Windows (neither is in `requirements.txt` yet, see section 5) |
| HTTPS | the session cookie is `Secure` in production; the site refuses a non-https `TV_PUBLIC_ORIGINS` | the host's TLS |
| Environment variables | secrets and origins never live in the repository | section 3 |
| Small database | the seeded database is a few MB; 1 GB is far more than enough | |
| No persistent disk | the cinematic loops are not in the repository; pages fall back to stills | `media/` is git-ignored |

## 2. Options compared (as of 24 October 2026)

Free tiers change often, so every row needs a re-check on the day. **Verified** means read on the provider's own documentation; **unconfirmed** means from search summaries
or third-party pages.

| Option | MySQL 8 | Free-tier facts | Fit |
|--------|---------|-----------------|-----|
| **Render free web service + Aiven free MySQL** | Aiven for MySQL (a managed MySQL) | Aiven (verified): 1 node, 1 CPU, 1 GB RAM, 1 GB disk, `max_connections` 76, no time limit, **may be powered off after inactivity** (with notice; you switch it back on), no static IP, no VPC, backups included, "learning and prototyping". Render (unconfirmed, from Render's own articles via search): web service sleeps after 15 minutes idle and takes up to about a minute to wake, 750 instance-hours a month, no persistent disk, no card; its free databases are PostgreSQL only. | **Best free pair.** Cost of the pair: slow first visit after idle; the database may need switching on; two dashboards. |
| **Oracle Cloud Always Free VM**, MySQL 8 installed on it | yes, the same as development | Two small x86 VMs and some Arm capacity are offered; the exact 2026 size and the idle-reclaim rule are described differently by different sources (**unconfirmed**); a card is needed at sign-up. | **Best fidelity, most work**: you run the operating system, patches, backups, certificates and MySQL. |
| TiDB Cloud Starter | MySQL-*compatible*, not MySQL | Verified: 5 GiB row storage, 5 GiB columnar, 50 million request units a month, no card for the free plan, TLS required; at quota it denies new connections. | Possible, **unproven**: the collation, `FIELD()` and foreign-key behaviour would need a compatibility run of the whole test suite first. |
| PythonAnywhere free | not for new accounts | Verified: MySQL only for accounts created before 15 January 2026; 1 web app that expires after a month; 512 MiB disk; (unconfirmed) outbound access limited to an allow-list. | **Not viable.** |
| Fly.io, Railway | any | (unconfirmed) no real free tier for new accounts any more (trial or credit based). | Not free. |
| Koyeb | external | (unconfirmed) sources disagree about a free compute tier. | Check the live page before considering it. |
| Shared cPanel hosting | usually MariaDB | | Out: no `utf8mb4_0900_ai_ci`. |

Sources: [PythonAnywhere free accounts](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [Aiven for MySQL free tier](https://aiven.io/docs/products/mysql/concepts/mysql-free-tier),
[TiDB Cloud plans](https://docs.pingcap.com/tidbcloud/select-cluster-tier/), [Render free tier](https://render.com/free).

**Recommendation to decide on (not made):** for a demonstration, Render + Aiven with the limits accepted openly; for the most faithful copy of development, an Oracle VM.

## 3. Settings every host needs

Set in the host's dashboard (never in a file in the repository). The site **refuses to start** without the first four (`docs/ACCOUNTS.md`).

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | at least 32 characters, at least 10 different ones; `python -c "import secrets; print(secrets.token_hex(32))"` |
| `TV_PUBLIC_ORIGINS` | the public address, `https://your-host-name` (no path) |
| `TV_TRUSTED_PROXIES` | the number of proxies in front of the app (1 on a platform that terminates TLS for you, 0 when the app is reached directly). It must be right: the client address, the HTTPS scheme (and so HSTS and the `Secure` cookie logic) come from it. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | the **runtime** account: `SELECT, INSERT, UPDATE, DELETE` on the site's database only |
| `TV_HSTS_MAX_AGE` | optional; seconds for the HSTS header, default one year in production, `0` turns it off (see section 4) |
| `TV_AUTOPLAY_ALWAYS` | ignored in production by design |

The setup and migration account (`MIGRATE_DB_USER`, `MIGRATE_DB_PASSWORD`) is used from **your own machine** to build the database and is **not** set on the host.

## 4. HTTP behaviour a host should know

* **HSTS.** In production, over HTTPS only, every response carries `Strict-Transport-Security: max-age=31536000` (configurable with `TV_HSTS_MAX_AGE`). It is never sent in development or testing,
  never over plain http, and has no `includeSubDomains` or `preload`. Behind a TLS-terminating proxy the site only knows the request is HTTPS if `TV_TRUSTED_PROXIES` is set correctly.
* **Liveness check.** Use `/robots.txt` for the host's "is it up" probe: it needs no database. `/health` checks the database too and answers 503 when MySQL is unreachable, so on a host that
  restarts unhealthy services a sleeping database would cause restart loops.
* **405 answers** carry an `Allow` header, as the HTTP specification requires.

## 5. What the code still needs before any deployment (proposed, not done)

1. A production WSGI server in a separate `requirements-prod.txt` (gunicorn for Linux hosts) and a one-line start command, `gunicorn wsgi:app --workers 1 --threads 4`.
   One worker keeps the in-process sign-in limit exact (`docs/ACCOUNTS.md`); the database pool (5) must be at least the number of threads.
2. **Database TLS options.** Managed MySQL services require TLS. With the connector's default the connection is encrypted but the server's certificate is **not verified**.
   Verifying it needs a small, optional setting (for example `DB_SSL_CA`) in `app/config.py`. That is a new configuration surface and needs your approval.
3. The cold-start and pool findings in `docs/STAGE5_AUDIT.md` (sections 3 and 5) matter most on a host that sleeps: the first request after a wake pays for a fresh database handshake,
   and `connection_timeout` is 5 s. Not changed in Stage 5.

## 6. Building the database on a new host (outline)

1. Create an empty MySQL 8 database and two accounts with the provider's tools: the runtime account (DML only) and a setup account (adds `CREATE, DROP, ALTER, INDEX, REFERENCES`).
   `python -m scripts.setup_db` is **local only by design** (it creates accounts for host `localhost`), so use the SQL in the README ("Prefer to create the accounts yourself", with the host
   your provider needs instead of `localhost`).
2. From your own machine, with the setup account in a local `.env` that points at the new host: `python -m scripts.init_db` loads `database/schema.sql` and `database/seed.sql` in one
   transaction. **A new database already contains everything migrations 001 to 010 add**; never run `migrate_db` against it.
3. Take the setup account out of `.env`; check `/health` and `/` on the host; create one throwaway account to test sign-up, then remove it (there is no account-deletion feature; use SQL).
4. The administrator tool refuses anything but the test database, so **no administrator can be created on a host**: the admin area stays unused there until you decide otherwise (`docs/ADMIN.md`).

## 7. Backups, rollback and what to watch

* Aiven keeps backups; on a self-run MySQL use `mysqldump --single-transaction`, kept outside the repository.
* Rolling back the site is redeploying the previous commit; the schema does not change between Stage 4B and Stage 5.
* Watch: the first-request delay after a sleep, the free database being switched off, the 76-connection limit (not a problem at a pool of 5), and the provider's terms for a fan site.
* The site hosts no Rockstar media; the disclaimer and the licence position in `docs/MEDIA_INVENTORY.md` are unchanged by where it runs.

## 8. Decisions this guide leaves to you

Which provider (or none yet); whether the optional database-TLS setting and the production requirements file may be added (Stage 5.6); which public name the site gets; and whether to enable the admin area anywhere beyond the test database.
