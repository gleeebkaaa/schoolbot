#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Постинг в Telegram-канал онлайн-школы 1–4 класс.
Режимы: draft (9:00 — только на проверку Глебу), publish (13/18/19:30 — в канал).
Переменные: BOT_TOKEN, CHANNEL, APPROVAL_CHAT_ID, COMMENTS_ENABLED, OPENAI_API_KEY, SLOT, MODE.
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
DRAFT_FILE = SCRIPT_DIR / "draft.json"
KNOWLEDGE_FILE = SCRIPT_DIR / "school_knowledge.md"

# Слоты: 9 = утро (на проверку), 13, 18, 19 = в канал
SLOT_POST_TYPE = {
    9: "утренний тематический",
    13: "тематический или методика КТП Школа России",
    18: "тематический или подборка из интернета для родителей 1-4 класс",
    19: "тематический развёрнутый",
}


def load_env():
    env_path = SCRIPT_DIR / ".env"
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_school_knowledge() -> str:
    """База знаний с сайта школы для промпта."""
    if KNOWLEDGE_FILE.is_file():
        return KNOWLEDGE_FILE.read_text(encoding="utf-8")
    return "Онлайн-школа 1–4 класс. Сайт: https://xn----7sbb8agcekdfh2j.online/ Запись бесплатного занятия, контакты: +7 (915) 442-70-17, info@online-school.ru"


def get_prompt(slot: int, comments_enabled: bool) -> str:
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    day_name = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][now.weekday()]
    post_type = SLOT_POST_TYPE.get(slot, "тематический")
    knowledge = load_school_knowledge()

    no_comment = ""
    if not comments_enabled:
        no_comment = " ЗАПРЕЩЕНО: призывы писать в комментариях, «ответьте ниже», «напишите в комментариях» — в канале комментарии отключены. Не упоминать комментарии вообще."

    return f"""Ты — руководитель онлайн-школы для детей 1–4 класс. Пишешь пост для Telegram-канала. Опирайся только на факты из базы знаний.

База знаний школы:
{knowledge}

Сегодня {date_str}, {day_name}. Слот поста: {post_type}.
Требования: развёрнутый, подробный пост (не один абзац). Уникальный и полезный для родителей и детей 1–4 класс. Тон — владелец школы: уверенный, тёплый, профессиональный. В конце — мягкий призыв к действию (запись на бесплатное занятие, сайт). Если используешь внешний источник — обязательно указать ссылку на ресурс.
{no_comment}

Выдай только готовый текст поста без заголовка и кавычек."""


def get_text_with_llm(slot: int, comments_enabled: bool) -> str | None:
    """Генерация текста поста через LLM (Groq / OpenRouter / OpenAI — что задано в .env)."""
    from llm import get_completion
    prompt = get_prompt(slot, comments_enabled)
    return get_completion(prompt, max_tokens=1000)


def get_text_fallback(slot: int, comments_enabled: bool) -> str:
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_name = days[now.weekday()]
    cta = "Сохраняйте пост и заходите на сайт за бесплатным занятием: https://xn----7sbb8agcekdfh2j.online/"
    return f"""📚 Добрый день, родители и ребята 1–4 класс!

{date_str}, {day_name}.

Сегодня предлагаем: 15–20 минут чтения и одно короткое задание — опиши тремя предложениями, что тебе понравилось за день. Для родителей — похвалите ребёнка за одну конкретную вещь.

{cta}"""


def strip_comment_phrases(text: str) -> str:
    """Убирает призывы к комментариям, если они проскочили (защита репутации)."""
    bad = [
        r"напишите в комментариях?[^.]*\.?",
        r"ответьте в комментариях?[^.]*\.?",
        r"пишите в комментариях?[^.]*\.?",
        r"оставьте комментарий[^.]*\.?",
        r"комментариях?[^.]*\.?",
        r"ответьте ниже[^.]*\.?",
        r"напишите ниже[^.]*\.?",
        r"делиться в комментариях?[^.]*\.?",
        r"под комментарием[^.]*\.?",
    ]
    out = text
    for p in bad:
        out = re.sub(p, " ", out, flags=re.I)
    return re.sub(r"\s+", " ", out).strip()


def get_media_url() -> str | None:
    """Уникальное медиа для поста (пока заглушка — можно подключить Unsplash/папку)."""
    # TODO: подключить источник медиа и учёт использованных (used_media.json)
    return os.environ.get("MEDIA_URL", "").strip() or None


def send_message(bot_token: str, chat_id: str, text: str, photo_url: str | None = None) -> bool:
    if photo_url:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": photo_url, "caption": text, "parse_mode": "HTML"}
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=20)
        data = r.json() if r.text else {}
        if not data.get("ok"):
            print(f"Telegram API ошибка: {data}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}", file=sys.stderr)
        return False


def save_draft(text: str, media_url: str | None, slot: int):
    DRAFT_FILE.write_text(
        json.dumps({"text": text, "media_url": media_url, "slot": slot, "created": datetime.now().isoformat()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_draft() -> dict | None:
    if not DRAFT_FILE.is_file():
        return None
    try:
        return json.loads(DRAFT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Пост в канал или черновик на проверку")
    parser.add_argument("--mode", choices=["draft", "publish"], default="publish", help="draft = на проверку Глебу, publish = в канал")
    parser.add_argument("--slot", type=int, default=9, choices=[9, 13, 18, 19], help="Слот: 9, 13, 18, 19")
    args = parser.parse_args()

    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    channel = os.environ.get("CHANNEL", "").strip()
    comments_enabled = os.environ.get("COMMENTS_ENABLED", "false").strip().lower() in ("1", "true", "yes")
    approval_chat_id = os.environ.get("APPROVAL_CHAT_ID", "").strip()  # @Wheres_themoney_Lebowski или ID

    if not bot_token or not channel:
        print("Задайте BOT_TOKEN и CHANNEL в .env", file=sys.stderr)
        sys.exit(1)

    text = get_text_with_llm(args.slot, comments_enabled)
    if not text:
        text = get_text_fallback(args.slot, comments_enabled)

    if not comments_enabled:
        text = strip_comment_phrases(text)

    media_url = get_media_url()

    if args.mode == "draft":
        if not approval_chat_id:
            print("Для режима draft задайте APPROVAL_CHAT_ID в .env (например @Wheres_themoney_Lebowski)", file=sys.stderr)
            sys.exit(1)
        save_draft(text, media_url, args.slot)
        ok = send_message(bot_token, approval_chat_id, f"📋 Черновик поста на 9:00 (слот {args.slot}).\n\nЧтобы опубликовать в канал, ответьте боту: Опубликовать\n\n---\n\n{text}", media_url)
        if ok:
            print("Черновик отправлен на проверку.")
        else:
            sys.exit(1)
        return

    # publish — повторная проверка перед каналом
    if not comments_enabled and ("комментар" in text.lower() or "ответьте ниже" in text.lower()):
        text = strip_comment_phrases(text)
    ok = send_message(bot_token, channel, text, media_url)
    if ok:
        print("Пост успешно отправлен в канал.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
