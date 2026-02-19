#!/bin/bash
# Деплой на VPS: копирование файлов и запуск bootstrap на сервере
# Использование: SSH_PASS='пароль' ./deploy.sh
# Или: export SSH_PASS=... ; ./deploy.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
SSH_HOST="${SSH_HOST:-82.152.8.99}"
SSH_USER="${SSH_USER:-root}"
SSH_PORT="${SSH_PORT:-22}"

if [ -z "$SSH_PASS" ]; then
  echo "Задайте пароль: export SSH_PASS='ваш_пароль'"
  exit 1
fi

# Проверка sshpass (для неинтерактивного ввода пароля)
if ! command -v sshpass &>/dev/null; then
  echo "Установите sshpass: brew install sshpass (macOS) или apt install sshpass (Linux)"
  exit 1
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
