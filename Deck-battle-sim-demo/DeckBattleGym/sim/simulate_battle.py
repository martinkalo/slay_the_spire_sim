import sys
import os
import json
# -----------------------------------------------
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
# -----------------------------------------------

from copy import deepcopy
from DeckBattleGym.envs.battle import Battle
from DeckBattleGym.envs.player import Player
from DeckBattleGym.envs.player_strategy import RandomStrategy
from DeckBattleGym.envs.loader import load_card_pool, load_deck_by_id, load_enemy_group


def run_simulation(deck_json_path, deck_id, 
                   enemygroup_json_path, enemygroup_id, 
                   num_simulations=100, 
                   output_dir=None):
    
    if output_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        output_dir = os.path.join(base_dir, "experiments")

    os.makedirs(output_dir, exist_ok=True)

    card_pool = load_card_pool()
    deck, deck_name = load_deck_by_id(deck_json_path, deck_id, card_pool)
    enemies_template, enemygroup_name = load_enemy_group(enemygroup_json_path, enemygroup_id)

    result_log = {
        "deck_id": deck_id,
        "deck_name": deck_name,
        "cards": [card.id for card in deck],
        "enemygroup_id": enemygroup_name,
        "initial_hp": 80,
        "simulations": []
    }

    for _ in range(num_simulations):
        player = Player(name="Hero", hp=80, energy=3, strategy=RandomStrategy())
        enemies = [deepcopy(e) for e in enemies_template]
        battle = Battle(player, enemies, deepcopy(deck), card_pool=card_pool,if_battle_log=False)

        battle.run()

        result_log["simulations"].append({
            "final_hp": player.hp,
            "turns_taken": battle.turn,
            "win": player.hp > 0,
            "turns": battle.simulation_log["turns"]
        })
    
    filename = f"{deck_name}_vs_{enemygroup_name}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(result_log, f, indent=2)

    print(f"[Done] Saved {num_simulations} simulations to {filepath}")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    deck_json_path = os.path.join(base_dir, "data", "deck.json")
    enemygroup_json_path = os.path.join(base_dir, "data", "enemy_group.json")
   
    run_simulation(
        deck_json_path=deck_json_path,
        deck_id="deck06",                             # <-- replace with your own deck_id
        enemygroup_json_path=enemygroup_json_path,
        enemygroup_id="group04",                      # <-- replace with your own enemygroup_id
        num_simulations=1000
    )


