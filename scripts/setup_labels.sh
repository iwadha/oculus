#!/usr/bin/env bash
set -euo pipefail
OWNER=iwadha REPO=oculus
labels=(
  "type:feature:#0E7C86"
  "type:bug:#D73A4A"
  "type:db:#6F42C1"
  "type:api:#1F6FEB"
  "type:web:#0E8A16"
  "type:worker:#A371F7"
  "priority:high:#FBCA04"
  "priority:medium:#C5DEF5"
  "priority:low:#E4E669"
  "status:blocked:#B60205"
  "status:in-progress:#5319E7"
  "status:ready:#0E8A16"
)
for l in "${labels[@]}"; do
  name="${l%%:*}"; rest="${l#*:}"; color="${rest##*:}"; desc="${rest%:*}"
  gh label create "$name" --color "${color#\#}" --description "$desc" -R "$OWNER/$REPO" 2>/dev/null || \
  gh label edit "$name" --color "${color#\#}" --description "$desc" -R "$OWNER/$REPO"
done
echo "Labels ensured."
