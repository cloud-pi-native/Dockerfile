#!/usr/bin/env bash
# Executed as the image's default runner user, before publishing version tags.
set -euo pipefail

"${1:-/home/runner/bin/Runner.Listener}" --version
node --version
pnpm --version

browsers_path="${2:-/opt/ms-playwright}"
for browser in chrome firefox; do
  executable="$(find "$browsers_path" -type f -name "$browser" -executable -print -quit)"
  if [[ -z "$executable" ]]; then
    echo "Missing executable Playwright browser: $browser" >&2
    exit 1
  fi
  "$executable" --version
done
