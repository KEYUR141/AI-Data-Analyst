# Technology Stack

Status: agreed baseline; exact dependency versions will be pinned during setup.

## Application stack

| Component | Choice | Responsibility |
| --- | --- | --- |
| Backend | Django 5.2 LTS | Upload endpoints, session ownership, conversation persistence, orchestration |
| Frontend | Django templates, HTMX, Tailwind CSS | Upload workspace, dataset preview, chat, results, responsive styling |
| Data processing | Pandas | CSV validation, schema profiling, data quality summaries, anomaly calculations |
| SQL analytics | DuckDB | Aggregations, filtering, joins, and read-only queries against session datasets |
| Charts | Plotly Python and Plotly.js | Interactive bar, line, pie, scatter, and other supported charts |
| Application database | PostgreSQL | Dataset metadata, conversations, messages, analysis runs, and results |
| LLM integration | Provider SDK, Pydantic | Provider adapter, structured analysis plans, validated output schemas |
| SQL validation | SQLGlot plus an explicit allowlist | Parse queries and enforce supported read-only operations |
| Testing | pytest, pytest-django | Data validation, query restrictions, numerical correctness, ownership checks |
| Runtime | Gunicorn, Docker Compose | Reproducible application and PostgreSQL services |
| Configuration | Environment variables | Secrets, upload limits, LLM model, database and runtime settings |
| Quality checks | Ruff | Formatting and linting |

The LLM provider and model remain undecided until API access and budget are known. Keep provider-specific code behind one adapter. No API key belongs in Git.

## Data responsibilities

PostgreSQL stores application state; DuckDB performs analytics. Uploaded data is not automatically imported into the application's PostgreSQL tables.

Store uploads in a private application-managed directory outside publicly served static assets. Use generated filenames and dataset IDs. Start with local persistent storage mounted through Docker; document that hosted deployments require durable storage.

Use an isolated DuckDB connection for each analysis run, with only the authorized datasets registered under generated table names. Disable external access and extension loading before processing generated queries. Do not share connections between users.

## AI execution contract

1. Validate files and profile columns before involving the LLM.
2. Send schemas, bounded previews, relevant prior messages, and dataset identifiers to the provider. Explain this data-sharing behavior in the UI and README.
3. Request a structured plan containing the analysis type, SQL or supported operation, chart specification, and assumptions.
4. Validate the plan and independently enforce ownership, SQL restrictions, resource limits, and chart constraints.
5. Execute the analysis with application-controlled tools.
6. Generate an explanation grounded in computed results; preserve the query, method, and assumptions for inspection.

Do not execute arbitrary LLM-generated Python. SQL generation satisfies the assignment's SQL and/or Pandas requirement. Explanations describe the method and evidence; they do not expose private model reasoning.

SQL parsing alone is insufficient isolation. Enforce registered-table access, prohibit filesystem/network readers and unsafe functions, disable external access, cap returned rows, and run analytics in a bounded worker process with a timeout. Limit both upload size and parsed dataset dimensions.

## Frontend approach

Use one Django application with server-rendered pages and HTMX requests. Use small JavaScript modules for Plotly rendering and interface behavior. Compile Tailwind into static assets; avoid relying on development CDNs in the final build.

Display answers, result tables, charts, analysis details, and actionable errors in the conversation. Keep implementation details such as provider configuration out of the main user workflow.

## Deferred additions

- React and Django REST Framework: reconsider if a separate frontend or public API becomes necessary.
- Celery and Redis: add if durable background queues are needed; initial bounded worker execution does not imply a durable job system.
- Vector database and agent framework: add only for a concrete retrieval or orchestration requirement.
- Forecasting, dashboards, report exports, and streaming: optional follow-on work after core acceptance checks pass.

## Reference documentation

- Django LTS release: https://www.djangoproject.com/weblog/2025/apr/02/django-52-released/
- DuckDB Python API: https://duckdb.org/docs/current/clients/python/overview
- Plotly Python: https://plotly.com/python/

