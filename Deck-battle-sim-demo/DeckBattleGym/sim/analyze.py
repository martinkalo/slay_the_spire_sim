import csv, math, statistics, sys, collections
from pathlib import Path


PATH = sys.argv[1] if len(sys.argv) > 1 else "experiment_results.csv"
c_value = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
BASE, CHAL, NAIVE = "mcts_rand", "mcts_heur", "naive"
CAP = 60                      


def mean(xs): return sum(xs) / len(xs) if xs else float("nan")
def se(xs): return statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


cells = collections.defaultdict(lambda: collections.defaultdict(dict))
with open(PATH, newline="") as f:
    for r in csv.DictReader(f):
        cells[(r["deck"], r["group"], r["hp"])][r["strategy"]][int(r["seed"])] = (
            int(r["win"]), float(r["final_hp"]), int(r["turns"]), float(r["secs"]))

strats = list(dict.fromkeys(s for by in cells.values() for s in by))
print("strategies in file:", strats)
if BASE not in strats:
    sys.exit(f"baseline {BASE} not in the file")

def main():
    print(f"a{c_value}")
    win_diffs, hp_diffs = [], []
    print(f"{'deck':7s}{'group':9s}{'win% R/N/A/B':>24s}{'HP R/N/A/B':>26s}{'note':>20s}   c")    
    out_rows = []
    for (deck, group, hp), by in sorted(cells.items()):
        def w(s): return mean([v[0] for v in by.get(s, {}).values()])
        def h(s): return mean([v[1] for v in by.get(s, {}).values()])
        a, b = by.get(BASE, {}), by.get(CHAL, {})
        common = sorted(set(a) & set(b))
        note = ""
        if common:
            wa, wb = w(BASE), w(CHAL)
            if wa == 0 and wb == 0:
                note = "no wins either"
            elif wa >= 0.97 and wb >= 0.97:
                note = "both win; HP only"
                hp_diffs += [b[s][1] - a[s][1] for s in common]
            else:
                note = "informative"
                win_diffs += [b[s][0] - a[s][0] for s in common]
        print(f"{deck:7s}{group:9s}{w('random'):6.0%}{w(NAIVE):6.0%}{w(BASE):6.0%}{w(CHAL):6.0%}"f"{h('random'):8.0f}{h(NAIVE):6.0f}{h(BASE):6.0f}{h(CHAL):6.0f}{note:>20s}  {c_value}")
        out_rows.append([deck, group, hp, round(w("random"), 3), round(w(NAIVE), 3), round(w(BASE), 3), round(w(CHAL), 3), round(h("random"), 1), round(h(NAIVE), 1), round(h(BASE), 1), round(h(CHAL), 1), note, c_value])
    def report(name, xs, unit):
        if xs:
            print(f"{name}: {mean(xs):+.3f} {unit} +/- {se(xs):.3f} (n={len(xs)})")

    print()
    report("win-rate gain, heuristic rollouts vs random rollouts (informative cells)", win_diffs, "")
    report("final-HP gain (cells where both always win)", hp_diffs, "HP")
    with open("summary.csv", "a", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["deck", "group", "hp",
             "win_random", "win_naive", "win_mcts_rand", "win_mcts_heur",
             "hp_random", "hp_naive", "hp_mcts_rand", "hp_mcts_heur",
             "note", "c_value"])        
        wr.writerows(out_rows)
    print("wrote summary.csv")
    for s in (NAIVE, BASE, CHAL):
        t = [v[2] for by in cells.values() for v in by.get(s, {}).values()]
        print(f"secs/battle {s}: {mean(t):.1f}")

if __name__ == "__main__":      
    main()
