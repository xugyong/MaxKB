#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BOOTSTRAP="python3"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
DJANGO_MANAGE="${ROOT_DIR}/apps/manage.py"
UI_DIR="${ROOT_DIR}/ui"
BACKEND_PORT="8080"
FRONTEND_PORT="3000"
CHAT_FRONTEND_PORT="3001"
HOST="0.0.0.0"
DB_CONTAINER="maxkb-postgres"
REDIS_CONTAINER="maxkb-redis"
DB_SERVICE="postgres"
REDIS_SERVICE="redis"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
PROJECT_NAME="maxkb"

ensure_venv() {
  if [ ! -d "${VENV_DIR}" ]; then
    "${PYTHON_BOOTSTRAP}" -m venv "${VENV_DIR}"
  fi
  # shellcheck disable=SC1091
  . "${VENV_DIR}/bin/activate"
}

compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}" "$@"
  else
    docker-compose -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}" "$@"
  fi
}

kill_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "${pids}" ]; then
      echo "Killing process(es) on port ${port}: ${pids}"
      kill -9 ${pids} 2>/dev/null || true
      sleep 1
    fi
  fi
}

ensure_db() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required for postgres and redis." >&2
    exit 1
  fi
  if ! docker ps --format '{{.Names}}' | grep -qx "${DB_CONTAINER}" || ! docker ps --format '{{.Names}}' | grep -qx "${REDIS_CONTAINER}"; then
    echo "Starting postgres and redis..."
    compose up -d "${DB_SERVICE}" "${REDIS_SERVICE}"
  fi
}

clear_cache() {
  find "${ROOT_DIR}" -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -prune -exec rm -rf {} + 2>/dev/null || true
  find "${ROOT_DIR}" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
}

start_backend() {
  if [ ! -f "${DJANGO_MANAGE}" ]; then
    echo "manage.py not found: ${DJANGO_MANAGE}" >&2
    exit 1
  fi
  kill_port "${BACKEND_PORT}"
  echo "Starting backend on ${BACKEND_PORT}..."
  "${PYTHON_BIN}" "${DJANGO_MANAGE}" runserver "${HOST}:${BACKEND_PORT}" &
  BACKEND_PID=$!
}

start_frontend() {
  if [ ! -d "${UI_DIR}" ]; then
    echo "ui directory not found: ${UI_DIR}" >&2
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found" >&2
    exit 1
  fi
  kill_port "${FRONTEND_PORT}"
  echo "Starting frontend on ${FRONTEND_PORT}..."
  (cd "${UI_DIR}" && npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}" --strictPort) &
  FRONTEND_PID=$!
}

start_chat_frontend() {
  if [ ! -d "${UI_DIR}" ]; then
    echo "ui directory not found: ${UI_DIR}" >&2
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found" >&2
    exit 1
  fi
  kill_port "${CHAT_FRONTEND_PORT}"
  echo "Starting chat frontend on ${CHAT_FRONTEND_PORT}..."
  (cd "${UI_DIR}" && npm run chat -- --host 0.0.0.0 --port "${CHAT_FRONTEND_PORT}" --strictPort) &
  CHAT_FRONTEND_PID=$!
}

wait_until_ready() {
  local i=0
  until curl -sS "http://127.0.0.1:${BACKEND_PORT}/" >/dev/null 2>&1; do
    if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
      echo "Backend exited." >&2
      exit 1
    fi
    i=$((i + 1))
    if [ "${i}" -ge 120 ]; then
      echo "Backend did not become ready in time." >&2
      exit 1
    fi
    sleep 1
  done
}

cleanup() {
  kill "${BACKEND_PID:-}" 2>/dev/null || true
  kill "${FRONTEND_PID:-}" 2>/dev/null || true
  kill "${CHAT_FRONTEND_PID:-}" 2>/dev/null || true
}

main() {
  ensure_venv
  ensure_db
  clear_cache
  trap cleanup EXIT
  start_backend
  wait_until_ready
  start_frontend
  start_chat_frontend
  wait
}

main "$@"
