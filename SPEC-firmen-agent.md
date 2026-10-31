# Spec: Firmen-Agent – lernt aus dem Unternehmen und baut sich selbst

Status: Entwurf 2026-10-14 · Grundlage: Gespräch vom 2026-10-14, `setup-entwurf/SPEC-build-agent.md`, `test-lead-agent/`

## 1 Vision

Ein Agent kommt ohne Wissen in ein Unternehmen und kann irgendwann alles. Er erkennt wiederkehrende Aufgaben in den Systemdaten. Mitarbeiter machen ihm Aufgaben vor und erklären laut, warum („Zeig's mir“). Daraus baut er mit dem `build-agent`-Harness eigene Agenten. Er übt mit eigenem Cursor, während der Mitarbeiter zusieht und korrigiert („Ich probier's“). Danach muss er sich im Backtest und im Schattenmodus bewähren und übernimmt erst dann allein. Grenzfälle gehen an den Sachbearbeiter.

Lernmethode: **ich mache vor → wir machen zusammen → du machst allein.**

Autonomie wird **pro Prozess** verdient, nie global. Der Kreislauf ist das Produkt, nicht die einzelne Aufgabe.

### Lernkreislauf pro Prozess
| Stufe | Wer | Ergebnis |
|---|---|---|
| 1 Entdecken | Agent liest Systemdaten | Kandidatenliste (Menge × Gleichförmigkeit × geringes Risiko) |
| 2 Zeig's mir | Mitarbeiter, freiwillig | Aufnahme: Bildschirm, Klicks, Sprache mit Begründung |
| 3 Bauen | Agent-Fabrik (`build-agent`) | versionierter Agent mit Regeln im Code und Eval-Fällen |
| 4 Ich probier's | Agent zeigt strukturierte Vorschau („Ich würde buchen: Konto 4930 …“), Mitarbeiter korrigiert; Cursor erst nach dem MVP | Korrekturen → neue Eval-Fälle → Neubau; Ende nach 3 Läufen ohne Korrektur |
| 5 Backtest | Agent auf historischen Fällen | Anteil, den er allein übernähme, und seine Fehlerquote darin, verglichen mit den Menschen |
| 6 Schatten | Agent läuft live mit, führt nichts aus | Wochenbericht + Knopf „Aktivieren“ |
| 7 Autonom | Agent | klare Fälle allein, Grenzfälle vorbereitet an Menschen, Stichproben, automatisches Rückstufen bei Qualitätsabfall |

### Leitplanken
- **Leitsatz: KI übersetzt und schlägt vor. Code entscheidet, ob ein Vorschlag gilt, und führt ihn aus. Autonomie gibt ein Mensch frei, auf Grundlage von Zahlen aus Code; zurückgenommen wird sie automatisch.** (Entschieden 2026-10-15, Herleitung: `ANALYSE-ki-vs-algorithmus.md`)
- **KI zur Bauzeit, Code zur Laufzeit.** Die KI schreibt Regeln und Prompts, der Backtest prüft sie. Im Betrieb läuft jeder Fall zuerst über Code (Regel, Tabelle, gelerntes Modell); nur was der Code nicht kennt, geht an ein LLM oder an einen Menschen. Grund: prüfbar, weniger Daten nach außen. Die API-Kosten sind kein Grund, sie liegen geschätzt bei ~60–130 $ pro Monat und Mittelständler (Annahmen: `ANALYSE-ki-vs-algorithmus.md` 4.5, ungemessen).
- Bildschirmdaten nur über „Zeig's mir“ (freiwillig, sichtbar), **keine Dauerüberwachung**.
- Bewertet wird der Agent, **nie einzelne Mitarbeiter** (§87 BetrVG, EU AI Act). Das ist eine Architekturregel, keine Richtlinie.
- Irreversible Aktionen (Zahlen, extern senden, löschen, buchen im Echtsystem) laufen nur nach Freigabe.
- Computer Use dient zum Lernen und als Ersatz. Im Betrieb gilt API vor Cursor. Nicht im MVP (2026-10-15).
- Die Obergrenze für eine Schwelle ist die Übereinstimmung der Menschen untereinander, nicht 100 %.

## 2 Architektur: Kern und Bereichspakete

**Kern:** gilt für alle Bereiche, umfasst über 110 der 124 Anforderungen.
**Bereichspaket:** wird dazugesteckt, Finance ist das erste. Ein Paket enthält:
- Konnektoren des Kernsystems (ERP, CRM, HR-Software, Ticketsystem),
- Dokumenttypen und Parser,
- Standardregeln und harte Grenzen (z. B. „Betrag > X → Mensch“),
- Prüf- und Aufbewahrungspflichten (Finance: GoBD),
- Testdaten (erfunden),
- optional Rollen-Startentwürfe aus agency-agents.

Ein Paket entspricht dem bestehenden Harness-Konzept `domains/<kontext>.md` + `templates/<kontext>/`.

Bereichsspezifische Anforderungen tragen unten **[Paket]**, alle anderen gehören zum Kern.

