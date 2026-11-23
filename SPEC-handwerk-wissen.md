# Spec: Wissen von der Baustelle

Status: Entwurf vom 2026-11-24. Der Name ist ein Arbeitstitel ([#18](https://github.com/Alextum207/agent-builder-harness/issues/18)). Die Spec löst [`SPEC-open-process-intelligence.md`](SPEC-open-process-intelligence.md) ab. Entscheidungen: [#28](https://github.com/Alextum207/agent-builder-harness/issues/28). Ideen: Miro-Board „Module 3“ (Tradeworker business).

## 1 Idee in einem Satz
Der Meister filmt seine Arbeit mit dem Handy, ohne dabei etwas erklären zu müssen. Nach dem Job stellt die KI ihm höchstens drei kurze Fragen, die er per Sprache beantwortet. Daraus entstehen Anleitungen und Job-Akten, die neue Leute auf der Baustelle per Sprache oder Foto abfragen.

## 2 Problem
Die Zahlen stammen vom Board.
- Rund 718.000 Handwerker zwischen 55 und 64 gehen in den nächsten Jahren in Rente. Jeder dritte Inhaber ist älter als 55.
- Ihr Wissen ist Erfahrungswissen: durch Tun gelernt und selten aufgeschrieben. Auf der Baustelle fehlt Zeit für Dokumentation, und es gibt keinen Schreibtisch dafür.
- Die meisten Betriebe haben weniger als 10 Leute und weder Personalabteilung noch Wissensmanagement.
- Es gibt rund 250.000 offene Stellen. Bis eine besetzt ist, vergehen 242 Tage. Quereinsteiger bauen inzwischen Wärmepumpen ein. 17 % der Beschäftigten kommen aus dem Ausland, dazu kommt die Sprachbarriere.
- Neue arbeiten oft ab dem ersten Tag allein vor Ort und rufen bei jeder Frage den Meister oder den Großhändler an.
- 91 % stimmen sich über WhatsApp ab. Nur 4 % nutzen KI, aber 83 % sehen Zeitersparnis als wichtigsten Nutzen digitaler Werkzeuge.
- **Gespräche:** Würth berichtet von vielen Anrufen, weil die Leute vor Ort nicht wissen, was zu tun ist. Viele Handwerker sagen: Bürosoftware gibt es genug, aber nichts, das auf der Baustelle hilft und den Wissensverlust aufhält.

## 3 Positionierung
**Hilfe auf der Baustelle, kein Bürotool.** Angebote, Rechnungen und Auftragsplanung decken vorhandene Handwerker-Programme ab. Wir ersetzen sie nicht, sondern binden sie an ([#37](https://github.com/Alextum207/agent-builder-harness/issues/37)).

| | Büro-Software für das Handwerk | Diese Lösung |
|---|---|---|
| Wo | Büro, Planung | Baustelle |
| Was | Aufträge, Angebote, Rechnungen, Zeiten | Wissen: wie man es macht, was man braucht, worauf man achten muss |
| Eingabe | Formulare | Video, Sprache, Foto; im Alltag kein Tippen |
| Daten | beim Anbieter | beim Betrieb, jederzeit exportierbar; Open Source, selbst betreibbar |

Grundsätze:
- **Das Wissen gehört dem Betrieb.** Großhändler oder Hersteller können ihr Produktwissen einspeisen und dafür bezahlen. Das Wissen aus dem Betrieb sehen sie nie, und diese Trennung ist technisch umgesetzt, nicht nur vertraglich.
- **Ergänzen statt ersetzen:** Wir lesen Aufträge aus der vorhandenen Software (rein) und stellen unser Wissen als MCP-Server bereit (raus).

## 4 Rollen
| Rolle | Tut | Zeitaufwand (Ziel) |
|---|---|---|
| **Meister / erfahrene Fachkraft** | filmt Jobs und beantwortet Nachfragen | Aufnahme ohne Mehraufwand, Nachfragen höchstens 2 Minuten pro Tag |
| **Geselle, Azubi, Quereinsteiger** | fragt vor Ort, sieht Anleitungen | Sekunden pro Frage |
| **Inhaber** | richtet einmal ein, gibt Einwilligungen frei | einmalig etwa 15 Minuten |
| **Kunde** | willigt vor der Aufnahme ein | ein Satz |

## 5 Ablauf im Alltag
```text
Morgens      Job in der App antippen (aus der Büro-Software oder per Foto vom Typenschild)
             Handy in die Brusthalterung, Weitwinkel, Ansteckmikro, Tipp auf „Kunde einverstanden“, Start
Während      einfach arbeiten. An wichtigen Stellen „Merken“ sagen, doppelt tippen oder Bluetooth-Knopf drücken
Danach       Stopp. Das Handy lädt im WLAN von selbst hoch und löscht das Video danach
Abends       eine Benachrichtigung: „2 kurze Fragen zu heute“
             Ausschnitt ansehen → Mikro-Knopf gedrückt halten → antworten | „Passt so“ | „Weiß nicht“
             am Ende „Passt so“ für die Anleitung, damit ist sie freigegeben
Nächster Tag Der Geselle fragt per Sprache: „Was brauche ich für die Wartung an dem Gerät?“
             Antwort: Materialliste früherer Jobs, Warnung, Video vom Meister ab 1:40
             Weiß der Assistent es nicht, landet die Frage beim Meister in den nächsten Nachfragen
```

## 6 Bedienregeln (im Code erzwungen, nicht nur Vorsatz)
| Regel | Wert | Wo |
|---|---|---|
| Nachfragen pro Job | höchstens 3 | [#38](https://github.com/Alextum207/agent-builder-harness/issues/38) |
| Benachrichtigungen pro Tag | höchstens 1, Uhrzeit wählt der Meister (Standard 17:00) | #38, #34 |
| Länge einer Frage | höchstens 15 Wörter, Du-Form, einfache Sprache | #38 |
| Sprachantwort | höchstens 60 Sekunden | #38 |
| unbeantwortete Fragen | verfallen nach 2 Tagen, kein Nachhaken | #38 |
| Tippen im Alltag | keins; nur Sprache, Foto und große Knöpfe | #34, #39 |
| Aufnahme vergessen zu stoppen | automatischer Stopp nach 4 Stunden | #34 |
| Upload | nur im WLAN, danach wird das Video vom Handy gelöscht | #34 |
| kein Netz im Keller | Anleitungen der heutigen Jobs offline auf dem Handy | #31 |
| Einrichtung | einmal per QR-Code, im Alltag kein Passwort | #34 |
| Sprache | Oberfläche und Anleitungen auf Deutsch, Englisch und einer weiteren Sprache | #30, #34 |

## 7 Architektur
```text
 Handy (App #34, Demo: Kamera-App + Browser #39)
   │ Video 720p, Weitwinkel + Marker
   ▼
 Backend (FastAPI)
   1 Zerlegen        ffmpeg → faster-whisper (Text + Wort-Zeitmarken) → PySceneDetect (Standbilder)
   2 Säubern         Abschnitte Arbeit | Erklärung | Smalltalk | Kunde → Smalltalk und Kunde sofort löschen
   3 Verstehen       Claude: Schritte, Werkzeug, Material, Warnungen, „erklärt ja/nein“        (#29)
   4 Nachfragen      Code wählt die 3 größten Lücken, Claude formuliert, Ausschnitt 10 s       (#38)
   5 Einarbeiten     Antworten → Job-Akte (#36) → Anleitung pro Gerät, mehrsprachig (#30)
   6 Freigabe        „Passt so“ vom Meister
   7 Wissensbasis    Company Brain (OKF) + Suche
   8 Fragen          Assistent (#31) │ MCP-Server für andere Tools (#37)
   9 Prozess-Sicht   OCEL-Events pro Schritt → Varianten, Fehler, Lücken pro Gerät         (#33)
 Anbindung rein: Handwerker-Software (Aufträge, Geräte, Material) (#37) │ WhatsApp-Export (#32)
```

| Baustein | Lizenz (geprüft am 2026-11-24) | Wofür |
|---|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT | Transkription lokal |
| [whisperX](https://github.com/m-bain/whisperX) | BSD-2-Clause | Alternative mit genaueren Wort-Zeitmarken |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT | Später: Transkription auf dem Handy |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | BSD-3-Clause | Standbilder bei Szenenwechsel |
| ffmpeg | LGPL/GPL je nach Build, Aufruf als externes Programm | Ton und Ausschnitte |
| [FastAPI](https://github.com/fastapi/fastapi) | MIT | Backend für Demo und App |
| [React Native](https://github.com/facebook/react-native) + [Expo](https://github.com/expo/expo) + [VisionCamera](https://github.com/margelo/react-native-vision-camera) | MIT | App für Android und iPhone (Empfehlung; Alternative Flutter, BSD-3) |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) / [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 | Gesichter unkenntlich machen |
| [fastmcp](https://github.com/PrefectHQ/fastmcp) / [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Apache-2.0 / MIT | MCP-Server |
| Claude über `agent_guardrails.claude_cli` | – | Schritte, Fragen, Übersetzung; im Pilot mit API-Key |

**Geprüfte Technik-Fakten:** VisionCamera wählt die Ultra-Weitwinkel-Kamera gezielt aus (`physicalDevices: ['ultra-wide-angle']`). Geht die App in den Hintergrund, pausiert die Aufnahme (Doku, „Interruptions“). Die App bleibt deshalb während der Aufnahme vorn, mit schwarzem Bildschirm. Laufzeit, Akku und Wärme misst der Spike in #34.

**Was aus dem Harness bleibt:**
| Vorhanden | Neue Rolle |
|---|---|
| `company-brain` | speichert Anleitungen und FAQ als OKF-Bundle |
| `test-rag-agent` | Grundlage für den Assistenten (#31) |
| `packages/agent-guardrails` | Rechte, Maskierung, Tracing, Chatmodell über die Claude-CLI |
| `packages/mail-connector` | Muster für Pseudonyme und OCEL; Vorlage für den WhatsApp-Export (#32) |
| `setup-entwurf/build-agent` | Bauweise, Evals, Guardrails für jeden neuen Agent-Teil |

Ruhend, bleibt als Referenz: das Finanz-ERP (`test-finance-agent`) und die Pakete der Process-Intelligence-Plattform.

## 8 Verarbeitung im Detail (#29)
1. **Eingang:** Video (MP4, 720p, Weitwinkel), Auftrag oder Gerät, Einwilligungs-Flag (Pflicht, ohne Flag keine Verarbeitung).
2. **Ton:** ffmpeg → WAV mit 16 kHz, mono.
3. **Transkript:** faster-whisper auf Deutsch, mit Wort-Zeitmarken.
4. **Marker:** feste Wortliste im Code (`merken`, `merk dir das`, `wichtig`) sowie Doppeltipp und Bluetooth-Knopf aus der App → Zeitmarken.
5. **Abschnitte:** Claude teilt das Transkript in Abschnitte vom Typ `arbeit`, `erklaerung`, `smalltalk` oder `kunde`. `smalltalk` und `kunde` werden sofort aus Transkript und Ton entfernt, nur Anfang und Ende bleiben gespeichert. Ein Code-Test beweist, dass danach kein Text aus diesen Abschnitten mehr vorhanden ist.
6. **Standbilder:** bei Szenenwechsel (PySceneDetect), alle 10 Sekunden und an jedem Marker.
7. **Schritte:** Claude sieht die Abschnitte `arbeit` und `erklaerung` und die Standbilder. Die Ausgabe ist ein Pydantic-Schema:
   `Schritt(nr, start, ende, handlung, werkzeug[], material[{artikel, menge}], warnung, erklaert: bool, bilder[])`.
   Material nur mit Beleg (Zeitmarke oder Bild). Ungültige Ausgaben werden einmal neu angefragt, danach als Fehler gemeldet.
8. **OCEL:** ein Event pro Schritt, Objekte `Auftrag`, `Geraet`, `Aufnahme`, Personen nur als Pseudonym (Muster `packages/mail-connector`).
9. **Rohdaten:** Das Rohvideo bleibt bis nach den Nachfragen. Danach werden nur die Ausschnitte behalten, auf die eine Anleitung verweist (#40).

**Datenmodell:** `Betrieb` → `Person` (Pseudonym, Rolle) · `Auftrag` → `Geraet` · `Aufnahme` → `Marker`, `Abschnitt`, `Standbild`, `Schritt` · `Nachfrage` → `Antwort` · `JobAkte` · `Anleitung` (pro Gerät und Tätigkeit, versioniert) · `FAQ`.

## 9 Nachfragen: der Kern (#38)
Die Kamera liefert das Rohmaterial, das Wissen kommt aus den Nachfragen. Niemand muss beim Arbeiten reden wie in einem Tutorial.

**Auswahl im Code**, Punkte pro Schritt:
| Signal | Punkte |
|---|---|
| Marker „Merken“ | +3 |
| sicherheitsrelevant (Strom, Kältemittel, Druck, Gas, Höhe; Liste im Code) | +3 |
| im Bild gehandelt, im Ton nicht erklärt | +2 |
| weicht von der vorhandenen Anleitung ab | +2 |
| Material oder Werkzeug unklar | +1 |
| schon beantwortet oder in der Anleitung | 0 |

Gefragt werden die 3 Schritte mit den meisten Punkten. Claude formuliert nur die Frage, der Code prüft Länge und Form. Zu jeder Frage gehört ein Ausschnitt von 10 Sekunden. Mögliche Antworten: Sprache (höchstens 60 s), „Passt so“, „Weiß nicht“.

Beispiel: *„Bei 2:30 drehst du am Ventil, bevor du den Filter ziehst. Warum?“*

Offene Fragen aus dem Assistenten („weiß ich nicht“, #31) kommen in dieselbe Liste und zählen zum Limit von 3.

## 10 Datenschutz und Recht
Wir geben keine Rechtsberatung. Vorlagen lassen wir vor dem Pilot gegenlesen (#40).
- **Aufnahmen nur zur Wissensweitergabe**, nie zur Leistungskontrolle. Keine Auswertung pro Person; ein Code-Test beweist, dass kein Endpunkt Zahlen pro Person liefert.
- **Start und Stopp nur durch die Person selbst.** Keine versteckten, fest montierten oder dauerhaft laufenden Kameras.
- **Einwilligung:** Alle Anwesenden wissen Bescheid. Der Kunde willigt vor jeder Aufnahme ein (Pflicht-Tipp in der App). Wer im Team nicht will, wird nicht gefilmt und hat keinen Nachteil. Gibt es einen Betriebsrat, braucht es eine Betriebsvereinbarung (§87 Abs. 1 Nr. 6 BetrVG).
- **Gesprochenes Wort:** Private Gespräche ohne Einwilligung aufzunehmen kann strafbar sein (§201 StGB). Deshalb werden Smalltalk- und Kunden-Abschnitte sofort nach der Transkription gelöscht.
- **Löschfristen** (im Code):

  | Daten | Gelöscht |
  |---|---|
  | Smalltalk- und Kunden-Abschnitte | sofort nach der Transkription |
  | Sprachantworten (Ton) | nach der Transkription |
  | Rohvideo | nach den Nachfragen; nur Ausschnitte, auf die Anleitungen verweisen, bleiben |
  | alles von einer Person | bei Widerruf |
- **Gesichter** auf Standbildern und Ausschnitten werden unkenntlich gemacht.
- **Mandanten getrennt:** Ein Betrieb sieht nie Daten eines anderen.
- **Betrieb:** Hosting in der EU, Vertrag zur Auftragsverarbeitung mit Hoster und LLM-Anbieter, Export der ganzen Wissensbasis jederzeit.

## 11 Phasen
### Phase A: Kurs-Demo (Meilenstein „Kurs-Demo“)
Läuft auf dem Laptop. Gefilmt wird mit der normalen Kamera-App (0,5×), „Merken“ wird laut gesagt. Gewerk: SHK. Für die Demo steht keine Wärmepumpe bereit, deshalb wird eine **Heizungswartung zu Hause** gefilmt: Druck prüfen, Heizkörper entlüften, Wasser nachfüllen, Schmutzfänger reinigen. Die Wärmepumpe bleibt das Ziel für den Pilot.

**Termin:** Kursabgabe Ende Februar 2027.

| Zeitraum | Ziel |
|---|---|
| bis Mitte Dezember 2026 | #29: Code-Tests grün, erstes Demo-Video gedreht |
| bis Mitte Januar 2027 | #38 und #36: Nachfragen und Job-Akte auf dem Demo-Video |
| bis Anfang Februar 2027 | #30 und #31: Anleitung und Assistent mit Evals |
| bis Mitte Februar 2027 | #39: Demo-Oberfläche, Durchstich mit einem Befehl |
| bis Ende Februar 2027 | Reserve, finales Demo-Video, Präsentation |

| Reihenfolge | Issue | Ergebnis |
|---|---|---|
| 1 | [#28](https://github.com/Alextum207/agent-builder-harness/issues/28) H0 | Spec, Handoff, Kamera-Regel (dieser PR) |
| 2 | [#29](https://github.com/Alextum207/agent-builder-harness/issues/29) H1 | Video → Schritte, Smalltalk-Filter, Marker |
| 3 | [#38](https://github.com/Alextum207/agent-builder-harness/issues/38) H10 | Nachfragen |
| 4 | [#36](https://github.com/Alextum207/agent-builder-harness/issues/36) H8 | Job-Akte mit Material |
| 5 | [#30](https://github.com/Alextum207/agent-builder-harness/issues/30) H2 | Anleitung pro Gerät, mehrsprachig |
| 6 | [#31](https://github.com/Alextum207/agent-builder-harness/issues/31) H3 | Assistent mit Weiterleitung an den Meister |
| 7 | [#39](https://github.com/Alextum207/agent-builder-harness/issues/39) H11 | Demo-Oberfläche im Browser |

**Fertig, wenn** ein Befehl den Durchstich auf dem Demo-Video startet: Video → 3 Nachfragen → Antworten → freigegebene Anleitung → Frage im Handy-Browser mit Videostelle. Jede Stufe hat einen Code-Test, die Modell-Stufen haben Evals mit k=3.

**Demo-Video:** selbst gedreht, nur mit Personen, die eingewilligt haben, ohne echte Kunden. Liegt nicht im Repo. Code-Tests laufen mit erfundenen Transkripten (JSON).

### Phase B: Pilot (Meilenstein „Pilot“)
| Reihenfolge | Issue | Ergebnis |
|---|---|---|
| 1 | [#34](https://github.com/Alextum207/agent-builder-harness/issues/34) H6 | Spike, dann App für Android und iPhone |
| 2 | [#40](https://github.com/Alextum207/agent-builder-harness/issues/40) H12 | Einwilligungen, Löschfristen, Gesichter, Mandanten, EU-Hosting |
| 3 | [#37](https://github.com/Alextum207/agent-builder-harness/issues/37) H9 | Anbindung der Handwerker-Software, MCP-Server |
| 4 | [#41](https://github.com/Alextum207/agent-builder-harness/issues/41) H13 | 4 Wochen mit einem SHK-Betrieb, Messung |
| optional | [#32](https://github.com/Alextum207/agent-builder-harness/issues/32) H4, [#33](https://github.com/Alextum207/agent-builder-harness/issues/33) H5 | WhatsApp-Export, Prozess-Sicht pro Gerät |

Nach dem MVP: [#35](https://github.com/Alextum207/agent-builder-harness/issues/35) H7 (Typenschild → Ersatzteil, Großhändler, gemeinsame Datenbank mit Lösungen, Kopfkamera).

## 12 Erfolg messen (Pilot, #41)
Gemessen wird nur pro Betrieb und Gerät, nie pro Person.
- Zeit des Meisters für Nachfragen pro Tag: Median höchstens 2 Minuten
- Anteil der beantworteten Nachfragen
- Anteil der Gesellen-Fragen, die der Assistent mit Beleg beantwortet
- Anrufe beim Meister vorher und nachher (freiwillige, anonyme Umfrage mit einer Frage pro Woche)
- freigegebene Anleitungen pro Woche
- abgebrochene Aufnahmen und Stellen, an denen die Bedienung hakt

## 13 Risiken
| Risiko | Gegenmaßnahme |
|---|---|
| Die Leute nehmen nicht auf | kein Mehraufwand beim Arbeiten, Wissen über Nachfragen, Pilot misst Abbrüche |
| Lärm auf der Baustelle | Ansteckmikrofon; Ton ist wichtiger als Bild |
| Akku und Wärme bei langer Aufnahme | Spike in #34, 720p, schwarzer Bildschirm |
| Kosten pro Job (Bilder an das Modell) | im Spike messen, Standbilder begrenzen |
| Falsche Anleitung | Freigabe durch den Meister; Warnungen werden nie gekürzt; Sicherheitsfragen immer mit Hinweis auf die Fachkraft |
| Recht und Einwilligung | #40, Vorlagen gegenlesen lassen |
| Handwerker-Software ohne offene API | Marktliste in #37; ohne Anbindung geht es per Foto vom Typenschild |
| Abhängigkeit von Konzernen | Wissen bleibt beim Betrieb, Open Source, Export |

## 14 Nicht im MVP
Smart-Brille, Live-Anleitung während der Arbeit, AR, Ersatzteilsuche, Bestellung beim Großhändler, gemeinsame Datenbank über Betriebe hinweg, Transkription auf dem Handy.

## 15 Offen
- Geklärt am 2026-11-24: Für die Demo gibt es keine Wärmepumpe, gefilmt wird stattdessen eine Heizungswartung zu Hause. Die Kursabgabe ist Ende Februar 2027.
- Für den Pilot: ein Betrieb mit Wärmepumpen-Jobs, zum Beispiel über Würth, die Innung oder eure Gespräche (#41).
- Name und Lizenz (#18). pm4py (AGPL) braucht nur #33; die Prozess-Sicht geht zur Not auch mit einfachem Zählen.
