# Template Hermes Plugin

Copy this folder, rename, edit `plugin.yaml`, implement `register(ctx)` in `__init__.py`. Set `default_enabled: true` when ready.

Use only the verified API surface (§2.4.6 of SOLOMON-PLAN.md). Long-lived state or services belong in `workers/_template-worker/`, not here.