## 3 Ist-Stand

| Vorhanden | Wo | Deckt ab |
|---|---|---|
| `build-agent`-Skill: Klären → Muster → Scaffold → Tools → Sicherheit → Evals → Kosten → Ausführen → Retro | `setup-entwurf/build-agent/` | Kern der Agent-Fabrik (I), Evals (V), Kosten (T) als Regeln |
| Lernkreislauf Inbox → Ledger → Playbook/Template | `build-agent/learnings/`, `domains/`, `templates/` | Lernen über Projekte (58), Bereichspakete (Abschnitt 2) |
| Getesteter Lead-Agent: `create_agent` + `HumanInTheLoopMiddleware`, Tool-Vertrag `status/summary/data/next_actions`, Log-Maskierung, Injection-Schutz, `run_evals.py` mit pass@k | `test-lead-agent/`, `templates/lead-qualification/` | Vorlage für jeden erzeugten Agenten: 52, 64, 67, 97, 102, 112, 114, 123 |
| Bekannte Fallstricke (Retry `on_failure="error"`, HITL-Resume pro `action_request`, TLS/truststore, `uv init --bare`) | `test-lead-agent/RETRO.md` | Betriebssicherheit der Fabrik |

**Größte Lücke im Ist-Stand:** `build-agent` ist ein Claude-Code-Skill und läuft interaktiv mit einem Menschen. Das Produkt braucht eine Fabrik, die automatisch auf einem Server läuft. Brücke (zu verifizieren): den Skill über das Claude Agent SDK ohne Oberfläche ausführen. Die Klär-Fragen beantwortet dann die Prozessbeschreibung aus Stufe 2, die menschlichen OKs werden zu Freigaben in der Web-Oberfläche.

## 4 Anforderungen (124)

**[MVP]** = erster Prototyp. **[Paket]** = bereichsspezifisch (Beispiel Finance).

### A. Plattform und Grundlagen
1. **[MVP]** Python als Hauptsprache, LangGraph für Abläufe, Pydantic für alle Datenformate, `uv` für Abhängigkeiten.
2. **[MVP]** Zentrale Datenbank (Postgres) für Firmen, Prozesse, Fälle, Agenten, Ergebnisse.
3. Dateispeicher für Aufnahmen, Dokumente, PDFs (S3-kompatibel, EU-Region).
4. Warteschlange für lange Aufgaben (Backtests, Builds, Aufnahme-Auswertung).
5. Zeitplaner für wiederkehrende Läufe (Schattenmodus, Stichproben, Berichte).
6. Mandantenfähigkeit: strikte Datentrennung auf Datenbank- und Speicherebene.
7. Hosting ausschließlich in der EU.
8. LLM-Anbieter mit EU-Datenverarbeitung und AVV.

### B. Konnektoren
9. **[MVP]** E-Mail-Postfach lesen (IMAP oder Microsoft Graph), zunächst ein Sammelpostfach.
10. **[MVP] [Paket]** Ein Zielsystem des Bereichs, im Prototyp als Testsystem (Finance: ERP mit Buchungen, Kreditoren, Belegen).
11. **[Paket]** Echte Anbindungen des Bereichs (Finance: DATEV, SAP, Lexware, sevDesk; je nach Kunde).
12. **[Paket]** Heikle Systeme nur lesend (Finance: Banking nur Kontoumsätze, Zahlungen nie direkt).
13. Ticketsysteme und CRM als weitere Quellen.
14. Integrationsbaukasten für Standard-Tools statt jede Anbindung selbst zu bauen.
15. Jede Anbindung meldet ihre Fähigkeiten: lesen, schreiben, irreversibel.
16. Zugangsdaten nur verschlüsselt im Secret-Speicher, nie in Code, Prompts oder Logs.

### C. Daten einlesen und vereinheitlichen
17. **[MVP]** Einheitliches Fall-Format für alle Quellen: Eingang, menschliche Handlung, Ergebnis, Zeitstempel, Quelle.
18. **[MVP]** Fälle quellenübergreifend verknüpfen (diese Mail → diese Buchung).
19. **[Paket]** Dokumente des Bereichs auslesen (Finance: PDF-Rechnungen, XRechnung/ZUGFeRD, Scans).
20. Doppelte und unvollständige Fälle erkennen und markieren.
21. Historischer Import der letzten Monate für den Backtest.

### D. Datenschutz bei den Daten
22. **[MVP]** Mitarbeiter pseudonymisiert („Bearbeiter 3“), nie mit Namen gespeichert.
23. Keine Auswertung pro Mitarbeiter: Das System kann technisch keine Leistungsberichte über Personen erzeugen.
24. Personenbezogene Daten von Kunden und Lieferanten werden in Logs maskiert.
25. Aufbewahrungsfristen pro Datenart, danach automatisch löschen.
26. Vollständiger Export und vollständige Löschung pro Firma.

