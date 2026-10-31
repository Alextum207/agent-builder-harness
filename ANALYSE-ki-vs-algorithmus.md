# Analyse: Wo braucht das Produkt KI, wo reicht ein Algorithmus?

Status: Empfehlung vom 2026-10-15, noch nicht entschieden, SPEC noch nicht angepasst.
Grundlage: Handoff vom 2026-10-15, `SPEC-firmen-agent.md`, Memories zu Vision und OSS-Bausteinen, `build-agent`-Skill (Mustertabelle, `evals.md`, `security.md`, `cost-and-caching.md`, Ledger).
Nachrechnung: `ANALYSE-ki-vs-algorithmus-nachrechnung.py` (nur Standardbibliothek, ca. 1 min). Alle Zahlen in Abschnitt 4 stammen aus diesem Skript.

## 1 Ergebnis

1. Der Leitsatz aus dem Zwischenstand stimmt in der Richtung, hat aber zwei Fehler. Ausführen ist Code (API-Aufruf), keine KI. Und „Entscheiden“ meint zwei Dinge: Die Fall-Entscheidung (welches Konto, welche Antwort) darf KI treffen, die Vertrauens-Entscheidung (darf das ohne Mensch durch) nie.
2. Neuer Leitsatz: **KI übersetzt und schlägt vor. Code entscheidet, ob ein Vorschlag gilt, und führt ihn aus. Autonomie gibt ein Mensch frei, auf Grundlage von Zahlen aus Code; zurückgenommen wird sie automatisch.**
3. Für die Fall-Entscheidung gibt es keine feste Zuordnung. Die Fabrik probiert eine Leiter von unten (Regel → gelerntes Modell → LLM liest, Regel entscheidet → LLM entscheidet → Agent) und nimmt die unterste Sprosse, die den Backtest besteht. Lösungen ohne KI sind damit ein normales Ergebnis.
4. Für die Autonomie pro Fall braucht es keinen kalibrierten Klassifikator: harte Regeln als Schranke, ein Score als Rangfolge, ein exakter Binomialtest auf versiegelten Daten als Schwelle. In der Simulation hält das Verfahren seine Zusage auch mit absichtlich unkalibriertem Score. Die Schwelle nach Punktwert bricht sie in 38–51 % der Läufe.
5. Die Statistik begrenzt das Produkt: Um „≤ 2 % Fehler“ zu belegen, braucht ein Prozess bei wahrer Quote 1 % rund 1.000 Fälle im übernommenen Anteil. Seltene Prozesse bleiben im Vorschlagsmodus. „Kann irgendwann alles“ heißt: alles als Vorschlag, das Häufige allein.
6. Von 63 Teilschritten in Abschnitt 3 brauchen 11 ein LLM, alle beim Lesen von Unstrukturiertem, beim Bauen oder als Ersatz für fehlende APIs. In der Vertrauensschicht keiner. Der Vorsprung liegt im Nachweis; Hermes gehört nicht in den kritischen Pfad.

## 2 Den Zwischenstand hinterfragt

### 2.1 Leitsatz

| Zwischenstand | Problem | Korrektur |
|---|---|---|
| „KI fürs Ausführen“ | widerspricht Anf. 62/63 und der Skill-Regel „Code statt Prompt“ | Ausführen = API-Aufruf mit geprüften Parametern. Computer Use nur beim Lernen und als Ersatz, danach in ein festes Skript übersetzen |
| „Algorithmus fürs Entscheiden“ | vermischt Fall-Entscheidung und Vertrauens-Entscheidung | Fall: Leiter (3.2). Vertrauen: nur Code |
| „KI darf hier nicht rein“ (Stufen) | der Zwischenstand setzt selbst zweimal KI in die Vertrauensschicht: LLM-Judge im Backtest, Konfidenz pro Fall | KI darf Messwerte liefern, wenn ihr eigener Fehler gemessen ist. Entschieden wird per fester Regel über diesen Messwerten |
| „deterministisch und auditierbar“ | das Recht verlangt Nachvollziehbarkeit (GoBD), Erklärbarkeit (DSGVO Art. 22 bei natürlichen Personen) und menschliche Aufsicht, nicht Determinismus | Determinismus ist der billigste Weg dahin, deshalb Pflicht in der Vertrauensschicht. In der Fall-Entscheidung reichen: Ein- und Ausgaben protokolliert, Herkunft jedes Felds, statistisches Tor |

Vier Klassen statt zwei:

| Klasse | Beispiele | Eigenschaften |
|---|---|---|
| **D** Code | Regeln, Formeln, Statistik, Verknüpfung | reproduzierbar, erklärbar, testbar |
| **M** eingefrorenes ML | Entscheidungsbaum, logistische Regression, Embeddings, OCR, Spracherkennung, NER | reproduzierbar, messbar, teils erklärbar, läuft lokal |
| **L** LLM-Aufruf | Extraktion aus Mails, Regel aus Erklärung, Entscheidung im Long Tail | streut, Daten gehen an den Anbieter, nur statistisch messbar, angreifbar über Injection |
| **A** LLM-Agent | Computer Use, Fabrik | mehrere Schritte, am schwersten zu prüfen |

Prüffrage pro Bauteil: Muss ein Prüfer das Ergebnis aus gespeicherten Daten nachrechnen können? Dann D. Prüft D das Ergebnis, bevor es wirkt? Dann sind M und L zulässig.

### 2.2 Weitere Korrekturen

