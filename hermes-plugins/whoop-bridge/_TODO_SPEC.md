# TODO — whoop-bridge spec

Required (§2.4.5 depth):
- [ ] OAuth + 5-min REST poller. Confirm: writes direct to db.biometrics (skips corpus/inbox/), or also drops a daily JSON in inbox/data/?
- [ ] Which metrics: recovery_pct, sleep_hours, strain, stress_flag, raw_payload?
- [ ] Refresh-token storage (Hermes OAuth manager).
- [ ] Polling cadence + backoff under rate-limit.