### E. Prozess-Entdeckung
27. **[MVP]** Ähnliche Fälle automatisch gruppieren.
28. **[MVP]** Pro Gruppe den typischen Ablauf ableiten (Schritte, Entscheidungen).
29. **[MVP]** Kandidaten bewerten nach Menge × Gleichförmigkeit × geringem Risiko.
30. **[MVP]** Vorschlagsliste mit Häufigkeit und Bewertung.
31. Abweichungen finden und daraus Rückfragen formulieren („Bei 12 Fällen wurde anders entschieden, warum?“).
32. Neue Prozesse auch nach dem Start fortlaufend erkennen.

### F. Firmenwissen
33. **[MVP]** Wissensspeicher pro Firma (Regeln, Ausnahmen, Besonderheiten).
34. Jede Wissenseinheit hat Quelle und Gültigkeitsdatum.
35. Wissen mit Zeitbezug, Regeländerungen versioniert.
36. Widersprüche erkennen → Rückfrage an einen Menschen statt raten.
37. Menschen können Wissen ansehen, korrigieren, löschen.

### G. „Zeig's mir“-Aufnahme
38. Desktop-App (Windows, später Mac), die der Mitarbeiter selbst startet.
39. Start/Stopp, Pause, sichtbare Anzeige „Aufnahme läuft“.
40. Nur gewähltes Fenster/Programm aufnehmen, nicht den ganzen Desktop.
41. Klicks, Tastatureingaben (ohne Passwörter), Fensterwechsel mitschreiben.
42. Mikrofon aufnehmen und transkribieren (Deutsch).
43. Sensible Bereiche schwärzen (Passwortfelder, Programme auf einer Sperrliste).
44. Mitarbeiter prüft die Aufnahme vor dem Hochladen und kann Teile löschen.
45. Upload verschlüsselt, Speicherung nur in der EU.
46. Browser-Plugin als leichtere Alternative für Web-Programme.

### H. Aufnahme auswerten
47. Aus Bild, Klicks und Sprache eine Schrittfolge erzeugen.
48. Gesprochene Begründungen als Regeln ins Firmenwissen übernehmen.
49. Unklare Stellen erkennen und nachfragen.
50. Schrittfolge vom Mitarbeiter bestätigen lassen, bevor gebaut wird.

### I. Agent-Fabrik
51. **[MVP]** Aus einer Prozessbeschreibung automatisch einen Agenten erzeugen (Prompt, Tools, Regeln, Grenzen).
52. **[MVP]** Harte Regeln im Code, nicht nur im Prompt.
53. **[MVP]** Eval-Fälle automatisch aus historischen Fällen erzeugen.
54. Rollen aus agency-agents als ersten Prompt-Entwurf nutzen.
55. Prompt-Optimierung gegen die Messgröße „Übereinstimmung mit dem Menschen“.
56. Jeder Agent ist versioniert (Änderung, Grund, Ergebnisse).
57. Rückkehr zu einer älteren Agent-Version mit einem Klick.
58. Erkenntnisse fließen ins Harness-Ledger, **ohne Kundendaten**, nur als allgemeine Muster.

### J. Ausführungsumgebung
59. **[MVP]** Jeder Agent läuft abgeschottet (kein Fremdmandant, nur freigegebene Netzwerkziele).
60. Code-Sandbox für Berechnungen, Tabellen, PDFs.
61. Computer-Use-Umgebung (VM bzw. Browser), in der der Agent Maus und Tastatur bedient.
62. API-Vorrang, Cursor nur als Ersatz.
63. Gelernte Cursor-Abläufe, wo möglich, durch API-Aufrufe oder fest abspielbare Skripte ersetzen.
64. Limits pro Lauf: Schritte, Kosten, Dauer.

### K. „Ich probier's“
65. Live-Ansicht dessen, was der Agent auf dem Bildschirm macht.
66. **[MVP]** Stopp-Knopf, sofortiger Halt.
67. **[MVP]** Jede schreibende Aktion wartet auf einen Klick des Mitarbeiters.
68. Bevorzugt in einem Testsystem bzw. einer Kopie üben.
69. **[MVP]** Korrektur per Text, später per Sprache.
70. **[MVP]** Jede Korrektur wird ein Eval-Fall.
71. **[MVP]** Nach einer Korrektur Neubau und erneuter Versuch.
72. **[MVP]** Abbruchregel: 3 Läufe hintereinander ohne Korrektur → bereit für den Backtest.

### L. Backtest
73. **[MVP]** Agent auf historischen Fällen laufen lassen, ohne Schreibzugriff.
74. **[MVP]** Zurückgehaltene Fälle, die nie zum Anpassen benutzt werden.
75. Übereinstimmung der Menschen untereinander messen (Obergrenze).
76. **[MVP]** Bericht mit zwei Kennzahlen: Anteil, den der Agent allein übernähme, und Fehlerquote darin, verglichen mit den Menschen.
77. Falsche Fälle einzeln auflisten.

