from typing import Literal
from pydantic import BaseModel


class CompletionBase(BaseModel):
    prompt: str
    system_prompt: str = (
        "You're a helpful assistant. Be concise and to the point, but don't omit details."
    )
    model: Literal["tinyllama-1.1b-chat-v1.0.Q4_K_M", "qwen2-beta-0_5b-chat-q8_0"]


class CreateCompletion(CompletionBase):
    pass


class QueueCompletion(BaseModel):
    command: list[str]
    connection_id: str
