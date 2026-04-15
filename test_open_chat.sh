#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MAXKB_BASE_URL:-http://localhost:8080}"
API_KEY="${MAXKB_API_KEY:-}"
APPLICATION_ID="${MAXKB_APPLICATION_ID:-}"
CHAT_ID="${MAXKB_CHAT_ID:-}"
QUESTION="${MAXKB_QUESTION:-上海南文档怎么上传？}"

if [[ -z "${API_KEY}" ]]; then
  echo "Please set MAXKB_API_KEY"
  exit 1
fi

if [[ -z "${APPLICATION_ID}" ]]; then
  echo "Please set MAXKB_APPLICATION_ID"
  exit 1
fi

payload=$(cat <<EOF
{
  "application_id": "${APPLICATION_ID}",
  "chat_id": "${CHAT_ID}",
  "stream": false,
  "re_chat": false,
  "messages": [
    {
      "role": "user",
      "content": "${QUESTION}"
    }
  ]
}
EOF
)

curl -sS -X POST "${BASE_URL}/api/open/v1/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "${payload}" | python -m json.tool