- **Übereinstimmung der Menschen ist die Messlatte, keine Obergrenze.** Irrt jeder Mensch mit Quote e, stimmen zwei Menschen zu etwa 1 − 2e überein, ein fehlerfreier Agent mit einem Menschen zu 1 − e. Ein Agent auf Höhe der Inter-Human-Übereinstimmung ist also „so gut wie ein Mensch“. Darüber ist möglich, 100 % nie. (Die Memory zur Produktvision sagt „ceiling“, das ist ungenau.)
- **Kappa nur beschreibend.** Bei schiefen Klassen (95 % Standardfall) wird Kappa klein trotz hoher Übereinstimmung (Kappa-Paradox). Schwellen werden auf Fehlerquoten gesetzt.
- **Wilson oder Clopper-Pearson ist zweitrangig.** In vier nachgerechneten Fällen (p 0,5–2 %, n 100–600) haben beide dieselbe tatsächliche Abdeckung. Wichtig ist Schranke statt Punktwert. Empfehlung: exakter Binomialtest (Clopper-Pearson), weil er eine formale Garantie hat und als Lehrbuchverfahren für Prüfer erklärbar ist.
- **„3 Läufe ohne Korrektur“ (Anf. 72) belegt nur eine Fehlerquote ≤ 63 %.** Taugt als „bereit für den Backtest“, nie als Qualitätsaussage.
- **Process Mining ist für uns zweitrangig.** Gebraucht werden Fall-Paare (Eingang → menschliche Entscheidung → Ergebnis) mit genug Historie. Viele KMU-Systeme (DATEV, Lexware) liefern ohnehin nur Endzustände, kein Ereignisprotokoll. Ein Ablaufgraph lohnt nur bei echten Statusverläufen (Tickets, Odoo-Chatter). pm4py (AGPL) wird überflüssig: Varianten zählen und ein Entscheidungsbaum reichen.

## 3 Zuordnung pro Teilschritt

### 3.1 Baustein 1: Prozesse entdecken

| # | Teilschritt | Klasse | Begründung, Änderung |
|---|---|---|---|
| 1 | Konnektoren, Import | D | |
| 2 | Mail-Verläufe rekonstruieren | D | Message-ID, In-Reply-To, References; sonst Betreff ohne „AW:/WG:“ + Teilnehmer + Zeitfenster |
| 3 | Mitarbeiter pseudonymisieren | D | Adressen sind aus dem Verzeichnis bekannt; Schlüssel getrennt speichern (Anf. 22, 23) |
| 4 | Personendaten Dritter im Text maskieren | M | Presidio (NER + Muster), lokal, vor jedem LLM-Aufruf |
| 5 | E-Rechnungen lesen | D | XRechnung/ZUGFeRD sind XML. Empfang im Inland B2B seit 2025 Pflicht, Ausstellung je nach Vorjahresumsatz ab 2027 bzw. 2028. Rechnungsextraktion wird damit zu D |
| 6 | PDF/Scan lesen | M, Rest L | OCR; LLM nur für Altbestand und Auslandsrechnungen |
| 7 | Anliegen und Felder aus Mails | L, später M | Bei echten Kundendaten LLM nur auf einer maskierten Stichprobe (einige Hundert Mails), daraus ein kleiner Klassifikator auf Embeddings für den Rest (Muster TnT-LLM). Grund ist Datensparsamkeit, nicht Kosten: 10.000 Mails kosten mit Haiku 5.5 rund 3 $ |
| 8 | Taxonomie der Anliegen | L + Mensch | LLM schlägt aus der Stichprobe vor, Mensch bestätigt, „Sonstiges“ wird nachgearbeitet |
| 9 | Clustering | M, optional | nicht nötig, solange LLM-Labels bezahlbar und erlaubt sind. Embeddings trotzdem für Ähnlichkeit, Duplikate, „untypischer Fall“ |
| 10 | Schlüssel aus Text (Rechnungs-, Bestellnummer) | D, Rest L | Regex für bekannte Formate, LLM für den Rest |
| 11 | Mail ↔ ERP verknüpfen | D | exakte Schlüssel, dann Punktwertung (Betrag, Datumsfenster, Lieferant, IBAN; Fellegi-Sunter). Precision vor Recall: unsichere Verknüpfung = keine. Falsche Verknüpfungen werden zu falschen Labels im Backtest |
| 12 | Varianten, Ablaufgraph | D | Varianten zählen; Graph nur bei echten Statusverläufen |
| 13 | Entscheidungspunkte | M | Entscheidungsbaum auf Fallmerkmalen; liefert Regel-Kandidaten direkt für die Leiter |
| 14 | Gleichförmigkeit | M | = kreuzvalidierte Trefferquote dieses Baums: Wie gut lässt sich vorhersagen, was Menschen taten? Untere Schätzung der Abdeckung |
| 15 | Abweichungen finden | D/M | seltene Varianten, vom Baum falsch vorhergesagte Fälle |
| 16 | Rückfragen formulieren | D | Vorlage. Nach der Regel fragen statt nach den Fällen („Gilt für Lieferant X Kostenstelle 100 oder 200?“), damit niemand als Abweichler erkennbar wird |
| 17 | Risiko | D | Maximum aus Risiko des Anliegens und Risiko der Aktion. Die Aktion (Bankdaten ändern, zahlen, extern senden) ist über die Konnektor-Fähigkeiten (Anf. 15) bekannt und hängt nicht davon ab, ob das LLM das Anliegen richtig erkannt hat. Katalog im Bereichspaket, inkl. Fällen mit Sonderrecht (DSGVO Art. 22; AI Act Anhang III, z. B. Bonität natürlicher Personen) |
| 18 | Minuten pro Fall | Kundenangabe | fragen statt messen: Bearbeitungszeit ist ein Leistungsdatum (§87 BetrVG) |
| 19 | Ranking | D | Stunden pro Monat = Menge × Minuten × geschätzte Abdeckung. Risiko als Sperre statt als Faktor. Spalte „Monate bis Nachweis“ aus Menge und Tabelle 4.1 |
| 20 | Laufend neu entdecken | D | Verteilung der Anliegen beobachten |

### 3.2 Zwischen Baustein 1 und 2: die Fabrik

Steht nicht in der Liste, aber hier fällt die eigentliche KI-oder-Algorithmus-Entscheidung, pro Prozess und anhand von Daten.

| Sprosse | Entscheider | Klasse | Typisch für |
|---|---|---|---|
| 0 | Tabelle, feste Regel | D | Lieferant → Konto, Zahlungsstatus nachschlagen |
| 1 | gelerntes Modell | M | Kontierung aus strukturierten Feldern |
| 2 | LLM liest, Regel entscheidet | L + D | Mail-Anfrage → Felder → Regel |
| 3 | LLM entscheidet, Regeln begrenzen | L | Long Tail, ähnliche frühere Fälle als Beispiele |
| 4 | Agent mit Tools | A | Schritte erst zur Laufzeit bekannt |

