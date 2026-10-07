# Design decisions

One line per decision, with the reason.

- Python 3.12 for the project (not the system 3.14): every library in the stack ships stable builds for it.
- Repo lives in `FrontDesk/replydesk`, named `replydesk`: matches the project name in the brief.
- Empty folders hold a `.gitkeep` file: git does not track empty folders; each one is deleted once real files exist.
- Push over SSH, not HTTPS: the `gh` token lacked the `workflow` scope needed to push `.github/workflows/`; the SSH key already works.
- One branch and one pull request per phase: `main` always holds finished, reviewed work.
