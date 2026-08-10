"""Tool-calling agent over the customer dataset.

The distinction that matters: the research pipeline in web_research.py is a *function*
-- text in, JSON out, one shot. This is an *agent*: it's given tools and decides for
itself which to call, in what order, and when it has enough to answer.

Provider-agnostic on purpose. It runs on OpenAI today and on Anthropic the moment a
token exists (the SSC-issued Claude Code token the hackathon brief mentions), because
which model backs it shouldn't be baked into the workflow.

Token accounting is returned with every reply -- partly because the hackathon judges on
it, mostly because an agent whose cost you can't see is one you can't put in production.
"""

import json
import os
from typing import Optional

from . import agent_tools
from .redaction import Pseudonymiser

_MAX_ITERATIONS = 6  # a runaway loop is the main cost risk with tool-calling

SYSTEM_PROMPT = """You are a Customer Success assistant for SecurityScorecard, helping a \
CSM decide where to spend their time.

You have tools over live customer data. Work in two passes:
1. SURVEY -- call list_customers once to see the whole portfolio cheaply.
2. DRILL -- pick the 2-4 accounts that matter for the question and call
   get_customer_detail on each. You need this: list_customers only tells you HOW MANY
   reasons fired, not what they were, and a CSM needs the actual reason.

Never answer with vague phrases like "5 reasons noted" -- if you find yourself about to
say that, you skipped the drill step. Go get the detail first.

Don't call get_customer_detail on all thirteen accounts; that's wasteful. Two to four
is right.

Rules:
- Ground every claim in tool output. Never invent scores, names, or events.
- Platform usage data is placeholder sample data, not a live feed. If you cite it, say so.
- Be concise and practical. A CSM wants to know who to contact and why, not a report.
- If asked to draft outreach, keep it short, specific, and free of hype.

Customers and people appear as labels (CUST_A, PERSON_1) rather than names, for data
protection. Use those labels exactly as given -- they are substituted back to real
names before the reader sees your answer. Never guess at or invent a real name."""


def is_configured() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))


def active_provider() -> Optional[str]:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return None


def _run_openai(messages: list[dict], masker: Pseudonymiser) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("AGENT_MODEL", "gpt-4o-mini")

    # The user's own question can name a customer, so it gets redacted too.
    convo = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": masker.redact(m["content"])} for m in messages
    ]
    tool_calls_made: list[dict] = []
    prompt_tokens = completion_tokens = 0

    for _ in range(_MAX_ITERATIONS):
        resp = client.chat.completions.create(
            model=model,
            messages=convo,
            tools=agent_tools.openai_schemas(),
        )
        if resp.usage:
            prompt_tokens += resp.usage.prompt_tokens
            completion_tokens += resp.usage.completion_tokens

        msg = resp.choices[0].message
        if not msg.tool_calls:
            return {
                "reply": masker.restore(msg.content or ""),
                "tool_calls": tool_calls_made,
                "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
                "provider": "openai",
                "model": model,
            }

        convo.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = agent_tools.call(tc.function.name, args)
            tool_calls_made.append({"tool": tc.function.name, "arguments": args})
            # Redact on the way out -- this is the payload that actually leaves us.
            safe = masker.redact(result)
            convo.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(safe, default=str)})

    return {
        "reply": "I wasn't able to finish that within the tool-call limit — try narrowing the question.",
        "tool_calls": tool_calls_made,
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "provider": "openai",
        "model": model,
    }


def _run_anthropic(messages: list[dict], masker: Pseudonymiser) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("AGENT_MODEL", "claude-sonnet-5")

    convo = [{"role": m["role"], "content": masker.redact(m["content"])} for m in messages]
    tool_calls_made: list[dict] = []
    prompt_tokens = completion_tokens = 0

    for _ in range(_MAX_ITERATIONS):
        resp = client.messages.create(
            model=model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=convo,
            tools=agent_tools.anthropic_schemas(),
        )
        prompt_tokens += resp.usage.input_tokens
        completion_tokens += resp.usage.output_tokens

        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {
                "reply": masker.restore(text),
                "tool_calls": tool_calls_made,
                "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
                "provider": "anthropic",
                "model": model,
            }

        convo.append({"role": "assistant", "content": resp.content})
        results = []
        for tu in tool_uses:
            result = agent_tools.call(tu.name, dict(tu.input))
            tool_calls_made.append({"tool": tu.name, "arguments": dict(tu.input)})
            safe = masker.redact(result)
            results.append(
                {"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(safe, default=str)}
            )
        convo.append({"role": "user", "content": results})

    return {
        "reply": "I wasn't able to finish that within the tool-call limit — try narrowing the question.",
        "tool_calls": tool_calls_made,
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "provider": "anthropic",
        "model": model,
    }


def run(messages: list[dict]) -> dict:
    """messages: [{role: 'user'|'assistant', content: str}, ...]

    Customer and person identities are pseudonymised before anything leaves this
    process and restored on the way back, so the model never receives a real name
    joined to a security score.
    """
    provider = active_provider()
    masker = Pseudonymiser()
    if provider == "anthropic":
        result = _run_anthropic(messages, masker)
    elif provider == "openai":
        result = _run_openai(messages, masker)
    else:
        raise RuntimeError("No model configured — set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
    result["pseudonymised"] = True
    return result
