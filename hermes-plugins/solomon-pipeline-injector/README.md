# solomon-pipeline-injector

The bridge between Hermes' Telegram gateway adapter and Solomon's decision pipeline.

Hooks `pre_llm_call`. When a Telegram message reaches the agent, this plugin writes a `db.events` row with `status = pending` for the `pipeline-tick` worker to pick up. The Hermes agent continues responding normally; Solomon's pipeline runs in parallel via the worker.

This is how Solomon stays decoupled from the per-turn agent invocation while still receiving real-time owner messages.
