import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from triage.retry import with_retries

log = logging.getLogger(__name__)

CUSTOMERS = {
    "john@acme.com": {"name": "John Smith", "plan": "pro", "latest_order_id": "A-1002"},
    "sarah@gmail.com": {"name": "Sarah Lee", "plan": "free", "latest_order_id": None},
}
ORDERS = {
    "A-1001": {"status": "delivered", "total": 120.0},
    "A-1002": {"status": "shipped", "total": 480.0, "eta": "2026-10-10"},
}


class LookupCustomerArgs(BaseModel):
    email: str


class OrderStatusArgs(BaseModel):
    order_id: str


def lookup_customer(args: LookupCustomerArgs) -> dict:
    return CUSTOMERS.get(args.email.lower()) or {"error": "customer not found"}


def get_order_status(args: OrderStatusArgs) -> dict:
    return ORDERS.get(args.order_id) or {"error": "order not found"}


TOOL_IMPLS = {
    "lookup_customer": (LookupCustomerArgs, lookup_customer),
    "get_order_status": (OrderStatusArgs, get_order_status),
}
DESCRIPTIONS = {
    "lookup_customer": "Find a customer by email. Returns name, plan and latest_order_id.",
    "get_order_status": "Get the status of an order by its order_id.",
}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": DESCRIPTIONS[name],
            "parameters": model.model_json_schema(),
        },
    }
    for name, (model, _) in TOOL_IMPLS.items()
]

SYSTEM_PROMPT = (
    "You are a support assistant. Use the tools to look up facts. "
    "Never guess order or customer data. If no tool can do what is asked, say so."
)


class AgentError(Exception):
    """Agent did not finish within max_steps."""


def run_tool(name: str, arguments: str) -> str:
    if name not in TOOL_IMPLS:
        return json.dumps({"error": f"unknown tool {name}"})
    model, fn = TOOL_IMPLS[name]
    try:
        args = model.model_validate_json(arguments)
    except ValidationError as e:
        return json.dumps({"error": "invalid arguments", "detail": str(e)[:300]})
    try:
        return json.dumps(fn(args))
    except Exception as e:  # tool bugs go back to the model, not crash the loop
        log.exception("tool %s failed", name)
        return json.dumps({"error": f"tool failed: {type(e).__name__}"})


async def run_agent(
    client: AsyncOpenAI, model: str, question: str, max_steps: int = 5
) -> str:
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    for step in range(1, max_steps + 1):
        r = await with_retries(
            lambda: client.chat.completions.create(
                model=model, messages=messages, tools=TOOLS
            )
        )
        msg = r.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        messages.append(
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
            log.info("step %d: %s(%s)", step, tc.function.name, tc.function.arguments)
            result = run_tool(tc.function.name, tc.function.arguments)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    raise AgentError(f"no final answer after {max_steps} steps")