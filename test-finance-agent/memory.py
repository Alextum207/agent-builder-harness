"""Memory über Sitzungen als Bau-Muster (Issue #5).

Speicher: LangGraph-Store (BaseStore). Test mit InMemoryStore, Betrieb mit SqliteStore oder PostgresStore,
ohne Codeänderung. Gegen dateibasiertes Memory (Anthropic-Memory-Tool) entschieden, weil der Store Namespaces
pro Firma/Agent mitbringt und dieselbe Schnittstelle in Postgres mandantenfähig wird (SPEC A 6).
Ohne Embeddings: Abruf über Themen-Schlüssel, nicht semantisch.

Regeln im Code, nicht im Prompt:
- Jeder Eintrag hat Inhalt, Quelle, Datum, Ablaufdatum und Vertrauensstufe (nutzer > tool > agent).
- Die Quelle bestimmt der Code, nicht das Modell: Das Modell muss einen wörtlichen Beleg nennen. Steht der Beleg
  in einer Nutzernachricht → nutzer, in einem Tool-Ergebnis → tool, sonst → agent (abgelehnt, kein Agent-Monolog).
- Personendaten nur mit Zweck; Injection-Marker werden abgelehnt.
- Konflikt: niedrigere Vertrauensstufe überschreibt nie eine höhere, solange diese gültig ist; bei gleicher Stufe
  gewinnt die neuere Aussage (Nutzer-Korrektur schlägt alte Nutzer-Aussage).
- Abgelaufene Einträge werden nie zurückgegeben.
"""
import datetime as dt
import re
from typing import Literal

from langchain.tools import ToolRuntime, tool
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field, ValidationError

from agent_guardrails import Policy, _text

Quelle = Literal["nutzer", "tool", "agent"]
TRUST = {"nutzer": 3, "tool": 2, "agent": 1}
LAUFZEIT_TAGE = {"nutzer": 365, "tool": 90, "agent": 0}


class Eintrag(BaseModel):
    thema: str = Field(pattern=r"^[a-z0-9:_-]{3,80}$")
    inhalt: str = Field(max_length=500)
    quelle: Quelle
    erstellt: dt.date
    gueltig_bis: dt.date
    zweck: str | None = None

    @property
    def vertrauen(self) -> int:
        return TRUST[self.quelle]


class Memory:
    def __init__(self, store: BaseStore, namespace: tuple[str, ...], policy: Policy, today: dt.date | None = None):
        self.store, self.ns, self.policy = store, namespace, policy
        self.today = today or dt.date.today()

    def _aktiv(self, e: Eintrag) -> bool:
        return e.gueltig_bis >= self.today

    def merken(self, thema: str, inhalt: str, quelle: Quelle, zweck: str | None = None,
               gueltig_bis: dt.date | None = None, tainted: bool = False) -> tuple[bool, str]:
        thema = re.sub(r"\s+", "-", thema.strip().lower())
        if quelle == "agent":
            return False, "abgelehnt: eigene Schlussfolgerungen des Agenten werden nicht gespeichert"
        if tainted and quelle != "nutzer":
            return False, "abgelehnt: Lauf enthält mögliche Injection, nur Nutzer-Aussagen werden gespeichert"
        if self.policy.injection_hits(inhalt):
            return False, "abgelehnt: Inhalt enthält Anweisungen (Injection-Marker)"
        if self.policy.pii_hits(inhalt) and not zweck:
            return False, "abgelehnt: Personendaten ohne angegebenen Zweck"
        neu = Eintrag(thema=thema, inhalt=inhalt, quelle=quelle, erstellt=self.today, zweck=zweck,
                      gueltig_bis=gueltig_bis or self.today + dt.timedelta(days=LAUFZEIT_TAGE[quelle]))
        alt = self.get(thema)
        if quelle == "tool":       # Vertrauensregel pro Objekt (erste zwei Segmente), nicht nur pro Schlüssel
            obj = thema.split(":")[:2]
            hoeher = [e for e in self.alle() if e.thema.split(":")[:2] == obj and e.vertrauen > neu.vertrauen]
            if hoeher:
                return False, f"abgelehnt: {hoeher[0].thema} hat höhere Vertrauensstufe ({hoeher[0].quelle})"
        if alt and alt.vertrauen > neu.vertrauen:
            return False, f"abgelehnt: vorhandener Eintrag hat höhere Vertrauensstufe ({alt.quelle})"
        self.store.put(self.ns, thema, neu.model_dump(mode="json"))
        return True, "gespeichert" + (f" (ersetzt Aussage vom {alt.erstellt})" if alt else "")

    def get(self, thema: str) -> Eintrag | None:
        item = self.store.get(self.ns, thema)
        e = Eintrag(**item.value) if item else None
        return e if e and self._aktiv(e) else None

    def alle(self) -> list[Eintrag]:
        items = self.store.search(self.ns, limit=1000)
        return sorted((e for e in (Eintrag(**i.value) for i in items) if self._aktiv(e)), key=lambda e: e.thema)

    def vorab_kontext(self, max_eintraege: int = 20) -> str:
        """Laden vorab, solange das Memory klein ist und fast jede Aufgabe es braucht (Entscheidung in context.md)."""
        eintraege = self.alle()[:max_eintraege]
        if not eintraege:
            return "(keine gemerkten Vereinbarungen)"
        return "\n".join(f"- {e.thema}: {e.inhalt} (Quelle {e.quelle}, Stand {e.erstellt})" for e in eintraege)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _zahlen(s: str) -> set[str]:
    return {re.sub(r"\s", "", z).replace(",", ".") for z in re.findall(r"\d+(?:[.,]\d+)?\s?%?", s)}


