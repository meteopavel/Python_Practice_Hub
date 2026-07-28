#!/usr/bin/env bash
#===============================================================================
# DEPLOY SCRIPT FOR Python_Practice_Hub (web-grader)
#
# Особенность именно этого проекта: деплой на ДВЕ разные машины —
#   роутер (executor, только внутри тоннеля) + Frankfurt (front, публичный).
#===============================================================================

set -euo pipefail

DEFAULT_COMMIT_MSG="Update project"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="$PROJECT_ROOT/.env"
ARCHIVE_DIR="$PROJECT_ROOT/secure"
ARCHIVE_NAME="sensitive_bundle.7z"
ARCHIVE_PATH="${ARCHIVE_DIR}/${ARCHIVE_NAME}"

cd "$PROJECT_ROOT"

QUIET=0
COMMIT_MSG=""
for arg in "$@"; do
    case "$arg" in
        -q|--quiet) QUIET=1 ;;
        *) COMMIT_MSG="$arg" ;;
    esac
done
COMMIT_MSG="${COMMIT_MSG:-$DEFAULT_COMMIT_MSG}"

log() {
    if [[ "$QUIET" -eq 0 ]]; then echo "$@"; fi
}

get_env() {
    local var_name="$1" env_file="$2"
    if [[ ! -f "$env_file" ]]; then echo ""; return; fi
    ( grep -E "^${var_name}=" "$env_file" 2>/dev/null || true ) | head -1 | cut -d'=' -f2-
}

require_env() {
    local var_name="$1" var_value="$2"
    if [[ -z "$var_value" ]]; then
        echo "❌ Переменная $var_name не задана в .env"
        exit 1
    fi
}

# Общие функции (run_with_heartbeat, timeout_run, rsync_via_tunnel) —
# используются во всех проектах, см. сам файл.
source "$(dirname "${PROJECT_ROOT}")/tools/deploy_helpers.sh"

log "🚀 Python_Practice_Hub deploy (роутер=executor + Frankfurt=front)"
log "📁 Project root: $PROJECT_ROOT"
log "----------------------------------------"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ Файл .env не найден: $ENV_FILE"
    echo "💡 Создай его из env.example: cp env.example .env"
    exit 1
fi

ARCHIVE_PASSWORD=$(get_env "ARCHIVE_PASSWORD" "$ENV_FILE")
SECURE_RSYNC_USER=$(get_env "SECURE_RSYNC_USER" "$ENV_FILE")
SECURE_RSYNC_HOST=$(get_env "SECURE_RSYNC_HOST" "$ENV_FILE")
SECURE_RSYNC_PATH=$(get_env "SECURE_RSYNC_PATH" "$ENV_FILE")

DEPLOY_BRANCH=$(get_env "DEPLOY_BRANCH" "$ENV_FILE")
DEPLOY_ROUTER_ALIAS=$(get_env "DEPLOY_ROUTER_ALIAS" "$ENV_FILE")
DEPLOY_ROUTER_REPO_DIR=$(get_env "DEPLOY_ROUTER_REPO_DIR" "$ENV_FILE")
DEPLOY_FRANKFURT_ALIAS=$(get_env "DEPLOY_FRANKFURT_ALIAS" "$ENV_FILE")
DEPLOY_FRANKFURT_REPO_DIR=$(get_env "DEPLOY_FRANKFURT_REPO_DIR" "$ENV_FILE")

require_env "DEPLOY_BRANCH" "$DEPLOY_BRANCH"
require_env "DEPLOY_ROUTER_ALIAS" "$DEPLOY_ROUTER_ALIAS"
require_env "DEPLOY_ROUTER_REPO_DIR" "$DEPLOY_ROUTER_REPO_DIR"
require_env "DEPLOY_FRANKFURT_ALIAS" "$DEPLOY_FRANKFURT_ALIAS"
require_env "DEPLOY_FRANKFURT_REPO_DIR" "$DEPLOY_FRANKFURT_REPO_DIR"

log "🔧 Deploy config:"
log "   Branch:    $DEPLOY_BRANCH"
log "   Роутер:    $DEPLOY_ROUTER_ALIAS:$DEPLOY_ROUTER_REPO_DIR (executor + tutor-llm)"
log "   Frankfurt: $DEPLOY_FRANKFURT_ALIAS:$DEPLOY_FRANKFURT_REPO_DIR (app + системный Caddy)"
log "----------------------------------------"

log "🔐 Проверка SSH-доступа к обеим машинам..."
ssh -o ConnectTimeout=5 -o BatchMode=yes "$DEPLOY_ROUTER_ALIAS" "echo ok" > /dev/null
ssh -o ConnectTimeout=5 -o BatchMode=yes "$DEPLOY_FRANKFURT_ALIAS" "echo ok" > /dev/null
log "✅ SSH-доступ есть"
log "----------------------------------------"

