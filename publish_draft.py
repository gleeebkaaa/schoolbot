#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Публикация одобренного черновика в канал. Запускать после одобрения Глебом.
Использование: python3 publish_draft.py           — публикует draft.json (утренний черновик)
               python3 publish_draft.py --index 3  — публикует draft_3.json (первичное наполнение)
"""

import os
import sys
import json
import argparse
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
    parser = argparse.ArgumentParser(description="Опубликовать одобренный черновик в канал")
    parser.add_argument("--index", type=int, default=None, help="Номер черновика первичного наполнения (draft_1.json … draft_7.json)")
    args = parser.parse_args()

    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    channel = os.environ.get("CHANNEL", "").strip()
    if not bot_token or not channel:
        print("Задайте BOT_TOKEN и CHANNEL в .env", file=sys.stderr)
        sys.exit(1)

    if args.index is not None:
        draft_file = SCRIPT_DIR / f"draft_{args.index}.json"
    else:
        draft_file = SCRIPT_DIR / "draft.json"

    if not draft_file.is_file():
        print(f"Черновик не найден: {draft_file.name}", file=sys.stderr)
        sys.exit(1)

    draft = json.loads(draft_file.read_text(encoding="utf-8"))
    text = draft.get("text", "")
    media_url = draft.get("media_url")

    if not text:
        print("Черновик пустой.", file=sys.stderr)
        sys.exit(1)

    url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    url_text = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload_text = {"chat_id": channel, "text": text, "disable_web_page_preview": True}

    try:
        if media_url:
            r = requests.post(url_photo, json={"chat_id": channel, "photo": media_url, "caption": text}, timeout=20)
        else:
            r = requests.post(url_text, json=payload_text, timeout=20)
        data = r.json() if r.text else {}
        if not data.get("ok"):
            print(f"Ошибка Telegram: {data}", file=sys.stderr)
            sys.exit(1)
        draft_file.unlink()
        print("Черновик опубликован в канал.")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
