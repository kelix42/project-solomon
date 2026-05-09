# Supervisor units

`install.sh` writes these unit files into the right OS location:

## macOS (launchd)

- `~/Library/LaunchAgents/io.solomon.hermes-gateway.plist`
- `~/Library/LaunchAgents/io.solomon.worker.plaud-ingest.plist`
- `~/Library/LaunchAgents/io.solomon.worker.corpus-inbox-watcher.plist`
- `~/Library/LaunchAgents/io.solomon.worker.pipeline-tick.plist`

Loaded via `launchctl load <plist>`.

## Linux (systemd --user)

- `~/.config/systemd/user/solomon-hermes-gateway.service`
- `~/.config/systemd/user/solomon-worker-plaud-ingest.service`
- `~/.config/systemd/user/solomon-worker-corpus-inbox-watcher.service`
- `~/.config/systemd/user/solomon-worker-pipeline-tick.service`

Loaded via `systemctl --user daemon-reload && systemctl --user enable --now <service>`.

## Templates

`io.solomon.worker.template.plist` and `solomon-worker.template.service` use placeholders that `install.sh` substitutes:

- `__SLUG__` — worker slug (plaud-ingest / corpus-inbox-watcher / pipeline-tick)
- `__MODULE__` — Python module name (plaud_ingest / corpus_inbox_watcher / pipeline_tick)
- `__SOLOMON_ROOT__` — absolute path to this repo
- `__HOME__` — `$HOME`
- `__PYTHON__` — `which python3` output

## Health check

`solomon-setup` skill checks `launchctl list | grep io.solomon` (macOS) or `systemctl --user list-units 'solomon-*'` (Linux). Missing units re-install on next `bash install.sh` run.
