import csv, math, statistics, sys, collections

PATH = sys.argv[1] if len(sys.argv) > 1 else "DeckBattleGym/experiment_results.csv"
BASELINE = "mcts_heur"
CAP = 60                       # battles with more turns than this hit the turn cap


def mean(xs): return sum(xs) / len(xs) if xs else float("nan")
def se(xs): return statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


cells = collections.defaultdict(lambda: collections.defaultdict(dict))
with open(PATH, newline="") as f:
    for r in csv.DictReader(f):
        cells[(r["deck"], r["group"], r["hp"])][r["strategy"]][int(r["seed"])] = (
            int(r["win"]), float(r["final_hp"]), int(r["turns"]), float(r["secs"]))

strats = list(dict.fromkeys(s for by in cells.values() for s in by))
print("strategies in file:", strats)
if BASELINE not in strats:
    sys.exit(f"baseline {BASELINE} not in the file")

# 1. overall per strategy
print(f"\n{'strategy':24s}{'battles':>8s}{'win%':>7s}{'HP':>7s}{'secs':>7s}{'capped':>8s}")
for s in strats:
    v = [x for by in cells.values() for x in by.get(s, {}).values()]
    capped = sum(1 for x in v if x[2] > CAP and x[0] == 0)
    print(f"{s:24s}{len(v):8d}{mean([x[0] for x in v]):7.0%}{mean([x[1] for x in v]):7.1f}"
          f"{mean([x[3] for x in v]):7.2f}{capped:8d}")

# 2. sort cells: where wins differ vs where everyone always wins
win_cells, hp_cells = [], []
for key, by in cells.items():
    wr = [mean([x[0] for x in d.values()]) for d in by.values()]
    if all(v == 0 for v in wr):
        continue
    (hp_cells if all(v >= 0.97 for v in wr) else win_cells).append(key)


def pooled(s, keys, i):
    d = []
    for k in keys:
        a, b = cells[k].get(BASELINE, {}), cells[k].get(s, {})
        d += [b[x][i] - a[x][i] for x in a if x in b]
    return d


print(f"\nvs {BASELINE}: {len(win_cells)} cells where wins differ, {len(hp_cells)} cells where all always win")
for s in strats:
    if s == BASELINE:
        continue
    dw, dh = pooled(s, win_cells, 0), pooled(s, hp_cells, 1)
    print(f"{s:24s} win {mean(dw):+.1%} +/- {se(dw):.1%}    HP {mean(dh):+.1f} +/- {se(dh):.1f}")

# 3. per-cell win rates for the informative cells
print("\nwin% per cell")
print(f"{'cell':20s}" + "".join(f"{i:>7d}" for i in range(len(strats))))
for k in sorted(win_cells):
    row = "".join(f"{mean([x[0] for x in cells[k].get(s, {}).values()]):7.0%}" for s in strats)
    print(f"{k[0] + '/' + k[1]:20s}{row}")
print("columns:", ", ".join(f"{i}={s}" for i, s in enumerate(strats)))

# 4. long-format summary for Excel/Sheets pivot tables
with open("summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["deck", "group", "hp", "strategy", "n", "win_rate", "mean_hp",
                "mean_turns", "mean_secs", "capped"])
    for k, by in sorted(cells.items()):
        for s in strats:
            v = list(by.get(s, {}).values())
            if v:
                w.writerow([*k, s, len(v), round(mean([x[0] for x in v]), 3),
                            round(mean([x[1] for x in v]), 1), round(mean([x[2] for x in v]), 1),
                            round(mean([x[3] for x in v]), 2),
                            sum(1 for x in v if x[2] > CAP and x[0] == 0)])
print("\nwrote summary.csv")