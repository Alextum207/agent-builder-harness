"""Liest einen Ordner mit Firmendokumenten ins Company Brain ein, als Bundle im Open Knowledge Format (OKF v0.3).

Jede Datei wird ein OKF-Konzept unter brain/context/<quelle>/<pfad>.md. Herkunft steht in `sources`,
Erzeugung in `generated`, die Prüfsumme in `x-sha256`. Unveränderte Dateien werden übersprungen, damit
eingetragene `verified`-Prüfungen erhalten bleiben. Gelöschte Quellen werden entfernt.
Danach werden brain/index.md (Bundle-Root) und brain/log.md fortgeschrieben.

    uv run python ingest.py <ordner> <quellname> [<brain-ordner>]   (Standard: company-brain/brain)
"""
import datetime as dt
import hashlib
import json
import re
import sys
from importlib.metadata import version
from pathlib import Path
from urllib.parse import quote

import truststore

truststore.inject_into_ssl()  # Docling lädt Modelle von Hugging Face; TLS-Proxy auf diesem Rechner

BRAIN = Path(__file__).parent / "brain"
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}
# Docling für Layout, Tabellen und Scans. Alles andere (txt, msg, json, md, …) über markitdown.
DOCLING_SUFFIXES = {".pdf", ".docx", ".xlsx", ".pptx", ".html", ".htm", ".csv",
                    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
OKF_VERSION = "0.3"


class Converter:
    """Lädt Docling erst beim ersten Dokument, das es braucht (Modelle laden dauert)."""

    def __init__(self):
        self._docling = self._markitdown = None

    def __call__(self, f: Path) -> tuple[str, str]:
        if f.suffix.lower() in DOCLING_SUFFIXES:
            if self._docling is None:
                from docling.datamodel.base_models import InputFormat
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                from docling.document_converter import DocumentConverter, PdfFormatOption
                # Standard-OCR ließ bei einem Scan den Betrag weg ("Betrag:" ohne Zahl); ganze Seite OCR fand ihn.
                # ponytail: OCR auch auf PDFs mit Textebene = langsamer; pro Datei umschalten, wenn Menge das braucht
                o = PdfPipelineOptions()
                o.ocr_options.force_full_page_ocr = True
                self._docling = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=o)})
            text = self._docling.convert(f).document.export_to_markdown()
            return text, f"company-brain/docling-{version('docling')}"
        if self._markitdown is None:
            from markitdown import MarkItDown
            self._markitdown = MarkItDown(enable_plugins=False)
        return self._markitdown.convert(str(f)).markdown, f"company-brain/markitdown-{version('markitdown')}"


def _wanted(p: Path, src: Path) -> bool:
    parts = p.relative_to(src).parts
    # ~$ = Office-Sperrdateien; . = versteckt (OKF schließt Punkt-Pfade ohnehin aus)
    return p.is_file() and not SKIP_DIRS & set(parts) and not any(x.startswith((".", "~$")) for x in parts)


def _title(text: str, fallback: str) -> str:
    # nur echte Überschriften ("# Titel", "## Titel"), nicht "#tag"
    return next((m[1].strip() for l in text.splitlines() if (m := re.match(r"#{1,6} +(\S.*)", l))), fallback)


def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)  # JSON-String ist gültiges YAML 1.2, auch mit ':' oder '#'


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ingest(src: Path, name: str, brain: Path = BRAIN, convert=None) -> dict:
    out_root = brain / "context" / name
    convert = convert or Converter()
    seen: set[Path] = set()
    stats = {"neu": 0, "unverändert": 0, "gelöscht": 0, "fehler": []}

    for f in sorted(p for p in src.rglob("*") if _wanted(p, src)):
        rel = f.relative_to(src)
        out = out_root / rel.with_name(rel.name + ".md")
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if out.exists() and f"\nx-sha256: {digest}\n" in out.read_text(encoding="utf-8").partition("\n---\n")[0] + "\n":
            seen.add(out)
            stats["unverändert"] += 1
            continue
        try:
            text, by = convert(f)
            text = text.strip()
        except Exception as e:  # eine kaputte Datei darf den Lauf nicht abbrechen
            stats["fehler"].append(f"{rel.as_posix()}: {type(e).__name__}: {e}"[:200])
            if out.exists():
                seen.add(out)  # alte, gute Fassung (samt `verified`) behalten statt löschen
            continue
        modified = dt.date.fromtimestamp(f.stat().st_mtime).isoformat()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            "---\n"
            "type: Reference\n"
            f"title: {_q(_title(text, f.name))}\n"
            "sources:\n"
            f"  - resource: {_q(f'{name}/{rel.as_posix()}')}\n"
            f"    last_modified: {modified}\n"
            f"generated: {{ by: {_q(by)}, at: {_q(_now())} }}\n"
            f"x-sha256: {digest}\n"
            "---\n\n"
            f"{text}\n",
            encoding="utf-8",
        )
        seen.add(out)
        stats["neu"] += 1

    if out_root.exists():
        for old in out_root.rglob("*.md"):
            if old not in seen:
                old.unlink()
                stats["gelöscht"] += 1

    write_index(brain)
    _log(brain, name, stats)
    return stats


def _field(head: str, key: str) -> str:
    raw = next((l.split(":", 1)[1].strip() for l in head.splitlines() if l.strip().startswith(key + ":")), "")
    return json.loads(raw) if raw.startswith('"') else raw


def write_index(brain: Path = BRAIN) -> None:
    """OKF-Bundle-Root: Metadaten im Frontmatter, darunter ein Abschnitt pro Quelle mit Links."""
    ctx = brain / "context"
    lines = [
        "---", f'okf_version: "{OKF_VERSION}"', 'title: "Company Brain"',
        'description: "Firmendokumente als Markdown, erzeugt von ingest.py"', "---", "",
        "Pro Dokument: Link, Wörter, Stand der Quelle. `⚠ leer` heißt meist: Scan, bei dem OCR nichts fand.",
    ]
    sources = sorted(p for p in ctx.iterdir() if p.is_dir()) if ctx.exists() else []
    for s in sources:
        lines += ["", f"## {s.name}", ""]
        for p in sorted(s.rglob("*.md")):
            head, _, body = p.read_text(encoding="utf-8").partition("\n---\n")
            words = len(body.split())
            flag = " ⚠ leer" if words == 0 else ""
            link = quote(p.relative_to(brain).as_posix())
            title = _field(head, "title")[:80].replace("[", r"\[").replace("]", r"\]")
            lines.append(f"- [{title}]({link}) · {words} Wörter{flag} · {_field(head, 'last_modified')}")
    brain.mkdir(parents=True, exist_ok=True)
    (brain / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _log(brain: Path, name: str, stats: dict) -> None:
    """OKF log.md: ohne Frontmatter, Überschriften im Format YYYY-MM-DD."""
    log = brain / "log.md"
    old = log.read_text(encoding="utf-8") if log.exists() else "# Log\n"
    day = f"## {dt.date.today().isoformat()}"
    entry = (f"- {name}: {stats['neu']} neu, {stats['unverändert']} unverändert, "
             f"{stats['gelöscht']} gelöscht, {len(stats['fehler'])} Fehler")
    log.write_text(old.rstrip("\n") + ("\n" if day in old else f"\n\n{day}\n\n") + entry + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    src = Path(sys.argv[1]).resolve()
    if not src.is_dir():
        sys.exit(f"Kein Ordner: {src}")
    s = ingest(src, sys.argv[2], Path(sys.argv[3]).resolve() if len(sys.argv) == 4 else BRAIN)
    print(json.dumps(s, ensure_ascii=False, indent=1))
