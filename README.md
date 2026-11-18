# Snack Overflow

Snack Overflow is an office-pantry dashboard with a React + Vite frontend, a Flask REST API, and PostgreSQL persistence. Members can browse snacks, consume stock, and vote for a snack of the week. Administrators can manage snacks and restock inventory.

## Features

- JWT login and public member registration with hashed passwords and server-side role checks.
- Dashboard counts and snack-of-the-week loaded from the API.
- A separate admin dashboard analysis module with all-time stock movement, most-consumed snacks, and vote-based community favorites.
- Member profile activity history, scoped to the signed-in member.
- Server-filtered snack search, category/status filters, and pagination.
- Member consume and vote/unvote actions; administrators can manage and restock but cannot consume.
- Admin snack create/edit/delete and restocking.
- Database-enforced quantity, role, activity, and vote constraints.
- Atomic stock changes with activity records in the same transaction.
- Focused API tests and an opt-in PostgreSQL concurrency integration test.

## Round 2 assignment requirements

### Frontend

- After login, the interface adapts to the user's role. Members do not see admin-only analysis, snack management, or restocking controls; the API independently enforces those permissions.
- The dashboard shows live pantry summaries and Snack of the Week. The snack list uses API-backed search, category/status filters, and pagination.
- Running-low and gone items have distinct status indicators. Members can consume and vote; admins can add, restock, edit, and delete snacks.
- Loading, empty, and error states are provided, and the layout adapts to phone-sized screens. Server conflict messages are shown to the user, including when another request consumed the remaining stock first.

### Concurrency and voting guarantees

- Consumption is a conditional database update (`quantity >= amount`), not an application-side read-then-write check. PostgreSQL serializes conflicting updates, so stock cannot become negative. With 10 simultaneous one-packet requests against stock of 3, exactly 3 succeed and the remainder receive `409 Conflict`.
- The database enforces `UNIQUE (user_id, snack_id)` on votes. This guarantees at most one active vote per user for each snack, including concurrent requests; duplicate attempts return `409 Conflict`. Users may vote for different snacks.
- Each successful consume or restock and its activity record are committed in the same transaction. If either write fails, both are rolled back.

### Security, API, and tests

