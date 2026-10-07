"""Run from the repo root or Project directory using the workspace Python.

One tiny live request consumes API quota and may incur charges if billing is
enabled. This checks inference access, not your balance or remaining quota.
"""

import os
import sys
from pathlib import Path

import django
import httpx
from django.core.exceptions import ImproperlyConfigured
from google.genai import errors, types


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent / "Project"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Project.settings")
    try:
        django.setup()
        from app.services.llm import GeminiConfig, create_gemini_client

        config = GeminiConfig.from_settings()
    except ImproperlyConfigured:
        print("CONFIG ERROR: Check .env, including GEMINI_API_KEY and GEMINI_MODEL.")
        return 2

    print(f"Testing Gemini model: {config.model}")
    print("Sending one small request (no dataset contents).")
    try:
        with create_gemini_client(config) as client:
            response = client.models.generate_content(
                model=config.model,
                contents="Reply with exactly: CONNECTION_OK",
                config=types.GenerateContentConfig(
                    max_output_tokens=128,
                    temperature=0,
                    http_options=types.HttpOptions(
                        retry_options=types.HttpRetryOptions(attempts=1)
                    ),
                ),
            )
    except errors.APIError as exc:
        # Do not print raw provider exceptions: they can include sensitive context.
        code = exc.code
        message = (exc.message or "").lower()
        if code == 429:
            print("QUOTA / RATE LIMIT (HTTP 429): Request limit or quota exhausted.")
            print("Check Google AI Studio usage and model quota. Free access may be unavailable;")
            print("this does not by itself establish that payment is required.")
        elif any(word in message for word in ("billing", "payment")):
            print(f"BILLING RESTRICTION (HTTP {code}): Check your project billing status.")
        elif code in (401, 403) or "api key" in message:
            print(f"AUTH / PERMISSION ERROR (HTTP {code}): Check the API key and project access.")
        elif code == 404:
            print("MODEL NOT FOUND (HTTP 404): Check GEMINI_MODEL and API availability.")
        elif code == 400:
            print("REQUEST ERROR (HTTP 400): Model or generation settings may be unsupported.")
        elif code and code >= 500:
            print(f"PROVIDER ERROR (HTTP {code}): Gemini is temporarily unavailable.")
        else:
            print(f"API ERROR (HTTP {code}): Check project status in Google AI Studio.")
        return 3
    except httpx.TimeoutException:
        print("TIMEOUT: Gemini did not respond within the configured timeout.")
        return 4
    except httpx.HTTPError:
        print("NETWORK ERROR: Check internet, proxy, firewall, and TLS configuration.")
        return 4

    if not response.text or not response.text.strip():
        print("API REACHED, BUT NO TEXT: Response may have been blocked or output exhausted.")
        return 5
    if response.text.strip() != "CONNECTION_OK":
        print("API WORKING: Text received, but it did not match the test instruction.")
        return 5
    print("SUCCESS: Gemini authentication, model access, and text generation work.")
    print("This does not guarantee future quota or structured-plan compatibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
