import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from copy import deepcopy
from DeckBattleGym.envs.battle import Battle
from DeckBattleGym.envs.player import Player
from DeckBattleGym.envs.player_strategy import RandomStrategy
from DeckBattleGym.envs.loader import load_card_pool, load_deck_by_id, load_enemy_group
from DeckBattleGym.sim.mcts import MCTS
from DeckBattleGym.sim.heuristic import heuristic_action, incoming_dmg

DECK_ID, GROUP_ID = "deck06", "group04"      
STRATEGY = "mcts"                           
ITERS, SEED = 2000, 0

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
card_pool = load_card_pool()
deck, _ = load_deck_by_id(os.path.join(base, "data", "deck.json"), DECK_ID, card_pool)
enemies_t, _ = load_enemy_group(os.path.join(base, "data", "enemy_group.json"), GROUP_ID)

b = Battle(Player("Hero", hp=80, energy=3, strategy=RandomStrategy()),
           [deepcopy(e) for e in enemies_t], deepcopy(deck),
           card_pool=card_pool, seed=SEED, record_actions=False)

if STRATEGY == "mcts":
    choose = MCTS(iterations=ITERS, seed=SEED, rollout_policy=heuristic_action, max_tree_turns=2).search
elif STRATEGY == "heuristic":
    choose = heuristic_action
else:
    def choose(s):
        plays = [a for a in s.legal_actions() if a[0] == "play"]
        return s.rng.choice(plays) if plays else ("end",)

b.start()
last_turn = None
while not b.is_terminal():
    if b.turn != last_turn:
        last_turn = b.turn
        print(f"\nTurn {b.turn} | HP {b.player.hp} | incoming {incoming_dmg(b)} | "f"enemies {[(i, e.hp) for i, e in enumerate(b.enemies) if e.hp > 0]}")
        print("  hand:", ", ".join(f"{c.name}({c.cost})" for c in b.hand))
    a = choose(b)
    if a[0] == "end":
        left = ", ".join(f"{c.name}({c.cost})" for c in b.hand)
        print(f"  END TURN  [energy {b.player.energy}, block {b.player.block}, hand left: {left or 'none'}]")
    else:
        c = b.hand[a[1]]
        tgt = f" -> [{a[2]}] {b.enemies[a[2]].name}" if a[2] is not None else ""
        print(f"  {c.name}{tgt}")
    b.apply(a)

print(f"\n{'WIN' if b.result()[0] else 'LOSS'} | HP {b.player.hp} | turns {b.turn}")