- Alle Sprossen haben dieselbe Schnittstelle `entscheide(fall) → Entscheidung | weiß nicht` und laufen gegen denselben Backtest. Die Vertrauensschicht weiß nicht, welche Sprosse dahinter steckt.
- Die Fabrik baut von unten und hört bei der ersten Sprosse auf, die die Schwelle schafft. Bei Gleichstand gewinnt die besser prüfbare, dann die billigere. Das ist die Skill-Regel „Einfach vor autonom“, eine Ebene tiefer.
- Mischformen sind der Normalfall: Sprosse 0/1 für den bekannten Kern, Sprosse 3 für den Long Tail, der Rest geht an Menschen.
- KI beim Bauen ist unkritisch, weil das Ergebnis geprüft wird: Das LLM schreibt Regel-Code oder Prompt aus Beschreibung und Daten, der Backtest entscheidet. Wo möglich: KI zur Bauzeit, Code zur Laufzeit.
- Sprosse 2 ist die sicherste Sprosse mit KI. Das LLM liefert nur schemageprüfte Felder; eine Prompt-Injection kann höchstens ein Feld verfälschen, und das prüft Code gegen Stammdaten (Rechnung existiert für diesen Lieferanten, Betrag passt zum offenen Posten).

### 3.3 Baustein 2: Backtest gegen frühere Entscheidungen

| # | Teilschritt | Klasse | Begründung, Änderung |
|---|---|---|---|
| 1 | Fallsammlung | D | aus der Verknüpfung |
| 2 | Wissensstand zum Entscheidungszeitpunkt | D | größtes Leck: Stammdaten von heute, Wissen aus späteren Fällen, spätere Fälle als Beispiele. Jede Abfrage im Replay mit Stichtag, jedes Wissen mit „gültig ab“ (Anf. 34, 35) |
| 3 | Replay | D | nur lesend; Schreib-Tools zeichnen nur den Vorschlag auf (Runner-Muster aus `evals.md`). Absturz oder Timeout zählt als „nicht übernommen“; ein LLM-Lauf mit 0 Model-Calls ist ungültig (Ledger-Regel) |
| 4 | Strukturierte Ausgaben vergleichen | D | exakt, mit Toleranz oder gegen eine Menge zulässiger Antworten |
| 5 | Freitext vergleichen | erst vermeiden, dann L + D | Antworten aus strukturierter Entscheidung + Vorlage erzeugen; dann gibt es pro Fall nichts Freies zu bewerten. Sonst zerlegt ein LLM beide Texte in Aussagen und Code vergleicht. LLM-Judge nur für Ton, mit gegen Menschen gemessener Fehlerquote, nie alleinige Grundlage für „autonom“ |
| 6 | Abweichung oder Fehler? | D + Mensch | Menschen irren auch. Uneinigkeiten blind schlichten lassen (ein Dritter sieht nicht, wer was entschied) → echte Fehler von Agent und Mensch auf diesen Fällen. Dazu eine kleine Stichprobe der Einigkeitsfälle, sonst bleiben gemeinsame Fehler unsichtbar |
| 7 | Menschliche Fehlerquote | D | Stornos, Umbuchungen, wieder geöffnete Tickets, Ablehnungen im Freigabe-Workflow; ergibt eine Untergrenze |
| 8 | Vergleich Agent vs. Mensch | D | im selben Anteil der Fälle, den der Agent übernähme. Über alle Fälle gerechnet wirkt der Mensch schlechter, weil er die schweren Fälle mitträgt |
| 9 | Fehlerliste (Anf. 77) | D | gruppiert nach Merkmalen, LLM darf zusammenfassen. Nur außerhalb des versiegelten Prüftopfs (3.4) |
| 10 | Übereinstimmung der Menschen | D | siehe 2.2 und 5.4 |

Grenze des Backtests: Einstufige Entscheidungen bewertet er sauber. Bei mehrstufigen Vorgängen (Rückfrage → Antwort des Lieferanten → nächste Entscheidung) prüft er jeden Schritt mit dem historischen Verlauf davor. Was die eigene Antwort des Agenten ausgelöst hätte, zeigt er nicht. Für die ersten autonomen Prozesse daher Entscheidungen mit einem Schritt wählen.

Optimiert die Fabrik nur auf Übereinstimmung, lernt der Agent die Fehler der Menschen mit. Geschlichtete Fälle haben deshalb Vorrang vor rohen menschlichen Entscheidungen.

### 3.4 Baustein 3: Hold-out

