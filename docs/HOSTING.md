# Hosting guide (draft, Stage 5)

**Status: a guide and an assessment. Nothing has been deployed, no provider has been chosen for production (a Render + Aiven college demonstration is prepared in section 9 and not started: no account or resource exists), no production migration has been run and the live database was never opened.**
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
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | the **runtime** account: `SELECT, INSERT, UPDATE, DELETE` on the site's database only. `DB_HOST` must be the host name in the database server's certificate (not an IP address) |
| `DB_SSL_CA` | **required in production**: the path of the database server's CA certificate (a PEM file the host supplies as a secret file, for example `/etc/secrets/db-ca.pem`; never in the repository). With it the connection verifies the server's certificate and host name (section 5, item 2). The site refuses to start in production without a readable CA file |
| `TV_HSTS_MAX_AGE` | optional; seconds for the HSTS header, default one year in production, `0` turns it off (see section 4) |
| `TV_AUTOPLAY_ALWAYS` | ignored in production by design |

The setup and migration account (`MIGRATE_DB_USER`, `MIGRATE_DB_PASSWORD`) is used from **your own machine** to build the database and is **not** set on the host.

## 4. HTTP behaviour a host should know

* **HSTS.** In production, over HTTPS only, every response carries `Strict-Transport-Security: max-age=31536000` (configurable with `TV_HSTS_MAX_AGE`). It is never sent in development or testing,
  never over plain http, and has no `includeSubDomains` or `preload`. Behind a TLS-terminating proxy the site only knows the request is HTTPS if `TV_TRUSTED_PROXIES` is set correctly.
* **Liveness check.** Use `/robots.txt` for the host's "is it up" probe: it needs no database. `/health` checks the database too and answers 503 when MySQL is unreachable, so on a host that
  restarts unhealthy services a sleeping database would cause restart loops.
* **405 answers** carry an `Allow` header, as the HTTP specification requires.

## 5. What the code needed before any deployment

1. **Done (branch `deploy/render-aiven-demo`).** A production WSGI server in a separate `requirements-prod.txt` (`gunicorn==26.2.0`, which is not in `requirements.txt`, so a Windows
   developer machine is unaffected) and a start command, `gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT wsgi:app` (section 9). One worker keeps the in-process sign-in limit
   exact (`docs/ACCOUNTS.md`); the database pool (5) must be at least the number of threads.
2. **Done (same branch). Database TLS verification.** Managed MySQL services require TLS. With the connector's default the connection is encrypted but the server's certificate is
   **not verified**. The optional setting `DB_SSL_CA` (`app/config.py`) names the CA certificate; with it, `Config.db_kwargs()` turns on `ssl_verify_cert` and `ssl_verify_identity`
   (certificate chain and host name), and the connector refuses a server without TLS instead of falling back. In production the site **refuses to start** when `DB_SSL_CA` is unset, is
   not a readable PEM file, holds no CA certificate, or when the connection options stop verifying (`check_database_tls`). Without `DB_SSL_CA`, development and tests behave as before.
   The connector also trusts the operating system's default CAs next to the file (it calls `load_default_certs()` before loading `ssl_ca`), so a certificate that chains to a public CA
   for the right host name would be accepted too; the host-name check still applies.
3. The cold-start and pool findings in `docs/STAGE5_AUDIT.md` (sections 3 and 5) matter most on a host that sleeps: the first request after a wake pays for a fresh database handshake,
   and `connection_timeout` is 5 s. Not changed in Stage 5 and not changed here.

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

Which provider (or none yet); which public name the site gets; and whether to enable the admin area anywhere beyond the test database. (The optional database-TLS setting and the production requirements file are built on the `deploy/render-aiven-demo` branch, section 5, and wait for review.)

## 9. Render + Aiven demonstration: runbook (prepared, nothing executed)

For a college demonstration only. The free tiers change, can sleep and are not a production plan (see section 2 and the comparison in the deployment research). Every step that creates an
account or resource, pushes, or deploys needs your explicit approval; nothing below has been done.

**Render web service**

| Setting | Value |
|---------|-------|
| Language / Python | Python; Render's default for new services is 3.14.8 (their documentation, read 24 October 2026). Override with `PYTHON_VERSION` (a full version such as `3.13.5`) or a `.python-version` file |
| Build command | `pip install -r requirements-prod.txt` |
| Start command | `gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT wsgi:app` |
| Health check path | `/robots.txt` (needs no database; `/health` answers 503 while MySQL is unreachable) |
| Plan | Free for rehearsal (spins down after 15 minutes without traffic; the next request takes about a minute); a paid instance for the demonstration day if it must stay awake |

