# Бот без API-ключа (Ollama)

Если нет Groq/OpenAI ключа, бот можно перевести на **Ollama** — локальная модель на сервере, ключ не нужен.

## Деплой через Git (рекомендуется)

1. **У себя:** закоммитьте изменения и запушьте в репозиторий.
   ```bash
   cd channel-poster
   git add -A && git status
   git commit -m "Ollama: скрипт и инструкции"
   git push
   ```

2. **На VPS (первый раз):** клонируйте репозиторий в `/opt/channel-poster` (если ещё не клонирован).
   ```bash
   ssh root@ВАШ_VPS
   # Если /opt/channel-poster пустой или не репозиторий:
   git clone https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПО.git /opt/channel-poster
   cd /opt/channel-poster
   ```
   На сервере в `/opt/channel-poster` должен лежать `.env` (BOT_TOKEN, CHANNEL и т.д.) — скопируйте его вручную один раз или создайте из `.env.example`.

3. **На VPS:** подтяните код и запустите скрипт.
   ```bash
   ssh root@ВАШ_VPS 'cd /opt/channel-poster && git pull && bash setup_ollama_for_openclaw.sh'
   ```

Дальше при любых правках: `git push` у себя → на VPS `cd /opt/channel-poster && git pull` (и при необходимости перезапуск сервисов).

## На VPS без Git (один раз)

Если репозиторий на сервер не клонируете, скопируйте только скрипт и выполните под **root**:
```bash
# С вашего компьютера (из каталога channel-poster):
scp setup_ollama_for_openclaw.sh root@ВАШ_VPS:/root/
ssh root@ВАШ_VPS 'bash /root/setup_ollama_for_openclaw.sh'
```

Скрипт при этом:
- ставит Ollama и запускает сервис;
- качает модель **llama3.2** (~2 GB);
- добавляет `OLLAMA_API_KEY=ollama-local` в `/opt/channel-poster/.env`;
- подключает этот `.env` к сервису openclaw (если ещё не подключён);
- переключает модель агента на `ollama/llama3.2` и перезапускает OpenClaw.

**Если после скрипта** бот всё ещё пишет про "No API key for provider groq":
   - откройте на сервере `/root/.openclaw/openclaw.json`;
   - найдите `agents.defaults.model.primary` (или вложенное `model.primary`) и замените значение на `"ollama/llama3.2"`;
   - выполните: `systemctl restart openclaw`.

## Требования к серверу

- Минимум ~2.5 GB свободной RAM для llama3.2 (3B). Если памяти мало, можно поставить меньшую модель:
  ```bash
  ollama pull llama3.2:1b
  ```
  и в конфиге указать `ollama/llama3.2:1b`.

## Проверка

- `ollama list` — должна быть модель llama3.2.
- `curl -s http://127.0.0.1:11434/api/tags` — Ollama отвечает.
- Напишите боту в Telegram — должен ответить.
