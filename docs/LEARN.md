# What I learned building ReplyDesk

One section per phase: what was built, why it is designed that way, and what the alternative would have been.

## Phase 0: Machine setup and repository

**What we built.** An empty but organised project: the folder layout for the back end, front end, agents, evaluation and docs; an MIT license; a `.gitignore`; a `.env.example`; and a public GitHub repo at https://github.com/Prathameshh-Patil/replydesk.

**Why it is designed this way.**
- The folder layout is decided up front so every later file has an obvious home, and each folder has one job (`agents/` holds agent instructions, `backend/app/agents/` holds the code that calls them, `eval/` measures quality).
- `.gitignore` lists `.env` before any secret exists, so a real Lyzr key can never be committed by accident. `.env.example` documents the variables without values.
- Git tracks files, not folders, so empty folders hold a `.gitkeep` placeholder until real files arrive.
- We push over SSH (a key on this laptop) rather than HTTPS with the `gh` login token. The token lacked the `workflow` permission that GitHub requires to touch `.github/workflows/`; an SSH key has full push rights to my own repos.
- Python 3.12 instead of the system 3.14: newest is not always best; libraries need time to ship builds for a new Python.

**Alternatives.** I could have started with a framework generator (`create-next-app`, a FastAPI template) and let it decide the layout. That is faster but gives files I didn't choose and can't explain. Or one repo per service (front end and back end separate): cleaner for big teams, but harder to run and explain for a solo project. A single repo ("monorepo") keeps it one clone, one README, one CI.

**Git commands used.** `git init` (make a repo), `git add` (stage files for the next snapshot), `git commit` (save the snapshot), `git remote` (where GitHub lives), `git push` (upload), `git switch -c` (create and move to a new branch), `gh pr create` / `gh pr merge` (open and merge a pull request).

**Self-check.**
1. *Why ignore `.env` before any secret exists?* A committed secret stays in git history even after deletion, and bots scan public repos for keys within minutes. Ignoring it first makes the mistake impossible.
2. *Why `.gitkeep`?* Git tracks files, not folders; an empty folder needs a placeholder file to be pushed.
3. *`add` vs `commit` vs `push`?* `add` stages changes, `commit` saves a snapshot locally, `push` uploads commits to GitHub.
4. *Why did the HTTPS push fail and SSH work?* The `gh` token lacked the `workflow` scope GitHub requires for `.github/workflows/`; the SSH key has full push rights to my repos.
5. *Why a branch and PR per phase?* `main` only holds finished, reviewed work; each PR is where CI runs and records what changed.

## Phase 1: Brief, pitch and sample data

