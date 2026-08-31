"""
LLM service module.

Provides a configured LLM instance with automatic fallback between
free OpenRouter models so a single overloaded provider doesn't break
the entire pipeline.
"""

from langchain_openai import ChatOpenAI
from config.settings import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Ordered list of free OpenRouter models — first available wins
_FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/free",   # last resort: random available free model
]


def _make_llm(model: str) -> ChatOpenAI:
    """Build a ChatOpenAI instance for the given model."""
    return ChatOpenAI(
        model=model,
        api_key=Config.LLM_API_KEY,
        base_url=Config.LLM_BASE_URL,
        temperature=Config.LLM_TEMPERATURE,
        max_retries=0,          # we handle retries ourselves across models
        timeout=Config.LLM_TIMEOUT,
    )


class _FallbackLLM:
    """
    Wraps multiple LLM instances.  On invoke(), tries each model in order
    and returns the first successful response.  Raises the last error only
    if all models fail.
    """

    def __init__(self):
        # Primary model from config, then the fallback list (deduped)
        primary = Config.LLM_MODEL
        models = [primary] + [m for m in _FALLBACK_MODELS if m != primary]
        self._models = models

    def invoke(self, prompt):
        last_err = None
        for model in self._models:
            try:
                llm = _make_llm(model)
                result = llm.invoke(prompt)
                if model != self._models[0]:
                    logger.info(f"LLM fallback succeeded with: {model}")
                return result
            except Exception as e:
                logger.warning(f"LLM model {model!r} failed: {type(e).__name__}: {str(e)[:120]}")
                last_err = e
        raise last_err


_instance = None


def get_llm() -> _FallbackLLM:
    """Return the shared LLM instance (singleton)."""
    global _instance
    if _instance is None:
        _instance = _FallbackLLM()
        logger.info(f"LLM service initialised. Primary model: {Config.LLM_MODEL}")
    return _instance
