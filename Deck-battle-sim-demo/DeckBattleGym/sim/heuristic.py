from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.enemy import AttackIntent, BlockIntent
from DeckBattleGym.envs.card import *

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

# here, we likely need to take a look at the other possible effects
# we also aren't considering the block intent. say we aren't able to overcome its block and do damage? what now?
def card_score(card, need_block, atk=None):
    # calculate the score of how good the card is 
    if atk is None:
        atk = sum(e.amount for e in card.effects if isinstance(e, AttackEffect))
    blk = sum(e.amount for e in card.effects if isinstance(e, BlockEffect))
    # take into consideration if the card has the strength buff
    str = sum(e.value for e in card.effects if isinstance(e, BuffEffect) and (e.name == "Strength"))
    # double strength, count how many
    db_str = sum(1 for e in card.effects if isinstance(e, DoubleStrengthEffect))
    # double block, count how many
    db_blk = sum(1 for e in card.effects if isinstance(e, DoubleBlockEffect))
    # hp effect
    hp_efct = sum(e.amount for e in card.effects if isinstance(e, HPEffect))

    # energy effect?
    egy = sum(e.amount for e in card.effects if isinstance(e, EnergyEffect))
    # draw effect 
    draw = sum(e.amount for e in card.effects if isinstance(e, DrawEffect))

    # exhaust by type (need to know how many of other type there are in hand for it to be useful)
    # to exhaust, we need to know how many types of cards that we should exhaust 
    # exhst = None

    # generate card (so far, this is only a negative thing?)
    gen = sum(e.amount for e in card.effects if isinstance(e, GenerateCardEffect))
    # perhaps expand to the power effects? but that's hard

    # vulnerable debuff?
    vul = sum(e.duration for e in card.effects if isinstance(e, DebuffEffect) and (e.name == "Vulnerable"))
    # weak
    weak = sum(e.duration for e in card.effects if isinstance(e, DebuffEffect) and (e.name == "Weak"))
    # lose strength
    lose_str = sum(e.value for e in card.effects if isinstance(e, DebuffEffect) and (e.name == "LoseStrength"))
    # no draw
    no_draw = sum(e.duration for e in card.effects if isinstance(e, DebuffEffect) and (e.name == "NoDraw"))
    effects = str * 2 + db_str + (db_blk * 2 if need_block > 0 else .75*blk) + (.5 * atk * vul) + (weak * blk * .75) + (hp_efct/2) + egy*.75 - (gen * .25) + (draw*.25) - (lose_str*.10) - (no_draw*.3)
    # other = sum(1 for e in card.effects if not isinstance(e, (AttackEffect, BlockEffect, HPEffect, DoubleStrengthEffect, DoubleBlockEffect, EnergyEffect, DrawEffect, GenerateCardEffect, BuffEffect, DebuffEffect)))
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
        # if we have an x card we want as much energy as possible 
        if any(isinstance(e, XAttackEffect) for e in card.effects) and any(c.cost == "x" for c in s.hand):
            val += 5.0
        if action[2] is not None:
            val += 1.0 / (1 + s.enemies[action[2]].hp)
        # break ties 
        return val + s.rng.random() * 0.01
    return max(plays, key=score)
"""
# if there is only 1 enemy left...
        if sum(e.hp > 0 for e in s.enemies) == 1:
            return

        # otherwise, if we are about to die...
        elif hp_percent <= .15:
            return

        # then it's whether or not an enemy is going to die? what percent is this?
        # then we need to see if our card combo can kill it 
        e_hps = [e.hp for e in s.enemies]
        e_maxs = [e.max_hp for e in s.enemies]
        hp_paired = zip((e_hps, e_maxs) for hps, maxs in zip(e_hps, e_maxs) if hps > 0)
        min_hp = min(hp_paired, key=lambda x: x[0])
	elif  min_hp[0]/min_hp[1] < .15:
            return

        # then, we have the lowest hp enemy
	else 
	    target = min(e_hp) 
"""