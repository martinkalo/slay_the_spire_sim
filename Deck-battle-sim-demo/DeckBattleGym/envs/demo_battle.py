import sys
import os
# -----------------------------------------------
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
# -----------------------------------------------

from DeckBattleGym.envs.player import Player
from DeckBattleGym.envs.battle import Battle
from DeckBattleGym.envs.loader import load_card_pool,load_deck_by_id, load_enemy_group


if __name__ == "__main__":
    card_pool = load_card_pool()
    #deck = build_starting_deck(card_pool)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    deck_json_path = os.path.join(base_dir, "data", "deck.json")
    enemygroup_json_path = os.path.join(base_dir, "data", "enemy_group.json")
    deck, _= load_deck_by_id(deck_json_path, "deck05", card_pool)   # debug deck
    player=Player(name="Hero", hp=80, energy=3)
    enemies, _ = load_enemy_group(enemygroup_json_path, "group07")
    battle = Battle(player, enemies, deck, card_pool=card_pool, if_battle_log=True)
    battle.run()