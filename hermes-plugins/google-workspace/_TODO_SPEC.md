# TODO — Google Workspace ingress + tool spec

This plugin needs Plaud-equivalent depth before implementation (§2.4.5 of SOLOMON-PLAN.md).

Required:
- [ ] Gmail watch + 60s backup poller pattern. Need: Gmail API vs IMAP, label/query filter for what counts as ingestable, attachment vs body, target subfolder, idempotency via Gmail message_id, env vars.
- [ ] Calendar events watch + 60s poller. Need: which calendars, what gets serialized (single events / recurring expansions / cancellations), filename per event, idempotency via eventId+sequence.
- [ ] Drive `changes.watch` API + 5-min poller. Need: which folder(s) are watched, MIME-to-category routing rules, file-size cap, idempotency via Drive fileId+revision.
- [ ] Tool surface: `gmail.list_messages`, `gmail.send_message`, `calendar.create_event`, `drive.search_files`, etc.
- [ ] env var list, OAuth flow.

When complete, set `default_enabled: true` in `plugin.yaml`.
