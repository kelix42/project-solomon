# Template worker

Copy this folder to make a long-lived background service. Workers are NOT Hermes plugins — they're separate Python processes supervised by launchd/systemd.

Use this for: IMAP listeners, file watchers, REST pollers, real-time pipelines. See §2.4.6.5.

For agent-conversation extensions (tools, hooks, slash commands), copy `hermes-plugins/_template-hermes-plugin/` instead.
