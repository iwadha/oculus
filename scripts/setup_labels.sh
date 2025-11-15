#!/usr/bin/env bash
set -euo pipefail
OWNER=iwadha REPO=oculus
mk() { gh label create "$1" -R "$OWNER/$REPO" --color "$2" --description "$3" 2>/dev/null || gh label edit "$1" -R "$OWNER/$REPO" --color "$2" --description "$3"; }
mk "type:worker" A371F7 "worker code & infra"
mk "type:api"    1F6FEB "backend/API"
mk "type:web"    0E8A16 "next.js UI"
mk "type:feature" 0E7C86 "feature request"
mk "type:bug"    D73A4A "bug"
mk "type:db"     6F42C1 "database/migrations"
mk "priority:high" FBCA04 "must-have"
mk "priority:medium" C5DEF5 "nice-to-have"
mk "priority:low" E4E669 "later"
mk "status:ready" 0E8A16 "ready to start"
mk "status:in-progress" 5319E7 "actively building"
mk "status:blocked" B60205 "blocked on dependency"
echo "Labels ensured."