- Passwords are stored as hashes. Protected routes require JWT authentication, and authorization and input validation are enforced on the server. Public registration can create member accounts only.
- API errors use the same `{ "error": { "code": "...", "message": "..." } }` response shape with appropriate HTTP status codes.
- Automated backend tests cover critical API behavior. The opt-in PostgreSQL test verifies the 10-request/3-packet concurrency case; run instructions are in [Tests](#tests). The seed script creates sample snacks and one admin and one member, is safe to rerun, and is never run automatically at application startup.

## Technology

- Frontend: React 18, Vite, Axios, Vitest.
- Backend: Python 3, Flask, Flask-SQLAlchemy, Flask-JWT-Extended.
- Database: PostgreSQL with Psycopg 3.
- Backend tests: Pytest.

## Requirements

- Python 3.10 or later.
- Node.js 18 or later and npm.
- PostgreSQL 14 or later.

## Install and configure

Commands below use PowerShell on Windows; use the corresponding activation and copy commands for your shell on other platforms.

1. Create a PostgreSQL database:

   ```powershell
   psql -U postgres -c "CREATE DATABASE snack_overflow;"
   ```

2. Create and activate a virtual environment from the project root, then install backend dependencies:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r backend\requirements.txt
   ```

3. Copy the environment template and edit `backend/.env`:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

   Set these values in `backend/.env`:

   | Variable | Purpose |
   | --- | --- |
   | `SECRET_KEY` | Flask application secret; generate a random value. |
   | `JWT_SECRET_KEY` | JWT signing secret; use a different random value from `SECRET_KEY`. |
   | `DATABASE_URL` | SQLAlchemy URL for the local PostgreSQL database, using the `postgresql+psycopg` driver. |
   | `CORS_ORIGINS` | Comma-separated frontend origins; local development uses `http://localhost:5173`. |
   | `SEED_ADMIN_PASSWORD` | Local password assigned to the seeded admin account. |
   | `SEED_MEMBER_PASSWORD` | Local password assigned to the seeded member account. |

   Generate each application secret independently, for example:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   A database URL has the form `postgresql+psycopg://<user>:<password>@localhost:5432/snack_overflow`. Put real values only in the ignored `backend/.env` file. URL-encode special characters in the database username or password.

4. Initialize a new database and add optional local starter records:

   ```powershell
   Set-Location backend
   python -m flask --app run:app db upgrade
   python seed.py
   ```

   The migration command creates the schema from the checked-in Alembic migrations. The seed script also runs migrations before seeding and reads account passwords from `SEED_ADMIN_PASSWORD` and `SEED_MEMBER_PASSWORD` only when it needs to create those accounts. It hashes the passwords and only creates missing accounts and snacks; rerunning it does not change existing passwords, user details, snack quantities, or duplicate records.

   For an existing database that already has tables but has no Alembic version record, back it up and verify its schema before proceeding. If it exactly matches the current models, record the baseline with:

   ```powershell
   flask --app run:app db stamp head
   ```

   Do not run `stamp` on an empty or partially initialized database. The legacy `migrations\001_stage2_schema.sql` file is a manual Stage 2 patch for older populated databases; it is not the initial schema migration and is not run automatically.

5. Start the backend locally from `backend`:

   ```powershell
   python run.py
   ```

   The API is available at `http://localhost:5000`.

6. In a separate terminal, install and start the frontend:

   ```powershell
   Set-Location frontend
   npm ci
   npm run dev
   ```

   Open `http://localhost:5173`. If the API is hosted elsewhere, set `VITE_API_URL` in the frontend environment to the API base URL (including `/api`).

## Docker Compose

The root `docker-compose.yml` runs PostgreSQL, the Flask backend, and the React frontend. Docker Compose v2 and Docker Desktop (or a compatible Docker Engine) are required.

1. Create the root Compose environment file and set a strong, URL-safe local database password:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Create the backend environment file and replace the example application secrets with distinct random values:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

   Compose supplies `DATABASE_URL` using the PostgreSQL service hostname `db`; do not use `localhost` for the backend-to-database connection. The backend entrypoint runs `flask db upgrade` before Gunicorn starts. It does not run the seed script, so startup will not create demo accounts or modify existing data.

3. Validate the Compose configuration and build/start the services:

   ```powershell
   docker compose config
   docker compose up --build -d
   ```

   Open the frontend at `http://localhost:5173`; the API is available at `http://localhost:5000`. Follow startup and migration logs with `docker compose logs -f backend`.

4. To create the optional local demo accounts and sample snacks, first set unique values for `SEED_ADMIN_PASSWORD` and `SEED_MEMBER_PASSWORD` in `backend/.env`, then run:

   ```powershell
   docker compose exec backend python seed.py
   ```

   The seed script does not reset existing passwords, user details, or stock.

To publish the configured images to Docker Hub, sign in with `docker login`, then run `docker compose build` followed by `docker compose push`. The image names are set in `docker-compose.yml`; change them to repositories you own before pushing if needed. Stop the services with `docker compose down`. The named PostgreSQL volume is retained, so database data remains available when the services are started again.

## Local accounts

The seed script creates these local accounts:

| Role | Email | Password source |
| --- | --- | --- |
| Admin | `admin@snackoverflow.local` | Local `SEED_ADMIN_PASSWORD` value |
| Member | `member@snackoverflow.local` | Local `SEED_MEMBER_PASSWORD` value |

Passwords are deliberately not included in this repository. Set unique, strong local values in `backend/.env`; never reuse production credentials. The seed script stores password hashes, not plaintext passwords.

## Database schema

| Table | Important fields and integrity rules |
| --- | --- |
| `user` | `id`, `name`, unique `email`, `password_hash`, and `role` constrained to `admin` or `member`. |
| `snack` | `id`, unique `name`, constrained `category`, non-negative `quantity`, and non-negative `low_stock_threshold` (default 5). |
| `vote` | `id`, foreign keys `user_id` and `snack_id`, and `created_at`; a database-level unique constraint prevents duplicate `(user_id, snack_id)` votes. |
| `activity` | `id`, foreign keys `user_id` and `snack_id`, constrained `action` (`consumed` or `restocked`), positive `amount`, and `created_at`. |

Snack status is derived at read time and is not stored: quantity `0` is `gone`; quantity from `1` through the low-stock threshold is `running_low`; quantity above the threshold is `stocked`.

## API

All routes are under `/api`. Except for `GET /health`, `POST /auth/login`, and `POST /auth/register`, routes require `Authorization: Bearer <JWT>`. Snack browsing, voting, activity history, and summary endpoints are available to authenticated users, with activity history scoped to the signed-in member. Consumption is member-only; activity analytics, snack creation/edit/deletion, and restocking are admin-only.

| Method and path | Access | Request / behavior |
| --- | --- | --- |
| `GET /health` | Public | Readiness response. |
| `POST /auth/login` | Public | JSON `{ "email": "...", "password": "..." }`; returns `access_token` and the authenticated user summary. |
| `POST /auth/register` | Public | JSON `{ "name": "...", "email": "...", "password": "..." }`; creates a member account and returns `201`, `access_token`, and the user summary. Passwords must be 8–128 characters; email addresses must be unique. A caller cannot choose an account role. |
| `GET /auth/me` | Authenticated | Returns the current user's id, name, email, and role. |
| `GET /snacks` | Authenticated | Optional `category`, `status`, `search`, `page`, and `per_page` query parameters. Defaults: page 1, 12 per page; `per_page` is 1–100. Search is limited to 120 characters. |
| `GET /snacks/<id>` | Authenticated | Returns a snack with its vote count and the current user's vote state. |
| `POST /snacks` | Admin | Creates a snack with `name`, `category`, optional `quantity`, and optional `low_stock_threshold`. |
| `PATCH /snacks/<id>` | Admin | Updates `name`, `category`, and/or `low_stock_threshold`. Stock changes use consume/restock routes. |
| `DELETE /snacks/<id>` | Admin | Deletes a snack without activity history; returns `409` if history prevents deletion. |
| `POST /snacks/<id>/consume` | Member | JSON `{ "amount": <positive integer> }`; returns `403` for administrators and `409` if available stock is insufficient. |
| `POST /snacks/<id>/restock` | Admin | JSON `{ "amount": <positive integer> }`. |
| `GET /snacks/<id>/vote` | Authenticated | Returns the current user's vote state and the snack's total vote count. |
| `POST /snacks/<id>/vote` | Authenticated | Records one vote; a duplicate returns `409`. |
| `DELETE /snacks/<id>/vote` | Authenticated | Removes the current user's vote; it cannot remove another user's vote. |
| `GET /snacks/summary` | Authenticated | Returns total, stocked, running-low, gone, and snack-of-the-week data. |
| `GET /activity` | Authenticated | Paginated activity history. Members see only their own activity; admins can see all activity. Supports `page` and `per_page` (1–100). |
| `GET /activity/summary` | Admin | All-time activity totals, top five consumed snacks, and top five current community favorites ranked by vote count. |

List responses include `items`, `page`, `per_page`, `total`, and `pages`. Categories are `sweet`, `savoury`, `drink`, and `healthy-ish`; statuses are `stocked`, `running_low`, and `gone`.

Errors use a consistent JSON envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Validation errors return `400`; missing/invalid authentication returns `401`; role failures return `403`; missing resources return `404`; duplicate names/votes and stock conflicts return `409`; unexpected server failures return `500`.

## Security and authorization

- Passwords are hashed with Werkzeug's password-hashing helpers.
- JWTs are required on protected endpoints. The API resolves the user from the token and checks the role on the server.
- Public registration always assigns the `member` role, rejects role fields, and hashes the submitted password. Administrator accounts must be provisioned separately.
- The server rejects administrator consume requests with `403`; hiding the consume control in the admin UI is only a usability measure, not the authorization boundary.
- Member activity queries are filtered by the authenticated user ID on the server. Admin activity analytics are restricted to admins and are calculated from committed activity records.
- Admins can open the separate Analysis module from the dashboard navigation. Favorite rankings use current database vote counts; they are not a historical vote trend.
- Request fields are validated and admin CRUD routes reject unsupported fields to prevent mass assignment.
- Users can only inspect/remove their own vote. Activity records are created from the authenticated identity, not from caller-supplied user IDs.
- Flask/JWT secrets, database URLs, and seed passwords belong only in ignored `.env` files; do not commit real credentials. Environment templates are examples, not production credentials. Replace the sample seed passwords with unique, strong values before running the seed script.
- The frontend stores its session token in `sessionStorage`; this is suitable for the current app but remains accessible to JavaScript running in the page.

## Stock transactions and concurrency

Consumption uses a database conditional update rather than reading a quantity into Python and later writing it:

```sql
UPDATE snack
SET quantity = quantity - :amount
WHERE id = :snack_id
  AND quantity >= :amount
RETURNING id, quantity;
```

PostgreSQL serializes conflicting row updates and rechecks the predicate against the latest row version. If no row is returned, the API reports `409` and does not add an activity. The stock update and activity insert run inside one database transaction; failure of either operation rolls back both. Restocking uses a guarded update in a transaction and records its activity in that same transaction. No Python lock is used as a substitute for database concurrency control.

The vote uniqueness constraint is enforced by PostgreSQL, so concurrent duplicate votes cannot both be committed. API tests use an in-memory SQLite database for fast endpoint coverage; only the PostgreSQL integration test below verifies the required concurrent PostgreSQL behavior.

## Tests

From the project root, activate the virtual environment, then run the backend suite:

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location backend
python -m pytest -q
```

The API tests cover login and invalid tokens, member registration and privilege-field rejection, member/admin authorization (including rejection of admin consumption), snack CRUD and validation, filtering/pagination/summary, consume/restock behavior, non-negative stock, vote uniqueness and user scoping, activity history privacy and pagination, admin activity and vote analytics, and activity rollback when an activity insert fails.

### PostgreSQL concurrency integration test

Use a local or disposable PostgreSQL test database. Set `POSTGRES_TEST_DATABASE_URL` to that database's SQLAlchemy URL in the environment or set `DATABASE_URL` in `backend/.env`. The test creates a uniquely named user/snack, sends ten simultaneous HTTP consume requests against quantity 3, checks the vote uniqueness constraint, verifies 3 successes, 7 HTTP 409 conflicts, final quantity 0, and exactly 3 consume activities, then removes its test records.

Run from `backend` in PowerShell:

```powershell
$env:RUN_POSTGRES_CONCURRENCY = "1"
python -m pytest -q tests\test_postgres_concurrency.py
Remove-Item Env:\RUN_POSTGRES_CONCURRENCY
```

The integration test skips during the normal suite unless `RUN_POSTGRES_CONCURRENCY=1`. Do not count a skipped run as evidence that PostgreSQL concurrency passed.

Frontend checks:

```powershell
Set-Location frontend
npm test
npm run build
```

## Known limitations

- There is no password-reset flow, token-refresh/revocation endpoint, vote-history log, or date-range analytics; favorite rankings use current votes and stock analytics are all-time totals.
- The frontend is configured for local development by default; production hosting, HTTPS, secret management, and deployment configuration must be supplied by the deployer.

video link : GitHub Repository: https://github.com/Arunmurugappan0/snack-overflow

Screen Recording: https://drive.google.com/file/d/1xrGj3Yi1lVEMhIbG4QFsKiKPOiUua2P2/view?usp=sharing
