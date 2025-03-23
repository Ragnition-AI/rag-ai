import operator
from typing_extensions import TypedDict
from typing import List, Annotated
from langchain.schema import Document


class ChatMessage(TypedDict):
    role: str  # "human" or "assistant"
    content: str

class GraphState(TypedDict):
    question: str  # User question
    generation: str  # LLM generation
    web_search: str  # Binary decision to run web search
    max_retries: int
    answers: int  # Number of answers generated
    loop_step: Annotated[int, operator.add]
    documents: List[Document]
    chat_history: List[ChatMessage]  # Chat history