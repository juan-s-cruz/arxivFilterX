import logging as log

logging = log.getLogger(__name__)

from huggingface_hub import InferenceClient

import os

client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
    # provider="auto",   # Automatically selects best provider
)

# Chat completion
response = client.chat.completions.create(
    model="microsoft/phi-4",
    messages=[{"role": "user", "content": "A story about hiking in the mountains"}],
)


def call_llm():
    return response.choices[0].message["content"]