def quelle_aus_beleg(beleg: str, messages, inhalt: str = "") -> Quelle:
    """nutzer nur, wenn der Beleg in der LETZTEN Nutzernachricht steht; nutzer und tool nur, wenn jede Zahl
    aus dem Inhalt auch im Beleg steht (sonst ließe sich Tool-Inhalt mit einem beliebigen Nutzerzitat einschleusen)."""
    b = _norm(beleg)
    if len(b) < 8 or not _zahlen(inhalt) <= _zahlen(b):
        return "agent"
    human = [m for m in messages if m.type == "human"]
    if human and b in _norm(_text(human[-1].content)):
        return "nutzer"
    for m in messages:
        if m.type == "tool" and b in _norm(_text(m.content)):
            return "tool"
    return "agent"


def memory_tools(mem: Memory):
    class MerkenIn(BaseModel):
        thema: str = Field(description="Schlüssel, klein, z. B. 'kreditor:70004:skonto'")
        inhalt: str = Field(description="Die Vereinbarung in einem Satz")
        beleg: str = Field(description="Wörtliches Zitat aus der Nachricht oder dem Dokument, aus dem die Vereinbarung stammt")

    @tool(args_schema=MerkenIn)
    def memory_merken(thema: str, inhalt: str, beleg: str, runtime: ToolRuntime) -> str:
        """Merkt sich eine dauerhafte Vereinbarung über diese Sitzung hinaus. Nur für Vereinbarungen, nicht für Zwischenergebnisse."""
        fehlend = sorted(_zahlen(inhalt) - _zahlen(_norm(beleg)))
        if fehlend:                         # konkreter Hinweis, damit das Modell korrigiert statt aufzugeben
            return (f"error: Inhalt enthält Angaben, die nicht im Beleg stehen: {', '.join(fehlend)}. "
                    "Speichere nur, was wörtlich im Beleg steht, und versuche es einmal erneut.")
        quelle = quelle_aus_beleg(beleg, runtime.state["messages"], inhalt)
        try:
            ok, grund = mem.merken(thema, inhalt, quelle, tainted=bool(runtime.state.get("guardrail_taint")))
        except ValidationError as exc:     # z. B. ungültiges Thema: Fehler ans Modell, Lauf läuft weiter
            return f"error: ungültige Eingabe ({exc.errors()[0]['msg']})"
        return f"{'ok' if ok else 'error'}: {grund} (Quelle erkannt: {quelle})"

    class SuchenIn(BaseModel):
        thema: str = Field(description="Schlüssel oder Präfix, z. B. 'kreditor:70004'")

    @tool(args_schema=SuchenIn)
    def memory_suchen(thema: str) -> str:
        """Sucht gemerkte Vereinbarungen nach Thema-Präfix."""
        treffer = [e for e in mem.alle() if e.thema.startswith(thema.strip().lower())]
        return "\n".join(f"{e.thema}: {e.inhalt} (Quelle {e.quelle}, Stand {e.erstellt})" for e in treffer) or "keine Treffer"

    return [memory_merken, memory_suchen]