* `wsgi:app` is the entry point (`wsgi.py`); it refuses to start unless `FLASK_ENV` is set. Gunicorn binds the port Render assigns through `$PORT`.
* **No database creation, migration or `init_db` is part of the build or start command**, ever: the web service only reads and writes through the runtime account.
* Gunicorn 26.2.0 is pure Python and requires Python 3.10 or newer, but its PyPI classifiers list 3.10 to 3.13, not 3.14. If the first build fails on 3.14, set `PYTHON_VERSION` to a 3.13 release.
  The project's tests were run on 3.14.6.

**Environment variables (names only; values are set in Render's dashboard, never in a file in the repository)**

`FLASK_ENV` (`production`), `SECRET_KEY`, `TV_PUBLIC_ORIGINS` (the service's exact `https://...onrender.com` origin, or your custom domain), `TV_TRUSTED_PROXIES` (decide with 9.1 below),
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (the **runtime** account), `DB_SSL_CA` (the secret file's path), and optionally `TV_HSTS_MAX_AGE` (use `300` on the first
deployments so a throwaway host name is not pinned to https for a year) and `PYTHON_VERSION`. `MIGRATE_DB_USER` and `MIGRATE_DB_PASSWORD` are **not** set on Render.

**The CA certificate as a Render secret file.** In the Aiven console open the service, then Overview, Connection information, CA Certificate, Download. In Render open the service, then
Environment, add a Secret File named `db-ca.pem` and paste the file's contents; Render makes it available at `/etc/secrets/db-ca.pem` (their documentation: also in the service's root
directory for non-Docker services; combined secret files are limited to 1 MB). Set `DB_SSL_CA=/etc/secrets/db-ca.pem` and `DB_HOST` to the service host name Aiven shows. The certificate is
not committed anywhere (a test fails if a certificate or key file appears in the source tree). Aiven's project CA can be rotated in two maintenance updates: download the new bundle before the
second one and update the secret file, or the site will refuse to connect (which is the safe failure).

**9.1 Deciding `TV_TRUSTED_PROXIES` (do not guess).** The setting is how many proxies you control in front of the app; the app reads the client address and the https scheme from the
right-hand end of `X-Forwarded-For` / `X-Forwarded-Proto` (`docs/ACCOUNTS.md`). Secondary sources say Render's traffic passes Cloudflare and Render's load balancers and that Render appends to
`X-Forwarded-For` rather than overwriting it; Render's own documentation was not found for this, so the number is **unconfirmed**. Too small and every visitor looks like a proxy (they share
one sign-in allowance); too large and a visitor can choose their own address. To measure it on the first rehearsal deployment: add `--access-logfile - --access-logformat '%({x-forwarded-for}i)s %({x-forwarded-proto}i)s "%(r)s" %(s)s'`
to the start command, open the site from a device whose public address you know, and read the log: the right-most entry that is your address, counted from the right, is the number to set.
Then remove the two logging flags (they record visitors' addresses), set the number, redeploy, and check that `curl -sI https://<host>/` shows `Strict-Transport-Security` (it appears only
when the scheme is trusted) and that repeated failed sign-ins from your device are limited per your address, not per proxy.

**9.2 Database (Aiven for MySQL).** Create an empty database and two accounts with Aiven's tools (section 6): the runtime account and a setup account. Confirm the server reports MySQL 8.0 or newer
before loading anything (Aiven's free-tier page does not state the version, and the schema needs `utf8mb4_0900_ai_ci`). From your own machine, with the downloaded CA file in a local `.env`
(`DB_SSL_CA`, `DB_HOST`, `DB_NAME`, the setup account) run `python -m scripts.init_db`; it reads the same verified settings, prints its target without the password, and refuses a database that
already has project tables. Check 27 tables, then remove the setup account from `.env`. Never run `migrate_db` against the new database.

**9.3 Still open before the demonstration:** the Aiven account, service and users (nothing exists yet); the confirmed MySQL version; the `TV_TRUSTED_PROXIES` number; whether the free database
is awake when the demonstration starts (Aiven may power it off after inactivity and you switch it back on); the first successful TLS-verified connection to the real Aiven service (the
verification is tested against the local test server and with throwaway certificates, not against Aiven); and the unchanged licensing question for Rockstar material.