### M. Schattenmodus
78. Parallel zu echten neuen Fällen mitlaufen, nichts ausführen.
79. Mit der späteren menschlichen Entscheidung vergleichen.
80. Wochenbericht: Trefferquote, geschätzte gesparte Zeit, auffällige Fälle.
81. Knopf „Aktivieren“, nur für Berechtigte.

### N. Autonomie und Grenzfälle
82. Autonomie-Stufe pro Prozess: aus, Schatten, Vorschlag, autonom.
83. Schwellenwerte pro Prozess, festgelegt vom Kunden.
84. Unsicherheit erkennen (widersprüchliche Läufe, untypischer Fall, harte Regel greift).
85. Unsichere Fälle an den Sachbearbeiter, mit Kontext und Entwurf.
86. Irreversible Aktionen immer mit Freigabe, sofern der Kunde es festlegt, auch auf Stufe „autonom“.
87. **[Paket]** Vier-Augen-Prinzip für kritische Aktionen (Finance: Zahlungen) einstellbar.

### O. Laufender Betrieb
88. Stichproben: festgelegter Anteil autonomer Fälle wird von Menschen nachgeprüft.
89. Qualitätsabfall erkennen (neue Formate, neue Regeln).
90. Bei Abfall automatisch eine Stufe zurück.
91. Not-Aus pro Prozess und für die ganze Firma.
92. Benachrichtigungen bei Fehlern, Grenzfällen, Qualitätsabfall (Teams, E-Mail).

### P. Rechte und Zugriff
93. Rollen: Admin, Prozessverantwortlicher, Sachbearbeiter, Prüfer.
94. Agent sieht nur die für seinen Prozess freigegebenen Systeme und Daten.
95. Login über Firmenkonto (Microsoft Entra ID / SSO).
96. Gespeichert wird, wer welche Stufe freigeschaltet hat.

### Q. Sicherheit
97. **[MVP]** Fremdinhalt (Mails, PDFs, Webseiten) ist Daten, keine Anweisung.
98. Tool-Ausgaben können Regeln und Rechte des Agenten nie ändern.
99. Erzeugter Agent-Code wird vor dem Einsatz automatisch geprüft.
100. Verschlüsselung bei Übertragung und Speicherung.
101. Penetrationstest vor dem ersten echten Kunden.

### R. Nachvollziehbarkeit und Prüfpflichten
102. **[MVP]** Jeder Schritt wird geloggt: was, warum, Daten, Ergebnis, Kosten.
103. Tracing und Bewertungen in selbst gehostetem System in der EU.
104. **[Paket]** Logs unveränderbar (Finance: GoBD).
105. Pro Aktion nachvollziehbar: Mensch oder Agent, welche Agent-Version.
106. **[Paket]** Exportierbare Berichte für Prüfer (Finance: Wirtschaftsprüfer, Revision).

### S. Recht und Mitbestimmung
107. Vorlage für eine Betriebsvereinbarung: was erfasst wird und was nicht.
108. Vorlage für eine Datenschutz-Folgenabschätzung (DSFA).
109. AVV mit jedem Kunden und mit dem LLM-Anbieter.
110. EU AI Act prüfen: Protokollierung, menschliche Aufsicht, Transparenz.
111. Rechtliche Prüfung durch einen Fachanwalt vor dem ersten echten Kunden.

### T. Kosten
112. **[MVP]** Budget pro Lauf im Code, Abbruch beim Überschreiten.
113. Kleines Modell für einfache Schritte, großes nur bei Bedarf.
114. Prompt-Caching (feste Teile vorn).
115. Kosten pro Prozess und Firma messen und anzeigen (Grundlage für Preise).

### U. Oberflächen
116. **[MVP]** Web-Oberfläche: gefundene Prozesse, Agenten, Berichte.
117. Inbox für Sachbearbeiter: Grenzfälle und Vorschläge zum Abnicken.
118. Dashboard pro Prozess: Stufe, Trefferquote, Menge, Kosten.
119. Teams-Anbindung für Rückfragen und Benachrichtigungen.
120. Oberfläche komplett auf Deutsch.

### V. Qualität des Systems selbst
121. **[MVP]** Evals für die Fabrik: Aus einer bekannten Prozessbeschreibung entsteht ein Agent, der besteht.
122. **[MVP] [Paket]** Erfundener Testdatensatz pro Bereich (Finance: Rechnungen, Lieferanten, Ausnahmen).
123. Freigabe-Test: Irreversible Aktion ohne Freigabe hinterlässt keine Wirkung.
124. Mandantentrennung testen: Firma A sieht nie Daten von Firma B.

## 5 Abdeckung durch Open Source, Integration, Lücken, Closed Source

Lizenz, Sterne und letzte Aktivität wurden am 2026-10-14 über die GitHub-API geprüft. „prüfen“ heißt: GitHub zeigt keine eindeutige Lizenz (oft gemischt oder Source-available), vor kommerzieller Nutzung klären. **AGPL/GPL** ist für einen geschlossenen SaaS-Dienst problematisch: nur getrennt betreiben oder rechtlich prüfen.

