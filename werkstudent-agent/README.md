# Werkstudent-Agent

Findet Werkstudentenstellen in München, schreibt geprüfte Anschreiben und legt nach Freigabe Gmail-Entwürfe an. Start: in Claude Code in diesem Ordner „Such mir neue Werkstudentenstellen“ (Skill `werkstudent-bewerbung`).

## Was du einmalig hochladen bzw. einrichten musst
| Was | Wohin | Wie |
|---|---|---|
| Gmail-Zugang | `.secrets/credentials.json` | 1. https://console.cloud.google.com → neues Projekt „werkstudent-agent“ 2. „APIs & Dienste → Bibliothek“ → **Gmail API** aktivieren 3. „OAuth-Zustimmungsbildschirm“ → Typ *Extern*, App-Name eintragen, unter *Testnutzer* deine Gmail-Adresse hinzufügen 4. „Anmeldedaten → Anmeldedaten erstellen → OAuth-Client-ID → **Desktop-App**“ → JSON herunterladen 5. Datei in `credentials.json` umbenennen und nach `.secrets/` legen. Beim ersten Entwurf öffnet sich der Browser zum Login, danach liegt `token.json` daneben. |
| Englischer Lebenslauf | `context/cv/Lebenslauf_Alexander_Saade_EN.pdf` | `Lebenslauf_Alexander_Saade_EN.docx` in Word öffnen → Speichern als PDF unter genau diesem Namen. |
| Firmenliste prüfen | `context/firmen.csv` | Zeilen streichen oder ergänzen (`ats`: greenhouse, ashby, lever, personio; `slug` aus der Karriere-URL). |
| Neue Fakten über dich | `context/profil.md` | Nur was hier steht, darf im Anschreiben stehen. |

Nichts davon kommt in Evals, Logs oder Git (`.gitignore`).

## Befehle
```
uv run python tools/scrape.py run [ba linkedin stepstone indeed ats]
uv run python tools/check_letter.py workspace/letters/<id>.md
uv run python tools/render.py workspace/letters/<id>.md
uv run python tools/gmail.py draft <id>                    (fragt immer nach Freigabe)
uv run python tools/gmail.py send <id> --confirm <id>      (fragt immer nach Freigabe)
uv run python evals/run_evals.py [k]
```

## Sicherheitsnetz
- `check_letter.py`: Zahlen, Tools, Firmen- und Eigennamen müssen in `profil.md` oder der Anzeige stehen. Nicht zu nah am Lebenslauf-Wortlaut, max. 3 Stationen, Sie-Form, Mail 4–6 Sätze, Adresse nur aus der Anzeige.
- `gmail.py`: legt Entwürfe nur für geprüfte Anschreiben an. Senden braucht `--confirm <id>`. Claude Code fragt vor jedem Aufruf (`.claude/settings.json` → `ask`). Scope `gmail.compose`: Lesen deiner Mails ist nicht möglich.
- Logs (`logs/`) maskieren E-Mail-Adressen.
