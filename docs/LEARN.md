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
