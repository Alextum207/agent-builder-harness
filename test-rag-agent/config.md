---
model: anthropic:claude-haiku-5-5
price_usd_per_mtok: {input: 0.10, output: 0.50}
max_suchen: {ohne_suche: 0, eine_suche: 2, mehrstufig: 3}   # Abbruch nach N Suchen
treffer_pro_suche: 4
log_retention_days: 30
personal_data: nein
kontext: wissens-agent
muster: Agentic RAG mit Adaptive-Router – ob und wie oft gesucht wird, hängt von der Frage ab; Ablauf als Graph
run_length: kurz
autonomy_level: beobachten   # beantwortet nur Fragen, schreibt nichts
guardrails: agent-guardrails 0.3.0
brain: brain                 # OKF-Bundle, erzeugt mit company-brain/ingest.py
---
