# CSV validation backend

## Request flow

`POST /datasets/validate/` -> `app/urls.py` -> `validation_views.validate_uploads` -> `services/validation.validate_csv` -> JSON containing per-file outcomes.

Send multipart files under the repeated `files` field. Django's normal CSRF protection applies. The browser upload form will be wired in the next milestone. No dataset records or permanent files are created by this endpoint.

The view handles HTTP and batches. The service checks one file and returns a `ValidatedCSV` dataclass or raises a coded Django `ValidationError`. `CSVLimits` holds the configurable limits. The view converts the dataclass to JSON and translates validation errors into user-facing messages.

## Accepted format

- `.csv` extension, case insensitive. MIME type is not trusted.
- Comma-delimited UTF-8, with an optional byte-order mark (BOM).
- Header required; names cannot be blank or duplicates after trimming and case folding. Original names are preserved.
- At least one data record; each record must match the header width.
- Empty cells, single-column datasets, quoted commas and quoted multiline values are supported. Empty physical lines are skipped.
- Values remain strings; dates, numbers and missing-value semantics will be handled in profiling.

Header presence is a declared format contract: a parser cannot reliably distinguish a textual first data row from a header. Other delimiters and encodings are not automatically detected in this version.

Defaults: 10 MiB per file, 100,000 data rows, 100 columns, 10 preview rows, five files per batch. Set `CSV_*` variables in `.env` to change them. Python's CSV parser also rejects fields exceeding its built-in field limit (typically 128 KiB).

The service reads at most the byte limit plus one, checks actual bytes as well as reported size, and resets the file pointer. It stores only preview rows, but decoding retains the bounded file text in memory during validation. Django spools larger incoming files to temporary disk. Per-file validation happens after HTTP multipart parsing; production must also enforce a total request-body limit at the proxy to protect temporary disk and bandwidth.

## Responses

Missing files or an invalid batch return HTTP 400; unsupported methods return 405. A processed batch returns 200 with `files` entries containing `filename` and `valid`. Valid entries include `columns`, `row_count`, `preview`, and `size_bytes`. Invalid entries contain `error.code` and `error.message`.

Mixed batches return every outcome independently. A 200 batch response does not mean all files were valid. This API provides validation only, not persistence, ownership, or analysis.

## Verification

Run `python -m pytest -q` from the repository root. Coverage includes encoding, headers, malformed records, quotes/newlines, empty cells, limits, misleading size metadata, mixed batches, and CSRF enforcement. Foundation tests continue to run alongside these checks.
