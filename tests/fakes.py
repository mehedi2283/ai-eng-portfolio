import json
from types import SimpleNamespace


class FakeClient:
    """Mimics client.chat.completions.parse(...). Each call returns the next scripted reply."""

    def __init__(self, replies: list):
        self.replies = list(replies)
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(parse=self._parse))

    async def _parse(self, **kwargs):
        self.calls += 1
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, dict) and "refusal" in item:
            message = SimpleNamespace(content=None, parsed=None, refusal=item["refusal"])
        else:
            # like the real SDK: raises ValidationError if the reply doesn't fit the model
            parsed = kwargs["response_format"].model_validate_json(item)
            message = SimpleNamespace(content=item, parsed=parsed, refusal=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def text_msg(text: str):
    return SimpleNamespace(content=text, tool_calls=None)


def tool_msg(name: str, args: dict, id: str = "call_1"):
    call = SimpleNamespace(id=id, function=SimpleNamespace(name=name, arguments=json.dumps(args)))
    return SimpleNamespace(content=None, tool_calls=[call])


class FakeChatClient:
    """Mimics client.chat.completions.create(...) with scripted assistant messages."""

    def __init__(self, replies: list):
        self.replies = list(replies)
        self.calls = 0
        self.seen: list[list] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        self.calls += 1
        self.seen.append(list(kwargs["messages"]))
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(choices=[SimpleNamespace(message=item)])