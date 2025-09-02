#!/usr/bin/env bash
set -euo pipefail

# --- RUN TESTS ---------------------------------------------------
echo "🔹 Running Playwright integration tests..."
unset KEYCLOAK_PORT

# Run tests and capture exit code (0 = success, non-zero = failure)
PLAYWRIGHT_HTML_OPEN=never pnpm run playwright:test --grep @integ ${PLAYWRIGHT_TEST} --reporter=html
TEST_EXIT_CODE=$?

# --- CHECK RESULTS -----------------------------------------------
if [ "$TEST_EXIT_CODE" -ne 0 ]; then
  echo "❌ Some Playwright tests failed. Uploading HTML report to Mattermost..."

  # Ensure report exists
  if [ ! -f "playwright-report/index.html" ]; then
    echo "⚠️ Report file not found at playwright/playwright-report/index.html"
    exit 1
  fi

  # Upload report file
  UPLOAD_RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $MATTERMOST_TOKEN" \
    -F "files=@$(pwd)/playwright/playwright-report/index.html" \
    -F "channel_id=$MATTERMOST_CHANNEL_ID" \
    "$MATTERMOST_URL/api/v4/files")

  # Extract file ID
  FILE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.file_infos[0].id')

  if [ "$FILE_ID" == "null" ] || [ -z "$FILE_ID" ]; then
    echo "❌ Failed to extract file ID from upload response."
    echo "$UPLOAD_RESPONSE"
    exit 1
  fi

  # Post message to Mattermost
  curl -s -X POST -H "Authorization: Bearer $MATTERMOST_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"channel_id\":\"$MATTERMOST_CHANNEL_ID\",\"message\":\"❌ Playwright tests failed. HTML report attached.\",\"file_ids\":[\"$FILE_ID\"]}" \
    "$MATTERMOST_URL/api/v4/posts"

  echo "✅ Report uploaded to Mattermost."

else
  echo "✅ All Playwright tests passed. No upload needed."
fi
