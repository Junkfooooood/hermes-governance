"""三省六部治理框架插件."""

from .governance_hook import on_pre_tool_call
from .governance_tool import GOVERNANCE_COMMITTEE_SCHEMA, governance_committee_handler


def register(ctx) -> None:
    """Register governance hooks and tools with the plugin system."""
    # Hook: intercept delegate_task in strict mode
    ctx.register_hook("pre_tool_call", on_pre_tool_call)

    # Tool: governance_committee
    ctx.register_tool(
        name="governance_committee",
        toolset="governance",
        schema=GOVERNANCE_COMMITTEE_SCHEMA,
        handler=governance_committee_handler,
        description="通过三省六部治理链执行任务",
        emoji="⚖️",
    )
