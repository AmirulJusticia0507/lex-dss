import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_national_laws import parse_articles, parse_law_page, parse_total


def test_parses_official_catalog_card_and_status():
    page = '''data dari 1.930 Peraturan
    <div class="col-md-12"><p style="padding-top: -2;">Undang-Undang Nomor 1 Tahun 2026</p>
    <p><a href="/id/uu-no-1-tahun-2026">Penyesuaian Pidana</a></p>
    <li>Dokumen : <a href="/files/uu-no-1-tahun-2026.pdf"></a></li>
    Tidak Berlaku<div class="col-md-12">'''
    law = parse_law_page(page)[0]
    assert parse_total(page) == 1930
    assert law.title == "Undang-Undang Nomor 1 Tahun 2026 tentang Penyesuaian Pidana"
    assert law.status == "tidak_berlaku"


def test_keeps_law_when_ditjen_pp_card_has_no_pdf():
    page = '''<div class="col-md-12"><p style="padding-top: -2;">Undang-Undang Nomor 1 Tahun 1945</p>
    <p><a href="/id/uu-no-1-tahun-1945">Contoh</a></p><div class="col-md-12">'''
    law = parse_law_page(page)[0]
    assert law.pdf_url is None


def test_splits_articles_and_omits_explanation():
    text = "Pasal 1\nIsi satu.\nPasal 2A\nIsi dua.\nPENJELASAN\nPasal 1\nBukan isi."
    assert parse_articles(text) == [("1", "Isi satu."), ("2A", "Isi dua.")]
