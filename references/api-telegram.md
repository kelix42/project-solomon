# Telegram — owner interface (Hermes gateway adapter)

Telegram is **not** a Solomon plugin. It's the Hermes gateway built-in adapter. Solomon configures it via `hermes gateway setup` during install.

## Setup

1. BotFather (on Telegram): create a bot, get the token.
2. `install.sh` step 5: pick "Telegram" in the optional integrations menu. Provide `TELEGRAM_BOT_TOKEN`.
3. Send `/start` to the bot from your account; the gateway captures `TELEGRAM_CHAT_ID`.
4. Hermes gateway service runs continuously (`hermes gateway start` via launchd/systemd).

## How Solomon participates

A Hermes plugin (`hermes-plugins/solomon-pipeline-injector/`) registers a `pre_llm_call` hook. Inbound:

- Text → `db.events` row with `source = telegram`, payload = the text. Pipeline-tick worker processes.
- Voice → transcribed via §2.5 backend, then same flow.
- Document/image → saved to `corpus/inbox/<routed-category>/`. No event (bulk-corpus path).
- Inline button callback → routed per the original message intent.

Outbound: built-in Hermes tools (`send_message`, `send_inline_keyboard`).

## Auth + rate

`TELEGRAM_CHAT_ID` allowlist enforced by Hermes gateway. Telegram-imposed rate limit: 1 message / 5s per chat; gateway handles backpressure.
