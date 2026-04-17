#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-maxkb-local:dev}"
CONTAINER_NAME="${CONTAINER_NAME:-maxkb-local}"
ADMIN_PORT="${ADMIN_PORT:-8090}"
API_PORT="${API_PORT:-8080}"

print_help() {
  cat <<'EOF'
Usage:
  ./run_local_docker.sh [build|run|stop|logs|shell|clean]

Defaults:
  IMAGE_NAME=maxkb-local:dev
  CONTAINER_NAME=maxkb-local
  ADMIN_PORT=8090
  API_PORT=8080

Examples:
  ./run_local_docker.sh build
  ./run_local_docker.sh run
  ./run_local_docker.sh logs
  ./run_local_docker.sh shell
  ./run_local_docker.sh stop
EOF
}

need_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required but not found in PATH." >&2
    exit 1
  fi
}

build_image() {
  echo "Building Docker image: ${IMAGE_NAME}"
  docker build -t "${IMAGE_NAME}" -f "${ROOT_DIR}/installer/Dockerfile" "${ROOT_DIR}"
}

run_container() {
  if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
    echo "Container ${CONTAINER_NAME} already exists. Removing it first."
    docker rm -f "${CONTAINER_NAME}" >/dev/null
  fi

  echo "Starting container: ${CONTAINER_NAME}"
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${ADMIN_PORT}:80" \
    -p "${API_PORT}:8080" \
    -v "${ROOT_DIR}/.maxkb-data:/opt/maxkb" \
    -e MAXKB_DB_HOST="${MAXKB_DB_HOST:-127.0.0.1}" \
    -e MAXKB_REDIS_HOST="${MAXKB_REDIS_HOST:-127.0.0.1}" \
    -e MAXKB_DB_PORT="${MAXKB_DB_PORT:-5432}" \
    -e MAXKB_REDIS_PORT="${MAXKB_REDIS_PORT:-6379}" \
    -e MAXKB_DB_NAME="${MAXKB_DB_NAME:-maxkb}" \
    -e MAXKB_DB_USER="${MAXKB_DB_USER:-postgres}" \
    -e MAXKB_DB_PASSWORD="${MAXKB_DB_PASSWORD:-postgres}" \
    -e MAXKB_REDIS_PASSWORD="${MAXKB_REDIS_PASSWORD:-}" \
    "${IMAGE_NAME}"

  echo
  echo "Waiting for services to start..."
  sleep 8
  docker logs --tail 80 "${CONTAINER_NAME}" || true
  echo
  echo "Admin UI: http://127.0.0.1:${ADMIN_PORT}/admin/"
  echo "Open API: http://127.0.0.1:${API_PORT}/api/open/v1/health"
}

stop_container() {
  if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
    docker rm -f "${CONTAINER_NAME}" >/dev/null
    echo "Stopped and removed ${CONTAINER_NAME}"
  else
    echo "Container ${CONTAINER_NAME} does not exist."
  fi
}

show_logs() {
  docker logs -f "${CONTAINER_NAME}"
}

open_shell() {
  docker exec -it "${CONTAINER_NAME}" bash
}

clean() {
  stop_container || true
  if [ -d "${ROOT_DIR}/.maxkb-data" ]; then
    echo "Local volume kept at ${ROOT_DIR}/.maxkb-data"
  fi
}

main() {
  need_docker
  local cmd="${1:-run}"
  case "${cmd}" in
    build)
      build_image
      ;;
    run)
      build_image
      run_container
      ;;
    stop)
      stop_container
      ;;
    logs)
      show_logs
      ;;
    shell)
      open_shell
      ;;
    clean)
      clean
      ;;
    -h|--help|help)
      print_help
      ;;
    *)
      echo "Unknown command: ${cmd}" >&2
      print_help
      exit 1
      ;;
  esac
}

main "$@"
