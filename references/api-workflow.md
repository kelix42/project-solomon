# Workflow Orchestrator — n8n / make.com

`hermes-plugins/workflow-bridge/` — single plugin accepts both n8n and make.com via webhook.

## Required env vars

- `WORKFLOW_WEBHOOK_URL` — the workflow's incoming webhook endpoint
- (optional) `WORKFLOW_HMAC_SECRET` — HMAC-SHA256 signing for the request body

## Tool exposed

`workflow.trigger(scenario_id, payload)` — POSTs JSON to the webhook URL.

## Inbound (deferred to v2.1)

A workflow can call back into Solomon via a webhook receiver (Hermes gateway's `webhook` adapter). The plugin scaffold ships with `_TODO_SPEC.md` for the inbound flow.

## v1 status

Plugin scaffold + `_TODO_SPEC.md`. Owner provides `WORKFLOW_WEBHOOK_URL` + scenario ID conventions before this is wired.
