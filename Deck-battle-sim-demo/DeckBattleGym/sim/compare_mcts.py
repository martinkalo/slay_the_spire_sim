import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from copy import deepcopy
from DeckBattleGym.envs.battle import Battle
from DeckBattleGym.envs.player import Player
from DeckBattleGym.envs.player_strategy import RandomStrategy
from DeckBattleGym.envs.loader import load_card_pool, load_deck_by_id, load_enemy_group
from DeckBattleGym.sim.mcts import play_battle
from DeckBattleGym.sim.heuristic import heuristic_action

DECK_ID, GROUP_ID = "deck07", "group05"     
N, ITERS = 10, 100                       

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
card_pool = load_card_pool()
deck, _ = load_deck_by_id(os.path.join(base, "data", "deck.json"), DECK_ID, card_pool)
enemies_t, _ = load_enemy_group(os.path.join(base, "data", "enemy_group.json"), GROUP_ID)


def make(seed, strategy=None):
    return Battle(Player("Hero", hp=80, energy=3, strategy=strategy or RandomStrategy()),
                  [deepcopy(e) for e in enemies_t], deepcopy(deck),
                  card_pool=card_pool, seed=seed)


def run_strategy(make_strategy):
    rows = []
    for s in range(N):
        b = make(s, make_strategy())
        b.run()
        rows.append({"win": b.simulation_log["win"], "final_hp": b.player.hp})
    return rows


def run_mcts(**kw):
    return [play_battle(make(s), iterations=ITERS, seed=s, **kw) for s in range(N)]


def summarize(name, rows):
    w = sum(r["win"] for r in rows) / len(rows)
    hp = sum(r["final_hp"] for r in rows) / len(rows)
    print(f"{name:24s} win {w:.0%}  avg final HP {hp:.1f}", flush=True)


if __name__ == "__main__":
    summarize("random", run_strategy(RandomStrategy))
    summarize("mcts (random rollouts)", run_mcts())
    summarize("mcts (heuristic)", run_mcts(rollout_policy=heuristic_action))