import asyncio
import json

import pytest

from fakes import FakeChatClient, text_msg, tool_msg
from triage.agent import AgentError, run_agent


def run(client, question="hi", **kw):
    return asyncio.run(run_agent(client, "fake-model", question, **kw))


def test_answer_without_tools():
    c = FakeChatClient([text_msg("hello")])
    assert run(c) == "hello"
    assert c.calls == 1


def test_tool_call_then_answer():
    c = FakeChatClient(
        [tool_msg("get_order_status", {"order_id": "A-1002"}), text_msg("Shipped.")]
    )
    assert run(c) == "Shipped."
    assert c.calls == 2
    last = c.seen[1][-1]
    assert last["role"] == "tool"
    assert json.loads(last["content"])["status"] == "shipped"


def test_multi_step_chain():
    c = FakeChatClient(
        [
            tool_msg("lookup_customer", {"email": "john@acme.com"}, id="c1"),
            tool_msg("get_order_status", {"order_id": "A-1002"}, id="c2"),
            text_msg("John's order has shipped."),
        ]
    )
    assert run(c) == "John's order has shipped."
    assert c.calls == 3


def test_unknown_tool_error_goes_back_to_model():
    c = FakeChatClient([tool_msg("delete_everything", {}), text_msg("Sorry.")])
    run(c)
    assert "unknown tool" in c.seen[1][-1]["content"]


def test_bad_arguments_error_goes_back_to_model():
    c = FakeChatClient([tool_msg("get_order_status", {"wrong": 1}), text_msg("ok")])
    run(c)
    assert "invalid arguments" in c.seen[1][-1]["content"]


def test_max_steps_guard():
    c = FakeChatClient([tool_msg("get_order_status", {"order_id": "A-1001"}) for _ in range(3)])
    with pytest.raises(AgentError):
        run(c, max_steps=3)
    assert c.calls == 3