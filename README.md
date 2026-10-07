# ReplyDesk

An AI support inbox with human approval. It reads customer messages, does the boring part, and leaves the final decision to a person.

> 🚧 Work in progress. Full README with live demo, architecture and results coming at the end of the build.

## How it works (planned)

A customer message comes in. Four small AI agents (built on Lyzr Agent Studio) handle it in order:

1. **Sorter**: category and urgency
2. **Extractor**: customer name, order ID, product, request
3. **Drafter**: a short reply that follows the business's guidelines
4. **Checker**: checks the draft against the guidelines

A support person then approves, edits or rejects the draft. Nothing is sent without a human click.

## Stack

Next.js + TypeScript + Tailwind · FastAPI + SQLAlchemy + Pydantic · PostgreSQL + Alembic · Lyzr Agent Studio · pytest + Playwright · Docker Compose · GitHub Actions

## License

MIT
