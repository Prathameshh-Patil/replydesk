#!/bin/sh
# Start an isolated copy of the whole stack (own ports, own database, fake model), create a test
# login, run the browser tests, then remove the copy. Used locally (npm run e2e) and in CI.
set -e
cd "$(dirname "$0")/../.."

export COMPOSE_PROJECT_NAME=replydesk-e2e
export API_PORT=8020 DB_PORT=5452 WEB_PORT=3020 AGENT_CLIENT=fake

docker compose up -d --build --wait
docker compose exec -T api python -m app.create_user "E2E Staff" e2e@replydesk.dev e2e-password-123 || true

set +e
(cd frontend && E2E_BASE_URL=http://localhost:3020 E2E_API_URL=http://localhost:8020 npx playwright test "$@")
status=$?
[ -z "$KEEP_STACK" ] && docker compose down -v
exit $status
