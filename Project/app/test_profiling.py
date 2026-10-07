import json

from django.core.files.uploadedfile import SimpleUploadedFile

from .services.profiling import profile_csv


def profile(content):
    upload = SimpleUploadedFile("data.csv", content.encode("utf-8"))
    result = profile_csv(upload)
    assert upload.tell() == 0
    json.dumps(result, allow_nan=False)
    return result


def test_numbers_dates_missing_and_duplicates():
    result = profile(
        "date,region,revenue\n2026-01-05,East,120\n2026-02-01,West,350\n2026-02-01,West,350\n2026-03-02,East, \n"
    )
    assert result["row_count"] == 4
    assert result["duplicate_row_count"] == 1
    date, region, revenue = result["columns"]
    assert date["type"] == "date"
    assert date["statistics"]["latest"] == "2026-03-02"
    assert region["distinct_count"] == 2
    assert revenue["missing_count"] == 1
    assert revenue["statistics"]["median"] == "350"


def test_identifiers_mixed_ambiguous_dates_and_empty_columns():
    result = profile("id,mixed,date,empty\n00123,12,01/02/2026,\n00456,unknown,02/03/2026, \n")
    assert [c["type"] for c in result["columns"]] == ["text", "text", "text", "empty"]
    assert result["columns"][3]["missing_count"] == 2


def test_invalid_iso_date_and_nonfinite_values_remain_text():
    result = profile("date,value,huge\n2026-02-30,NaN,1e999999\n")
    assert all(c["type"] == "text" for c in result["columns"])


def test_decimal_precision_and_even_median():
    result = profile("value\n0.1\n0.2\n")
    stats = result["columns"][0]["statistics"]
    assert stats["mean"] == "0.15"
    assert stats["median"] == "0.15"


def test_blank_lines_and_literal_na():
    result = profile("\ufeffname\n\nNA\nnull\n")
    assert result["row_count"] == 2
    assert result["columns"][0]["missing_count"] == 0
