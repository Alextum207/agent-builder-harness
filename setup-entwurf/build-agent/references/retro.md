# Retro und Lernkreislauf

Läuft automatisch als letzte Phase jedes Builds. Auch nutzen, wenn der Nutzer später ein Problem aus dem Betrieb meldet.
Alle Pfade unten sind relativ zum Skill-Ordner (Base directory dieses Skills), außer `RETRO.md`, die ins Agent-Projekt gehört.

## Inhalt
- 1 Belege sammeln
- 2 RETRO.md schreiben
- 3 Vorschläge in die Inbox
- 4 Freigabe und Ledger
- 5 Playbooks und Templates
- 6 Aufräumen
- 7 Git

## 1 Belege sammeln
- Eval-Report: pass@1/pass@3/pass^3, Kosten pro erfolgreichem Lauf, Latenz.
- Logs: Schritte pro Lauf, Tool-Fehler, Loop-Guard- oder Limit-Abbrüche.
- Build-Verlauf: Bugs, Fehlversuche, Korrekturen durch den Nutzer, veraltete API-Annahmen.
- Was wurde aus `templates/` oder `domains/` wiederverwendet, und hat es gepasst?

## 2 RETRO.md im Projekt
```markdown
# Retro <datum> – <agent> (kontext: <tag>)
## Ergebnis
Evals: pass@3 … | pass^3 kritisch … | Kosten/Lauf … | Latenz …
## Was funktioniert hat
## Was nicht funktioniert hat (mit Ursache)
## Wiederverwendet aus Skill
## Vorschläge an den Skill
```

## 3 Vorschläge in die Inbox
Nur Erkenntnisse mit Beleg. Kein Beleg → kein Vorschlag. An `learnings/inbox.md` anhängen:
```
- <datum> | kontext: <tag> | projekt: <absoluter pfad> | stärke: regel | hinweis
  Erkenntnis: <was> → <Beleg: Messwert vorher/nachher (n=<fälle>), Bug, Kosten>
  Ziel: ledger | domain | template | reference
```
Belegstärke:
- Messwerte immer mit Fallzahl `n`, vorher und nachher mit **denselben** Fällen gemessen.
- `regel`: n ≥ 10 oder ein reproduzierbarer Bug mit klarer Ursache.
- `hinweis`: alles darunter. Hinweise zählen für Playbooks nicht als Bestätigung, bis ein weiteres Projekt sie mit Messung stützt.
- Keine Kundennamen, Personendaten oder vertraulichen Details im Eintrag.
Kontext: der Projekt-Tag oder bei bereichsübergreifenden Erkenntnissen `allgemein`, `tools`, `evals`, `kosten`, `sicherheit`.

## 4 Freigabe und Ledger
- Dem Nutzer jeden Inbox-Eintrag zeigen: übernehmen / ändern / verwerfen.
- Übernommen: aus der Inbox entfernen, an `learnings/ledger.md` anhängen, committen (Abschnitt 7).
- Verworfen: aus der Inbox entfernen, nichts weiter.
- Nichts gelangt ohne OK in Ledger, Domains, Templates oder References.

## 5 Playbooks und Templates
Nach dem Übernehmen zählen, wie viele verschiedene Projekte im Ledger diesen Kontext haben:
- **1 Projekt:** Entwurf vorschlagen: `domains/<kontext>.md` (Status `entwurf`) und `templates/<kontext>/` aus dem getesteten Projektcode.
- **Anonymisieren, bevor etwas in `templates/` oder `domains/` landet (Pflicht):**
  - Ohne `.env`, `workspace/`, `logs/`, Eval-Reports.
  - Kundennamen, Firmennamen, Produktnamen, URLs, CRM-Feldnamen des Kunden, echte Beispieldaten durch Platzhalter ersetzen (`<FIRMA>`, `<CRM_FELD_SCORE>`, erfundene Leads).
  - Kundenspezifische Prompt-Passagen entfernen oder verallgemeinern.
  - Danach `grep` nach dem Kundennamen und `@` über das Template laufen lassen; Treffer = nicht fertig.
  - Dem Nutzer die Liste der ersetzten Stellen zeigen.
- **2+ Projekte mit Belegstärke `regel`:** Playbook auf Status `bestätigt` heben, Erkenntnisse beider Projekte einarbeiten, Template auf den besseren Stand bringen.
- **Erkenntnis in 2+ Kontexten bestätigt:** Änderung an der passenden `references/*.md` vorschlagen. Nur dann ändern sich die stabilen Regeln.
- Keine leeren Bereichs-Gerüste vorab anlegen.

Playbook-Format:
```markdown
---
status: entwurf | bestätigt
projekte: [<pfad>, <pfad>]
---
# <Kontext>
## Bewährtes Muster
## Tools, die sich bewährt haben
## Typische Fehler und Gegenmittel
## Eval-Fälle, die immer dazugehören
## Kosten-Richtwerte
```

## 6 Aufräumen
Vorschlagen, sobald ein Kontext mehr als ~50 Ledger-Einträge hat oder eine Datei über ~300 Zeilen wächst. Immer nur einen Kontext:
- Widersprüche auflösen: neuere und besser belegte Regel bleibt.
- Doppeltes zusammenfassen.
- Veraltetes streichen (z. B. alte Library-Versionen).
Änderungsliste zeigen, erst nach OK umsetzen, dann committen.

## 7 Git
- Fehlt `.git` im Skill-Ordner: `git init` und ersten Commit anlegen.
- Pro übernommener Erkenntnis bzw. Aufräumaktion ein Commit: `learn(<kontext>): <kurz> [<projektname>]` oder `consolidate(<kontext>): <kurz>`.
- Rücknahme auf Wunsch: passenden Commit mit `git log` finden, mit `git revert` zurücknehmen.
