import sys, os, json, csv, math, time, statistics
from copy import deepcopy
from functools import lru_cache
from multiprocessing import Pool, cpu_count
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from DeckBattleGym.envs.battle import Battle
from DeckBattleGym.envs.player import Player
from DeckBattleGym.envs.player_strategy import RandomStrategy
from DeckBattleGym.envs.loader import load_card_pool, load_deck_by_id, load_enemy_group
from DeckBattleGym.sim.mcts import play_battle
from DeckBattleGym.sim.heuristic import heuristic_action
from DeckBattleGym.sim.encode import ValueFn

DECKS = None                 
GROUPS = None               
START_HPS = [80]             
SEEDS = range(30)
ITERS = 500
STRATS = ["mcts_heur", "mcts_value_pw0.0", "mcts_value_pw0.05", "mcts_value_pw0.1", "mcts_value_mix"]
BASELINE, CHALLENGER = "mcts_heur", "mcts_value"     
OUT_CSV = "experiment_results.csv"

STRATEGIES = {                
    "random":          ("run",  RandomStrategy,    {}),
    "mcts_rand":       ("mcts", None, {}),
    "mcts_heur":       ("mcts", None, {"rollout_policy": heuristic_action}),
    "mcts_heur_2deep": ("mcts", None, {"rollout_policy": heuristic_action, "max_tree_turns": 2}),
}

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DECK_PATH = os.path.join(BASE, "data", "deck.json")
GROUP_PATH = os.path.join(BASE, "data", "enemy_group.json")

VPATH = os.path.join(BASE, "value_net.npz")
for pw in (0.0, 0.05, 0.1):
    STRATEGIES[f"mcts_value_pw{pw}"] = ("mcts", None,
        {"value_path": VPATH, "c": 0.3, "progress_weight": pw})
STRATEGIES["mcts_value_mix"] = ("mcts", None,
    {"value_path": VPATH, "c": 0.3, "progress_weight": 0.05, "value_mix": 0.5, "rollout_policy": heuristic_action})


@lru_cache(maxsize=None)
def pool():
    return load_card_pool()

@lru_cache(maxsize=None)
def get_deck(deck_id):
    return load_deck_by_id(DECK_PATH, deck_id, pool())[0]

@lru_cache(maxsize=None)
def get_enemies(group_id):
    return load_enemy_group(GROUP_PATH, group_id)[0]

@lru_cache(maxsize=None)
def get_value_fn(path):
    return ValueFn(path)


def make(deck_id, group_id, hp, seed, strategy):
    return Battle(Player("Hero", hp=hp, energy=3, strategy=strategy),
                  [deepcopy(e) for e in get_enemies(group_id)], deepcopy(get_deck(deck_id)),
                  card_pool=pool(), seed=seed, record_actions=False)


def run_task(task):
    deck_id, group_id, hp, strat, seed = task
    kind, cls, kw = STRATEGIES[strat]
    t0 = time.time()
    if kind == "run":
        b = make(deck_id, group_id, hp, seed, cls())
        b.run()
        win, final_hp, turns = b.simulation_log["win"], b.player.hp, b.turn
    else:
        kw = dict(kw)                                              
        if "value_path" in kw:                                     
            kw["value_fn"] = get_value_fn(kw.pop("value_path")) 
        b = make(deck_id, group_id, hp, seed, RandomStrategy())
        r = play_battle(b, iterations=ITERS, seed=seed, **kw)
        win, final_hp, turns = r["win"], r["final_hp"], r["turns"]
    return {"deck": deck_id, "group": group_id, "hp": hp, "strategy": strat, "seed": seed,
            "win": int(win), "final_hp": max(0, final_hp), "turns": turns,
            "secs": round(time.time() - t0, 2)}


def se(xs):
    return statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def summarize(rows):
    cells = {}
    for r in rows:
        cells.setdefault((r["deck"], r["group"], r["hp"]), {}).setdefault(r["strategy"], {})[r["seed"]] = r
    for (deck, group, hp), by_strat in sorted(cells.items()):
        print(f"\n== {deck} vs {group} (start HP {hp}) ==")
        for strat, bys in by_strat.items():
            rs = list(bys.values())
            hps = [r["final_hp"] for r in rs]
            capped = sum(1 for r in rs if r["turns"] > 60)
            print(f"  {strat:20s} win {sum(r['win'] for r in rs) / len(rs):4.0%}  "
                  f"HP {statistics.mean(hps):5.1f} +/- {se(hps):4.1f}  "
                  f"turns {statistics.mean(r['turns'] for r in rs):4.1f}  "
                  f"capped {capped}  secs/battle {statistics.mean(r['secs'] for r in rs):5.2f}")
        a = by_strat.get(BASELINE)
        for name, b in by_strat.items():
            if not a or name == BASELINE:
                continue
            common = [s for s in a if s in b]
            if not common:
                continue
            dh = [b[s]["final_hp"] - a[s]["final_hp"] for s in common]
            dw = [b[s]["win"] - a[s]["win"] for s in common]
            m, e = statistics.mean(dh), se(dh)
            verdict = "real" if abs(m) > 2 * e else "noise"
            print(f"  {name} - {BASELINE}: HP {m:+.1f} +/- {e:.1f} ({verdict}), "
                  f"wins {statistics.mean(dw):+.0%}")


def main():
    decks = DECKS or list(json.load(open(DECK_PATH, encoding="utf-8")).keys())
    groups = GROUPS or list(json.load(open(GROUP_PATH, encoding="utf-8")).keys())
    tasks = [(d, g, hp, st, sd) for d in decks for g in groups
             for hp in START_HPS for st in STRATS for sd in SEEDS]
    print(sorted({t[:4] for t in tasks[2590:2680]}))
    print(f"{len(tasks)} battles on {max(1, cpu_count() - 1)} workers", flush=True)

    rows = []
    with Pool(max(1, cpu_count() - 1)) as p:
        for i, row in enumerate(p.imap_unordered(run_task, tasks, chunksize=1), 1):
            rows.append(row)
            if i % 50 == 0:
                print(f"  {i}/{len(tasks)}", flush=True)

    with open(os.path.join(BASE, OUT_CSV), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summarize(rows)


if __name__ == "__main__":      
    main()