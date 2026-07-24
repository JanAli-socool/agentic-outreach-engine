"""LLM client layer. Groq only. Model routing: cheap vs strong."""
from langchain_groq import ChatGroq
from agent.config import settings


def get_cheap_llm(temperature: float = 0.0) -> ChatGroq:
    """Cheap fast model for classification, verification, routing."""
    return ChatGroq(
        model=settings.cheap_model,
        temperature=temperature,
        api_key=settings.groq_api_key,
        max_retries=2,
        timeout=30,
    )


def get_strong_llm(temperature: float = 0.4) -> ChatGroq:
    """Strong model for final generation. Only used when it matters."""
    return ChatGroq(
        model=settings.strong_model,
        temperature=temperature,
        api_key=settings.groq_api_key,
        max_retries=2,
        timeout=60,
    )