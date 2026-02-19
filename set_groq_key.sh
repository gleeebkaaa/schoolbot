#!/bin/bash
# Добавить GROQ_API_KEY на VPS и перезапустить OpenClaw.
# Запуск на сервере: ./set_groq_key.sh gsk_твой_ключ
# Или: bash set_groq_key.sh gsk_...
set -e
KEY="$1"
if [ -z "$KEY" ]; then
  echo "Использование: $0 gsk_твой_ключ"
  echo "Ключ бесплатно: console.groq.com → API Keys"
  exit 1
fi
ENV_FILE="${ENV_FILE:-/opt/channel-poster/.env}"
if grep -q '^GROQ_API_KEY=' "$ENV_FILE" 2>/dev/null; then
  sed -i "s/^GROQ_API_KEY=.*/GROQ_API_KEY=$KEY/" "$ENV_FILE"
else
  echo "GROQ_API_KEY=$KEY" >> "$ENV_FILE"
fi
echo "GROQ_API_KEY добавлен в $ENV_FILE"
systemctl restart openclaw
echo "OpenClaw перезапущен."
