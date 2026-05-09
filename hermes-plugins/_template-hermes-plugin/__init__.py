"""Template Hermes plugin for Solomon.

Verified API surface only (§2.4.6 of SOLOMON-PLAN.md):
  ctx.register_tool(name, schema, handler, toolset=None, check_fn=None)
  ctx.register_command(name, handler, description="")
  ctx.register_cli_command(name, help, setup_fn, handler_fn)
  ctx.register_skill(name, path)
  ctx.register_hook(hook_name, callback)
  ctx.dispatch_tool(name, arguments)
  ctx.inject_message(content, role="user")

NOT provided by Hermes (plugin must implement itself):
  - ctx.subscribe / ctx.schedule / ctx.db / ctx.pinecone / ctx.telegram / ctx.env / ctx.logger
  - ctx.invoke_skill (skills are LLM-readable markdown, not Python-callable)
  - ctx.lock / ctx.on_unload (plugins are stateless event handlers)

For long-lived state or services, copy `workers/_template-worker/` instead.
"""
import os


def register(ctx):
    """Called once on Hermes startup. Wire everything here."""
    # Example: register a tool the agent can call
    # ctx.register_tool(
    #     name="my_tool",
    #     schema={"type": "function", "function": {"name": "my_tool", "parameters": {...}}},
    #     handler=my_tool_handler,
    # )

    # Example: register a hook
    # ctx.register_hook("post_llm_call", on_llm_response)

    # Example: register a slash command for Telegram / CLI
    # ctx.register_command("my-command", my_command_handler, description="What it does")
    pass


def my_tool_handler(args):
    """Tool handler signature: takes a dict of args, returns a string or dict."""
    return {"ok": True}


def on_llm_response(session_id, user_message, assistant_response, **kwargs):
    """Hook signature varies; see §2.4.6 for the full list."""
    pass
