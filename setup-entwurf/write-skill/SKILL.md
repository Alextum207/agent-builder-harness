---
name: write-skill
description: Writes or revises Claude Code skills and agent SOPs using a fixed structure (Trigger, Steps, Edge cases, Success metric, Evaluation) and Anthropic's skill-authoring best practices. Use when the user wants to create, write, improve, or review a skill, SKILL.md, or SOP.
---

# Write a skill

## Trigger
- Neuer Skill, neue SOP für einen Agent, oder bestehenden Skill verbessern/prüfen.
- **Nicht** für Regeln, die immer gelten (gehören in CLAUDE.md), und nicht für einen einzelnen festen Befehl (Alias oder Slash-Command reicht).

## Steps
1. **Lücke belegen:** Aufgabe einmal ohne Skill durchspielen oder den Nutzer fragen, was ohne Skill schiefgeht. Daraus drei Testszenarien ableiten, bevor viel Text entsteht (Quelle: S1 „evaluations first“).
2. **Frontmatter:**
   - `name`: max. 64 Zeichen, nur Kleinbuchstaben, Ziffern, Bindestriche; nicht „anthropic“/„claude“.
   - `description`: max. 1.024 Zeichen, **dritte Person**, was der Skill tut + „Use when …“ mit den Worten, die ein Nutzer sagen würde. Einziger Teil, der immer im Kontext ist.
   - `disable-model-invocation: true`, wenn er nur per `/name` laufen darf.
3. **Body mit genau diesen Abschnitten:**
   - `## Trigger`: wann, und wann **nicht**.
   - `## Steps`: nummeriert, imperativ, ein Schritt pro Aktion; Tools, Befehle, Dateien benennen. Bei langen Abläufen eine Checkliste zum Kopieren.
   - `## Edge cases`: bekannte Fehlerfälle und was dann zu tun ist.
   - `## Success metric`: beobachtbare Kriterien für „fertig“.
   - `## Evaluation`: wie die Metrik geprüft wird (Befehl, Test, Checkliste).
4. **Knapp schreiben:** Claude ist schlau; nur hinzufügen, was es nicht schon weiß. Eine Voreinstellung statt vieler Optionen. Ein Begriff pro Sache durchgehend.
5. **Freiheitsgrad passend wählen:** fragile Abläufe exakt vorgeben (Skript, fester Befehl), offene Aufgaben als Heuristik.
6. **Aufteilen:** SKILL.md unter 500 Zeilen (besser < 150). Details in Dateien daneben, **nur eine Ebene tief** von SKILL.md verlinkt. Dateien über 100 Zeilen bekommen oben ein Inhaltsverzeichnis. Deterministische Arbeit als Skript, das ausgeführt (nicht gelesen) wird.
7. **Pfade** immer mit `/`, keine zeitabhängigen Angaben („ab August …“), MCP-Tools voll qualifiziert (`Server:tool`).
8. **Speichern:** global `~/.claude/skills/<name>/SKILL.md`, Projekt `.claude/skills/<name>/SKILL.md`, Agent-SOPs in `skills/` des Agents. Eigene Entwürfe zuerst in den Projektordner zum Review.
9. **Testen:** die drei Szenarien aus Schritt 1 durchspielen, plus ein Prompt, der **nicht** auslösen darf. Ergebnisse berichten.

## Edge cases
- Überschneidung mit vorhandenem Skill: den erweitern statt einen Fast-Duplikat anlegen.
- Skill braucht Secrets: nur Namen von Umgebungsvariablen, nie Werte.
- Skill wird zu groß: nach Bereichen in Referenzdateien aufteilen, SKILL.md als Router.

## Success metric
- Alle fünf Abschnitte vorhanden und gefüllt; Description in dritter Person mit „Use when“.
- Limits eingehalten (Name, Description, Zeilen, eine Verweisebene).
- Drei Szenarien bestanden, Negativ-Test löst nicht aus.

## Evaluation
- Datei gegenlesen anhand dieser Liste.
- Test-Ergebnisse (positiv und negativ) im Chat zeigen.

Quelle S1: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
