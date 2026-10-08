# ReplyDesk front end

Next.js (App Router) + TypeScript + Tailwind. Every page is a client component that calls the API
(`lib/api.ts`) with the staff login token.

- `npm run dev`: http://localhost:3010 (expects the API on http://localhost:8010)
- `npm run lint`, `npm run typecheck`, `npm run build`
- `npm run e2e`: starts an isolated Docker copy of the whole stack with the fake model, runs the two
  Playwright tests, removes the copy.
