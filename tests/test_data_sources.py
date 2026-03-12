"""Tests for uploaded data-file summarization."""

from io import BytesIO

from openpyxl import Workbook

from src.data_sources import summarize_file_bytes


def test_summarize_csv_suggests_chart():
    summary = summarize_file_bytes(
        "metrics.csv",
        b"month,revenue\nJan,10\nFeb,15\nMar,18\n",
    )

    assert summary["file_type"] == "csv"
    assert "Rows: 3" in summary["summary"]
    assert "chart" in summary["suggested_diagram_types"]


def test_summarize_json_object():
    summary = summarize_file_bytes(
        "services.json",
        b'{"services":[{"name":"api","owner":"platform"}],"environment":"prod"}',
    )

    assert summary["file_type"] == "json"
    assert "Top-level structure: object" in summary["summary"]
    assert "architecture" in summary["suggested_diagram_types"]


def test_summarize_xlsx_workbook():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Revenue"
    sheet.append(["month", "revenue"])
    sheet.append(["Jan", 10])
    sheet.append(["Feb", 12])
    stream = BytesIO()
    workbook.save(stream)

    summary = summarize_file_bytes("metrics.xlsx", stream.getvalue())

    assert summary["file_type"] == "xlsx"
    assert "Sheet 'Revenue'" in summary["summary"]
    assert "chart" in summary["suggested_diagram_types"]
