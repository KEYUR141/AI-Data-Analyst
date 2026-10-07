"""Validate CSV structure without coercing values or storing uploaded files."""

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from django.core.exceptions import ValidationError


@dataclass(frozen=True)
class CSVLimits:
    max_bytes: int = 10 * 1024 * 1024
    max_rows: int = 100_000
    max_columns: int = 100
    preview_rows: int = 10

    def __post_init__(self):
        if min(self.max_bytes, self.max_rows, self.max_columns, self.preview_rows) < 1:
            raise ValueError("CSV limits must be positive.")


@dataclass(frozen=True)
class ValidatedCSV:
    columns: list[str]
    row_count: int
    preview: list[list[str]]
    size_bytes: int


def validate_csv(upload, limits: CSVLimits | None = None) -> ValidatedCSV:
    """Return structural metadata or raise a coded Django ValidationError.

    Policy: comma-delimited UTF-8 (optional BOM), unique nonblank headers,
    at least one data row. Blank lines are ignored; empty cells are allowed.
    Read at most max_bytes + 1, regardless of the supplied size metadata.
    The file position is reset so later storage can read the original bytes.
    """
    limits = limits or CSVLimits()
    if Path(upload.name or "").suffix.lower() != ".csv":
        raise ValidationError("Choose a file with a .csv extension.", code="extension")
    if upload.size is not None and upload.size > limits.max_bytes:
        raise ValidationError("CSV exceeds the configured file size limit.", code="file_size")
    try:
        upload.seek(0)
        raw = upload.read(limits.max_bytes + 1)
    finally:
        upload.seek(0)
    if len(raw) > limits.max_bytes:
        raise ValidationError("CSV exceeds the configured file size limit.", code="file_size")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("Save the CSV using UTF-8 encoding.", code="encoding") from exc
    if not text.strip():
        raise ValidationError("CSV is empty.", code="empty")
    if "\x00" in text:
        raise ValidationError("CSV contains unsupported null bytes.", code="null_bytes")

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    columns = None
    count = 0
    preview = []
    try:
        for row in reader:
            if not row:
                continue
            if columns is None:
                columns = row
                if len(columns) > limits.max_columns:
                    raise ValidationError("CSV has too many columns.", code="column_limit")
                names = [name.strip().casefold() for name in columns]
                if any(not name for name in names):
                    raise ValidationError("Every column needs a header name.", code="blank_header")
                if len(set(names)) != len(names):
                    raise ValidationError(
                        "Column names must be unique, ignoring case and outer spaces.",
                        code="duplicate_header",
                    )
                continue
            if len(row) != len(columns):
                raise ValidationError(
                    f"CSV record ending at line {reader.line_num} has {len(row)} cells; "
                    f"expected {len(columns)}.",
                    code="row_width",
                )
            count += 1
            if count > limits.max_rows:
                raise ValidationError("CSV has too many data rows.", code="row_limit")
            if len(preview) < limits.preview_rows:
                preview.append(row)
    except csv.Error as exc:
        raise ValidationError(
            f"Malformed CSV or oversized cell near line {reader.line_num}.", code="parse"
        ) from exc
    if not count:
        raise ValidationError("CSV needs a header and at least one data row.", code="no_rows")
    return ValidatedCSV(columns=columns, row_count=count, preview=preview, size_bytes=len(raw))
