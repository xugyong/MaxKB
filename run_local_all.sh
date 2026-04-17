#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-maxkb}"
COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/docker-compose.yml}"
CMD="${1:-up}"

need_docker_compose() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose is available"
    return 0
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose is available"
    return 0
  fi
  echo "Docker Compose is required but not found." >&2
  exit 1
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}" "$@"
  else
    docker-compose -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}" "$@"
  fi
}

show_help() {
  cat <<'EOF'
Usage:
  ./run_local_all.sh up        # start all services without rebuilding
  ./run_local_all.sh down      # stop and remove containers
  ./run_local_all.sh logs      # follow logs
  ./run_local_all.sh ps        # show service status
  ./run_local_all.sh rebuild   # rebuild image and start
  ./run_local_all.sh health    # check local health endpoint

Ports:
  Admin UI: http://127.0.0.1:8090/admin/
  Open API: http://127.0.0.1:8090/api/open/v1/health
EOF
}

up() {
  compose up -d
  echo
  echo "Services started."
  echo ""
  echo "Access paths:"
  echo "  Frontend admin UI:   http://127.0.0.1:8090/admin/"
  echo "  Frontend chat UI:    http://127.0.0.1:8090/chat/"
  echo "  Frontend tool UI:    http://127.0.0.1:8090/tool/"
  echo "  Backend health:      http://127.0.0.1:8090/api/open/v1/health"
  echo "  Backend admin API:   http://127.0.0.1:8090/admin/api/"
  echo "  Backend chat API:    http://127.0.0.1:8090/chat/api/"
  echo "  Backend tool API:    http://127.0.0.1:8090/tool/api/"
  echo "  Direct backend port: http://127.0.0.1:8080/"
}

down() {
  compose down
}

logs() {
  compose logs -f
}

ps_cmd() {
  compose ps
}

rebuild() {
  compose build --no-cache
  compose up -d
}

health() {
  curl -sS http://127.0.0.1:8090/api/open/v1/health || true
}

need_docker_compose

case "${CMD}" in
  up)
    up
    ;;
  down)
    down
    ;;
  logs)
    logs
    ;;
  ps)
    ps_cmd
    ;;
  rebuild)
    rebuild
    ;;
  health)
    health
    ;;
  -h|--help|help)
    show_help
    ;;
  *)
    echo "Unknown command: ${CMD}" >&2
    show_help
    exit 1
    ;;
esac
