import importlib.util
from pathlib import Path


def _fetcher_module():
    path = Path(__file__).parents[1] / "scripts" / "sipp_fetcher.py"
    spec = importlib.util.spec_from_file_location("sipp_fetcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sipp_date_parser_accepts_supported_formats():
    parse_date = _fetcher_module()._parse_date
    assert parse_date("2026-09-29").year == 2026
    assert parse_date("29-09-2026").month == 9
    assert parse_date("not-a-date") is None
