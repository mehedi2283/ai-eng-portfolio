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