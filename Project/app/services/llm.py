"""Gemini client configuration. No API requests occur on module import."""

from dataclasses import dataclass, field

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google import genai
from google.genai import types


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str = field(repr=False)
    model: str
    timeout_seconds: int
    max_output_tokens: int
    temperature: float

    @classmethod
    def from_settings(cls):
        config = cls(
            api_key=settings.GEMINI_API_KEY.strip(),
            model=settings.GEMINI_MODEL.strip(),
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
            max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            temperature=settings.GEMINI_TEMPERATURE,
        )
        if not config.api_key or not config.model:
            raise ImproperlyConfigured("Set GEMINI_API_KEY and GEMINI_MODEL in .env.")
        if config.timeout_seconds <= 0 or config.max_output_tokens <= 0:
            raise ImproperlyConfigured("Gemini timeout and output token limit must be positive.")
        if not 0 <= config.temperature <= 2:
            raise ImproperlyConfigured("GEMINI_TEMPERATURE must be between 0 and 2.")
        return config

    def generation_options(self):
        return types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )


def create_gemini_client(config=None):
    """Caller must close the client, preferably using `with`.

    Explicit Developer API selection prevents unrelated Vertex configuration
    from changing the provider. The SDK HTTP timeout is in milliseconds.
    """
    config = config or GeminiConfig.from_settings()
    return genai.Client(
        api_key=config.api_key,
        vertexai=False,
        http_options=types.HttpOptions(timeout=config.timeout_seconds * 1000),
    )