Die Closed-Source-Angaben stammen aus Marktkenntnis und wurden **nicht** einzeln geprüft (Funktionsumfang, EU-Hosting, Preise vor Nutzung klären).

### A. Plattform
| Open Source | Lizenz | Integration mit Ist-Stand |
|---|---|---|
| langchain-ai/langgraph | MIT | schon im Stack; Postgres-Checkpointer für Zustand und Freigaben |
| hatchet-dev/hatchet | MIT | Warteschlange + Zeitplaner (4, 5) in einem, Postgres-basiert |
| procrastinate-org/procrastinate | MIT | leichtere Alternative: Warteschlange direkt in Postgres |
| temporalio/temporal | MIT | erst nötig bei sehr langen, ausfallsicheren Abläufen, für MVP zu schwer |

Lücke: keine. Mandantentrennung (6) ist Eigenbau (Postgres Row-Level-Security + getrennte Speicher-Präfixe).

### B. Konnektoren
| Open Source | Lizenz | Integration |
|---|---|---|
| ComposioHQ/composio | MIT | Standard-Tools (14) als LangChain-Tools; Ausgaben in den Tool-Vertrag `status/summary/data/next_actions` einwickeln |
| airbytehq/airbyte | prüfen | historischer Massenimport (21) |
| odoo/odoo (Community) | LGPL-3, prüfen | **Testsystem für MVP (10)**: echtes ERP mit Oberfläche (für Cursor) und API (für API-Vorrang) |
| frappe/erpnext | GPL-3.0 | Alternative zu Odoo, nur als getrennt betriebenes Testsystem |

Lücke: deutsche Finance-Systeme (11). → Closed: **DATEV**-Schnittstellen (DATEV-Marktplatz, Partnerprogramm nötig), Lexware/sevDesk-APIs, Unified-APIs wie **Merge.dev**, **Apideck**, **Codat** (Buchhaltung). Banking lesend (12): **finAPI**, **Tink**, **GoCardless Bank Account Data** (PSD2).

### C. Daten einlesen
| Open Source | Lizenz | Integration |
|---|---|---|
| docling-project/docling | MIT | PDF/Scan → strukturierter Text (19) als Tool |
| Unstructured-IO/unstructured | Apache-2.0 | Alternative, viele Formate |
| mindee/doctr | Apache-2.0 | OCR für schlechte Scans |
| invoice-x/invoice2data | MIT | Rechnungsfelder per Vorlage |
| pretix/python-drafthorse | Apache-2.0 | ZUGFeRD lesen/schreiben |
| akretion/factur-x | prüfen | Factur-X/ZUGFeRD |

Lücke: Fall-Format und Verknüpfung (17, 18, 20) sind Eigenbau (Pydantic-Modell). Hohe Extraktionsgenauigkeit ohne Training → Closed: **Rossum**, **Klippa**, **Mindee API**, **Azure Document Intelligence**.

### D. Datenschutz
| Open Source | Lizenz | Integration |
|---|---|---|
| data-privacy-stack/presidio (früher microsoft/presidio) | MIT | Maskierung (22, 24) ersetzt die bisherige einfache Log-Maskierung im Lead-Agenten; deutsche Erkenner selbst ergänzen |

Lücke: „technisch keine Leistungsberichte über Personen“ (23) ist Architektur (Pseudonym-Schlüssel getrennt gespeichert, keine Abfragen pro Bearbeiter). Kein Produkt deckt das ab.

### E. Prozess-Entdeckung (Kern-USP)
| Open Source | Lizenz | Integration |
|---|---|---|
| MaartenGr/BERTopic | MIT | Fälle gruppieren (27) |
| pm4py | **AGPL-3.0** | Ablauf aus Ereignissen ableiten (28); nur für Experimente oder getrennt |

**Größte Lücke:** Ablauf ableiten, Kandidaten bewerten, Rückfragen (28–32). Kein OSS-Projekt erledigt „finde Prozesse und mach daraus Agent-Kandidaten“. Eigenbau. → Closed (Konkurrenz und Referenz, nicht zum Einbauen): **Celonis** (inkl. Make), **UiPath Process/Task Mining**, **Microsoft Power Automate Process Mining**, **SAP Signavio**, **Mimica** (Task Mining → Automatisierungsvorschläge, am nächsten an der Idee), **Skan.ai**, **Soroco Scout**.

### F. Firmenwissen
| Open Source | Lizenz | Integration |
|---|---|---|
| getzep/graphiti | Apache-2.0 | Wissensgraph mit Zeitbezug (33–36), Quelle pro Fakt; als Tool `wissen_suchen` / `wissen_eintragen` |
| mem0ai/mem0 | Apache-2.0 | einfachere Alternative |
| topoteretes/cognee | Apache-2.0 | Alternative |

Lücke: Oberfläche zum Ansehen und Korrigieren (37). Eigenbau.

