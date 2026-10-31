"""Sammelt Werkstudentenstellen (München) und schreibt workspace/tracker.csv + workspace/postings/<id>.txt.

uv run python tools/scrape.py run                 alle Quellen
uv run python tools/scrape.py run ba linkedin     nur diese Quellen
uv run python tools/scrape.py add <quelle> <url> <firma> <titel> <ort> <textdatei>   (z. B. Indeed via Chrome)
uv run python tools/scrape.py page <id> <url>     Firmenseite als Beleg speichern (Initiativbewerbung)
"""
import truststore; truststore.inject_into_ssl()
import base64, csv, hashlib, json, re, sys, time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
WS, POSTINGS, LOGS = ROOT / "workspace", ROOT / "workspace" / "postings", ROOT / "logs"
TRACKER = WS / "tracker.csv"
FIELDS = ["id", "quelle", "firma", "titel", "ort", "url", "score", "stunden", "lohn", "mindestlaufzeit",
          "kuendigungsfrist", "kontakt_email", "gefunden", "status"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"}
QUERIES = ["Werkstudent Process Mining", "Werkstudent Prozessmanagement", "Werkstudent Data Science",
           "Werkstudent Data Analytics", "Werkstudent KI", "Werkstudent AI", "Working Student AI", "Working Student Data"]
PAUSE, MAX_TEXT = 1.5, 20000

WERK = re.compile(r"werkstudent|working student|studentische|student assistant|studentjob", re.I)
RAUS = re.compile(r"praktik|internship|\bintern\b|thesis|abschlussarbeit|masterarbeit|bachelorarbeit|dual|stuttgart", re.I)
ORT = re.compile(r"münchen|munich|muenchen|garching|unterföhring|ismaning|unterschleißheim|aschheim|feldkirchen|"
                 r"planegg|martinsried|oberhaching|taufkirchen|ottobrunn|neubiberg|hallbergmoos|grasbrunn", re.I)
FACH = {  # Gewicht pro Treffer in Titel+Text; Titel zählt doppelt
    r"process mining|prozess-?mining|celonis|signavio|process intelligence": 5,
    r"\bki\b|\bai\b|künstliche intelligenz|artificial intelligence|machine learning|\bllm|agent|genai|generative": 3,
    r"data science|data analytics|datenanalyse|analytics|\bdata\b|daten": 2,
    r"prozess|process|automatisierung|automation|workflow": 2,
    r"python|sql|power ?bi|n8n": 1,
}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def mask(text: str) -> str:  # DSGVO: keine Klartext-Adressen in Logs
    return EMAIL.sub(lambda m: m.group()[0] + "***@" + m.group().split("@")[1], text)


def log(event: dict):
    LOGS.mkdir(exist_ok=True)
    with (LOGS / f"scrape-{date.today()}.jsonl").open("a", encoding="utf-8") as f:
        f.write(mask(json.dumps({"ts": time.time(), **event}, ensure_ascii=False)) + "\n")


def get(url, **kw):
    time.sleep(PAUSE)
    headers = {**UA, **kw.pop("headers", {})}
    for versuch in range(3):   # BA trennt Verbindungen oft, LinkedIn drosselt (429): warten, erneut
        try:
            r = requests.get(url, headers=headers, timeout=25, **kw)
        except requests.ConnectionError:
            if versuch == 2:
                raise
            time.sleep(5 * (versuch + 1))
            continue
        if r.status_code != 429 or versuch == 2:
            break
        time.sleep(20)
    if r.status_code in (403, 429, 999):
        raise PermissionError(f"blockiert ({r.status_code})")
    r.raise_for_status()
    return r


def html_text(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text("\n", strip=True)


def job(quelle, firma, titel, ort, url, text=""):
    return {"quelle": quelle, "firma": firma.strip(), "titel": titel.strip(), "ort": ort.strip(), "url": url.split("?")[0] if quelle != "ba" else url, "text": text}


# ---------- Quellen: liefern Listen von job(); Text darf leer sein (dann detail()) ----------
def src_ba(out):
    for q in QUERIES:
        r = get("https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs",
                params={"was": q, "wo": "München", "umkreis": 25, "size": 50, "veroeffentlichtseit": 60},
                headers={"X-API-Key": "jobboerse-jobsuche"}).json()
        for j in r.get("ergebnisliste", []):
            ort = ", ".join(l["adresse"].get("ort", "") for l in j.get("stellenlokationen", []))
            ref = j["referenznummer"]
            out.append(job("ba", j.get("firma", ""), j.get("stellenangebotsTitel", ""), ort,
                           f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}"))


def src_linkedin(out):
    for q in QUERIES:
        for start in (0, 25):
            s = BeautifulSoup(get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                                  params={"keywords": q, "location": "München, Bayern, Deutschland", "start": start}).text, "html.parser")
            for c in s.select("div.base-search-card"):
                a, h3, h4, loc = (c.select_one(x) for x in ("a.base-card__full-link", "h3", "h4", ".job-search-card__location"))
                if a and h3:
                    out.append(job("linkedin", h4.get_text(strip=True) if h4 else "", h3.get_text(strip=True),
                                   loc.get_text(strip=True) if loc else "", a["href"]))


def src_stepstone(out):
    for q in QUERIES:
        slug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
        s = BeautifulSoup(get(f"https://www.stepstone.de/jobs/{slug}/in-muenchen").text, "html.parser")
        for a in s.select('[data-at="job-item"]'):
            t, f, o = (a.select_one(f'[data-at="{x}"]') for x in ("job-item-title", "job-item-company-name", "job-item-location"))
            if t and t.get("href"):
                out.append(job("stepstone", f.get_text(strip=True) if f else "", t.get_text(strip=True),
                               o.get_text(strip=True) if o else "", urljoin("https://www.stepstone.de", t["href"])))


def src_indeed(out):  # blockt meist (403) → Skill nutzt Claude in Chrome + `add`
    for q in QUERIES[:2]:
        s = BeautifulSoup(get("https://de.indeed.com/jobs", params={"q": q, "l": "München"}).text, "html.parser")
        for c in s.select("div.job_seen_beacon"):
            a, f, o = c.select_one("h2 a"), c.select_one('[data-testid="company-name"]'), c.select_one('[data-testid="text-location"]')
            if a:
                out.append(job("indeed", f.get_text(strip=True) if f else "", a.get_text(strip=True),
                               o.get_text(strip=True) if o else "", urljoin("https://de.indeed.com", a["href"])))


def src_ats(out):
    with (ROOT / "context" / "firmen.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name, ats, slug = row["firma"], row["ats"], row["slug"]
            try:
                if ats == "greenhouse":
                    for j in get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"}).json()["jobs"]:
                        out.append(job("ats", name, j["title"], j["location"]["name"], j["absolute_url"],
                                       html_text(BeautifulSoup(j.get("content", ""), "html.parser").get_text())))
                elif ats == "ashby":
                    for j in get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}").json()["jobs"]:
                        locs = [j.get("location", "")] + [x.get("location", "") for x in j.get("secondaryLocations", [])]
                        out.append(job("ats", name, j["title"], ", ".join(locs), j["jobUrl"], j.get("descriptionPlain", "")))
                elif ats == "lever":
                    for j in get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"}).json():
                        out.append(job("ats", name, j["text"], j["categories"].get("location", ""), j["hostedUrl"],
                                       j.get("descriptionPlain", "")))
                elif ats == "personio":
                    for p in ElementTree.fromstring(get(f"https://{slug}.jobs.personio.de/xml").content).iter("position"):
                        text = "\n".join(html_text(v.text) for v in p.iter("value"))
                        offices = ", ".join(o.text or "" for o in p.iter("office"))
                        out.append(job("ats", name, p.findtext("name", ""), offices,
                                       f"https://{slug}.jobs.personio.de/job/{p.findtext('id')}", text))
            except Exception as e:  # eine kaputte Firma stoppt nicht die Liste
                log({"quelle": "ats", "firma": name, "fehler": str(e)[:200]})


SOURCES = {"ba": src_ba, "linkedin": src_linkedin, "stepstone": src_stepstone, "indeed": src_indeed, "ats": src_ats}


def detail(j) -> str:
    u = j["url"]
    if j["quelle"] == "ba":
        ref = u.rsplit("/", 1)[1]
        d = get("https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/" + base64.b64encode(ref.encode()).decode(),
                headers={"X-API-Key": "jobboerse-jobsuche"}).json()
        return d.get("stellenangebotsBeschreibung", "")
    if j["quelle"] == "linkedin":
        jid = re.search(r"(\d{8,})", u).group(1)
        s = BeautifulSoup(get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}").text, "html.parser")
        box = s.select_one(".show-more-less-html__markup") or s
        return box.get_text("\n", strip=True)
    s = BeautifulSoup(get(u).text, "html.parser")
    for x in s(["script", "style", "nav", "header", "footer"]):
        x.decompose()
    box = s.select_one('[data-at="job-ad-content"]') or s.select_one("main") or s
    return box.get_text("\n", strip=True)


# ---------- Filter, Score, Felder: alles Code, nicht LLM ----------
def passt(j) -> bool:
    return bool(WERK.search(j["titel"]) and not RAUS.search(j["titel"]) and ORT.search(j["ort"]) and not re.search(r"stuttgart", j["ort"], re.I))


def score(j) -> int:
    t, x = j["titel"].lower(), j["text"].lower()
    return sum(w * (2 * bool(re.search(p, t)) + bool(re.search(p, x))) for p, w in FACH.items())


def felder(text: str) -> dict:
    def first(p):
        m = re.search(p, text, re.I)
        return re.sub(r"\s+", " ", m.group(0)).strip()[:80] if m else "nicht angegeben"
    return {
        "stunden": first(r"\d{1,2}\s*(?:[-–]|bis)?\s*\d{0,2}\s*(?:Std\.?|Stunden|h|hours)\s*(?:pro|/|per|die|a|in der)?\s*(?:Woche|week|wöchentlich)"),
        "lohn": first(r"\d{1,3}(?:[.,]\d{1,2})?\s*(?:€|EUR|Euro)\s*(?:brutto\s*)?(?:/|pro|per|je)\s*(?:Stunde|Std\.?|h|hour)"),
        "mindestlaufzeit": first(r"(?:mind(?:estens|\.)?|minimum(?: of)?|at least|für)\s*\d{1,2}\s*(?:Monate|Monaten|months|Semester)"),
        "kuendigungsfrist": first(r"(?:Kündigungsfrist|notice period)[^.\n]{0,60}"),
        "kontakt_email": ";".join(sorted(set(EMAIL.findall(text)))) or "nicht angegeben",
    }


def jid(j) -> str:
    return j["quelle"][:2] + "-" + hashlib.sha1(j["url"].encode()).hexdigest()[:8]


def load() -> dict:
    if not TRACKER.exists():
        return {}
    with TRACKER.open(encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def save(rows: dict):
    WS.mkdir(exist_ok=True)
    with TRACKER.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: -int(r["score"] or 0)))


def store(j, rows) -> bool:
    """Speichert passenden Job; True wenn neu. Tracker-Status bestehender Einträge bleibt erhalten."""
    i = jid(j)
    if i in rows or any(r["firma"].lower() == j["firma"].lower() and r["titel"].lower() == j["titel"].lower() for r in rows.values()):
        return False
    POSTINGS.mkdir(parents=True, exist_ok=True)
    text = j["text"][:MAX_TEXT]
    (POSTINGS / f"{i}.txt").write_text(
        f"Quelle: {j['quelle']}\nURL: {j['url']}\nFirma: {j['firma']}\nTitel: {j['titel']}\nOrt: {j['ort']}\n\n<anzeige>\n{text}\n</anzeige>\n",
        encoding="utf-8")
    rows[i] = {"id": i, "quelle": j["quelle"], "firma": j["firma"], "titel": j["titel"], "ort": j["ort"], "url": j["url"],
               "score": score(j), **felder(text), "gefunden": str(date.today()), "status": "neu"}
    return True


def run(names):
    rows, neu = load(), 0
    for name in names:
        found = []                 # Teilergebnisse bleiben erhalten, wenn eine Quelle mitten drin blockt
        try:
            SOURCES[name](found)
            status = "ok"
        except PermissionError as e:
            found, status = [], str(e)
        except Exception as e:
            found, status = [], f"fehler: {str(e)[:150]}"
        kandidaten = [j for j in found if passt(j)]
        n_neu = 0
        for j in kandidaten:
            if jid(j) in rows:
                continue
            if not j["text"]:
                try:
                    j["text"] = detail(j)
                except Exception as e:
                    log({"quelle": name, "url": j["url"], "detail_fehler": str(e)[:150]})
                    continue           # ohne Anzeigentext kein Anschreiben möglich; nächster Lauf holt sie
            if score(j) > 0 and store(j, rows):
                n_neu += 1
        neu += n_neu
        log({"quelle": name, "status": status, "gefunden": len(found), "filter_ok": len(kandidaten), "neu": n_neu})
        print(f"{name:10} {status:22} gefunden={len(found):4} nach_filter={len(kandidaten):4} neu={n_neu}", flush=True)
        save(rows)                 # nach jeder Quelle sichern, ein Abbruch verliert nichts
    print(f"neu gesamt: {neu} | tracker: {TRACKER}")


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("run", [])
    if cmd == "run":
        run(args or list(SOURCES))
    elif cmd == "add":
        quelle, url, firma, titel, ort, textfile = args
        rows = load()
        j = job(quelle, firma, titel, ort, url, Path(textfile).read_text(encoding="utf-8"))
        print(("gespeichert: " + jid(j)) if passt(j) and store(j, rows) else "nicht gespeichert (Filter oder Duplikat)")
        save(rows)
    elif cmd == "page":
        i, url = args
        POSTINGS.mkdir(parents=True, exist_ok=True)
        (POSTINGS / f"{i}.firma.txt").write_text(f"URL: {url}\n\n<firmenseite>\n{detail({'quelle': 'web', 'url': url})[:MAX_TEXT]}\n</firmenseite>\n", encoding="utf-8")
        print(f"gespeichert: {POSTINGS / (i + '.firma.txt')}")
    else:
        sys.exit(__doc__)
