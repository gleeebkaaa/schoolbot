# Постер в Telegram-канал (подборки 1–4 класс)

Скрипт по расписанию готовит пост и отправляет его в ваш канал. Работает с шаблоном (без API) или с OpenAI для генерации текста.

## 1. Подготовка

- Создайте канал в Telegram, добавьте бота (из @BotFather) как **администратора** с правом «Публикация сообщений».
- Узнайте **username канала** (например `@mychannel`) или ID канала (например `-1001234567890`).

## 2. Локально / на VPS

```bash
cd channel-poster
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Отредактируйте `.env`:

```env
BOT_TOKEN=ваш_токен_от_BotFather
CHANNEL=@username_вашего_канала
# Опционально, для генерации текста через ИИ:
# OPENAI_API_KEY=sk-...
```

Проверка:

```bash
python3 post.py
```

## 3. Деплой на VPS (82.152.8.99)

Подключение (пароль потом смените):

```bash
ssh root@82.152.8.99
```

На сервере:

```bash
apt update && apt install -y python3 python3-pip python3-venv
mkdir -p /opt/channel-poster
```

С вашего компьютера залейте файлы в `/opt/channel-poster/` (через scp или вручную):

```bash
scp post.py requirements.txt .env root@82.152.8.99:/opt/channel-poster/
```

На VPS снова:

```bash
cd /opt/channel-poster
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python3 post.py
```

Если пост ушёл в канал — настраиваем cron (раз в день в 9:00):

```bash
crontab -e
```

Добавьте строку (подставьте свой путь к python):

```
0 9 * * * /opt/channel-poster/.venv/bin/python3 /opt/channel-poster/post.py >> /var/log/channel-poster.log 2>&1
```

## 4. Без OpenAI

Если `OPENAI_API_KEY` не задан, скрипт постит текст по **шаблону** (дата, день недели, советы для родителей и детей). Внешние API не нужны.

## 5. Безопасность

- Пароль от VPS и токен бота после настройки смените.
- Файл `.env` не коммитьте в git (уже в `.gitignore`).
