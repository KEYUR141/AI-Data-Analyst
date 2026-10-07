# Gemini configuration

Create an API key in https://aistudio.google.com/apikey and put it in the repository-root `.env`. Select a Gemini model available to your project and quota in Google AI Studio.

```dotenv
GEMINI_API_KEY="your-key"
GEMINI_MODEL="your-supported-model-id"
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_OUTPUT_TOKENS=4096
GEMINI_TEMPERATURE=0.1
```

The key and model are deliberately empty in the template. No model's free-tier access is assumed. Restart Django after changing `.env`. Never commit or share the key.

Settings load these values without requiring credentials for ordinary uploads. `GeminiConfig.from_settings()` validates credentials and generation limits only when AI features are invoked. The config hides the key from its generated representation. `create_gemini_client` uses the official `google-genai` SDK with an explicit API key, Developer API mode, and an HTTP timeout. Callers must close it using a context manager. Avoid logging client objects or request credentials.

Structured planning is implemented; see [analysis planning](analysis-planning.md). Live requests are initiated through the dataset preview form. Model availability, authentication, and quota still require a live smoke check.

Google's free tier can use submitted content to improve its products; use synthetic data during development. Free quotas and supported models can change.

References:

- https://ai.google.dev/gemini-api/docs/libraries
- https://googleapis.github.io/python-genai/
- https://ai.google.dev/gemini-api/docs/pricing
