import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from .services.validation import CSVLimits, validate_csv


def uploaded(content, name="data.csv"):
    return SimpleUploadedFile(name, content)


def test_bom_quotes_newlines_missing_values_and_bounded_preview():
    file = uploaded(b'\xef\xbb\xbfproduct,note\r\n"A,B","two\nlines"\r\nC,\r\n')
    result = validate_csv(file, CSVLimits(preview_rows=1))
    assert result.columns == ["product", "note"]
    assert result.row_count == 2
    assert result.preview == [["A,B", "two\nlines"]]
    assert file.tell() == 0


@pytest.mark.parametrize(
    "content,name,code",
    [
        (b"", "data.csv", "empty"),
        (b"a\n1", "data.txt", "extension"),
        (b"a\n\xff", "data.csv", "encoding"),
        (b"a\n\x00", "data.csv", "null_bytes"),
        (b"a,b\n", "data.csv", "no_rows"),
        (b"a,\n1,2", "data.csv", "blank_header"),
        (b"A, a\n1,2", "data.csv", "duplicate_header"),
        (b"a,b\n1", "data.csv", "row_width"),
        (b"a\n1,2", "data.csv", "row_width"),
        (b'a,b\n1,"unfinished', "data.csv", "parse"),
    ],
)
def test_invalid_input(content, name, code):
    with pytest.raises(ValidationError) as caught:
        validate_csv(uploaded(content, name))
    assert caught.value.code == code


@pytest.mark.parametrize(
    "limits,code",
    [
        (CSVLimits(max_bytes=3), "file_size"),
        (CSVLimits(max_rows=1), "row_limit"),
        (CSVLimits(max_columns=1), "column_limit"),
    ],
)
def test_limits(limits, code):
    with pytest.raises(ValidationError) as caught:
        validate_csv(uploaded(b"a,b\n1,2\n3,4"), limits)
    assert caught.value.code == code


def test_actual_bytes_checked_even_if_size_metadata_is_wrong():
    file = uploaded(b"a\n123456")
    file.size = 1
    with pytest.raises(ValidationError) as caught:
        validate_csv(file, CSVLimits(max_bytes=4))
    assert caught.value.code == "file_size"
    assert file.tell() == 0


def test_blank_lines_and_single_column_are_supported():
    result = validate_csv(uploaded(b"\na\n\n1\n2\n"))
    assert result.row_count == 2


def test_batch_reports_each_file_independently():
    response = Client().post(
        "/datasets/validate/", {"files": [uploaded(b"a\n1", "good.csv"), uploaded(b"", "bad.csv")]}
    )
    assert response.status_code == 200
    assert [entry["valid"] for entry in response.json()["files"]] == [True, False]


def test_endpoint_requires_files_and_post():
    client = Client()
    assert client.get("/datasets/validate/").status_code == 405
    assert client.post("/datasets/validate/").status_code == 400


def test_endpoint_preserves_csrf_protection():
    response = Client(enforce_csrf_checks=True).post(
        "/datasets/validate/", {"files": uploaded(b"a\n1")}
    )
    assert response.status_code == 403
