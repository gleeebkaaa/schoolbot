#!/bin/bash
# Переключение бота OpenClaw на Ollama (без API-ключа).
# Запускать на VPS под root: bash setup_ollama_for_openclaw.sh
set -e

echo "=== 1. Установка Ollama ==="
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
  systemctl daemon-reload
  systemctl enable ollama
else
  echo "Ollama уже установлен."
fi

echo "=== 2. Запуск Ollama и загрузка модели (llama3.2, ~2 GB) ==="
systemctl start ollama || true
sleep 3
# Модель с поддержкой tool calling для OpenClaw
ollama pull llama3.2

echo "=== 3. Включение Ollama в OpenClaw ==="
ENV_FILE="/opt/channel-poster/.env"
mkdir -p "$(dirname "$ENV_FILE")"
if [ -f "$ENV_FILE" ]; then
  if ! grep -q '^OLLAMA_API_KEY=' "$ENV_FILE"; then
    echo 'OLLAMA_API_KEY=ollama-local' >> "$ENV_FILE"
    echo "Добавлен OLLAMA_API_KEY в $ENV_FILE"
  fi
else
  echo 'OLLAMA_API_KEY=ollama-local' > "$ENV_FILE"
  echo "Создан $ENV_FILE с OLLAMA_API_KEY"
fi

# Подключить .env к сервису openclaw, если ещё не подключён
SVC="/etc/systemd/system/openclaw.service"
if [ -f "$SVC" ] && ! grep -q 'EnvironmentFile=/opt/channel-poster/.env' "$SVC"; then
  sed -i.bak '/\[Service\]/a EnvironmentFile=/opt/channel-poster/.env' "$SVC"
  echo "В openclaw.service добавлен EnvironmentFile"
  systemctl daemon-reload
fi

echo "=== 4. Переключение модели агента на Ollama ==="
export OLLAMA_API_KEY=ollama-local
export PATH="/usr/bin:/usr/local/bin:$PATH"
CFG="/root/.openclaw/openclaw.json"
# Способ 1: CLI (если поддерживается)
openclaw config set agents.defaults.model.primary "ollama/llama3.2" 2>/dev/null && echo "Модель задана через CLI." || true
# Способ 2: правка JSON, если в конфиге ещё groq
if [ -f "$CFG" ] && grep -q 'groq' "$CFG" 2>/dev/null; then
  if command -v node &>/dev/null; then
    node -e "
    const fs=require('fs');
    const p='$CFG';
    let j=JSON.parse(fs.readFileSync(p,'utf8'));
    if (!j.agents) j.agents={};
    if (!j.agents.defaults) j.agents.defaults={};
    if (!j.agents.defaults.model) j.agents.defaults.model={};
    j.agents.defaults.model.primary='ollama/llama3.2';
    fs.writeFileSync(p, JSON.stringify(j, null, 2));
    console.log('Модель в конфиге заменена на ollama/llama3.2');
    " 2>/dev/null || true
  else
    echo "В $CFG замените groq/... на \"ollama/llama3.2\" в agents.defaults.model.primary"
  fi
fi

echo "=== 5. Перезапуск OpenClaw ==="
systemctl restart openclaw
sleep 4
systemctl is-active openclaw && echo "OpenClaw запущен." || (echo "Проверьте: journalctl -u openclaw -n 30 --no-pager"; exit 1)

echo ""
echo "Готово. Бот теперь использует локальную модель Ollama (llama3.2), ключ не нужен."
echo "Проверка: напишите боту в Telegram."
