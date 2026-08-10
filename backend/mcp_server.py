#!/usr/bin/env python
"""MCP server exposing the Upsell Machine tools.

The hackathon brief's provocation is to build "without relying on our current frontend
platforms". This is that taken to its conclusion: the same tools the in-app agent uses,
published over the Model Context Protocol so *any* MCP client -- Claude Desktop, an
IDE, another agent -- can query the upsell workflow with no UI of ours involved.

It's a second entry point, not a second implementation. Every tool here delegates to
the same functions in app/services/agent_tools.py that back the Ask tab, so the two
can't drift apart.

Run it directly for stdio transport:

    .venv/Scripts/python mcp_server.py

Or point Claude Desktop at it -- see MCP.md for the config block.
"""

import sys
from pathlib import Path

# Allow running as a script from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server import MCPServer  # noqa: E402

from app.services import agent_tools  # noqa: E402

mcp = MCPServer(
    name="upsell-machine",
    title="Upsell Machine — SecurityScorecard Customer Success",
    version="0.1.0",
    instructions=(
        "Tools for Customer Success work on a SecurityScorecard portfolio: which accounts "
        "need attention, why, and who to contact.\n\n"
        "Work in two passes. Call list_customers once to survey the portfolio cheaply, then "
        "call get_customer_detail only for the two to four accounts that matter for the "
        "question -- list_customers reports how many signals fired, not what they were.\n\n"
        "Platform usage figures are placeholder sample data, not a live feed. Say so if you "
        "cite them. Everything else -- scores, grades, industries, supplier detection -- is "
        "live SecurityScorecard data."
    ),
)


@mcp.tool()
def list_customers() -> list[dict]:
    """Survey the whole portfolio: one compact line per customer with score, grade,
    industry, assigned CSM and signal level. Start here."""
    return agent_tools.list_customers()


@mcp.tool()
def get_customer_detail(customer_id: str) -> dict:
    """Full detail for one account: score history, why its signal fired, platform usage,
    tracked decision-makers and recent news. Use the id from list_customers."""
    return agent_tools.get_customer_detail(customer_id)


@mcp.tool()
def get_opportunities(customer_id: str | None = None) -> list[dict]:
    """Current opportunity cards -- the concrete signals a CSM would act on -- across the
    portfolio, or for one account if customer_id is given."""
    return agent_tools.get_opportunities(customer_id)


@mcp.tool()
def get_supplier_risk(customer_id: str) -> dict:
    """Third-party suppliers detected in a customer's footprint, worst-scoring first.
    Useful for supply-chain risk conversations."""
    return agent_tools.get_supplier_risk(customer_id)


if __name__ == "__main__":
    mcp.run()
