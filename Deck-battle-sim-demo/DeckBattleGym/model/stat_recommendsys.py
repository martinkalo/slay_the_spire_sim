import os
import json
from collections import defaultdict, Counter


def recommend_action_ranking(hand, turn, action_stats):
    stat_key = f"turn={turn}"

    ranking = []
    if stat_key in action_stats:
        for (card_id, target_ids), count in action_stats[stat_key].most_common():
            for card in hand:
                if card.id == card_id:
                    ranking.append((card, list(target_ids)))
                    break  

    return ranking


def generate_action_stats(examine_path, only_wins=True):
    if not os.path.exists(examine_path):
        raise FileNotFoundError(f"Simulation file not found: {examine_path}")

    with open(examine_path) as f:
        log = json.load(f)

    action_stats = defaultdict(Counter)

    for sim in log["simulations"]:
        if only_wins and not sim["win"]: 
            continue
        for turn in sim["turns"]:
            turn_num = turn["turn"]
            stat_key = f"turn={turn_num}"

            for action in turn["actions"]:
                card_id = action["card"]
                targets = tuple(sorted(action.get("targets", [])))  
                action_stats[stat_key][(card_id, targets)] += 1
    
    return action_stats
