#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единая точка вызова LLM для постов. Порядок: Groq (бесплатно) → OpenRouter (есть бесплатные модели) → OpenAI.
Переменные: GROQ_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY.
"""

import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_env():
    env_path = SCRIPT_DIR / ".env"
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_completion(prompt: str, max_tokens: int = 1000) -> str | None:
    """
    Генерирует текст через LLM. Пробует по порядку: Groq → OpenRouter → OpenAI.
    Возвращает None при ошибке или отсутствии ключей.
    """
    _load_env()
    messages = [{"role": "user", "content": prompt}]
    payload = {"messages": messages, "max_tokens": max_tokens}

    # 1. Groq (бесплатный тир, быстрый)
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={**payload, "model": "llama-3.1-8b-instant"},
                timeout=60,
            )
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if text:
                return text
        except Exception as e:
            if "requests" in sys.modules:
                print(f"Groq: {e}", file=sys.stderr)

    # 2. OpenRouter (много бесплатных моделей: openrouter.ai)
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if or_key:
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json", "HTTP-Referer": "https://xn----7sbb8agcekdfh2j.online"},
                json={**payload, "model": "meta-llama/llama-3.1-8b-instruct:free"},
                timeout=60,
            )
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if text:
                return text
        except Exception as e:
            if "requests" in sys.modules:
                print(f"OpenRouter: {e}", file=sys.stderr)

    # 3. OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={**payload, "model": "gpt-4o-mini"},
                timeout=60,
            )
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if text:
                return text
        except Exception as e:
            if "requests" in sys.modules:
                print(f"OpenAI: {e}", file=sys.stderr)

    return None
