from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.enemy import AttackIntent, BlockIntent
from DeckBattleGym.envs.card import AttackEffect, BlockEffect

END = ("end",)
KILL_BONUS = 8.0

def incoming_dmg(battle):
    # total the damage coming to the player including buffs or nerfs 
    total = 0 
    for e in battle.enemies:
        if e.hp > 0 and e.intent_sq:
            for intent in e.intent_sq[e.intent_index % len(e.intent_sq)]:
                if isinstance(intent, AttackIntent):
                    total += EffectCalculator.modified_damage(intent.amount, e, battle.player)
    return total

def attack_value(s, card, idx):
    atk = sum(e.amount for e in card.effects if isinstance(e, AttackEffect))
    if not atk or idx is None:
        return atk 
    t = s.enemies[idx]
    dmg = EffectCalculator.modified_damage(atk, s.player, t)
    need = t.hp + t.block
    return min(dmg, need) + (KILL_BONUS if dmg >= need else 0.0)

def card_score(card, need_block, atk=None):
    # calculate the score of how good the card is 
    if atk is None:
        atk = sum(e.amount for e in card.effects if isinstance(e, AttackEffect))
    blk = sum(e.amount for e in card.effects if isinstance(e, BlockEffect))
    other = sum(1 for e in card.effects if not isinstance(e, (AttackEffect, BlockEffect)))
    score = atk + (blk if need_block > 0 else 0.2 * blk) + 6 * other
    cost = card.cost if isinstance(card.cost, (int, float)) else 1
    return score / max(cost, 1)

def heuristic_action(s): 
    plays = [action for action in s.legal_actions() if action[0] =="play"]
    if not plays:
        return END
    # is the enemy threatening to kill us 
    need = incoming_dmg(s) - s.player.block
    def score(action):
        card = s.hand[action[1]]
        val = card_score(card, need, atk=attack_value(s, card, action[2]))
        if action[2] is not None:
            val += 1.0 / (1 + s.enemies[action[2]].hp)
        # break ties 
        return val + s.rng.random() * 0.01
    return max(plays, key=score)