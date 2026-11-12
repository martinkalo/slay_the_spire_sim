import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from copy import deepcopy
from DeckBattleGym.envs.battle import Battle
from DeckBattleGym.envs.player import Player
from DeckBattleGym.envs.player_strategy import RandomStrategy
from DeckBattleGym.envs.loader import load_card_pool, load_deck_by_id, load_enemy_group
from DeckBattleGym.sim.mcts import play_battle

DECK_ID, GROUP_ID = "deck06", "group04" 
N, ITERS = 30, 200

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
card_pool = load_card_pool()
deck, _ = load_deck_by_id(os.path.join(base, "data", "deck.json"), DECK_ID, card_pool)
enemies_t, _ = load_enemy_group(os.path.join(base, "data", "enemy_group.json"), GROUP_ID)

def make(seed):
    return Battle(Player("Hero", hp=80, energy=3, strategy=RandomStrategy()),
                  [deepcopy(e) for e in enemies_t], deepcopy(deck),
                  card_pool=card_pool, seed=seed, record_actions=False)

def summarize(name, rows):
    w = sum(r["win"] for r in rows) / len(rows)
    hp = sum(r["final_hp"] for r in rows) / len(rows)
    print(f"{name:8s} win {w:.0%}  avg final HP {hp:.1f}")

rand_rows = []
for s in range(N):
    b = make(s); b.run()
    rand_rows.append({"win": b.simulation_log["win"], "final_hp": b.player.hp})

mcts_rows = [play_battle(make(s), iterations=ITERS, seed=s) for s in range(N)]

summarize("random", rand_rows)
summarize("mcts", mcts_rows)