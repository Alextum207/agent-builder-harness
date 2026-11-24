"""Selbsttest ohne Model-Calls: uv run python test_ingest.py"""
import tempfile
from pathlib import Path

import docx
import openpyxl

from ingest import ingest

with tempfile.TemporaryDirectory() as tmp:
    src, brain = Path(tmp, "src"), Path(tmp, "brain")
    (src / "finance").mkdir(parents=True)
    (src / "finance" / "freigabe.html").write_text(
        "<h1>Freigaberegel: Rechnungen</h1><p>Rechnungen über 5000 EUR gibt die Leitung frei.</p>", encoding="utf-8")
    (src / "kreditoren.csv").write_text("nr,name\n70001,Muster GmbH\n", encoding="utf-8")
    d = docx.Document()
    d.add_heading("Reisekosten", 1)
    d.add_paragraph("Hotel bis 120 EUR pro Nacht.")
    d.save(src / "reisekosten.docx")
    wb = openpyxl.Workbook()
    wb.active.append(["Konto", "Bezeichnung"])
    wb.active.append([4930, "Bürobedarf"])
    wb.save(src / "kontenplan.xlsx")
    (src / "notiz.txt").write_text("Skonto immer ziehen.", encoding="utf-8")
    (src / "~$sperre.docx").write_text("x", encoding="utf-8")
    (src / "leer.txt").write_text("", encoding="utf-8")

    s = ingest(src, "laufwerk", brain)
    assert s["neu"] == 6 and not s["fehler"], s
    ctx = brain / "context/laufwerk"
    doc = (ctx / "finance/freigabe.html.md").read_text(encoding="utf-8")
    assert doc.startswith("---\ntype: Reference\n") and "5000 EUR" in doc, doc
    assert 'title: "Freigaberegel: Rechnungen"' in doc and '- resource: "laufwerk/finance/freigabe.html"' in doc, doc
    assert '"company-brain/docling-' in doc and "x-sha256: " in doc, doc
    assert "Muster GmbH" in (ctx / "kreditoren.csv.md").read_text(encoding="utf-8")
    assert "120 EUR" in (ctx / "reisekosten.docx.md").read_text(encoding="utf-8")
    assert "Bürobedarf" in (ctx / "kontenplan.xlsx.md").read_text(encoding="utf-8")
    assert "markitdown-" in (ctx / "notiz.txt.md").read_text(encoding="utf-8")
    assert not (ctx / "~$sperre.docx.md").exists()
    index = (brain / "index.md").read_text(encoding="utf-8")
    assert index.startswith('---\nokf_version: "0.3"\n'), index
    assert "[Freigaberegel: Rechnungen](context/laufwerk/finance/freigabe.html.md)" in index, index
    assert "⚠ leer" in index, index

    # Ein Mensch bestätigt ein Dokument; ein Lauf ohne Änderung darf das nicht überschreiben
    p = ctx / "notiz.txt.md"
    p.write_text(p.read_text(encoding="utf-8").replace("x-sha256", 'verified: { by: "human:b3", at: "2030-01-01" }\nx-sha256'), encoding="utf-8")
    s = ingest(src, "laufwerk", brain)
    assert s["unverändert"] == 6 and s["neu"] == 0, s
    assert "human:b3" in p.read_text(encoding="utf-8")

    (src / "kreditoren.csv").unlink()
    (src / "leer.txt").write_text("jetzt mit Text", encoding="utf-8")
    s = ingest(src, "laufwerk", brain)
    assert s["gelöscht"] == 1 and s["neu"] == 1, s
    assert "kreditoren" not in (brain / "index.md").read_text(encoding="utf-8")
    log = (brain / "log.md").read_text(encoding="utf-8")
    assert log.count("\n## ") == 1 and log.count("- laufwerk:") == 3, log


# Regressionen mit Fake-Konverter (lädt kein Docling)
kaputt = set()


def fake(f: Path) -> tuple[str, str]:
    if f.name in kaputt:
        raise ValueError("kaputt")
    return f.read_text(encoding="utf-8"), "fake"


with tempfile.TemporaryDirectory() as tmp:
    src, brain = Path(tmp, "src"), Path(tmp, "brain")
    src.mkdir()
    (src / "regel.txt").write_text("# Regel\nalt", encoding="utf-8")
    (src / "Q&A [v2] #1.txt").write_text("# Titel [Entwurf]\nText", encoding="utf-8")
    (src / "tags.txt").write_text("#tag ohne Leerzeichen\n\n## Echter Titel\nText", encoding="utf-8")
    assert ingest(src, "x", brain, convert=fake)["neu"] == 3
    ctx = brain / "context/x"
    # 7: "#tag" ist keine Überschrift
    assert 'title: "Echter Titel"' in (ctx / "tags.txt.md").read_text(encoding="utf-8")
    # 6: Link kodiert, eckige Klammern im Titel escaped
    index = (brain / "index.md").read_text(encoding="utf-8")
    assert r"- [Titel \[Entwurf\]](context/x/Q%26A%20%5Bv2%5D%20%231.txt.md)" in index, index
    # 5: Neue Fassung lässt sich nicht konvertieren → alte, geprüfte Fassung bleibt
    p = ctx / "regel.txt.md"
    p.write_text(p.read_text(encoding="utf-8").replace("x-sha256", 'verified: { by: "human:b3", at: "2030-01-01" }\nx-sha256'), encoding="utf-8")
    (src / "regel.txt").write_text("# Regel\nneu", encoding="utf-8")
    kaputt.add("regel.txt")
    s = ingest(src, "x", brain, convert=fake)
    assert len(s["fehler"]) == 1 and s["gelöscht"] == 0 and s["neu"] == 0, s
    assert "human:b3" in p.read_text(encoding="utf-8")
    assert "Regel" in (brain / "index.md").read_text(encoding="utf-8")

print("ok")