log "🔐 Этап 1/4: backup sensitive files"

BACKUP_OK=1
if [[ -z "$ARCHIVE_PASSWORD" || -z "$SECURE_RSYNC_USER" || -z "$SECURE_RSYNC_HOST" || -z "$SECURE_RSYNC_PATH" ]]; then
    log "⚠️  Backup: переменные ARCHIVE_PASSWORD / SECURE_RSYNC_* не заданы — пропускаем"
    log "   (пока нечего бэкапить кроме .env — ни БД, ни секретов ещё нет)"
    BACKUP_OK=0
fi

if [[ "$BACKUP_OK" -eq 1 ]]; then
    if ! command -v 7z &> /dev/null; then
        echo "⚠️  Backup: команда 7z не найдена — пропускаем"
        BACKUP_OK=0
    fi
fi

if [[ "$BACKUP_OK" -eq 1 ]]; then
    mkdir -p "${ARCHIVE_DIR}"
    [[ -f "${ARCHIVE_PATH}" ]] && rm -f "${ARCHIVE_PATH}"
    log "🔒 Создаём зашифрованный архив (.env)..."
    (
        cd "${PROJECT_ROOT}"
        7z a -p"${ARCHIVE_PASSWORD}" -mhe=on "${ARCHIVE_PATH}" ".env" > /dev/null
    )
    log "📤 Отправляем архив на backup-сервер..."
    run_with_heartbeat "отправка backup" \
        rsync_via_tunnel "${SECURE_RSYNC_USER}" "${SECURE_RSYNC_HOST}" \
        "${ARCHIVE_PATH}" "${SECURE_RSYNC_PATH}"
    log "✅ Архив отправлен на backup-сервер."
fi

log "----------------------------------------"
log "📦 Этап 2/4: commit & push"
git add .
if ! git diff --staged --quiet; then
    GIT_Q=""
    [[ "$QUIET" -eq 1 ]] && GIT_Q="-q"
    git commit $GIT_Q -m "$COMMIT_MSG"
    git push $GIT_Q origin "$DEPLOY_BRANCH"
    log "✅ Закоммичено: $COMMIT_MSG"
else
    log "⚠️ Нет изменений для коммита"
    GIT_Q=""
    [[ "$QUIET" -eq 1 ]] && GIT_Q="-q"
    git push $GIT_Q origin "$DEPLOY_BRANCH"
fi

log "----------------------------------------"
log "🖥️ Этап 3/4: роутер (executor + tutor-llm)"

run_router() {
    ssh "$DEPLOY_ROUTER_ALIAS" bash -s <<EOF
set -euo pipefail
cd "$DEPLOY_ROUTER_REPO_DIR"
git fetch origin "$DEPLOY_BRANCH" -q
git checkout "$DEPLOY_BRANCH" -q
git pull origin "$DEPLOY_BRANCH" -q
cd executor
docker compose up -d --build
docker compose ps
echo "✅ Router (executor) deploy completed"
cd ../tutor-llm
docker compose up -d --build
docker compose ps
echo "✅ Router (tutor-llm) deploy completed"
EOF
}

if [[ "$QUIET" -eq 1 ]]; then
    ROUTER_OUT=$(run_router 2>&1) || { echo "❌ Ошибка деплоя роутера:"; echo "$ROUTER_OUT"; exit 1; }
    echo "$ROUTER_OUT" | grep -E "Up |✅ Router"
else
    run_router
fi

log "----------------------------------------"
log "🖥️ Этап 4/4: Frankfurt (front)"

run_vps() {
    ssh "$DEPLOY_FRANKFURT_ALIAS" bash -s <<EOF
set -euo pipefail
cd "$DEPLOY_FRANKFURT_REPO_DIR"
git fetch origin "$DEPLOY_BRANCH" -q
git checkout "$DEPLOY_BRANCH" -q
git pull origin "$DEPLOY_BRANCH" -q
docker compose up -d --build app
docker compose ps
echo "✅ Frankfurt (front) deploy completed"
EOF
}

if [[ "$QUIET" -eq 1 ]]; then
    FRANKFURT_OUT=$(run_vps 2>&1) || { echo "❌ Ошибка деплоя Frankfurt:"; echo "$FRANKFURT_OUT"; exit 1; }
    echo "$FRANKFURT_OUT" | grep -E "Up |✅ Frankfurt"
else
    run_vps
fi

log "----------------------------------------"
echo "✅ Деплой завершён успешно (роутер + Frankfurt)"
