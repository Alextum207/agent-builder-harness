"""Rendert workspace/letters/<id>.md im Azubiyo-Layout nach .docx und .pdf (PDF über MS Word / docx2pdf).

uv run python tools/render.py workspace/letters/<id>.md
"""
import re, sys
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from check_letter import PROFIL, parse

ROOT = Path(__file__).resolve().parent.parent


def absender() -> list[str]:
    block = re.search(r"## Kontakt\n(.+?)\n\n", PROFIL.read_text(encoding="utf-8"), re.S).group(1)
    return block.strip().splitlines()


def render(md: Path) -> Path:
    d = parse(md.read_text(encoding="utf-8"))
    doc = Document()
    s = doc.sections[0]
    s.top_margin, s.bottom_margin, s.left_margin, s.right_margin = Cm(2), Cm(2), Cm(2.5), Cm(1.5)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Arial", Pt(11)
    st.paragraph_format.space_after, st.paragraph_format.line_spacing = Pt(0), 1.0

    def para(text="", bold=False, right=False, after=0):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        if right:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        lines = text.splitlines() or [""]
        for i, line in enumerate(lines):
            r = p.add_run(line)
            r.bold = bold
            if i < len(lines) - 1:
                r.add_break()
        return p

    para("\n".join(absender()), right=True, after=33)     # ① Absender
    para(d["EMPFAENGER"], after=22)                         # ② Empfänger
    para(d["DATUM"], right=True, after=22)                  # ③ Datum
    para(d["BETREFF"], bold=True, after=22)                 # ④ Betreff ohne „Betreff“
    para(d["ANREDE"], after=11)                             # ⑤ Anrede
    for block in re.split(r"\n\s*\n", d["TEXT"]):           # ⑥–⑪ Absätze, je eine Leerzeile
        para(" ".join(block.split()), after=11).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    para(d["GRUSS"], after=33)                              # ⑫ Grußformel, Platz für Unterschrift
    para(absender()[0], after=11)
    para("Anlagen: Lebenslauf" if d["SPRACHE"] == "de" else "Enclosure: CV")
    out = md.with_suffix(".docx")
    doc.save(out)
    return out


if __name__ == "__main__":
    docx = render(Path(sys.argv[1]))
    from docx2pdf import convert
    convert(str(docx), str(docx.with_suffix(".pdf")))
    print(f"{docx}\n{docx.with_suffix('.pdf')}")