| # | Teilschritt | Klasse | Begründung, Änderung |
|---|---|---|---|
| 1 | Zeitbasierter Split | D | bestätigt, weil er den Betrieb nachstellt. Ergänzt: Ganze Vorgänge und Duplikate bleiben in einem Topf, Sperrzone von z. B. 2 Wochen zwischen den Töpfen, mindestens ein Monatsabschluss im Prüftopf |
| 2 | Drei Töpfe | D | **Entwicklung** (älteste Daten: bauen, Korrekturen, Zeig's mir, Kandidatenschwellen), **Prüftopf** (neuere Daten: versiegelt, entscheidet über die Schwelle; das ist der Hold-out aus Anf. 74), **Schatten** (live: bestätigt) |
| 3 | Tresor | D, Architektur | Die größere Gefahr ist, wer hineinschaut: Fabrik, DSPy, Prozessverantwortliche bei der Fehlerdurchsicht. Zugriff nur über eine Schnittstelle, die Kennzahlen liefert, nie Einzelfälle. Höchstens drei Prüfungen pro Topf (je mit δ/3), danach wandert er in die Entwicklung und ein neuerer rückt nach |
| 4 | Größe | D | aus der Statistik, Tabelle 4.1 |
| 5 | Auffrischen | D | Der Schattenmodus liefert jede Woche frische, nie gesehene Fälle. Der beste Hold-out ist die Zukunft |

### 3.5 Baustein 4: Schwelle und Stufen

| # | Teilschritt | Klasse | Begründung, Änderung |
|---|---|---|---|
| 1 | Stufen | D | Zustand pro Prozess **und Segment** (z. B. bekannte vs. neue Lieferanten): aus → Schatten → Vorschlag → autonom. Freigabe irreversibler Aktionen bleibt eine eigene Einstellung (Anf. 86) |
| 2 | Hochstufen | D + Mensch | Code prüft und schaltet den Knopf frei, ein Berechtigter drückt (Anf. 81, 96). Nie automatisch hoch |
| 3 | Kriterien | D | obere Schranke der Fehlerquote im übernommenen Anteil ≤ α (exakter Test, 95 %) auf dem Prüftopf; Mindestzahl Fälle; Mindestdauer mit Monatsabschluss; kein kritischer Fehler (Liste im Bereichspaket, analog `critical: true` in `evals.md`); Agent-Version seit der Messung unverändert. Die Historie belegt, der Schatten bestätigt mit einem einseitigen Test „nicht schlechter als α“, der weniger Fälle braucht |
| 4 | α festlegen | Kunde | Vorschlag = menschliche Fehlerquote im selben Anteil. Die Oberfläche zeigt die Kurve „Abdeckung gegen belegbare Fehlerquote“, der Kunde wählt den Punkt (Anf. 83). Jede Stufe hat ihr eigenes α, Vorschlag lockerer als autonom |
| 5 | Segmente | D | vorher aus den Entwicklungsdaten festlegen, wenige und grob. Segmente erst nach Blick in den Prüftopf zu suchen ist p-Hacking. Die 95-%-Zusage gilt pro Segment; wer sie für alle gleichzeitig verlangt, teilt δ durch die Zahl der Segmente |
| 6 | Belege für „autonom“ | D | aus Schatten und blinden Stichproben. Im Vorschlagsmodus nicken Menschen ab (Automation Bias); seine Annahmequote ist kein sauberer Beleg |
| 7 | Stichproben im Betrieb (Anf. 88) | D | zufällig mit protokolliertem Seed, blind (Prüfer sieht die Agent-Entscheidung nicht). Risikogewichtet nur mit Gewichtung in der Schätzung |
| 8 | Rückstufen mit Label | D | Stichprobenfehler, Stornos, Beschwerden. Langsam, siehe 4.3 |
| 9 | Rückstufen ohne Label | D, Signale M | sofort verfügbar: Anteil neuer Lieferanten und Formate, Abstand zu bekannten Fällen, Uneinigkeit zwischen Regel-Sprosse und LLM, Anteil „weiß nicht“, Schemafehler, Änderungen im Zielsystem (Kontenrahmen, Update). Diese Signale stufen vorläufig zurück, die Label-Signale entscheiden |
| 10 | Not-Aus | D | pro Prozess und Firma (Anf. 91) |

Grenzfälle gehen an Warteschlangen oder Rollen, nie an Personen nach deren Leistung. Der AI Act nennt in Anhang III Nr. 4 die „Zuweisung von Aufgaben auf der Grundlage des individuellen Verhaltens“ als Hochrisiko-Anwendung.

### 3.6 Baustein 5: „Zeig's mir“

Vorab: Die Historie liefert Tausende Beispiele, eine Vorführung eines. Vorführungen sind stark bei Prozessen ohne Systemspur (Excel, Telefon, Desktop-Programme ohne Protokoll), beim Warum (Kriterien), beim Wie in Oberflächen ohne API und bei der Akzeptanz durch Mitarbeiter und Betriebsrat. Rolle im System: Vorführungen liefern Hypothesen und Ausführungsrezepte, die Historie liefert die Belege.

| # | Teilschritt | Klasse | Begründung, Änderung |
|---|---|---|---|
| 1 | Klicks, Tasten, Fenster aufnehmen | D | Plattform: Windows UI Automation, im Browser DOM-Ereignisse (rrweb) |
| 2 | Passwortfelder, gesperrte Programme schwärzen | D | über die Rolle im Accessibility-Baum (`IsPassword`, `type=password`), nicht über Bilderkennung |
| 3 | Sichtbare Personendaten im Bild | M | OCR + Muster (IBAN) |
| 4 | Sprache → Text | M | faster-whisper lokal, Wort-Zeitstempel (whisperX) |
| 5 | Sprache ↔ Klick | D | Zeitstempel-Join |
| 6 | Rohereignisse → Schritte | D, sonst L | Mit Accessibility-Baum deterministisch („Klick auf ‚Speichern‘ in ‚Buchung erfassen‘“). Ohne Baum nur Pixel, dann ist Bildverstehen nötig. Das betrifft Citrix- und Remote-Sitzungen ohne Zusatzkomponente auf dem Server; DATEV läuft in vielen Kanzleien so |
| 7 | Herkunft eingetippter Werte | D | Wert mit Eingangsdokument und zuvor sichtbaren Werten abgleichen → Variable oder Konstante. Formatumwandlungen per Beispiel (FlashFill-Prinzip) sind ebenfalls D |
| 8 | Warum → Regel-Hypothese | L | aus „Büromaterial geht immer auf 4930“ wird eine Regel mit Geltungsbereich |
| 9 | Regel prüfen | D | gegen die Historie aller Mitarbeiter, aggregiert: Stimmt „immer“? Bei Widerspruch Rückfrage an den Prozessverantwortlichen, ohne Personenbezug |
| 10 | Unklare Stellen | L + D | LLM findet Vagheit („meistens“), Code findet Lücken (Wert ohne Herkunft) |
| 11 | Schrittfolge bestätigen | Mensch | Anf. 50 |
| 12 | Nachmachen | D vor L | API → festes Skript über Selektoren → Computer Use nur, wo beides fehlt oder das Skript bricht. Eine Reparatur durch Computer Use wird erst nach Freigabe zum neuen Skript |
| 13 | Korrektur der Entscheidung | D | strukturierte Vorschau statt Cursor: „Ich würde buchen: Konto 4930, Kostenstelle 100, Steuerschlüssel 9“. Korrektur = Feld-Diff = sofort ein exakter Eval-Fall. Cursor-Probe nur für die Ausführung in Systemen ohne API |
| 14 | Korrektur in Worten | L → Mensch | LLM macht daraus die Soll-Ausgabe des Falls und eine Regel-Hypothese; Mensch bestätigt; die Hypothese läuft durch #9 |
| 15 | Eval-Fall speichern | D | nur im Entwicklungstopf |
| 16 | Neubau | L, Tor D | Regeländerung als Code-Diff, DSPy nur für Prompt-Sprossen. Alle bisherigen Fälle müssen bestehen, der Backtest darf nicht schlechter werden |
| 17 | Abbruchregel | D | „3 Läufe ohne Korrektur“ = bereit für den Backtest, keine Qualitätsaussage (≤ 63 %) |
| 18 | Datenschutz | D | Rohaufnahme nach Auswertung löschen, Abstände zwischen Schritten nicht speichern (Leistungsdaten), keine Auswertung pro Person. Auch eine freiwillige Aufnahme ist eine technische Einrichtung nach §87 Abs. 1 Nr. 6 BetrVG (nach BAG reicht die objektive Eignung zur Überwachung) → Betriebsvereinbarung (Anf. 107) |

Kosten: Computer Use ist das einzige KI-Bauteil, bei dem Kosten zählen (Tabelle 4.5).

### 3.7 Zählung

| Baustein | Teilschritte | davon mit LLM |
|---|---|---|
| 1 Entdecken | 20 | 4 (#6, 7, 8, 10, jeweils nur für einen Teil) |
| 2 Backtest | 10 | 1 (#5, nur wo Vorlagen nicht reichen) |
| 3 Hold-out | 5 | 0 |
| 4 Schwelle, Stufen | 10 | 0 (ein Score darf aus einem LLM kommen, die Entscheidung ist D) |
| 5 Zeig's mir | 18 | 6 (#6 ohne Accessibility-Baum, 8, 10, 12 als Ersatz, 14, 16) |
| **Summe** | **63** | **11** |

Die Fabrik (3.2) ist nicht mitgezählt, weil die Sprosse pro Prozess aus den Daten folgt.

## 4 Zahlen

### 4.1 Wie viele Fälle braucht ein Nachweis?

Einseitig, 95 %, exakter Binomialtest. „Fälle“ = Fälle im übernommenen Anteil, nicht alle Fälle des Prozesses.

| Ziel | wahre Quote | nötige Fälle (80 % Chance, dass der Nachweis gelingt) |
|---|---|---|
| ≤ 1 % | 0,5 % | ~1.950 |
| ≤ 2 % | 1 % | ~975 |
| ≤ 3 % | 2 % | ~1.625 |
| ≤ 4 % | 2 % | ~525 |
| ≤ 5 % | 3 % | ~625 |

Ganz ohne Fehler: ≤ 1 % braucht 299 Fälle, ≤ 2 % 149, ≤ 5 % 59.

Beispiel: 400 Fälle im Monat, die Hälfte übernehmbar → für „≤ 2 %“ rund 5 Monate Historie. Daraus folgt: Historischer Import (Anf. 21) mindestens 12 Monate, und „Monate bis Nachweis“ gehört ins Ranking.

### 4.2 Schwelle wählen: Punktwert gegen Schranke (Simulation)

Aufbau: Score mit Information, aber absichtlich unkalibriert; Gesamtfehler ohne Auswahl 16 %; Ziel ≤ 2 % mit 95 %; 200 Läufe je Zelle. Optimum bei bekannter Wahrheit: 43 % Abdeckung.

| Verfahren | 1.000 Prüffälle: Ziel verfehlt / Abdeckung | 3.000 Prüffälle |
|---|---|---|
| Punktwert (lockerste Schwelle mit gemessener Quote ≤ 2 %) | 40 % / 42 % | 38 % / 43 % |
| Schranke, Bonferroni über 28 Schwellen | 0 % / 1 % | 0 % / 16 % |
| Schranke, feste Reihenfolge aus Entwicklungsdaten (empfohlen) | 3 % / 10 % | 4 % / 29 % |

Bei 300 Prüffällen belegt kein sicheres Verfahren eine Schwelle; der Punktwert verfehlt dort in 51 %.

Lesart: Der Punktwert sieht gut aus und bricht die Zusage in vier von zehn Fällen. Die Schranke hält sie (≤ 5 %, wie zugesagt). Ihr Preis ist Abdeckung, und die wächst mit der Datenmenge.

Empfohlenes Verfahren (Learn-Then-Test mit fester Reihenfolge): Auf den Entwicklungsdaten die Kandidatenschwellen ordnen, beginnend bei der Schwelle mit der besten erwarteten Schranke, dann Richtung locker. Auf dem Prüftopf der Reihe nach mit dem exakten Test prüfen, beim ersten Durchfallen stoppen, die lockerste bestandene nehmen. MAPIE (BSD-3) bietet dasselbe als `BinaryClassificationController(risk="precision")` mit Hoeffding-Bentkus-Schranken, die konservativer sind. Für den MVP reicht der exakte Test, MAPIE dient als Gegenprobe.

### 4.3 Rückstufen über Stichproben ist langsam

Ziel α = 2 %. Alarm, wenn unter den letzten N geprüften Fällen mindestens k Fehler sind:

| N | k | Fehlalarm | erkennt Anstieg auf 4 % / 6 % / 10 % mit |
|---|---|---|---|
| 50 | 4 | 1,8 % | 14 % / 35 % / 75 % |
| 100 | 6 | 1,5 % | 21 % / 56 % / 94 % |
| 200 | 8 | 4,9 % | 55 % / 92 % / 100 % |
| 400 | 14 | 3,3 % | 73 % / 99 % / 100 % |

Bei 200 autonomen Fällen im Monat und 10 % Stichprobe dauern 200 geprüfte Fälle zehn Monate. Deshalb die label-freien Frühsignale aus 3.5 #9 und bei kleinen Mengen eine höhere Stichprobenquote.

### 4.4 Doppelt bearbeitete Fälle

95-%-Intervall bei 90 % beobachteter Übereinstimmung: 50 Fälle 78–97 %, 100 Fälle 82–95 %, 200 Fälle 85–94 %, 400 Fälle 87–93 %.

### 4.5 Kosten

Preise laut claude-api-Skill, Stand 2026-10-06: Haiku 5.5 0,10 $ / 0,50 $, Sonnet 5.5 2 $ / 10 $, Opus 5.5 4 $ / 20 $ pro Million Ein-/Ausgabe-Tokens.

| Bauteil | Kosten |
|---|---|
| Eine Mail klassifizieren + Felder, Haiku 5.5 (~1.500 Tokens ein, ~300 aus) | ~0,03 Cent |
| 10.000 historische Mails einmal labeln | ~3 $ |
| Computer-Use-Lauf, 30 Schritte, Sonnet 5.5 (Annahme ~9.000 Eingabe-Tokens pro Schritt mit drei Screenshots im Verlauf) | ~0,50–1 $ |
| DSPy-Optimierung, z. B. 4.000 Aufrufe à 3.000 Tokens, Sonnet 5.5 | ~25–40 $ einmalig pro Prozess |
| Regel, Baum, API-Aufruf | ~0 |

LLM-Kosten entscheiden die KI-oder-Algorithmus-Frage fast nirgends. Es entscheiden Prüfbarkeit, Datensparsamkeit, Angriffsfläche und Latenz, bei Computer Use zusätzlich die Kosten.

## 5 Antworten auf die offenen Fragen

### 5.1 Darf build-agent eine Lösung ohne KI liefern?

Ja, und sie ist die erste Sprosse, die die Fabrik probiert (3.2). Gründe:
- Kosten pro Fall ~0, Latenz Millisekunden.
- Reproduzierbar und erklärbar: Verfahrensdokumentation nach GoBD und die „involvierte Logik“ nach DSGVO Art. 13–15 und 22 sind mit Regeln einfach.
- Keine Injection-Fläche, keine Datenübermittlung an einen LLM-Anbieter, läuft beim Kunden.
- Gleicher Backtest, also fairer Vergleich mit den KI-Sprossen.

Für den Skill heißt das: Die Mustertabelle in `clarify-and-pattern.md` beginnt bei „Kein Agent: einzelner Call“. Davor fehlen zwei Zeilen (Vorschlag in 7.2).

### 5.2 Wie viel des USP ist KI? Was heißt das für Hermes, Pitch und Kosten?

- 11 von 63 Teilschritten brauchen ein LLM. Ohne KI gäbe es keine Entdeckung in Postfächern und kein Zeig's mir. Mit KI allein gäbe es keinen Nachweis. KI ermöglicht das Produkt; der Vorsprung liegt im Nachweis, in der Daten-Anbindung und in den Bereichspaketen.
- Modellfortschritt hilft uns (bessere Extraktion → mehr Abdeckung) und entwertet nichts, weil Prüfer, Betriebsrat und AI Act den Nachweis pro Firma verlangen, egal wie gut das Modell ist. Celonis oder UiPath könnten die Statistik nachrüsten. Schutz bietet die Verbindung aus Kreislauf, deutschem Recht (BetrVG, GoBD) und Bereichspaketen.
- Pitch: „Bevor wir etwas allein machen, zeigen wir auf Ihren eigenen Daten, welchen Anteil wir mit welcher belegten Fehlerquote übernehmen. Sinkt die Qualität, nehmen wir es automatisch zurück.“ Dazu ehrlich: Häufiges wird autonom, Seltenes bleibt Vorschlag. Wenig KI ist im deutschen Mittelstand ein Argument: Teile laufen ohne LLM, weniger Daten gehen nach außen, Prüfer können die Regeln lesen.
- Kosten: LLM-Kosten pro Fall sind vernachlässigbar, Computer Use ist der einzige teure KI-Teil. Die echten Kosten sind Anbindung, Verknüpfung und menschliche Zeit (Kalibrierrunde, Zeig's mir). Der Preis gehört daher an den Prozess oder den übernommenen Fall, nicht an Tokens.
- Hermes: Die Fall-Laufzeit ist ein Workflow (Skill-Regel „Workflow vor Agent“) und braucht keinen Agent-Unterbau. Hermes-Skills sind Anleitungen, die das LLM zur Laufzeit befolgt oder nicht; unsere Entscheider sind Code oder gemessene Artefakte. Hermes verbessert sich ungemessen selbst, und genau das soll unser Tor verhindern. Für Zeig's mir sind die Bausteine Aufnahme und Computer-Use-Umgebung (OpenAdapt, rrweb, cua). Möglicher Platz für Hermes bleibt der Gesprächskanal (Rückfragen, Benachrichtigungen) und ein späterer Ad-hoc-Assistent für Aufgaben ohne Historie, der dauerhaft im Vorschlagsmodus läuft. Empfehlung: Hermes aus dem MVP nehmen und die Entscheidung vertagen, bis Teams-Kanal oder Ad-hoc-Assistent anstehen.

### 5.3 Konfidenz pro Fall: Klassifikator oder Regeln? Wie kalibrieren?

Beides, in drei Lagen:
1. **Harte Regeln (D)** aus Bereichspaket und vom Kunden. Sie können Fälle nur aus der Autonomie nehmen, nie hinein (Betrag > X, neue Bankverbindung, neuer Lieferant, Pflichtfeld fehlt).
2. **Score (M/L) als Rangfolge** aus wenigen Signalen: Stimmen Regel-Sprosse und LLM überein (zwei Schlüssel, wie beim Vier-Augen-Prinzip)? Sind die extrahierten Felder gegen Stammdaten bestätigt? Wie nah ist der Fall an bekannten Fällen, und wie einig waren sich die Menschen dort? Bei Bedarf Selbstkonsistenz über drei Läufe. Im MVP genügt eine UND-Verknüpfung dieser Signale. Erst wenn die Abdeckung zu klein bleibt, kommt eine logistische Regression darüber (erklärbar).
3. **Schwelle (D):** exakter Test auf dem Prüftopf, Verfahren aus 4.2.

Kalibrieren im engeren Sinn (Platt, isotonisch) braucht es nur, wenn der Sachbearbeiter eine Prozentzahl sehen soll. Für die Garantie ist es unnötig (Simulation 4.2). Die Selbstauskunft des LLM („90 % sicher“) wird nicht verwendet. Token-Logprobs sind für die Claude-API nicht dokumentiert und fallen als Signal aus.

Die Garantie gilt, solange die Zukunft dem Prüftopf ähnelt. Deshalb bestätigt der Schatten, und die Frühsignale aus 3.5 #9 stufen bei Drift zurück.

### 5.4 Doppelt bearbeitete Fälle: wo nötig, gibt es sie in Finanzdaten?

Gebraucht für: die Messlatte „so gut wie ein Mensch“, die menschliche Fehlerquote, die Kalibrierung eines LLM-Judges und das Erkennen von Feldern mit mehreren zulässigen Antworten. Niedrige Übereinstimmung heißt dort: Eine Regel fehlt, also Rückfrage statt Automatisierung.

In Finanzdaten gibt es sie, aber selten blind:

| Quelle | taugt für | Haken |
|---|---|---|
| Vier-Augen-Freigaben (sachlich/rechnerisch, Zahlungsfreigabe) | Untergrenze der Fehlerquote (Ablehnungen) | nicht blind: Der Zweite sieht die Erstentscheidung, die Übereinstimmung fällt zu hoch aus |
| Korrekturen des Steuerberaters an vorkontierten Belegen | Fehlersignal | nur wo der Kunde vorkontiert |
| Stornos, Umbuchungen, wieder geöffnete Tickets | Fehlersignal | nur ein Teil der Fehler wird entdeckt |
| Prüferstichproben (Wirtschaftsprüfer, Revision) | Fehlersignal | wenige Fälle |
| Zwillingsfälle: fast gleiche Eingänge (gleicher Lieferant, gleiche Art), bearbeitet von verschiedenen Personen | vorsichtige Schätzung der Übereinstimmung zwischen Menschen | Pseudonym nur nötig, um dieselbe Person auszuschließen; nur aggregiert |
| Blinde Kalibrierrunde: 100–200 historische Fälle, eine zweite Person entscheidet, ohne die erste Entscheidung zu sehen | sauberste Messung | rund 3–17 Stunden Arbeitszeit pro Prozess |

Empfehlung: Kalibrierrunde als fester Onboarding-Schritt. In diesem Moment sehen die Mitarbeiter auch, dass der Agent bewertet wird und nicht sie. 100 Fälle ergeben bei 90 % Übereinstimmung ein Intervall von 82–95 % (4.4).

§87 BetrVG: nur aggregiert, keine Übereinstimmung pro Person, Kennzahlen nur bei mindestens k = 5 beteiligten Personen (Vorschlag), sonst unterdrücken.

### 5.5 Erster Prototyp: Welche Teile sind reine Algorithmen und kommen zuerst?

Szenario: Sammelpostfach „buchhaltung@“ mit erfundenen Mails zu vier Anliegen.

| Anliegen | Menge | erwartetes Ergebnis |
|---|---|---|
| Zahlungsstatus-Anfrage | hoch | Kandidat 1. Die Entscheidung ist Nachschlagen im offenen Posten (D), KI nur zum Lesen (Sprosse 2) |
| Rechnungseingang | mittel | Kontierung über Sprosse 0/1, Long Tail über Sprosse 3 |
| Bankverbindung ändern | selten | über die Aktion gesperrt (Betrugsmuster) |
| Sonstiges | Rest | bleibt beim Menschen |

Der Generator baut Störungen mit bekannter Wahrheit ein: 3 % menschliche Fehler, eine abweichende Hausregel bei einer Person, 5 % nicht erklärbare Entscheidungen, Duplikate, fehlende Verknüpfungen, ein Formatwechsel ab einem Stichtag, Stornos als Fehlersignal, 10 % doppelt bearbeitet. So lässt sich jede spätere Messung gegen die Wahrheit prüfen.

Reihenfolge; die Schritte 1–6 laufen ohne API-Key:
1. Generator mit bekannter Wahrheit + Fake-ERP als JSON. Odoo erst, wenn eine Oberfläche gebraucht wird.
2. Fall-Format, Import, Verknüpfung, Pseudonyme.
3. Drei Töpfe und Tresor-Schnittstelle.
4. Sprosse 0/1 (Tabelle, Entscheidungsbaum) mit Orakel-Feldern aus dem Generator statt LLM-Extraktion; Replay, Grader, Kennzahlen, exakter Test, Schwellenwahl. Ein Test stellt sicher, dass dieser Code keinen LLM-Client importiert. Ergebnis: der erste Schattenbericht ganz ohne LLM.
5. Stufen, Rückstufung, Not-Aus, dazu ein Fabrik-Eval der Statistik: Wiederholte Simulation zeigt, dass die zugesagte Fehlerquote hält (wie 4.2).
6. Entdeckungs-Ranking auf Generatordaten mit Orakel-Anliegen. Erwartet: Zahlungsstatus oben, Bankdaten gesperrt.
7. Erst jetzt KI, eins nach dem anderen und jeweils gegen denselben Backtest: LLM-Anliegen und -Felder (Haiku 5.5) mit gemessenem Verlust gegenüber dem Orakel, dann Sprosse 3 für den Long Tail, dann Antwortvorlagen.
8. Fabrik v0: Das LLM schreibt Regeln oder Prompt aus Beschreibung und Daten, der Backtest ist das Tor.
9. Oberfläche v0: Kandidaten, Kurve Abdeckung/Fehler, Bericht, Aktivieren-Knopf.
10. „Ich probier's“ v0 als strukturierte Vorschau; Cursor in Odoo danach.

Nicht im ersten Prototyp: Zeig's mir, Computer Use, Hermes.

## 6 Folgen für die Architektur

| Schicht | Klasse | Inhalt |
|---|---|---|
| Daten | D | Konnektoren, Fall-Format, Verknüpfung, Pseudonyme, Abfragen mit Stichtag |
| Verstehen | M/L | Extraktion, Anliegen, Sprache, Bild; austauschbar und gemessen |
| Entscheiden | Leiter D → A | `entscheide(fall) → Entscheidung \| weiß nicht` |
| Vertrauen | nur D | Töpfe, Tresor, Replay, Kennzahlen, Test, Stufen, Rückstufung, Not-Aus, Protokoll |
| Wirkung | D | API-Aufrufe hinter dem Freigabe-Tor; Computer Use nur als Ersatz |
| Bauen | L zur Bauzeit, Tor D | Fabrik, Auswertung von Zeig's mir |

Regel: Die Vertrauensschicht hängt von keinem LLM ab, auch nicht indirekt. LLM-Messwerte (Judge, Score) kommen nur als gespeicherte Zahlen mit gemessener Fehlerquote hinein.

## 7 Vorschläge (nicht umgesetzt, warten auf Freigabe)

### 7.1 SPEC-firmen-agent.md

| Stelle | Änderung |
|---|---|
| 1 Leitplanken | neuer Leitsatz; Asymmetrie (hoch nur durch Menschen, runter automatisch); „Obergrenze“ → „Messlatte: Übereinstimmung der Menschen; 100 % nie erreichbar“ |
| 1 Lernkreislauf Stufe 4, Anf. 72 | „Ende nach 3 Läufen ohne Korrektur“ → „bereit für den Backtest, keine Qualitätsaussage“ |
| E 27–29 | Clustering optional; Abläufe über Varianten + Entscheidungsbaum; Gleichförmigkeit = Vorhersagbarkeit; Ranking = Stunden × Abdeckung, Risiko als Sperre, Spalte „Monate bis Nachweis“ |
| neu in E | Risiko aus der Aktion (Anf. 15) zusätzlich zum Anliegen; Katalog mit Art.-22- und Anhang-III-Fällen |
| D 23 | Mindestgruppe k = 5 für alle Zeit- und Übereinstimmungswerte; Minuten pro Fall erfragen statt messen |
| A 21 | Import mindestens 12 Monate |
| H 47–48 | Schritte aus dem Accessibility-Baum (D), Herkunft von Werten (D), Regeln aus Sprache (L) mit Prüfung gegen die Historie |
| I 51 | „Agent“ → „Entscheider“ (Regel, Modell, Prompt oder Agent); Leiter von unten |
| K 61, 65–69 | strukturierte Vorschau für Entscheidungen; Cursor nur für Ausführung ohne API; 61 und 65 aus dem MVP |
| L 73–77 | drei Töpfe + Tresor; 75 Messlatte + blinde Kalibrierrunde; 76 Vergleich im selben Anteil, Schranke statt Punktwert; 77 nur außerhalb des versiegelten Topfs |
| M 78–80 | Schatten bestätigt mit einseitigem Test |
| N 82–84 | Stufe pro Prozess und Segment; Schwelle per exaktem Test, Kunde wählt den Punkt auf der Kurve; 84 = drei Lagen aus 5.3; Belege aus Schatten und blinden Stichproben |
| O 88–90 | blinde Zufallsstichproben; label-freie Frühsignale stufen vorläufig zurück |
| 7 Weg zum MVP | Reihenfolge aus 5.5 (Orakel zuerst, KI danach); in 7.3 „LLM leitet pro Gruppe Schritte ab“ streichen |
| 8 Offene Entscheidungen | Hermes: vertagt, nicht im MVP |

### 7.2 build-agent (Entwurf in `setup-entwurf/build-agent/`)

In `references/clarify-and-pattern.md` zwei Zeilen vor „Kein Agent“:

| Situation | Muster | Umsetzung |
|---|---|---|
| Entscheidung folgt aus wenigen strukturierten Feldern, Historie zeigt feste Zuordnung | **Kein LLM: Regel/Tabelle** | Python-Funktion oder Tabelle, ein Test pro Regel; Evals wie gehabt, Scaffold und Caching entfallen |
| Entscheidung aus strukturierten Feldern, Historie zeigt ein Muster | **Kein LLM: gelerntes Modell** | Entscheidungsbaum oder logistische Regression (scikit-learn), eingefroren und versioniert |

Dazu die Regel: „Leiter von unten: Jede Sprosse läuft gegen dieselben Evals, die unterste, die besteht, gewinnt.“

Inbox-Einträge im Format von `learnings/inbox.md`:

```
- 2026-10-15 | kontext: allgemein | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness | stärke: hinweis
  Erkenntnis: Mustertabelle braucht Sprossen ohne LLM (Regel/Tabelle, gelerntes Modell) vor „Kein Agent“ → Beleg: ANALYSE-ki-vs-algorithmus.md, noch kein Build (n=0)
  Ziel: reference
- 2026-10-15 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness | stärke: hinweis
  Erkenntnis: Abnahme-Schwellen als obere Schranke (exakter Binomialtest) statt Punktwert → Beleg: Simulation, Punktwert verfehlte das Ziel in 38–51 % der Läufe, Schranke in ≤ 4 % (n=200 Läufe × 3 Datengrößen)
  Ziel: reference
```

## 8 Annahmen und nicht Geprüftes

- Rechtliche Aussagen (BetrVG, AI Act, DSGVO, GoBD, E-Rechnung) sind nicht anwaltlich geprüft; Anf. 111 bleibt.
- Preise aus dem claude-api-Skill (Stand 2026-10-06). Tokens pro Computer-Use-Schritt sind geschätzt.
- Die Simulation nutzt ein synthetisches Score-Modell; die echte Abdeckung hängt vom Prozess ab.
- Hermes-Fakten stammen aus der Memory (Prüfung im Code am 2026-10-15) und wurden hier nicht neu geprüft.
- „DATEV läuft oft über Citrix/Remote“ ist Marktkenntnis, nicht geprüft.
