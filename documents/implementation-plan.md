# Implementation Plan

## Objective and scope

Build an AI-powered data analyst that validates CSV uploads, answers natural-language questions with computed evidence, generates insights and charts, produces SQL, detects anomalies, and maintains conversation context.

Source: the two-page AI Engineer Assignment from Digital Back Office Ltd. All project work stays in `D:\Interview_Assignments\Digital Back\AI-Data-Analyst`.

Required: support uploading one or more files. Cross-file analysis is optional in the brief; implement basic explicit-key joins only after single-dataset behavior is reliable. Docker support is preferred. The submission explicitly asks for a 10–30 second demo video, so provide one even if a live link is also available.

## Proposed layout

This is a target layout for the user's boilerplate setup, not a structure already created by this document.

```text
AI-Data-Analyst/
  config/                 # Django settings, root URLs, ASGI/WSGI
  apps/
    datasets/             # Uploads, ownership, profiling, previews
    conversations/        # Sessions, messages, history
    analysis/             # Planning, execution, charts, anomalies
  templates/
  static/
  tests/
  sample_data/
  documents/
  manage.py
  pyproject.toml
  Dockerfile
  compose.yaml
  .env.example
  .gitignore
  README.md
```

Use service modules inside the apps for business logic. Keep views thin and separate provider calls, query validation, execution, anomaly methods, and chart generation. Exclude secrets, local uploads, database files, virtual environments, and generated static assets from Git as appropriate.

## Phase 1: Foundation

- Create Django project and app packages; configure PostgreSQL and environment-based settings.
- Establish template/static builds, a base page, URL routing, and health checks.
- Add Ruff and pytest configuration, `.env.example`, and ignore rules.
- Decide the LLM provider and configure its adapter without coupling application code to its SDK.

Acceptance: the application starts locally, migrations run, and the base page loads. Missing required configuration produces a clear error.

## Phase 2: Uploads and dataset profiling

- Model datasets with owner session, original filename, generated storage path, status, schema, dimensions, and profile metadata.
- Accept multiple uploads and define whether a mixed-validity batch produces per-file results; use per-file results initially.
- Validate size, encoding, delimiter/header behavior, duplicate column names, empty files, malformed rows, and parsed row/column limits.
- Infer types conservatively; preserve original values and disclose any explicit conversions.
- Show previews and profiles: types, missing values, duplicates, basic numeric statistics, and date coverage.
- Add removal behavior and clean up associated stored files.

Acceptance: valid files appear in the dataset panel; invalid files receive actionable messages. Another session cannot preview, query, or delete those datasets.

## Phase 3: Reliable analysis execution

- Register authorized datasets in isolated DuckDB connections.
- Build a query validator for a deliberately restricted SELECT subset, including safe CTEs and aggregates.
- Enforce registered-table access and permitted functions; block writes, extensions, external reads, and unsupported statements.
- Execute in bounded worker processes with configurable time, memory, and result limits. Handle timeout and cancellation explicitly.
- Return a consistent result schema including columns, rows, truncation status, executed query, timing, and errors.

Acceptance: revenue totals, monthly trends, and customer rankings match independently calculated sample results. Unsafe or excessive queries fail without exposing other files or session data.

## Phase 4: Natural-language conversation

- Persist conversations, user/assistant messages, selected datasets, analysis runs, and result references.
- Define Pydantic schemas for supported operations, generated SQL, chart requests, assumptions, and clarification requests.
- Include relevant bounded conversation history and schema context in provider calls.
- Ask for clarification when metrics or terms such as 'underperforming' have no defined meaning.
- Validate plans before execution; bound any query-repair attempt and record its outcome.
- Explain computed results with the analysis method, applied filters, assumptions, and visible SQL.
- Handle unavailable providers, rate limits, malformed responses, and unsupported requests gracefully.

Acceptance: follow-up questions such as 'now only show the East region' preserve the intended metric and dataset. Numerical claims agree with tool output, and failed runs do not appear as successful answers.

## Phase 5: Charts, insights, and anomalies

- Translate validated chart specifications into Plotly figures using computed results.
- Support bar, line, pie, and scatter; check column types, ordering, aggregation, point limits, and suitable values.
- Generate business summaries grounded in results and identify limitations of small or incomplete datasets.
- Implement transparent numeric anomaly detection using IQR fences initially. Report the column, value, threshold, and method for each flag.
- Define handling for missing values, small samples, zero-IQR columns, and grouped analysis. Explain that statistical flags do not establish business errors.

Acceptance: required chart types render correctly; known injected anomalies are flagged with reproducible explanations. Ordinary records are not described as anomalous without a method supporting the claim.

## Phase 6: Usability and optional cross-file analysis

- Complete the upload-and-chat workspace with loading states, empty states, errors, dataset selection, and inspectable analysis details.
- Ensure keyboard access, readable charts, and responsive layouts.
- If core checks pass, support joins only with explicit user-selected keys and join type. Report unmatched keys and duplicate-key multiplication risks before presenting conclusions.

Acceptance: a new user can upload a sample CSV, ask a question, view a chart, and inspect SQL without setup knowledge. Cross-file behavior never silently guesses relationships.

## Phase 7: Verification and delivery

- Test parsing edge cases, session ownership, SQL restrictions, timeouts, expected numerical results, chart specifications, and anomaly thresholds.
- Mock provider calls for deterministic tests. Include a small evaluation set of questions and expected results; run live provider smoke checks only with configured credentials.
- Add structured logs with analysis IDs, durations, operation types, and failure categories; avoid logging secrets or full datasets.
- Build Docker Compose support and verify setup from a clean checkout.
- Include a synthetic sales dataset with regions, products, customers, dates, revenue, and intentional quality/anomaly cases.
- Write the README with setup, configuration, architecture diagram, assumptions, limits, test commands, screenshots, and demo link.
- Record a 10–30 second demo showing upload, a natural-language answer, a chart, and an anomaly explanation.

Acceptance: required features are demonstrable, automated checks pass, documented startup works, and the submission repository contains all required artifacts.

## Core demonstration questions

| Question | Evidence to verify |
| --- | --- |
| Which region generated the highest revenue? | Grouped revenue sums and highest region |
| Show monthly sales trends. | Defined date column, monthly aggregation, ordered line chart |
| Which products are underperforming? | Explicit criterion or clarification before calculation |
| What are the top five customers? | Defined ranking metric and descending results |
| Generate SQL for this analysis. | Inspectable SQL consistent with the executed analysis |
| Detect anomalies in the dataset. | Method, thresholds, flagged rows, and limitations |
| Now only show the East region. | Correct use of prior analysis context |

## Decisions and constraints to finalize

- LLM provider, model, API budget, and disclosure of data sent to the provider.
- Default upload, dataset, query, and response limits; expose them as configuration and document tested limits.
- Date conventions, currency assumptions, null handling, and the treatment of ambiguous column types.
- Dataset retention and session expiry. Use session-scoped access initially; account authentication remains optional.
- Hosting target if a live app is desired. A repository plus screenshots and the required demo video can satisfy the submission without hosting.

## Working sequence

The user is preparing the boilerplate. Once it exists, inspect and adapt these proposed paths to the actual structure, then implement phases in dependency order. Revisit optional scope only after required functionality and verification are complete.
