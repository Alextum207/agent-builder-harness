"""Nachrechnung zu ANALYSE-ki-vs-algorithmus.md, Abschnitt 4. Nur stdlib, kein Produktcode.

Aufruf: python ANALYSE-ki-vs-algorithmus-nachrechnung.py  (ca. 1 min, Seed fest)
"""
import math, random

def binom_cdf(k, n, p):
    if k < 0: return 0.0
    if k >= n or p <= 0: return 1.0
    if p >= 1: return 0.0
    lp, lq, lg = math.log(p), math.log1p(-p), math.lgamma
    return min(1.0, sum(math.exp(lg(n+1)-lg(i+1)-lg(n-i+1)+i*lp+(n-i)*lq) for i in range(k+1)))

def cp_upper(x, n, delta=0.05):
    """Einseitige Clopper-Pearson-Obergrenze (= exakter Binomialtest)."""
    if n == 0 or x >= n: return 1.0
    lo, hi = x / n, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if binom_cdf(x, n, mid) > delta else (lo, mid)
    return hi

def wilson_upper(x, n, z=1.6449):
    p = x / n
    return (p + z*z/(2*n) + z*(p*(1-p)/n + z*z/(4*n*n))**0.5) / (1 + z*z/n)

print("== A  Null Fehler: noetige Faelle fuer Obergrenze <= alpha (95 %, einseitig)")
for a in (0.005, 0.01, 0.02, 0.05):
    print(f"  alpha {a:.1%}: n >= {math.ceil(math.log(0.05)/math.log(1-a))}")

print("== B  '3 Laeufe ohne Korrektur' belegt Fehlerquote <=", f"{cp_upper(0, 3):.0%}")

print("== C  Noetige akzeptierte Faelle, damit wahre Quote p mit 80 % Chance als <= alpha belegt wird")
for p, a in ((0.005, 0.01), (0.01, 0.02), (0.02, 0.03), (0.02, 0.04), (0.03, 0.05)):
    n, x = 25, 0
    while True:
        while cp_upper(x + 1, n) <= a: x += 1
        if cp_upper(x, n) <= a and binom_cdf(x, n, p) >= 0.8: break
        n += 25
    print(f"  wahr {p:.1%}, Ziel {a:.0%}: n ~ {n}")

print("== D  Wilson vs. Clopper-Pearson: tatsaechliche Abdeckung der 95-%-Obergrenze")
for p, n in ((0.01, 100), (0.01, 300), (0.02, 200), (0.005, 600)):
    pmf = lambda k: math.comb(n, k) * p**k * (1-p)**(n-k)
    cov_w = sum(pmf(k) for k in range(n+1) if wilson_upper(k, n) >= p)
    cov_c = sum(pmf(k) for k in range(min(n, 80)+1) if cp_upper(k, n) >= p)
    print(f"  p {p:.1%}, n {n}: Wilson {cov_w:.1%}, Clopper-Pearson {cov_c:.1%}")

print("== E  Rueckstufung: Stichproben-Fenster N, Alarm ab k Fehlern (Fehlalarm <= 5 % bei alpha = 2 %)")
for N in (50, 100, 200, 400):
    k = next(k for k in range(N) if 1 - binom_cdf(k-1, N, 0.02) <= 0.05)
    fa = 1 - binom_cdf(k-1, N, 0.02)
    pw = [1 - binom_cdf(k-1, N, q) for q in (0.04, 0.06, 0.10)]
    print(f"  N {N}: k {k}, Fehlalarm {fa:.1%}, erkennt 4 % / 6 % / 10 % mit {pw[0]:.0%} / {pw[1]:.0%} / {pw[2]:.0%}")

print("== F  Zweifach bearbeitete Faelle: 95-%-Intervall der Uebereinstimmung bei 90 % beobachtet")
for n in (50, 100, 200, 400):
    x = round(0.9 * n)
    print(f"  n {n}: {1 - cp_upper(n - x, n, 0.025):.0%} - {cp_upper(x, n, 0.025):.0%}")

print("== G  Simulation: Schwelle waehlen, Score absichtlich unkalibriert, Ziel Fehler <= 2 % (95 %)")
rnd = random.Random(7)
def draw(n):
    out = []
    for _ in range(n):
        z = rnd.gauss(0, 1)                                         # Leichtigkeit des Falls
        p_ok = 1 / (1 + math.exp(-(2.5*z + 3.0)))                   # wahre Trefferchance
        s = 1 / (1 + math.exp(-(1.0*z + 0.3 + rnd.gauss(0, 0.5))))  # verrauschter, unkalibrierter Score
        out.append((s, rnd.random() > p_ok))
    return out
def stats(data, t):
    acc = [e for s, e in data if s >= t]
    return sum(acc), len(acc)
grid = [0.30 + 0.025*i for i in range(28)]
alpha, delta = 0.02, 0.05
pop = draw(400_000)
true = {t: (lambda x, n: (x/n if n else 0, n/len(pop)))(*stats(pop, t)) for t in grid}
print(f"  Gesamtfehler ohne Auswahl: {sum(e for _, e in pop)/len(pop):.1%}")
best = min(t for t in grid if true[t][0] <= alpha)
print(f"  Optimum (wahre Werte bekannt): Abdeckung {true[best][1]:.0%}")

def naive(dev, cal):       # niedrigste Schwelle mit Punktwert <= alpha
    return min((t for t in grid if (lambda x, n: n and x/n <= alpha)(*stats(cal, t))), default=None)
def bonferroni(dev, cal):  # jede Schwelle einzeln mit delta/K
    return min((t for t in grid if cp_upper(*stats(cal, t), delta/len(grid)) <= alpha), default=None)
def sequence(dev, cal):    # Reihenfolge aus Entwicklungsdaten, Pruefung auf Kalibrierdaten, Stopp beim 1. Durchfallen
    def expected(t):
        x, n = stats(dev, t)
        return cp_upper(round(x*len(cal)/len(dev)), round(n*len(cal)/len(dev)), delta)
    start = min(range(len(grid)), key=lambda i: expected(grid[i]))
    chosen = None
    for i in range(start, -1, -1):
        if cp_upper(*stats(cal, grid[i]), delta) > alpha: break
        chosen = grid[i]
    return chosen

for n_cal in (300, 1000, 3000):
    res = {f.__name__: [] for f in (naive, bonferroni, sequence)}
    for _ in range(200):
        dev, cal = draw(n_cal), draw(n_cal)
        for f in (naive, bonferroni, sequence):
            t = f(dev, cal)
            res[f.__name__].append((true[t][0] > alpha, true[t][1]) if t is not None else (False, 0.0))
    for name, r in res.items():
        print(f"  n_cal {n_cal:>4} {name:10}: Ziel verfehlt in {sum(v for v, _ in r)/len(r):4.0%} der Laeufe, "
              f"mittlere Abdeckung {sum(c for _, c in r)/len(r):4.0%}")
