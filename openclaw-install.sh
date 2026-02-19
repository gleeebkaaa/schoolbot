#!/bin/bash
# Установка OpenClaw на VPS + Telegram. Запуск на сервере.
# На сервере: TELEGRAM_BOT_TOKEN='...' ./openclaw-install.sh
set -e
BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"

if [ -z "$BOT_TOKEN" ]; then
  echo "Задайте TELEGRAM_BOT_TOKEN (export TELEGRAM_BOT_TOKEN='...')"
  exit 1
fi

echo "Установка Node.js 22..."
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
node -v

echo "Установка OpenClaw..."
export PATH="/usr/bin:${PATH}"
npm install -g openclaw@latest

echo "Создание конфига..."
mkdir -p /root/.openclaw
cat > /root/.openclaw/openclaw.json << EOF
{
  "identity": {
    "name": "Онлайн-школа",
    "theme": "помощник для родителей и детей 1-4 класс",
    "emoji": "📚"
  },
  "agent": {
    "workspace": "/root/.openclaw/workspace"
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "$BOT_TOKEN",
      "dmPolicy": "pairing",
      "groups": { "*": { "requireMention": true } }
    }
  },
  "gateway": {
    "bind": "127.0.0.1",
    "port": 18789
  }
}
EOF

echo "Создание systemd-сервиса..."
cat > /etc/systemd/system/openclaw.service << 'SVCEOF'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment=HOME=/root
Environment=OPENCLAW_CONFIG_PATH=/root/.openclaw/openclaw.json
ExecStart=/usr/bin/openclaw gateway
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable openclaw
systemctl start openclaw
sleep 3
systemctl status openclaw --no-pager || true
echo "OpenClaw установлен. Для одобрения лички: ssh на сервер, затем: openclaw pairing list telegram && openclaw pairing approve telegram <CODE>"
echo "Логи: journalctl -u openclaw -f"
