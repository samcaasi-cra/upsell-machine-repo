# MCP server

The hackathon brief's provocation is to build *"without relying on our current frontend
platforms."* This is that taken to its conclusion: the same tools the in-app agent uses,
published over the **Model Context Protocol**, so any MCP client can query the upsell
workflow with **no UI of ours involved at all**.

A CSM opens Claude Desktop and asks *"which of my accounts need attention today?"* —
and gets an answer grounded in live SecurityScorecard data.

It's a second **entry point**, not a second implementation. Every tool delegates to the
same functions in `app/services/agent_tools.py` that back the `/agent/chat` endpoint, so
the two can't drift apart.

Since the board doesn't link to the agent, **this is the primary way to reach it** — and
the clearest demonstration that the workflow isn't tied to any interface we built.

---

## Tools exposed

| Tool | Purpose |
|---|---|
| `list_customers` | Survey the portfolio — one compact line per customer |
| `get_customer_detail` | Everything about one account: score history, signals, usage, decision-makers, news |
| `get_opportunities` | Current opportunity cards, all accounts or one |
| `get_supplier_risk` | Detected third-party suppliers, worst-scoring first |

The server also ships **instructions** telling the client to survey first and drill only
into what matters — the same two-pass discipline the in-app agent follows, so a
connected client is token-efficient by default rather than fetching everything.

---

## Connecting Claude Desktop

Add this to your Claude Desktop config:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "upsell-machine": {
      "command": "C:\\Users\\PC\\Desktop\\Hackathon\\backend\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\PC\\Desktop\\Hackathon\\backend\\mcp_server.py"]
    }
  }
}
```

Use absolute paths and your own venv location. On macOS/Linux the interpreter is
`.venv/bin/python`. Restart Claude Desktop after editing; the tools appear under the
connector menu.

`API_KEY` is read from `backend/.env` as usual — the server loads it the same way the
web app does.

---

## Running it directly

```bash
cd backend
.venv/Scripts/python mcp_server.py
```

It speaks MCP over stdio and will sit waiting for a client, which is expected — there's
nothing to see in the terminal.

---

## Things worth knowing

**No pseudonymisation on this path.** The in-app agent masks customer identities before
calling a third-party model. Here the *client* is the model host, so masking would break
the tool contract — the client needs real ids to call `get_customer_detail`. Whoever
connects a client is choosing where that data goes, which is why this is aimed at
sanctioned internal tooling rather than arbitrary clients.

**Read-only.** Nothing here writes, triggers research, or spends money. Worst case a
client reads customer data it was already entitled to.

**Reuses the live SSC client**, including its 10-minute response cache, so a chatty
client doesn't hammer the API.
