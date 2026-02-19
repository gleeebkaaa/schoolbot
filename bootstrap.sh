#!/bin/bash
# Запускается на VPS: установка Python, venv, зависимости, cron
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv
cd /opt/channel-poster
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
echo "Проверка отправки поста..."
.venv/bin/python3 post.py || true
# Cron: каждый день в 9:00 МСК (6:00 UTC)
(crontab -l 2>/dev/null | grep -v "channel-poster/post.py"; echo "0 6 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/post.py >> /var/log/channel-poster.log 2>&1") | crontab -
echo "Готово. Cron: ежедневно в 9:00 МСК."
