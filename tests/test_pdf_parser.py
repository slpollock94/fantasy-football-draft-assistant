import types
import sys

# Provide a minimal pdfplumber stub if the real package is unavailable
sys.modules.setdefault("pdfplumber", types.SimpleNamespace(open=lambda path: None))

from ff_draft_assistant import pdf_parser

class DummyPage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text

class DummyPDF:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

def test_parse_pdf_and_mark(monkeypatch):
    sample = "1. Christian McCaffrey RB SF\n2. Justin Jefferson WR MIN"
    dummy_pdf = DummyPDF([DummyPage(sample)])
    monkeypatch.setattr(pdf_parser, "pdfplumber", types.SimpleNamespace(open=lambda _: dummy_pdf))
    sheet = pdf_parser.PDFPlayerSheet("dummy.pdf")
    sheet.parse_pdf()
    assert len(sheet.players) == 2
    sheet.mark_drafted("Christian McCaffrey")
    available = [p.name for p in sheet.get_available_players()]
    assert "Justin Jefferson" in available
    assert "Christian McCaffrey" not in available

def test_save_and_load(tmp_path):
    sheet = pdf_parser.PDFPlayerSheet("dummy.pdf")
    sheet.players = [pdf_parser.Player("Test Player", "QB", "NYJ", 1)]
    file = tmp_path / "players.json"
    sheet.save(file)
    new_sheet = pdf_parser.PDFPlayerSheet("dummy.pdf")
    new_sheet.load(file)
    assert new_sheet.players[0].name == "Test Player"
