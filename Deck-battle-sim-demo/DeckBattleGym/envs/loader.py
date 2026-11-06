import os
import json
import random
from DeckBattleGym.envs.card import Card, AttackEffect,XAttackEffect,BlockEffect,BlockBasedAttack, BuffEffect, DebuffEffect, DrawEffect, EnergyEffect, HPEffect, ReaperAttackEffect, DoubleBlockEffect, DoubleStrengthEffect, PowerEffect, StatusEffect, ExhaustByTypeEffect, GenerateCardEffect
from DeckBattleGym.envs.enemy import Enemy, AttackIntent,BlockIntent,BuffIntent,DebuffIntent,HealIntent,InsertCardIntent,SpawnIntent
from functools import lru_cache
import copy

@lru_cache(maxsize=None)
def _enemy_defs(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)}

def parse_effect(effect_dict):
    effect_type = effect_dict["effect"]

    if effect_type == "attack":
        return AttackEffect(
            amount=effect_dict["value"]
        )
    elif effect_type == "x_attack":
        return XAttackEffect(
            damage_per_hit=effect_dict["value"]
        )
    elif effect_type == "block":
        return BlockEffect(
            amount=effect_dict["value"]
        )
    elif effect_type == "buff":
        return BuffEffect(
            name=effect_dict["name"],
            value=effect_dict["value"],
            duration=effect_dict.get("duration",None)
            #target_self=effect_dict.get("target_self", True)
        )
    elif effect_type == "debuff":
        return DebuffEffect(
            name=effect_dict["name"],
            duration=effect_dict["duration"],
            value=effect_dict.get("value",None)
            #target_user=effect_dict.get("target_user", False)
        )
    elif effect_type == "draw":
        return DrawEffect(
            amount=effect_dict["value"]
        )
    elif effect_type == "energy":
        return EnergyEffect(
            amount=effect_dict["value"]
        )
    elif effect_type == "hp":
        return HPEffect(
            amount=effect_dict["value"]
        )
    elif effect_type == "reaper":
        return ReaperAttackEffect(
            ratio=effect_dict.get("ratio", 1),
            attack=effect_dict.get("attack", 1)
        )
    elif effect_type == "power":
        return PowerEffect(
            name=effect_dict["name"],
            value=effect_dict.get("value", 1)
        )
    elif effect_type =="double_block":
        return DoubleBlockEffect()
    elif effect_type =="double_strength":
        return DoubleStrengthEffect()
    elif effect_type == "exhaust_by_type":
        return ExhaustByTypeEffect(
            block_per_card=effect_dict.get("block_per_card", 0),
            attack_per_card=effect_dict.get("attack_per_card", 0),
            exclude_types=effect_dict.get("exclude_types", []),
            include_types=effect_dict.get("include_types")
        )
    elif effect_type == "status":
        return StatusEffect(
            name=effect_dict["name"],
            temporary=effect_dict.get("temporary", True)
        )
    elif effect_type == "generate_card":
        return GenerateCardEffect(
            card_id=effect_dict["card_id"],
            amount=effect_dict.get("amount", 1),
            destination=effect_dict.get("destination", "hand")
        )
    elif effect_type == "block_attack":
        return BlockBasedAttack()
    else:
        raise ValueError(f"Unknown effect type: {effect_type}")