### G. „Zeig's mir“-Aufnahme
| Open Source | Lizenz | Integration |
|---|---|---|
| OpenAdaptAI/OpenAdapt | MIT | **wichtigster Fund**: nimmt Bildschirm + Eingaben auf und lernt daraus Abläufe (38–41, 47); als Basis der Desktop-App prüfen |
| rrweb-io/rrweb | MIT | Browser-Plugin (46): zeichnet Web-Sitzungen als Ereignisse auf, schwärzt Eingabefelder |
| SYSTRAN/faster-whisper | MIT | Transkription Deutsch (42), lokal oder auf eigenem EU-Server |
| m-bain/whisperX | BSD-2 | Transkription mit Zeitstempeln pro Wort, um Sprache mit Klicks zu verknüpfen |
| screenpipe/screenpipe | prüfen | Daueraufnahme, **widerspricht der Leitplanke**; nur Code-Ideen |

Lücke: Freigabe-Vorschau, Löschen von Teilen, Sperrliste (43, 44). Eigenbau auf OpenAdapt. → Closed: **Scribe**, **Tango** (Aufnahme → Schritt-für-Schritt-Anleitung, gute Vorlage für die Bedienung).

### H. Aufnahme auswerten
| Open Source | Lizenz | Integration |
|---|---|---|
| OpenAdaptAI/OpenAdapt | MIT | Aufnahme → Schrittfolge (47) |

Lücke: Begründungen aus der Sprache → Regeln (48), Rückfragen (49). Eigenbau mit LLM, Ergebnis in Graphiti. Bestätigung (50) = Freigabe-Muster aus dem Harness.

### I. Agent-Fabrik
| Open Source | Lizenz | Integration |
|---|---|---|
| eigener `build-agent`-Harness | – | **Kern**: Scaffold, Tools, Sicherheit, Evals, Retro, Ledger (51–53, 56, 58) |
| `templates/lead-qualification` | – | Vorlage für jeden erzeugten Agenten |
| msitarzewski/agency-agents | MIT | Startentwürfe (54) in Phase Scaffold |
| stanfordnlp/dspy | MIT | Prompt-Optimierung (55); nur den Prompt optimieren, Ergebnis in den `create_agent`-Agenten übernehmen (Prototyp nötig) |
| ShengranHu/ADAS | Apache-2.0 | nur Ideen, inaktiv seit 2025-01 |

Lücke: Harness läuft nur interaktiv in Claude Code (siehe Abschnitt 3). → Brücke über das **Claude Agent SDK** (closed Modell, SDK offen; Skill-Unterstützung zu verifizieren). Versionierung und Rücksprung (56, 57): Git pro Agent, wie im Harness für Learnings vorgesehen.

### J. Ausführungsumgebung
| Open Source | Lizenz | Integration |
|---|---|---|
| e2b-dev/E2B | Apache-2.0 | Code-Sandbox (60) |
| trycua/cua | MIT | VMs für Computer Use (61), auch Windows-Desktops |
| browser-use/browser-use | MIT | Agent bedient Browser (61) |
| browserbase/stagehand | MIT | Browser-Automation mit festen Schritten + KI, gut für 63 |
| steel-dev/steel-browser | Apache-2.0 | selbst gehostete Browser-Infrastruktur mit Live-Ansicht |
| anthropics/claude-quickstarts | MIT | Referenz-Implementierung Computer Use |
| browser-use/workflow-use | **AGPL-3.0** | „einmal aufnehmen, fest abspielen“ (63); nur Ideen oder getrennt |
| Skyvern-AI/skyvern | **AGPL-3.0** | Alternative Browser-Agent; nur getrennt |
| daytonaio/daytona | – (archiviert) | nicht verwenden |

Lücke: keine grundsätzliche. Netzwerk-Sperre pro Agent (59) ist Konfiguration. → Closed: Computer-Use-Modelle (**Claude Computer Use**, **OpenAI CUA**), gehostete Browser (**Browserbase**), gehostete Sandboxes (**E2B Cloud**).

### K. „Ich probier's“
| Open Source | Lizenz | Integration |
|---|---|---|
| novnc/noVNC | prüfen (MPL-2.0) | Live-Ansicht der VM im Browser (65) |
| steel-dev/steel-browser | Apache-2.0 | Live-Ansicht für Browser-Fälle |
| LangGraph `interrupt` / `HumanInTheLoopMiddleware` | MIT | Freigabe pro schreibender Aktion (67), **schon im Lead-Agenten getestet** |
| langchain-ai/agent-inbox | MIT, **archiviert** | nur als Vorlage für die Freigabe-Oberfläche |

Lücke: Korrektur → Eval-Fall → Neubau → Abbruchregel (69–72). Das ist der Kern des Lernkreislaufs und Eigenbau, verbindet aber vorhandene Harness-Teile (`evals/cases.jsonl`, `run_evals.py`).

