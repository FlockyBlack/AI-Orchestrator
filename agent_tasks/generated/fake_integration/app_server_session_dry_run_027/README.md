# ORCH 027 app-server session dry-run integration

Этот артефакт фиксирует две части проверки.

1. Fake app-server integration: `generated/manual_app_server_dry_run/20260511T132652Z/app_server_dry_runs/20260511T132652Z/`
   - процесс стартовал;
   - минимальный initialize probe прошел;
   - stdout/stderr/result сохранены;
   - процесс остановлен.

2. Real app-server readiness check: `real_app_server_readiness_check.json`
   - команда рендерится как `codex app-server --listen stdio://`;
   - реальный app-server был запущен один раз через явный `--operator-approved` dry-run;
   - минимальный initialize probe прошел;
   - процесс остановлен чисто;
   - артефакты: `real/generated/manual_app_server_dry_run/20260511T132728Z/app_server_dry_runs/20260511T132728Z/`.

Проверка не создает daemon, scheduler, background worker, browser automation flow, authenticated flow, OpenRouter/Polymarket вызовы, wallet/signing или торговые действия.
