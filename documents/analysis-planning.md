# Analysis planning

## Backend flow

From an owned dataset preview, submit the planning form. `POST /datasets/<uuid>/plan/` accepts a form field `question` with 1–2000 characters and requires CSRF protection.

`planning_views.plan` checks session ownership before provider access. `planning.generate_plan` sends the question, dataset ID, column names, and inferred types to Gemini. It sends no file paths, filenames, preview rows, or full data. Column names and questions may still contain sensitive information; the UI discloses this transfer.

The Gemini request uses JSON schema output, then `PLAN_ADAPTER` independently parses the returned text. Two variants are supported:

- `analyze`: dataset_id, SQL, method explanation, assumptions, optional chart.
- `clarify`: a clarification question.

`plan_schemas.py` forbids extra fields, constrains text lengths, validates the UUID, and restricts chart types to bar, line, pie, and scatter. The backend then checks the dataset ID and passes SQL through `sql_validator.py`. No private model reasoning or calculated answer is requested.

## Current SQL subset

One SELECT from the fixed table `dataset`, with optional filtering, grouping, ordering, and a restricted function list. Joins, CTEs, subqueries, other tables, schema-qualified tables, arbitrary functions, external readers, writes, and multiple statements are rejected. Column references are checked against the selected schema; output aliases are supported in ORDER BY.

Validation is a planning check, not an execution sandbox or proof of correct business semantics. Some DuckDB syntax and type errors can still pass these checks. Chart axes are bounded strings; their existence and numeric suitability must be verified against actual query results in the execution/chart milestone. Execution must independently revalidate SQL and enforce dataset registration, external-access restrictions, memory/time limits, and result caps.

## Output and errors

Success returns `{"plan": {...}, "executed": false}`. Invalid questions return 400, unauthorized datasets 404, invalid/missing provider configuration 503, and provider or plan failures 502. Errors do not include provider response bodies or credentials. Provider calls use the configured HTTP timeout. No application repair/retry loop is implemented; SDK behavior may include retries.

## Testing and manual check

Run `python -m pytest -q`. Tests use a mocked Gemini client for deterministic schema, provider-timeout, SQL-policy, and ownership checks. They do not establish real-key validity, free quota, or model compatibility.

To make a live request, set GEMINI_API_KEY and GEMINI_MODEL, restart Django, upload the synthetic sample, open its preview, and submit a question. The form displays JSON rather than a completed chat interface. Live requests send schema context to Google and consume your project's quota.

Persistent chat history, plan storage, SQL execution, result-based answers, and charts remain subsequent milestones. Questions needing unavailable history should produce clarification.
