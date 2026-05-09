# TODO — workflow-bridge spec

Required (§2.4.5 depth):
- [ ] Outbound: tool exposed to agent (`workflow.trigger(scenario_id, payload)`).
- [ ] Inbound: webhook receiver via Hermes gateway's webhook adapter; payload schema; HMAC auth (`WORKFLOW_HMAC_SECRET`); scenario-to-category routing for `corpus/inbox/`; idempotency via scenario+run_id.
- [ ] env vars beyond `WORKFLOW_WEBHOOK_URL`.