**What we built.** `docs/BRIEF.md` (the store, its users, the problem, what's out of scope, labelling rules), `agents/guidelines.md` (13 reply rules for Pixel & Plug, a fictional electronics store), `eval/emails.csv` (60 labelled customer messages) and `docs/PITCH.md` (30-second, 2-minute and architecture versions).

**Why it is designed this way.**
- The test data exists before any code. It's the definition of "correct", so later I can measure the agents instead of eyeballing them. Writing it first also stops me unconsciously choosing examples the agents happen to get right.
- Written labelling rules ("label by the action needed, not the mood"; "two problems: label the one involving money or safety") make the labels consistent. The same rules go into the Sorter's instructions, so the agent and the test agree on what "correct" means.
- The hard cases are deliberate: angry, Hinglish, missing order ID, two issues, vague, spam and three prompt-injection attempts. Easy messages don't reveal failures.
- Every expected detail was checked by a script to appear literally in the message, so "the extractor invented a detail" can later be measured exactly.
- The guidelines are short, numbered rules. The Checker can cite a rule number, and a human can see which rule a draft broke.

**Alternatives.** Use a public dataset of support tickets: bigger, but not about one business with one policy, so the guidelines couldn't be checked against it. Generate thousands of messages with an LLM: cheap, but labels made by an LLM to test an LLM are circular. Sixty hand-checked messages are small but trustworthy.

**Self-check.**
1. *Why write the labelled test set before building the agents?* It defines "correct" up front and lets me measure changes with numbers instead of impressions.
2. *Why is an angry message about a late order `order_status`, not `complaint`?* Categories are chosen by the action needed; mood affects urgency, not category.
3. *What does an empty `exp_order_id` cell mean, and why does it matter?* The correct answer is `null`; if the Extractor returns a value there, it invented one, which is the failure we most want to catch.
4. *Why include prompt-injection messages?* Customer text reaches the AI, so a customer can try to give it orders; I need proof the system ignores them and that a human still sees everything.
5. *Why is the business fictional?* A demo should not impersonate a real company's support desk, and a fictional store lets me write its policy myself.

## Phase 2: Back-end skeleton, Docker and CI

**What we built.** A FastAPI app with one route, `GET /health`; settings read from environment variables; a Dockerfile for the API; a `docker-compose.yml` that starts the API and PostgreSQL together; one pytest test; ruff for linting and formatting; and a GitHub Actions workflow that lints and tests every pull request.

**How to run it.** `cp .env.example .env`, then `docker compose up --build`. Open http://localhost:8010/health and http://localhost:8010/docs. Tests: `cd backend && python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pytest`.

**Why it is designed this way.**
- **Settings in one class** (`app/core/settings.py`): every config value has one home, a type and a default. Change the environment, not the code, to point at a different database.
- **`/health`** lets Docker, CI and the hosting platform ask "are you alive?" without logging in.
- **Docker** packages Python 3.12 and exact library versions, so my laptop, CI and the server run the same thing. The Dockerfile installs libraries *before* copying code, so a code change rebuilds in seconds (Docker reuses the cached library layer).
- **Compose** starts the database first and waits for its health check before starting the API (`depends_on: condition: service_healthy`). Inside Compose the API reaches the database by its service name `db`, not `localhost`.
- **Ports 8010 and 5442**: my machine already runs other projects on 8000 and 5432. The first time, `/health` answered from *another app* on port 8000; I caught it because the OpenAPI title said "Slotwise". Lesson: check *what* answered, not just *that* something answered.
- **Exact version pins** (`fastapi==0.142.3`): a fresh install next month gets the same code, so CI failures mean my code changed, not a library.
- **CI** gives every PR a green or red mark before merge, so `main` never holds broken code.

**Alternatives.** Run Postgres installed directly on the Mac: no Docker needed, but the version and setup differ per machine. Poetry or uv instead of `requirements.txt`: better lock files, but one more tool to explain; plain pip is enough here. Flask or Django instead of FastAPI: Flask lacks built-in validation and automatic docs, and Django brings a lot I won't use.

**Self-check.**
1. *Image vs container?* An image is the frozen package (code + Python + libraries); a container is a running instance of it.
2. *Why does the API use `db` as the database host inside Compose but `localhost` from my laptop?* Compose puts containers on a private network where each service is reachable by its name; from the laptop you go through the published port on localhost.
3. *Why copy `requirements.txt` before the code in the Dockerfile?* Docker caches each step; libraries change rarely, so code-only changes skip the slow install.
4. *What does CI run, and when?* On every PR and every push to `main`: `ruff check`, `ruff format --check`, and `pytest`.
5. *Why read settings from environment variables?* The same code runs locally, in CI and in production with different values, and secrets stay out of the code.

## Phase 3: Tickets and login

**What we built.** Three database tables (`users`, `tickets`, `agent_runs`) defined as SQLAlchemy models and created by the first Alembic migration; staff login with bcrypt-hashed passwords and JWT tokens; a command to create staff users; and ticket endpoints: create (public), CSV import, list with filters (newest first) and detail with agent runs. 23 tests run against a real PostgreSQL test database, locally and in CI.

**How to run it.** `docker compose up --build` (the API runs migrations on start). Create a login: `docker compose exec api python -m app.create_user "Demo Staff" demo@replydesk.dev 'demo-pass-123'`. Open http://localhost:8010/docs → **Authorize** (email in "username") → `POST /tickets/import` with `eval/emails.csv` → `GET /tickets`. Tests: `cd backend && .venv/bin/pytest`.

**Why it is designed this way.**
- **Models are the single source of truth.** Alembic's autogenerate compares them with the database and writes the migration; `alembic check` in CI fails if a model changes without a migration. I still read every generated migration: the first one had the status check constraint written twice and would have failed.
- **Status is a fixed list** (`new`, `processing`, …) enforced twice: by a Python enum in code and a CHECK constraint in the database. Stored as text rather than a Postgres ENUM type, because adding a value to text plus a constraint is a simple migration.
- **`agent_runs` is its own table**, not a JSON list inside the ticket: one row per call makes it easy to count failures, average durations per agent, and show a timeline.
- **`POST /tickets` is public; everything else needs a login.** Customers don't have accounts. Staff accounts come from a command, not a sign-up page.
- **Same error for "unknown email" and "wrong password"**, so an attacker can't use login to discover which emails have accounts.
- **JWT instead of server sessions**: the API stores nothing per login; the signed token proves who you are. Downside: a token can't be revoked before it expires (8 hours), which is acceptable for a demo.
- **CSV import saves the good rows and reports the bad ones** with row numbers, in one transaction. A typo in row 37 shouldn't block 59 good messages, and the user learns exactly what to fix.
- **Newest first needs a tie-breaker**: rows imported in one transaction get the same `created_at` (Postgres's `now()` is the transaction's start time), so we also sort by `id`.
- **Tests use a separate database that is always forced**, never taken from `DATABASE_URL`, because tests empty every table. I verified it: after running tests with `DATABASE_URL` pointing at the dev database, the dev database still had its 60 tickets.

**Alternatives.** Async SQLAlchemy: handles more simultaneous requests, but harder to read and debug; FastAPI runs sync routes in a thread pool, which is plenty here. SQLite for tests: faster, but it handles JSON, constraints and timestamps differently from Postgres, so tests could pass and production fail. Server-side sessions or a hosted auth service instead of JWT: revocable, but more moving parts.

**Self-check.**
1. *Why a migration instead of `create_all()` on startup?* `create_all` only creates missing tables; it can't change an existing one. Migrations are versioned steps that bring any database (mine, CI's, production) to the same structure, and they're reviewed in git.
2. *What happens to a ticket's agent runs if the ticket is deleted?* They are deleted too (`ON DELETE CASCADE`), so the audit trail never points at a missing ticket.
3. *What is inside our JWT, and can a user change it?* The user ID (`sub`) and an expiry (`exp`). They can read it but not change it: any change breaks the signature, which only the server's secret can produce.
4. *Why bcrypt and not SHA-256 for passwords?* bcrypt is deliberately slow and salted, so cracking a leaked hash takes years instead of seconds; SHA-256 is built to be fast.
5. *A CSV has 60 rows and row 12 has a bad email. What happens?* 59 tickets are created and the response lists `{"row": 12, "error": "Invalid: customer_email"}`.
