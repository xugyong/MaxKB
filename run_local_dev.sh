#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DJANGO_MANAGE="${DJANGO_MANAGE:-${ROOT_DIR}/apps/manage.py}"
PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

# Local defaults for development/debugging.
export MAXKB_DB_HOST="${MAXKB_DB_HOST:-127.0.0.1}"
export MAXKB_DB_PORT="${MAXKB_DB_PORT:-5432}"
export MAXKB_DB_NAME="${MAXKB_DB_NAME:-maxkb}"
export MAXKB_DB_USER="${MAXKB_DB_USER:-postgres}"
export MAXKB_DB_PASSWORD="${MAXKB_DB_PASSWORD:-postgres}"
export MAXKB_REDIS_HOST="${MAXKB_REDIS_HOST:-127.0.0.1}"
export MAXKB_REDIS_PORT="${MAXKB_REDIS_PORT:-6379}"
export MAXKB_REDIS_DB="${MAXKB_REDIS_DB:-0}"
export MAXKB_REDIS_PASSWORD="${MAXKB_REDIS_PASSWORD:-}"
export MAXKB_LOCAL_MODEL_HOST="${MAXKB_LOCAL_MODEL_HOST:-127.0.0.1}"
export MAXKB_LOCAL_MODEL_PORT="${MAXKB_LOCAL_MODEL_PORT:-11636}"
export MAXKB_LOCAL_MODEL_PROTOCOL="${MAXKB_LOCAL_MODEL_PROTOCOL:-http}"

load_docker_env() {
  local container_name="$1"
  local env_prefix="$2"
  local target_prefix="$3"
  local source_user_var="${env_prefix}_USER"
  local source_password_var="${env_prefix}_PASSWORD"
  local source_db_var="${env_prefix}_DB"
  local target_user_var="${target_prefix}_USER"
  local target_password_var="${target_prefix}_PASSWORD"
  local target_db_var="${target_prefix}_DB"
  local user_value password_value db_value

  if ! command -v docker >/dev/null 2>&1; then
    echo "[env] docker not found, skip loading ${container_name}" >&2
    return 0
  fi

  if ! docker ps --format '{{.Names}}' | grep -qx "${container_name}"; then
    echo "[env] container ${container_name} is not running, skip" >&2
    return 0
  fi

  local env_dump cmd_dump
  env_dump="$(docker inspect "${container_name}" --format '{{range .Config.Env}}{{println .}}{{end}}')"
  cmd_dump="$(docker inspect "${container_name}" --format '{{join .Config.Cmd " "}}')"

  user_value="$(printf '%s\n' "${env_dump}" | awk -F= -v k="${source_user_var}" '$1==k{print substr($0, index($0, "=")+1); exit}')"
  password_value="$(printf '%s\n' "${env_dump}" | awk -F= -v k="${source_password_var}" '$1==k{print substr($0, index($0, "=")+1); exit}')"
  db_value="$(printf '%s\n' "${env_dump}" | awk -F= -v k="${source_db_var}" '$1==k{print substr($0, index($0, "=")+1); exit}')"

  if [ -z "${password_value}" ] && [ "${env_prefix}" = "REDIS" ]; then
    password_value="$(printf '%s\n' "${cmd_dump}" | awk '
      {
        for (i = 1; i <= NF; i++) {
          if ($i == "--requirepass" && (i + 1) <= NF) {
            print $(i + 1)
            exit
          }
        }
      }
    ')"
  fi

  echo "[env] ${container_name}: ${source_user_var}=${user_value:-<empty>} ${source_db_var}=${db_value:-<empty>} ${source_password_var}=${password_value:-<empty>}" >&2

  if [ -n "${user_value}" ]; then
    export "${target_user_var}=${user_value}"
  fi
  if [ -n "${password_value}" ]; then
    export "${target_password_var}=${password_value}"
  fi
  if [ -n "${db_value}" ]; then
    export "${target_db_var}=${db_value}"
  fi
}

load_docker_defaults() {
  load_docker_env "${POSTGRES_CONTAINER_NAME:-maxkb-postgres}" "POSTGRES" "MAXKB_DB"
  load_docker_env "${REDIS_CONTAINER_NAME:-maxkb-redis}" "REDIS" "MAXKB_REDIS"
}

