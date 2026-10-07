# Design decisions

One line per decision, with the reason.

- Python 3.12 for the project (not the system 3.14): every library in the stack ships stable builds for it.
- Repo lives in `FrontDesk/replydesk`, named `replydesk`: matches the project name in the brief.
- Empty folders hold a `.gitkeep` file: git does not track empty folders; each one is deleted once real files exist.
- Push over SSH, not HTTPS: the `gh` token lacked the `workflow` scope needed to push `.github/workflows/`; the SSH key already works.
- One branch and one pull request per phase: `main` always holds finished, reviewed work.
- Business: Pixel & Plug, a fictional Indian online electronics store: every category (billing, order, technical, refund, complaint) fits naturally, and a fictional name avoids impersonating a real company.
- Categories are labelled by the action the customer needs, not their mood: makes labels consistent; mood goes into urgency.
- The Extractor reads only the subject and body; a name counts only if the customer writes it: so "invented a detail" can be measured exactly.
- Test set written before any agent code: defines "correct" up front, so improvements are measured, not guessed.
- Settings via `pydantic-settings` (Pydantic's official add-on): typed config from env vars in one class.
- Plain `pip` + pinned `requirements.txt` / `requirements-dev.txt`, not Poetry/uv: fewer tools to learn; pins keep builds repeatable.
- Local host ports 8010 (API) and 5442 (Postgres), configurable in `.env`: 8000 and 5432 are used by other projects on this machine.
- `httpx2` instead of `httpx` for tests: Starlette's TestClient deprecated `httpx`.
- Postgres 17 in Docker for local development: same database as production, no local install.
- Sync SQLAlchemy (not async): simpler to read and debug; FastAPI runs sync routes in a thread pool.
- Integer IDs: simple and readable in URLs; nothing here needs unguessable IDs because every read needs a login.
- Ticket status stored as text + CHECK constraint (not a Postgres ENUM type): adding a status later is an easy migration.
- `agent_runs` is a separate table: one row per agent call makes counts, timings and timelines simple queries.
- Login via the OAuth2 password form (`username` = email): makes Swagger's "Authorize" button work with no extra code.
- No public sign-up; staff accounts are created with `python -m app.create_user`: strangers must not be able to become staff.
- `bcrypt` and `PyJWT` directly (not passlib): passlib is unmaintained; these two are small and widely used.
- Tests run against a real Postgres test database, always forced in `conftest.py`: same behaviour as production, and tests can never wipe the dev database.
- CSV import saves valid rows and reports invalid ones by row number: one bad row shouldn't block the rest.
- The API runs `alembic upgrade head` on start-up: the database is always migrated before the app serves requests.
