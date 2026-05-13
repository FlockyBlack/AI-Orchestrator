# ORCH-PMBOT-TRADING-MVP-046G Telegram RU UX and Local Mini App Dev Mode

## Быстрый старт на русском

1. Сгенерируй или найди локальные артефакты Mini App: `telegram_mini_app_operator_panel_044.html` и `telegram_mini_app_operator_panel_044.json`.
2. Для простого просмотра открой HTML-файл локально в браузере. Это статичная review-only панель; она не включает торговлю.
3. Для проверки через Telegram Mini App подними локальный HTTP-сервер из директории с артефактами:

```powershell
python -m http.server 8080
```

4. Подними временный HTTPS-туннель к локальному серверу одним из вариантов:

```powershell
cloudflared tunnel --url http://localhost:8080
```

```powershell
ngrok http 8080
```

5. Скопируй выданный HTTPS URL и задай его в `PMBOT_TELEGRAM_MINI_APP_URL`.

В текущем PowerShell-окне:

```powershell
$env:PMBOT_TELEGRAM_MINI_APP_URL = "https://example-tunnel.example"
```

Для Windows User environment:

```powershell
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_MINI_APP_URL", "https://example-tunnel.example", "User")
```

6. Перезапусти Telegram runtime. Если он уже запущен, останови его через `Ctrl+C`, открой новый терминал после изменения User environment и запусти:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

7. В Telegram нажми `/start`, выбери `🇷🇺 Русский`, затем открой `🧩 Mini App` или `/panel`.

## English Operator Notes

To preview the Mini App without Telegram, open the generated `telegram_mini_app_operator_panel_044.html` artifact directly in a browser.

To test Telegram Mini App launch locally without buying a domain, serve the artifact directory:

```powershell
python -m http.server 8080
```

Then expose that local server through a temporary HTTPS tunnel:

```powershell
cloudflared tunnel --url http://localhost:8080
```

or:

```powershell
ngrok http 8080
```

Set the tunnel URL:

```powershell
$env:PMBOT_TELEGRAM_MINI_APP_URL = "https://example-tunnel.example"
```

Restart the Telegram runtime:

```powershell
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Temporary tunnel URLs usually change after restart. When the tunnel URL changes, update `PMBOT_TELEGRAM_MINI_APP_URL` and restart the Telegram runtime again.

## Safety

The Telegram bot and Mini App remain review-only. This local Mini App workflow does not enable trading, live order submission, wallet integration, signing, authenticated Polymarket calls, or autonomous execution. Telegram pause and kill-switch actions remain local operator-control markers only.
