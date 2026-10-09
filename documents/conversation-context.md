# Persistent conversations

Each dataset has a default conversation for its owning session. Creation is serialized with a PostgreSQL dataset-row lock. Before a valid question is processed, a user Message and running AnalysisRun are saved. Completion atomically records an assistant Message and either computed results, a clarification, or a sanitized failure.

The dataset preview restores the latest 20 runs, including tables, SQL, and saved charts. This display bound does not delete older history. Current-page messages are retained as new questions are submitted. Session expiry or losing the cookie loses access; no cross-device authentication has been added.

`services/conversations.py` builds Gemini context from up to six completed or clarification runs, bounded to 18000 serialized characters. It includes prior question, response, and plan, not raw result rows or charts. Failed/running records are excluded. The current question and dataset schema are supplied separately. This permits follow-up references and clarification answers while keeping context bounded. No automatic history summarization is implemented.

Plans and results are stored locally in PostgreSQL, including bounded row sets and figure JSON. Queries and chart specifications remain inspectable. Assistant text currently describes the method; result-grounded narrative generation remains a later milestone.

Provider and execution failures are persisted. Unexpected process termination can leave a run marked running; the refreshed page exposes its status. Durable job recovery, deduplicating retried HTTP requests, and serializing concurrent questions are not implemented yet. Parallel browser tabs can produce overlapping runs.

Deleting a dataset cascades its conversations, messages, and analysis runs, as defined by model relations. All endpoints first verify session dataset ownership.

Verification: tests cover persistence, refresh restoration, clarification history, failed-run exclusion, model consistency, and unauthorized access. Try 'Show revenue by region' followed by 'Now show it monthly', then refresh to verify restoration. Gemini may still clarify ambiguous references.
