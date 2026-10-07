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
