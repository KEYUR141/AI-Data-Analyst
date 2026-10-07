# Dataset upload and persistence

## Backend flow

1. The home template submits multipart `files` to `POST /datasets/upload/`, including a CSRF token.
2. `dataset_views.upload` checks the batch and creates a Django session if necessary.
3. `services.datasets.save_dataset` calls the existing CSV validator.
4. After validation succeeds, private storage saves the original bytes under a random UUID filename.
5. `Dataset.objects.create` stores the owner session, original name, storage name, dimensions, columns, preview, and timestamp in PostgreSQL.
6. The view reports each file outcome and redirects to the workspace. The workspace lists only datasets belonging to the current session.

The database stores metadata and the first preview rows, not the entire CSV. Actual files live in ignored `var/uploads/`. No public media route or raw download endpoint is provided.

`GET /datasets/<uuid>/` performs an ownership-filtered lookup before rendering a preview. `POST /datasets/<uuid>/delete/` uses the same check and removes the private file and its database row. An unauthorized session gets 404 for both routes. Templates escape uploaded names and values.

The storage service cleans up a newly saved file when database insertion fails. Filesystem and database operations cannot be committed atomically: process crashes can leave orphan files, and a database failure after file deletion can leave stale metadata. Reconciliation and scheduled retention cleanup remain future work.

## Manual verification

Start Django and upload `sample_data/sales.csv`. Check its five-row preview, refresh the workspace, and confirm the dataset persists. In a private browser window, confirm it is absent. Remove it in the original window and confirm it disappears.

Session cookies establish access, not permanent accounts. Losing the cookie or session expiry loses access to the associated files. Account ownership and automatic expiry cleanup are not implemented yet.

## Tests

`python -m pytest -q` covers upload/storage bytes, listing, preview, deletion, isolation, mixed batches, failed-insert cleanup, HTML escaping, and CSRF protection. Integration tests use the isolated SQLite test database and temporary private storage; the actual PostgreSQL Dataset migration has also been applied locally.

## Next milestone

Add dataset profiling (types, missing values, statistics), then restricted SQL execution. Values currently remain strings; charts and natural-language analysis are not active yet.
