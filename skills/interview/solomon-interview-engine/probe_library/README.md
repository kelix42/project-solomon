# Probe Library

One YAML per domain. Each declares a semver `version`. **Lower priority number wins** (priority 1 fires before priority 9). Slot `{phrase}` is replaced verbatim with the owner's last phrase.

## Schema

```yaml
domain: <slug>
version: <semver>             # bump per the rules below
priority: <1-10>              # domain-level: how critical for cloning judgment (10 = most critical)
keywords:
  <keyword>:
    - priority: <1-10>        # probe-level within this keyword (lower = fires first)
      template: "<text with {phrase} slot>"
fallbacks:
  - "<generic forward prompt when keywords run dry>"
```

## Semver bump rules

- **Patch** (0.1.0 → 0.1.1) — new templates under existing keywords.
- **Minor** (0.1.0 → 0.2.0) — new keywords.
- **Major** (0.1.0 → 1.0.0) — breaking schema changes (e.g., field rename).

`coverage.library_version_seen` is compared against `version` on launch by `solomon-coverage-tracker`. A bump triggers a `mentoring_queue` row (`source = probe_library_update`, priority 7) so the owner can opt into a re-probe.

## Files

- `pricing.yaml`
- `hiring.yaml`
- `ops.yaml`
- `customer.yaml`
- `vendor.yaml`
- `finance.yaml`
- `_generic.yaml` — cross-domain fallback prompts when a domain's keywords + fallbacks all run dry.
