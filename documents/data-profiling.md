# Data profiling

Upload flow: `dataset_views.upload` -> `save_dataset` -> `validate_csv` -> `profile_csv` -> private storage -> Dataset record with a JSON profile.

Read `Project/app/services/profiling.py` for the calculations. The profiler reads the entire validated, byte-bounded CSV with the same record semantics as validation, builds a Pandas DataFrame of original strings, and generates a versioned JSON-compatible dictionary. It resets the upload pointer before storage reads the original bytes.

## Rules

- Whitespace-only or empty cells count as missing. Literal `NA`, `null`, and `NaN` are text, not automatically missing.
- Inference considers all nonblank values. Mixed values remain text.
- Numeric syntax supports signed integers, decimals, and scientific notation. Leading-zero values such as `00123` remain text. Finite values exceeding 100 digits of precision or exponent magnitude 100 remain text to bound arithmetic.
- Dates require valid, exact `YYYY-MM-DD` syntax. Ambiguous dates and timestamps remain text.
- Numeric minimum, maximum, mean, and median use Decimal arithmetic and are stored as strings to avoid binary floating-point precision loss. Repeating means are rounded to the calculation precision (220 significant digits).
- Distinct counts ignore surrounding whitespace and exclude missing cells. Duplicate rows compare the original strings exactly and count repeats after the first occurrence.
- Types are descriptive hints, not transformations; the stored file and preview remain unchanged. Numeric-looking identifiers without leading zeros may still be inferred as numbers; semantic column roles will require user confirmation or additional schema handling.

Profiles are stored in `Dataset.profile`, including row count, duplicate count, and per-column results. The preview page displays them. Pre-existing Dataset rows have an empty profile; re-upload to calculate one. No background backfill runs automatically.

## Verification and limits

Run `python -m pytest -q`. Tests cover dates, numbers, decimal precision, mixed types, missing values, identifiers, extreme exponents, invalid dates, blank lines, BOM, duplicate rows, and persisted profiles.

The profile is synchronous and uses memory proportional to dataset size; byte/row/column validation limits apply first. Profiling evaluates the full data, rather than extrapolating from the preview. SQL execution and natural-language analysis are subsequent milestones.
