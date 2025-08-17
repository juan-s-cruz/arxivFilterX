import os
import logging as log

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from huggingface_hub import InferenceClient


logging = log.getLogger(__name__)
transformers.logging.set_verbosity_error()

if torch.cuda.is_available():
    torch.device("cuda:0")

model_location = "llm_search/models"

tokenizer = AutoTokenizer.from_pretrained(model_location)

model = AutoModelForCausalLM.from_pretrained(
    model_location, torch_dtype=torch.float16, device_map="auto"
)


system_role = """
You are an expert physicist and can elaborate on any topic related to physics. 
Given a subfield of physics, you will provide a detailed explanation of the topic in 
a small text of maximum two paragraphs.
"""

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

generation_args = {
    "max_new_tokens": 500,
    "return_full_text": False,
    # "temperature": 0.01,
    "do_sample": False,
}


def call_llm(topic: str) -> str:
    """
    Call the LLM with a given topic and return the generated text.

    Args:
        topic (str): The topic to generate text about.
    """
    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": topic},
    ]
    output = pipe(messages, **generation_args)
    return output[-1]["generated_text"]