### L. Backtest
| Open Source | Lizenz | Integration |
|---|---|---|
| eigenes `run_evals.py` | – | Basis; um Abdeckung und Fehlerquote (76) erweitern |
| promptfoo/promptfoo | MIT | wenn Berichte und Vergleiche größer werden |
| confident-ai/deepeval | Apache-2.0 | LLM-Judge-Metriken |
| UKGovernmentBEIS/inspect_ai | MIT | strenge Eval-Läufe |
| scikit-learn-contrib/MAPIE | BSD-3 | Konfidenz-Schwellen statistisch absichern (Abdeckung vs. Fehler) |

Lücke: Übereinstimmung zwischen Menschen (75) ist eine kleine Eigenrechnung.

### M. Schattenmodus
OSS: Bausteine aus L + Zeitplaner aus A. **Lücke: Eigenbau** (das Verkaufsargument, gehört nicht ausgelagert).

### N. Autonomie und Grenzfälle
| Open Source | Lizenz | Integration |
|---|---|---|
| scikit-learn-contrib/MAPIE | BSD-3 | Unsicherheit (84) |
| HITL-Middleware | MIT | Freigaben (86, 87) |

Lücke: Stufenmodell pro Prozess (82, 83). Eigenbau, eine Tabelle + Prüfung im Code vor jeder Aktion.

### O. Laufender Betrieb
| Open Source | Lizenz | Integration |
|---|---|---|
| evidentlyai/evidently | Apache-2.0 | Qualitätsabfall und Datenänderung erkennen (89) |
| langfuse/langfuse | MIT-Kern | Stichproben-Bewertung (88) |

Lücke: automatisches Rückstufen und Not-Aus (90, 91). Eigenbau, wenige Zeilen auf dem Stufenmodell.

### P. Rechte und Zugriff
| Open Source | Lizenz | Integration |
|---|---|---|
| keycloak/keycloak | Apache-2.0 | SSO, Entra-ID-Anbindung (95) |
| cerbos/cerbos | Apache-2.0 | Rechte-Regeln (93, 94) |

Lücke: keine. → Closed: **Microsoft Entra ID** ist beim Kunden ohnehin vorhanden; Auth0/WorkOS als gehostete Alternative.

### Q. Sicherheit
| Open Source | Lizenz | Integration |
|---|---|---|
| NVIDIA/garak | Apache-2.0 | Angriffs-Tests gegen erzeugte Agenten (101) |
| promptfoo (Red Teaming) | MIT | Injection-Fälle als Eval (97) |
| NVIDIA-NeMo/Guardrails | prüfen | Laufzeit-Leitplanken |
| semgrep/semgrep | LGPL-2.1 | Prüfung des erzeugten Agent-Codes (99), als getrenntes Programm unkritisch |
| protectai/llm-guard | MIT, **archiviert** | nicht verwenden |

Lücke: keine. Injection-Muster aus dem Lead-Agenten bleibt Grundlage. → Closed: Pentest-Dienstleister (101).

### R. Nachvollziehbarkeit
| Open Source | Lizenz | Integration |
|---|---|---|
| langfuse/langfuse | MIT-Kern, prüfen | Tracing (102, 103), selbst gehostet in der EU, LangGraph-Anbindung |
| codenotary/immudb | prüfen | unveränderbares Protokoll (104) |

Lücke: GoBD-Konformität (104, 106) ist Nachweis- und Prozessarbeit, kein Code allein. → Closed: Prüfung bzw. Testat durch Wirtschaftsprüfer (IDW PS 880 o. ä.).

### S. Recht und Mitbestimmung
OSS: keine. **Lücke vollständig.** → Closed/Dienstleistung: Fachanwalt Arbeitsrecht (107), Datenschutzberatung (108, 110), Compliance-Plattformen (**Vanta**, **Drata**, **Secfix**) für ISO 27001/SOC 2.

### T. Kosten
| Open Source | Lizenz | Integration |
|---|---|---|
| BerriAI/litellm | MIT-Kern, prüfen | Modell-Routing und Budgets pro Mandant (113, 115) |
| Harness-Regeln | – | Budget pro Lauf, Caching (112, 114) schon im Lead-Agenten |

Lücke: keine.

### U. Oberflächen
| Open Source | Lizenz | Integration |
|---|---|---|
| argilla-io/argilla | Apache-2.0 | Inbox für Korrekturen und Grenzfälle (117), Korrekturen direkt als Eval-Daten |
| HumanSignal/label-studio | Apache-2.0 | Alternative |
| microsoft/teams-sdk | MIT | Teams-Anbindung (119) |

Lücke: Haupt-Web-Oberfläche und Dashboard (116, 118). Eigenbau.

### V. Qualität des Systems
OSS: Eval-Werkzeuge aus L. Lücke: Fabrik-Evals (121) und Finance-Testdaten (122). Eigenbau, Erweiterung von `templates/*/evals/`.

## 6 Lückenübersicht

