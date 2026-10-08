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

## Phase 4: One agent, end to end (the Sorter)

**What we built.** The Sorter agent (`agents/sorter.md`), the only file that talks to a language model (`backend/app/agents/client.py`), the Pydantic schema for the Sorter's answer, the parse → validate → retry-once → `needs_manual` logic (`runner.py`), a fake client for tests, and `pipeline.py` running the Sorter in a background task. Every call is saved in `agent_runs`.

**How to run it.** Put a Gemini key in `.env` (`LLM_API_KEY=`), then `docker compose up --build`. In http://localhost:8010/docs: `POST /tickets` with a message, then (after Authorize) `GET /tickets/{id}`: within ~3 seconds it has a `category`, `urgency` and one `agent_runs` entry. Tests (no network, no cost): `cd backend && .venv/bin/pytest`.

**The path from API request to database row** (what I should be able to explain):
1. `POST /tickets` (`routers/tickets.py`) validates the body with `TicketCreate`, saves the ticket with status `new`, schedules `run_pipeline(ticket.id)` as a background task, and returns `201` at once.
2. After the response is sent, `run_pipeline` (`pipeline.py`) opens its own database session, sets the status to `processing`, and builds the message the agent sees: only `Subject:` and `Message:`, never the customer's email.
3. `run_agent` (`agents/runner.py`) calls `call_agent("sorter", message)`.
4. `call_agent` (`agents/client.py`) loads the Instructions block from `agents/sorter.md` as the system prompt and POSTs to the OpenAI-compatible `/chat/completions` endpoint (Gemini) with temperature 0 and JSON mode. It returns the reply text.
5. `run_agent` validates that text against `SorterOutput` (category and urgency must be from the fixed lists, reason must exist), writes an `agent_runs` row (input, output, ok, error, duration) and commits it.
6. If validation or the call failed, it tries exactly once more. If that also fails, it returns `None` and the pipeline sets the ticket to `needs_manual`.
7. On success the pipeline copies `category` and `urgency` onto the ticket and sets `ready_for_review`. Any unexpected crash also ends in `needs_manual`, never stuck in `processing`.

**Measured.** One real Sorter call: 2.3–3.2 s. A ticket submitted through the API was sorted 2.8 s after the POST (`billing` / `high` for a double charge). The 10 hardest labelled messages (a first look, not the official eval): category correct on 9 of 9, urgency on 8 of 9; E32 ("It stopped working") got `medium` where we labelled `low`; E49 hit the daily quota before it ran.

**Why it is designed this way.**
- **One client file.** The rest of the code knows only `call_agent(agent_name, message) -> str`. This paid off immediately: the provider changed twice this phase (Lyzr → Ollama → Gemini) and the pipeline, runner, schema and all tests didn't change.
- **The .md file is the agent.** Instructions are read from `agents/sorter.md` on every call, so editing the file changes the agent and the change shows up as a git diff, which is how Phase 8 improvements will be recorded.
- **Code decides, the model only reads and writes.** The model returns JSON; Pydantic decides whether it's acceptable. A wrong value (e.g. `"shipping"`) is treated exactly like broken JSON.
- **Two kinds of retry, in two places.** A bad *answer* is retried once by `runner.py`, then `needs_manual`. A *rate limit* (HTTP 429) isn't the agent's fault: `client.py` waits as long as the provider asks (max 60 s, at most twice). Without that split, tickets would land in the manual queue just because we were sending requests too fast.
- **Every attempt is a row in `agent_runs`**, including failures, committed immediately, so the audit trail survives a later crash and shows exactly what the model said.
- **Examples in the prompt are not from the test set.** Otherwise the eval would be partly testing memorisation.
- **The fake client** has the same signature as the real one, so tests can script "bad JSON, then good JSON" and check the retry exactly, with no network and no cost.

