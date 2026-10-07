# DuckDB execution

The planning endpoint now executes validated analysis plans and returns computed columns and rows. Clarification responses do not execute anything. The browser shows a result table, calculation notes, and optional SQL details. Plotly and result-grounded narrative generation will follow.

Flow: owned dataset -> Gemini plan -> schema/SQL validation -> `execution.execute_analysis` revalidation -> standalone `duckdb_worker.py` -> result table.

The worker reads only the server-selected private file, checks its size and schema, and materializes a table called `dataset`. Profiled numbers become DOUBLE and ISO dates become DATE. Blank numeric/date values become NULL; text stays unchanged. Duplicate rows are retained. Numeric calculations use floating-point arithmetic, so this is not exact financial accounting. Old datasets without a profile retain text columns and should be re-uploaded.

Each run gets a new in-memory connection and a separate process. After server-controlled ingestion, external access is disabled and configuration locked. Automatic extension installation/loading and disk spilling are disabled. Generated SQL never supplies a file path. SQL restrictions remain one flat SELECT against the registered dataset.

Defaults: 20-second worker timeout (including startup and ingestion), one DuckDB thread, 256 MB DuckDB buffer-memory limit, 200 returned rows. Result truncation is shown explicitly. The parent kills a timed-out subprocess. DuckDB's memory setting is not a hard process-wide memory ceiling; Pandas and some query allocations are outside it. Production should add container/OS resource limits, concurrency quotas, and total HTTP-body limits. A subprocess is not an OS security sandbox.

Tests run real DuckDB workers against synthetic data: region totals, highest product (Desk, 27000), monthly totals, NULL handling, truncation, policy rejection before process launch, and timeout handling. Region total is 61720, including the intentional duplicate and outlier. These tests require no Gemini calls.

To try it, restart Django, refresh the preview page, and ask: 'What is the revenue of the highest-grossing product?' Generated SQL can still fail because of unsupported operations or type errors; such failures produce an error rather than an invented answer.