| Lücke | Art | Lösung |
|---|---|---|
| Prozess-Entdeckung → Agent-Kandidaten (E 28–32) | **USP** | Eigenbau |
| Korrektur-Kreislauf bis zur Schwelle (K 69–72) | **USP** | Eigenbau aus Harness-Teilen |
| Schattenmodus + Bericht + Aktivieren (M) | **USP** | Eigenbau |
| Stufenmodell pro Prozess, Rückstufen (N 82–83, O 90–91) | USP | Eigenbau |
| Harness automatisch statt interaktiv (I) | Technik | Claude Agent SDK prüfen |
| Begründungen → Regeln (H 48–49) | Technik | Eigenbau mit LLM + Graphiti |
| Aufnahme-Freigabe, Sperrliste (G 43–44) | Technik | Eigenbau auf OpenAdapt |
| „keine Leistungsberichte“ (D 23) | Architektur | Eigenbau |
| Deutsche Finance-Systeme (B 11, 12) | Zugang | Closed: DATEV, Unified-APIs, PSD2-Anbieter |
| Extraktion mit hoher Genauigkeit (C 19) | Qualität | Closed optional: Rossum, Azure Document Intelligence |
| GoBD, Betriebsvereinbarung, DSFA, AI Act (R, S) | Recht | Dienstleister, Compliance-Plattform |

Die Lücken, die zum USP gehören, sollen Eigenbau bleiben. Alles andere wird eingekauft oder übernommen.

## 7 Weg vom Ist-Stand zum MVP

1. **Testwelt:** Odoo Community in Docker mit erfundenen Finance-Daten (10, 122) + Sammelpostfach mit erfundenen Mails (9).
2. **Fall-Format** als Pydantic-Modell + Import aus Mail und Odoo-API (17, 18).
3. **Entdeckung v0:** BERTopic gruppiert, LLM leitet pro Gruppe Schritte ab, Bewertung Menge × Gleichförmigkeit × Risiko (27–30).
4. **Fabrik v0:** Prozessbeschreibung → Agent nach `templates/lead-qualification`-Muster, Eval-Fälle aus historischen Fällen (51–53). Zuerst halbautomatisch in Claude Code, danach über das Agent SDK.
5. **Ich probier's v0:** strukturierte Vorschau der Entscheidung statt Cursor, Freigabe pro schreibender Aktion über HITL-Middleware, Korrektur als Feld-Diff → `cases.jsonl` → Neubau, Abbruchregel (66–72).
6. **Backtest v0:** `run_evals.py` erweitert um Abdeckung und Fehlerquote, zurückgehaltene Fälle (73, 74, 76).
7. **Oberfläche v0:** eine einfache Web-Seite mit Kandidaten, Agenten, Bericht (116).
8. **Fabrik-Eval** (121) und **Retro** nach Harness-Regeln.

Nicht im MVP: Computer Use und Live-Ansicht (61, 65), Aufnahme-App (G, H), echte Konnektoren, Graphiti (Wissen anfangs als Datei), Rechte, Teams, Recht.

### Spätere Ausbaustufe: eigenes Modell pro Firma
Der Schattenmodus liefert pro Kunde Tausende Fälle mit richtiger Antwort. Daraus lässt sich ein kleines Modell pro Firma feinabstimmen, das beim Kunden selbst läuft (Daten bleiben im Haus, Lauf fast kostenlos). Voraussetzungen: genug Fälle, GPU-Rechenzeit, Evals gegen das API-Modell. Test vom 2026-10-14: granite4.1:8b und ornith:9b ohne Fine-Tuning nur 4/6 (granite fiel auf die Injection herein), 5- bis 10-mal langsamer als Haiku auf CPU. Deshalb nicht vor dem Schattenmodus.

Konkret (entschieden 2026-10-15):
- **Was lokal geht:** Mails lesen (kleiner Klassifikator auf Embeddings für das Anliegen, Regex für Nummern), Rechnungen (XML ohne KI; PDF über OCR + Vorlagen), Sprache (Whisper). Sonderfälle entscheiden und Regeln bauen bleiben bei Claude.
- **Trainingsdaten:** Labels aus der Verknüpfung Mail ↔ ERP (automatisch, aber nur die einfachen Fälle) + eine von Claude gelabelte und von Menschen geprüfte Stichprobe der schweren Fälle + Schattenmodus.
- **Einsatz:** Start mit Haiku. Das lokale Modell ersetzt es pro Kunde nur, wenn es im Backtest gleich gut ist. Angeboten als Option für datenschutzsensible Kunden; Kosten sind kein Grund (Ersparnis ~2–3 $ pro Monat, dafür Training und Betrieb pro Kunde).

## 8 Offene Entscheidungen
- Desktop-App auf OpenAdapt aufbauen oder eigene, schlankere Aufnahme? (Prototyp)
- DSPy zusammen mit LangChain: passt das? (Prototyp)
- Claude Agent SDK als automatische Fabrik: Skill-Unterstützung und Kosten verifizieren.
- Odoo oder ERPNext als Testsystem (Lizenz: Odoo LGPL ist leichter als ERPNext GPL).
- Welche Closed-Source-Bausteine sind beim ersten Kunden Pflicht (DATEV?), welche optional.