**What went wrong, and what I learned.**
- Lyzr was dropped in favour of a provider-agnostic client. A local open model (Ollama, `gpt-oss:20b`) was tried: 13 GB download over an unstable connection, and tight on a 16 GB Mac, so it was abandoned for a hosted API.
- `gemini-3.8-flash` and `gemini-3.7-flash` (the newest) never answered within 40 s on the free tier; `gemini-3.5-flash` answered in ~3 s. Newest isn't always usable.
- The free tier allows **5 requests per minute and 20 per day** per model (read from Gemini's own 429 error: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, limit 20). A ticket will need 4 calls once all agents exist, so this is a real constraint for the eval and the live demo.
- A Docker build failed with a pip hash mismatch while the network was saturated: a corrupted download, caught by pip's safety check. Retrying later fixed it; bypassing the check would have been wrong.

**Alternatives.** Let the provider validate the schema (structured outputs): less code, but ties us to one provider's feature, and we still need our own check. One big agent: fewer calls, but when it fails you can't tell which part failed. A task queue (Celery + Redis) instead of background tasks: survives restarts and can limit concurrency, but adds two moving parts; deliberately out of scope.

**Self-check.**
1. *What does `POST /tickets` return, and when do the agents run?* It returns the saved ticket (status `new`) immediately; the Sorter runs afterwards in a background task.
2. *The model returns `{"category": "shipping", ...}`. What happens?* Pydantic rejects it (not in the allowed list), an `agent_runs` row records the error, the call is retried once, and if it fails again the ticket goes to `needs_manual`.
3. *What's the difference between the retry in `runner.py` and the waiting in `client.py`?* `runner.py` retries a bad or missing answer once; `client.py` waits and resends only when the provider says "too many requests" (429), because that isn't a failure of the agent.
4. *Why does nothing outside `client.py` know which provider we use?* So the provider can change without touching the pipeline or tests. It changed twice this phase with no other code changes.
5. *Why don't the tests call Gemini?* They'd be slow, cost quota (only 20 calls/day free), and give different answers; the fake client makes them fast, free and repeatable.

## Phase 5: The other three agents and the pipeline

**What we built.** Three more agents: the Extractor (`agents/extractor.md`: name, order ID, product, request; never invents), the Drafter (`agents/drafter.md`: a short reply following the guidelines) and the Checker (`agents/checker.md`: `ok` plus a list of problems). A Pydantic schema for each. `pipeline.py` now runs sort → extract → draft → check, saving each result before the next step. `POST /tickets/{id}/rerun` continues from the step that failed. 60 tests.

**How to run it.** `docker compose up --build`, submit `POST /tickets`, then `GET /tickets/{id}`: status `ready_for_review`, with `category`, `urgency`, `extracted`, `draft_reply`, `checker_ok`, `checker_problems` and four `agent_runs` with timings. Without using any Gemini quota: `AGENT_CLIENT=fake docker compose up -d` (canned answers). Tests: `cd backend && .venv/bin/pytest`.

**Why it is designed this way.**
- **The pipeline is a list of four plain functions**, each paired with the ticket field that proves it's done (`category`, `extracted`, `draft_reply`, `checker_ok`). The loop skips steps whose field is already filled. That one rule gives "resume from the failed step" for free.
- **Commit after every step.** A failure at step 3 keeps steps 1 and 2 in the database, so a rerun costs only the remaining calls (which matters with 20 free calls a day).
- **The Checker never blocks.** A draft with problems still goes to `ready_for_review`, with the problems shown; the human decides. Only a *broken* agent (bad output twice, or the API failing) sends a ticket to `needs_manual`.
- **Rules the code can check, the code checks.** The Checker's `ok` must match whether `problems` is empty (a Pydantic validator). An extracted order ID must literally appear in the message, or the code drops it and notes it on the agent run; the raw output is kept, so the eval can still count invention attempts.
- **One guidelines file, two agents.** `{{GUIDELINES}}` in the Drafter and Checker prompts is filled from `agents/guidelines.md`, so the writer and the reviewer can never follow different rules.
- **Examples are now actually sent.** Until this phase the loader sent only the Instructions block, so the Sorter's examples were documentation, not prompt. Now the Examples section is appended ("few-shot" prompting). None of them come from the test set.
- **Each agent sees only what it needs.** Sorter and Extractor: subject and body. Drafter: the message plus the Sorter and Extractor results. Checker: the message plus the draft. None of them see the customer's email address.

**Alternatives.** One agent that does all four jobs: one call instead of four (cheaper on our 20/day quota), but one failure gives no clue which part went wrong, and the Checker would be checking its own work. Running Extractor and Sorter in parallel: faster, but more complex code and it would burst the 5-per-minute limit. A workflow engine (Temporal, Airflow): durable and resumable, but heavy for four sequential steps; a loop over a list does the job.

**Verified.** All 60 tests pass, including a failure at each of the four steps (earlier results kept, later steps never called) and a rerun that resumes from each failed step. Through the Docker API (fake client), a new ticket reached `ready_for_review` with a draft, a checker result and four agent runs with timings. *Real-model run: pending until the Gemini daily quota resets.*

**Self-check.**
1. *The Drafter fails twice. What does the ticket look like, and what does a rerun do?* Status `needs_manual`; `category`, `urgency` and `extracted` are saved; `draft_reply` and `checker_ok` are empty. A rerun skips sort and extract and starts at the Drafter.
2. *The Checker says `ok: false`. Does the ticket go to `needs_manual`?* No. It goes to `ready_for_review` with the problems listed; the Checker informs the human, it doesn't decide.
3. *How does the code stop the Extractor inventing an order ID?* The prompt forbids it, and the pipeline also checks the ID appears in the message; if not, it's set to null and the agent run is annotated, with the raw output kept for the eval.
4. *Why do the Drafter and Checker share `guidelines.md` instead of each having their own rules?* So the writer and the reviewer can never disagree about the rules; change one file and both follow.
5. *Why four agents instead of one?* When something goes wrong, the `agent_runs` timeline shows exactly which step failed, each prompt stays short and focused, and the Checker reviews someone else's work rather than its own.

## Phase 6: Human review

**What we built.** `POST /tickets/{id}/approve` (send the draft as is, or an edited reply), `POST /tickets/{id}/reject`, the `edited` column (our second migration), and `GET /stats`: counts by status and category, share of drafts approved without edits, Checker pass rate, and average time per agent step. 73 tests.

**How to run it.** `docker compose up --build`, then in http://localhost:8010/docs (after Authorize): pick a `ready_for_review` ticket, `POST /tickets/{id}/approve` with no body (unedited) or `{"final_reply": "..."}` (edited), or `/reject`. Then `GET /stats`.

**Why it is designed this way.**
- **"Edited" is decided once, at approval, and stored.** The draft and the final reply are both kept, so I can later compare them; the boolean makes the headline number ("share approved without edits") a simple count. Whitespace at the ends doesn't count as an edit.
- **Only tickets waiting for review can be decided** (`ready_for_review` or `needs_manual`); anything else gets 409 Conflict. Approving twice, or approving something the agents are still working on, is refused rather than silently overwriting.
- **A `needs_manual` ticket can still be answered**: the human writes the whole reply. That's the point of the manual queue.
- **Reject sends nothing** and keeps the draft for the record. A rerun clears the old review and gets a fresh draft.
- **Who and when** (`reviewed_by`, `reviewed_at`) are saved on every decision: an audit trail for humans, like `agent_runs` is for agents.
- **Stats leave failed agent calls out of the averages**: a 60-second timeout would make a 2-second step look like a 30-second one.

**Alternatives.** Store a full edit history (every version of the reply): richer, but more tables for a number I don't need yet. Compute "edited" on the fly in `/stats` by comparing texts: no extra column, but the rule would live in a SQL query instead of one obvious line of Python. A separate `reviews` table: needed if a ticket could be reviewed several times by different people; overkill here.

**Verified.** 73 tests pass. Through the Docker API: approve unedited → `edited: false`; approve with a new reply → `edited: true`; reject → `rejected`; approving again → 409; `/stats` → `share_approved_without_edits: 0.5` (local test data, not a result).

**Self-check.**
1. *How is "approved without edits" measured?* At approval the final reply is compared with the draft (ignoring leading and trailing whitespace); the result is stored in `edited`. The share is unedited approvals divided by all approvals that had a draft.
2. *Why a migration for one new column?* The table already exists in every database (mine, CI's, later production); a migration is the reviewed, repeatable way to change it. `create_all` can't add a column to an existing table.
3. *What happens if two staff approve the same ticket?* The first succeeds; the second gets 409 because the ticket is no longer waiting for review.
4. *Can a `needs_manual` ticket be approved?* Yes, with a reply the human writes; without one there's nothing to send, so it's refused (422).
5. *Why are failed agent runs excluded from "average time per step"?* Timeouts and errors would distort how long a working step takes; failures are counted separately in `agent_runs`.

## Phase 7: Front end

**What we built.** A Next.js front end (`frontend/`): staff login; the inbox (tabs for To review / Needs manual / All / Approved / Rejected, filters for category and urgency, badges, refreshes every 5 s); the ticket page (customer message on the left; extracted details, editable draft, checker problems and Approve / Reject / Rerun on the right; a timeline of the four agent steps with timings, expandable to each input and output); a stats page (four numbers, one bar chart, step timings); and a public "New message" form. It runs in Docker Compose next to the API and database. Two Playwright tests drive a real browser through the whole stack.

**How to run it.** `docker compose up --build`, then open http://localhost:3010 and log in (local demo login: `demo@replydesk.dev` / `demo-pass-123`, created with `python -m app.create_user`). Write to the store at http://localhost:3010/new. Browser tests: `cd frontend && npm run e2e`.

**Why it is designed this way.**
- **Every page is a client component calling our API.** The browser holds the login token and calls FastAPI directly; Next.js only serves the pages. One backend, one source of truth; the front end has no database access.
- **`page.tsx` files are thin wrappers** that put one client component inside `<Suspense>`. This Next.js version (16, with Cache Components) requires that for components reading the URL (`useSearchParams`, `useParams`), or the build fails.
- **Login state uses `useSyncExternalStore`**, React's tool for reading an outside store (here `localStorage`), instead of copying it into state in an effect. Clearing the token on a 401 makes every guarded page redirect to login by itself.
- **The draft box keeps only the reviewer's edits as state** (`null` = untouched). What's shown is `edits ?? draft`. The button says "Approve with edits" as soon as the text differs, matching what the API will record.
- **Polling, not WebSockets.** The ticket page checks every 1.5 s while the agents work, then stops; the inbox refreshes every 5 s. Simple, and enough for a support inbox.
- **Filters live in the URL** (`/?status=needs_manual&urgency=high`), so a view can be bookmarked or shared.
- **The chart has one job (how many tickets per category)**: horizontal bars in one colour, value labels, a hover/focus readout in the header (a floating tooltip covered neighbouring bars), and a "Show table" view so colour is never the only way to read it.
- **Browser tests run against the real Docker stack** in an isolated copy (own ports and database, fake model): they test the images we'd deploy, cost nothing, and never touch the dev data.
- **CORS** is set on the API to allow exactly the front end's address; any other site's page is refused.

**Alternatives.** Server components fetching data on the server: faster first paint, but the token would need to be in a cookie and the code splits across server and browser; harder to explain. A UI kit (shadcn, MUI): nicer components, more code I didn't write. A chart library (Recharts): unnecessary for one bar chart; plain HTML bars are accessible and dependency-free. Storing the token in an httpOnly cookie: safer against XSS (scripts can't read it), but the API would need cookie auth and CSRF protection; noted as a next step.

**Verified.** Lint, typecheck and production build pass. Both Playwright tests pass against the Docker stack: (1) log in and approve a drafted reply, then see "Approved without edits"; (2) submit a message as a customer, log in, and see it reach "ready for review" with all four steps in the timeline. I also took screenshots of every page and fixed what they showed (the chart tooltip covered other bars).

**Self-check.**
1. *Why must `useSearchParams` sit inside `<Suspense>` here?* With Cache Components, Next.js prerenders a static shell; URL data isn't known at build time, so the component that reads it must be in a Suspense boundary that can render a fallback. Without it the build fails.
2. *What is CORS, and why did the API need it?* Browsers block a page from one origin (localhost:3010) calling another (localhost:8010) unless the API allows it; we allow only the front end's origin.
3. *Where is the login token stored, and what's the trade-off?* In `localStorage`: simple, but any script on the page could read it. An httpOnly cookie is safer but needs cookie auth and CSRF protection on the API.
4. *How does the ticket page know when the agents are done?* It polls `GET /tickets/{id}` every 1.5 s while the status is `new` or `processing`, and stops when it changes.
5. *Why do the browser tests use Docker and the fake model?* They test the same images we'd deploy, run identically on my laptop and in CI, cost no API quota, and give the same answers every time.
