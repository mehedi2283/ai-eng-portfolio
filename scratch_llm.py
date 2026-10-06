from openai import OpenAI

from triage.config import Settings

s = Settings()
client = OpenAI(api_key=s.openai_api_key)
r = client.chat.completions.create(
    model=s.model_name,
    messages=[{"role": "user", "content": "Say hi in 3 words"}],
)
print(r.choices[0].message.content)