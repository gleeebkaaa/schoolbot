#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Постинг в Telegram-канал: подборка для родителей и детей 1–4 класс.
Запуск: python3 post.py
Переменные окружения: BOT_TOKEN, CHANNEL, опционально OPENAI_API_KEY
"""

import os
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)


def load_env():
    """Загружает .env из текущей папки (формат KEY=value)."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_text_with_openai(api_key: str) -> str | None:
    """Генерирует текст поста через OpenAI API."""
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    day_name = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][now.weekday()]

    prompt = f"""Сегодня {date_str}, {day_name}. Напиши один короткий пост для Telegram-канала онлайн-школы.
Аудитория: родители и дети 1–4 класс.
Формат: приветливый тон, 2–3 абзаца. Включи:
1) одну идею занятия или поделки на сегодня;
2) одну мысль или совет для родителей;
3) призыв к действию (например, написать в комментариях или сохранить пост).
Без заголовка "Пост" и без кавычек — только готовый текст для публикации."""

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return text if text else None
    except Exception as e:
        print(f"OpenAI ошибка: {e}", file=sys.stderr)
        return None


def get_text_template() -> str:
    """Текст поста по шаблону (без внешнего API)."""
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_name = days[now.weekday()]

    return f"""📚 Добрый день, родители и ребята 1–4 класс!

{date_str}, {day_name}.

Сегодня предлагаем:
• 15–20 минут чтения — любую книгу по вкусу.
• Одно простое задание: опиши тремя предложениями, что тебе понравилось за сегодня.
• Для родителей: похвалите ребёнка за одну конкретную вещь (урок, помощь, инициативу).

Сохраняйте пост в закладки и делитесь в комментариях, чем занимались сегодня. 👇"""


def send_to_telegram(bot_token: str, channel: str, text: str) -> bool:
    """Отправляет сообщение в канал через Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json() if r.text else {}
        if not data.get("ok"):
            print(f"Telegram API ошибка: {data}", file=sys.stderr)
            return False
        print("Пост успешно отправлен в канал.")
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}", file=sys.stderr)
        return False


def main():
    load_env()
    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    channel = os.environ.get("CHANNEL", "").strip()

    if not bot_token or not channel:
        print("Задайте BOT_TOKEN и CHANNEL в .env или в окружении.", file=sys.stderr)
        sys.exit(1)

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        text = get_text_with_openai(openai_key)
    else:
        text = None
    if not text:
        text = get_text_template()

    if not send_to_telegram(bot_token, channel, text):
        sys.exit(1)


if __name__ == "__main__":
    main()