usage() {
  cat <<'EOF'
Usage:
  ./run_local_dev.sh init      # create venv and install dependencies
  ./run_local_dev.sh migrate   # run database migrations
  ./run_local_dev.sh run       # start Django dev server
  ./run_local_dev.sh test      # run end-to-end verification script
  ./run_local_dev.sh shell     # open virtualenv shell
  ./run_local_dev.sh check     # run Django system check
  ./run_local_dev.sh collect   # collect static files

Environment overrides:
  VENV_DIR, PYTHON_BIN, HOST, PORT
  MAXKB_DB_HOST, MAXKB_DB_PORT, MAXKB_DB_NAME, MAXKB_DB_USER, MAXKB_DB_PASSWORD
  MAXKB_REDIS_HOST, MAXKB_REDIS_PORT, MAXKB_REDIS_DB, MAXKB_REDIS_PASSWORD
  MAXKB_LOCAL_MODEL_HOST, MAXKB_LOCAL_MODEL_PORT, MAXKB_LOCAL_MODEL_PROTOCOL
EOF
}

ensure_venv() {
  if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtualenv at ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
}

install_deps() {
  ensure_venv
  if [ "${SKIP_INSTALL:-0}" = "1" ]; then
    echo "Skipping dependency installation (SKIP_INSTALL=1)"
    return 0
  fi

  if [ -f "${ROOT_DIR}/pyproject.toml" ]; then
    if command -v uv >/dev/null 2>&1; then
      echo "Installing dependencies with uv (offline-friendly if cache exists)"
      uv pip install --system -r "${ROOT_DIR}/pyproject.toml" || true
      uv pip install -r "${ROOT_DIR}/pyproject.toml" || true
    else
      echo "uv not found, skipping automatic dependency installation"
      echo "If dependencies are missing, install them manually inside the venv."
    fi
  else
    echo "pyproject.toml not found in ${ROOT_DIR}" >&2
    exit 1
  fi
}

run_migrations() {
  setup_env
  if [ ! -f "${DJANGO_MANAGE}" ]; then
    echo "manage.py not found: ${DJANGO_MANAGE}" >&2
    exit 1
  fi
  echo "Running migrations"
  python "${DJANGO_MANAGE}" migrate
}

free_port() {
  if [ "${AUTO_FREE_PORT:-0}" != "1" ]; then
    if command -v lsof >/dev/null 2>&1; then
      local pids
      pids="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
      if [ -n "${pids}" ]; then
        echo "Port ${PORT} is already in use: ${pids}" >&2
        echo "Set AUTO_FREE_PORT=1 if you really want the script to try freeing it." >&2
        return 1
      fi
    fi
    return 0
  fi

  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "${pids}" ]; then
      echo "Found process(es) listening on port ${PORT}: ${pids}"
      kill ${pids} 2>/dev/null || true
      sleep 1
      pids="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
      if [ -n "${pids}" ]; then
        echo "Port ${PORT} is still in use after kill attempt: ${pids}" >&2
        return 1
      fi
    fi
  fi
}

run_server() {
  setup_env
  if [ ! -f "${DJANGO_MANAGE}" ]; then
    echo "manage.py not found: ${DJANGO_MANAGE}" >&2
    exit 1
  fi
  free_port
  echo "Starting Django dev server at http://${HOST}:${PORT}"
  python "${DJANGO_MANAGE}" runserver "${HOST}:${PORT}"
}

run_test() {
  setup_env
  if [ ! -f "${ROOT_DIR}/test_maxkb_end_to_end.py" ]; then
    echo "test_maxkb_end_to_end.py not found" >&2
    exit 1
  fi
  echo "Running end-to-end verification"
  python "${ROOT_DIR}/test_maxkb_end_to_end.py"
}

setup_env() {
  ensure_venv
  load_docker_defaults
  if [ -n "${EXTRA_PYTHONPATH:-}" ]; then
    export PYTHONPATH="${EXTRA_PYTHONPATH}:${PYTHONPATH:-}"
  fi
}

run_shell() {
  ensure_venv
  echo "Opening shell in virtualenv. Type 'deactivate' to exit."
  exec "${SHELL:-/bin/bash}"
}

run_check() {
  ensure_venv
  python "${DJANGO_MANAGE}" check
}

run_collect() {
  ensure_venv
  python "${DJANGO_MANAGE}" collectstatic --noinput
}

main() {
  local cmd="${1:-help}"
  case "${cmd}" in
    init)
      install_deps
      ;;
    migrate)
      run_migrations
      ;;
    run)
      run_server
      ;;
    test)
      run_test
      ;;
    shell)
      run_shell
      ;;
    check)
      run_check
      ;;
    collect)
      run_collect
      ;;
    help|-h|--help)
      usage
      ;;
    *)
      echo "Unknown command: ${cmd}" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
