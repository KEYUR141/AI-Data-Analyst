# Findings and anomaly detection

The planner supports an anomalies action with 1?10 numeric columns. Its isolated worker excludes missing values, calculates quartiles with Pandas linear interpolation, and flags values strictly outside Q1 - 1.5*IQR and Q3 + 1.5*IQR. Under four observations and zero-IQR columns are skipped with explanations.

Each flag includes its one-based data-row number (excluding header and blank lines), column, value, fences, and reason. The full column is evaluated; returned flags are bounded. One row may produce multiple flags. Duplicates remain included. Statistical flags do not establish business errors.

Summaries are deterministic descriptions of actual results: named single-row values, first result and numeric maximum for multiple rows, or anomaly counts and methods. Truncated results are labeled. LLM-generated methodology and assumptions remain in the stored plan. This avoids another API call and invented numerical claims. Saved assistant messages use the computed summary.
