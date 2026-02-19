#!/bin/bash
# Запускается на VPS: установка Python, venv, зависимости, cron
# Расписание: 9:00 draft, 13/18/19:30 publish, опросы 1-2 раза в день
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv
cd /opt/channel-poster
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
echo "Проверка поста (publish, слот 13)..."
.venv/bin/python3 post.py --mode=publish --slot=13 || true

# Удаляем старые записи channel-poster
(crontab -l 2>/dev/null | grep -v "channel-poster" || true) > /tmp/cron.new || true

# МСК = UTC+3: 9:00 МСК = 6 UTC, 13 = 10 UTC, 18 = 15 UTC, 19:30 = 16:30 UTC
echo "0 6 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/post.py --mode=draft --slot=9 >> /var/log/channel-poster.log 2>&1" >> /tmp/cron.new
echo "0 10 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/post.py --mode=publish --slot=13 >> /var/log/channel-poster.log 2>&1" >> /tmp/cron.new
echo "0 15 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/post.py --mode=publish --slot=18 >> /var/log/channel-poster.log 2>&1" >> /tmp/cron.new
echo "30 16 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/post.py --mode=publish --slot=19 >> /var/log/channel-poster.log 2>&1" >> /tmp/cron.new
# Опрос 1 раз в день в 12:00 МСК (9 UTC)
echo "0 9 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/send_poll.py >> /var/log/channel-poster.log 2>&1" >> /tmp/cron.new
# Опрос 2 раз (опционально) в 17:00 МСК (14 UTC)
echo "0 14 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/send_poll.py >> /var/log/channel-poster.log 2>&1" >> /tmp/cron.new

crontab /tmp/cron.new
rm -f /tmp/cron.new
echo "Готово. Cron: 9:00 draft, 13/18/19:30 publish, опросы 12:00 и 17:00 МСК."
