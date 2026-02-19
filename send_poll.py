#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отправка квиза/опроса в канал. 1–2 раза в день между постами.
Переменные: BOT_TOKEN, CHANNEL. Запуск: python3 send_poll.py "Вопрос?" "Вариант 1" "Вариант 2" ...
Или без аргументов — отправит дефолтный опрос для родителей 1–4 класс.
"""

import os
import sys
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent


def load_env():
    env_path = SCRIPT_DIR / ".env"
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    load_env()
    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    channel = os.environ.get("CHANNEL", "").strip()
    if not bot_token or not channel:
        print("Задайте BOT_TOKEN и CHANNEL в .env", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        question = sys.argv[1]
        options = list(sys.argv[2:])[:10]
    else:
        question = "Какой формат занятий удобнее для вашего ребёнка?"
        options = ["Утро", "День", "Вечер", "Выходные"]

    url = f"https://api.telegram.org/bot{bot_token}/sendPoll"
    payload = {"chat_id": channel, "question": question, "options": options, "is_anonymous": False}
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json() if r.text else {}
        if not data.get("ok"):
            print(f"Ошибка: {data}", file=sys.stderr)
            sys.exit(1)
        print("Опрос отправлен в канал.")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
