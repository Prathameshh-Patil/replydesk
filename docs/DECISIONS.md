# Design decisions

One line per decision, with the reason.

- Python 3.12 for the project (not the system 3.14): every library in the stack ships stable builds for it.
- Repo lives in `FrontDesk/replydesk`, named `replydesk`: matches the project name in the brief.
- Empty folders hold a `.gitkeep` file: git does not track empty folders; each one is deleted once real files exist.