def parse_intent(intent_dict):
    intent_type = intent_dict["type"]

    if intent_type == "attack":
        return AttackIntent(amount=intent_dict["value"])
    elif intent_type == "block":
        return BlockIntent(
            amount=intent_dict["value"],
            target_selector=intent_dict.get("target_selector", "self")
            )
    elif intent_type == "buff":
        return BuffIntent(
            name=intent_dict["name"],
            target_selector=intent_dict.get("target_selector", "self"),
            value=intent_dict["value"],
            duration=intent_dict.get("duration", None)
        )
    elif intent_type == "debuff":
        return DebuffIntent(
            name=intent_dict["name"],
            duration=intent_dict["duration"],
            value=intent_dict.get("value",None)
        )
    elif intent_type == "heal":
        return HealIntent(
            amount=intent_dict["value"],
            target_selector=intent_dict.get("target_selector", "self")
        )
    elif intent_type == "insert_card":
        return InsertCardIntent(
            card_id=intent_dict["card_id"],
            amount=intent_dict.get("amount", 1),
            destination=intent_dict.get("destination", "discard")
        )
    elif intent_type == "spawn":
        return SpawnIntent(
            threshold=intent_dict["threshold"],
            summon_enemy_id=intent_dict["summon_enemy_id"],
            amount=intent_dict.get("amount",2)
        )

@lru_cache(maxsize=None)
def _parsed_intents(enemy_id, file_path):
    entry = _enemy_defs(file_path)[enemy_id]
    return [[parse_intent(i) for i in turn] for turn in entry.get("intent_sq", [])]

def load_card_pool(filename="card.json"):
    base_dir = os.path.dirname(os.path.dirname(__file__))  # DeckBuilderGym/
    file_path = os.path.join(base_dir, "data", filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_card_by_id(card_pool, card_id):
    for card_def in card_pool:
        if card_def["id"] == card_id:
            effects = [parse_effect(eff) for eff in card_def["effects"]]
            return Card(
                id=card_def["id"],
                name=card_def["name"],
                rarity=card_def.get("rarity",None),
                cost=card_def["cost"],
                target_selector=card_def["target_selector"],
                effects=effects,
                card_type=card_def["card_type"],
                playable=card_def.get("playable", True),
                ethereal=card_def.get("ethereal", False),
                exhaust=card_def.get("exhaust", False),
                innate=card_def.get("innate", False),
                retain=card_def.get("retain", False),
                shuffle_back=card_def.get("shuffle_back", False)
            )
    raise ValueError(f"Card ID {card_id} not found")


def generate_reward_choices(card_pool, num_choices=3):
    non_basic = [c for c in card_pool if c["rarity"] not in {"basic"}]
    selected_defs = random.sample(non_basic, k=num_choices)
    return [load_card_by_id(card_pool, c["id"]) for c in selected_defs]


def build_starting_deck(card_pool):
    starting_ids = ["1"] * 5 + ["2"] * 5 + ["3"] + ["4"] + ["5"]+["6"]+["7"]
    return [load_card_by_id(card_pool, cid) for cid in starting_ids]


def load_enemy_by_id(enemy_id: str, json_path="data/enemy.json") -> Enemy:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, json_path)
    entry = _enemy_defs(file_path).get(enemy_id)
    if entry is None:
        raise ValueError(f"[Loader Error] Enemy with id '{enemy_id}' is not found.")
    return Enemy(
        id=entry["id"], name=entry["name"],
        hp=entry["hp"], max_hp=entry["hp"],
        block=entry.get("block", 0),
        buffs=copy.deepcopy(entry.get("buffs", {})),
        debuffs=copy.deepcopy(entry.get("debuffs", {})),
        intent_sq=_parsed_intents(enemy_id, file_path),  
        tags=entry.get("tags", None),
        die_after_turn=entry.get("die_after_turn", None),
    )


def load_deck_by_id(deck_json_path, deck_id, card_pool):
    with open(deck_json_path, "r") as f:
        deck_data = json.load(f)
    entry = deck_data[deck_id]
    return [load_card_by_id(card_pool, cid) for cid in entry["cards"]], entry["name"]


def load_enemy_group(group_path, group_id):
    with open(group_path, "r") as f:
        group_data = json.load(f)
    enemy_ids = group_data[group_id]["enemy_ids"]
    enemy_objs = [load_enemy_by_id(eid) for eid in enemy_ids]
    return enemy_objs, group_data[group_id]["name"]

