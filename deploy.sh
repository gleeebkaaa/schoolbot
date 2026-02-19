#!/bin/bash
# Деплой на VPS.
# Варианты:
#   SSH_PASS='пароль' ./deploy.sh           — копирование файлов по scp и bootstrap
#   SSH_PASS='пароль' ./deploy.sh git        — на сервере git pull (нужен клон в /opt/channel-poster)
#   SSH_PASS='пароль' ./deploy.sh git ollama — git pull + запуск setup_ollama_for_openclaw.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
SSH_HOST="${SSH_HOST:-82.152.8.99}"
SSH_USER="${SSH_USER:-root}"
SSH_PORT="${SSH_PORT:-22}"
USE_GIT="${1:-}"
RUN_OLLAMA="${2:-}"

if [ -z "$SSH_PASS" ]; then
  echo "Задайте пароль: export SSH_PASS='ваш_пароль'"
  exit 1
fi

if ! command -v sshpass &>/dev/null; then
  echo "Установите sshpass: brew install sshpass (macOS) или apt install sshpass (Linux)"
  exit 1
fi

if [ "$USE_GIT" = "git" ]; then
  echo "Деплой через Git: pull на сервере..."
  CMD="cd /opt/channel-poster && git pull"
  [ "$RUN_OLLAMA" = "ollama" ] && CMD="$CMD && bash setup_ollama_for_openclaw.sh"
  sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "$CMD"
  echo "Готово."
  exit 0
fi

echo "Создаём каталог на сервере..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "mkdir -p /opt/channel-poster"

echo "Копируем файлы..."
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=accept-new -P "$SSH_PORT" \
  post.py requirements.txt .env bootstrap.sh \
  "$SSH_USER@$SSH_HOST:/opt/channel-poster/"

echo "Запускаем установку на сервере..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "chmod +x /opt/channel-poster/bootstrap.sh && /opt/channel-poster/bootstrap.sh"

echo "Деплой завершён."
