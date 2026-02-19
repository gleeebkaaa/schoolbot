#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Первичное наполнение канала: бот формирует план постов, генерирует черновики
и отправляет каждый лично на проверку @Wheres_themoney_Lebowski (Id: 5294591231).
Публикация в канал только после одобрения (ответ боту цифрой или «Опубликовать N»).
Запуск: python3 primary_fill.py [--dry-run]
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
KNOWLEDGE_FILE = SCRIPT_DIR / "school_knowledge.md"
APPROVAL_CHAT_ID = "5294591231"  # Gleb, все посты на проверку ему


def load_env():
    env_path = SCRIPT_DIR / ".env"
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_knowledge() -> str:
    if KNOWLEDGE_FILE.is_file():
        return KNOWLEDGE_FILE.read_text(encoding="utf-8")
    return "Онлайн-школа 1–4 класс. Сайт: https://xn----7sbb8agcekdfh2j.online/"


# План первичного наполнения: темы и порядок (развёрнутые, полезные, ведут к записи)
FILL_PLAN = [
    {"theme": "Приветствие и о канале", "hint": "Кто мы, для кого этот канал, что здесь будет (подборки, советы, польза для родителей 1–4 класс). Мягкий призыв подписаться и записаться на бесплатное занятие."},
    {"theme": "Для кого наша школа", "hint": "Повышение успеваемости, семейное обучение, спортсмены, путешественники, занятые родители и т.д. Коротко по каждому. Ссылка на сайт и запись."},
    {"theme": "Как проходят уроки", "hint": "Индивидуальный подход, интерактив, обратная связь 24/7. Игровой формат, яркие материалы. Призыв записаться на бесплатное занятие."},
    {"theme": "Методика и программа (КТП Школа России)", "hint": "Почему опираемся на программу, как это помогает родителям и детям. Развёрнуто, с пользой. Запись на диагностику/первое занятие."},
    {"theme": "Курсы: математика, русский, чтение, окружающий мир", "hint": "Кратко по каждому курсу, для кого, что даёт. Не реклама, а польза. Сайт и запись."},
    {"theme": "Первое занятие бесплатно", "hint": "Что ждёт на первом занятии, как записаться, контакты. Дружелюбно, без давления."},
    {"theme": "Контакты и запись", "hint": "Сайт, телефон, email. Короткий призыв записаться на бесплатное занятие. Подпись от имени школы."},
]


def generate_post(theme: str, hint: str, index: int, total: int) -> str | None:
    """Генерация поста через LLM (Groq / OpenRouter / OpenAI)."""
    knowledge = load_knowledge()
    prompt = f"""Ты — руководитель онлайн-школы для детей 1–4 класс. Напиши один пост для Telegram-канала (первичное наполнение).

База знаний:
{knowledge}

Тема поста {index} из {total}: {theme}.
Подсказка: {hint}

Требования: развёрнутый пост (2–4 абзаца), тон владельца школы — уверенный, тёплый. В конце — призыв к действию (запись на бесплатное занятие, сайт https://xn----7sbb8agcekdfh2j.online/). Не упоминать комментарии. Только готовый текст, без заголовка и кавычек."""
    try:
        from llm import get_completion
        return get_completion(prompt, max_tokens=800)
    except Exception as e:
        print(f"LLM ошибка: {e}", file=sys.stderr)
        return None


def fallback_post(theme: str, hint: str, index: int, total: int) -> str:
    return f"""📚 {theme}

{hint}

Записаться на бесплатное занятие и узнать больше: https://xn----7sbb8agcekdfh2j.online/
Телефон: +7 (915) 442-70-17."""


def send_to_approver(bot_token: str, chat_id: str, index: int, total: int, theme: str, text: str, dry_run: bool) -> bool:
    msg = f"📋 Первичное наполнение. Пост {index}/{total}\nТема: {theme}\n\nЧтобы опубликовать этот пост в канал, ответьте боту: {index}\n\n---\n\n{text}"
    if dry_run:
        print(f"[DRY-RUN] Отправка поста {index}/{total} на проверку (chat_id={chat_id})")
        print("---")
        print(msg[:500] + "..." if len(msg) > 500 else msg)
        return True
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "disable_web_page_preview": True},
            timeout=20,
        )
        data = r.json() if r.text else {}
        if not data.get("ok"):
            print(f"Telegram ошибка: {data}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}", file=sys.stderr)
        return False


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Первичное наполнение канала: план постов и отправка на проверку Глебу")
    parser.add_argument("--dry-run", action="store_true", help="Не отправлять в Telegram, только сгенерировать и сохранить черновики")
    args = parser.parse_args()

    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    channel = os.environ.get("CHANNEL", "").strip()
    approval_chat_id = os.environ.get("APPROVAL_CHAT_ID", APPROVAL_CHAT_ID).strip().replace("@", "")
    if not approval_chat_id.isdigit():
        approval_chat_id = APPROVAL_CHAT_ID

    if not bot_token or not channel:
        print("Задайте BOT_TOKEN и CHANNEL в .env", file=sys.stderr)
        sys.exit(1)

    total = len(FILL_PLAN)
    print(f"План: {total} постов. Все черновики отправляются на проверку @Wheres_themoney_Lebowski (Id: {approval_chat_id}). Публикация — после ответа боту цифрой (1–{total}).")

    for i, item in enumerate(FILL_PLAN, start=1):
        theme = item["theme"]
        hint = item["hint"]
        text = generate_post(theme, hint, i, total)
        if not text:
            text = fallback_post(theme, hint, i, total)
        draft_path = SCRIPT_DIR / f"draft_{i}.json"
        draft_path.write_text(
            json.dumps({"text": text, "media_url": None, "theme": theme, "index": i}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Пост {i}/{total} сохранён: {draft_path.name}")
        if not send_to_approver(bot_token, approval_chat_id, i, total, theme, text, args.dry_run):
            print(f"Не удалось отправить пост {i} на проверку.", file=sys.stderr)
            sys.exit(1)
    print("Готово. Проверьте Telegram. Чтобы опубликовать пост, ответьте боту цифрой (1–7) или на сервере: python3 publish_draft.py --index N.")


if __name__ == "__main__":
    main()
