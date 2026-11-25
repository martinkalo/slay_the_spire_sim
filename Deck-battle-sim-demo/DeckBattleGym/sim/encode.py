# this file is for markov decision process 

import numpy as np
from DeckBattleGym.envs.card import (AttackEffect, XAttackEffect, BlockEffect, DrawEffect, EnergyEffect, BuffEffect, DebuffEffect, PowerEffect, ReaperAttackEffect)
from DeckBattleGym.envs.enemy import AttackIntent
from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.utils import get_buff_value, has_debuff

class ValueFn:
    def __init__(self, path):
        d = np.load(path)
        self.mean, self.scale, n = d["mean"], d["scale"], int(d["n"])
        self.layers = [(d[f"W{i}"], d[f"b{i}"]) for i in range(n)]

    def __call__(self, s):
        x = (encode(s) - self.mean) / self.scale
        for W, b in self.layers[:-1]:
            x = np.maximum(0.0, x @ W + b)
        W, b = self.layers[-1]
        return float(np.clip(x @ W + b, 0.0, 1.0)[0])

K = 5 
N_CARD = 12 
cache = {}

def card_feats(c):
    # get the values from the card and add it to the cache 
    f = cache.get(c.id)
    if f is None:
        atk = xatk = blk = draw = energy = debuff = strength = power = 0.0
        for e in c.effects:
            if isinstance(e, AttackEffect): atk += e.amount
            elif isinstance(e, ReaperAttackEffect): atk += e.attack
            elif isinstance(e, XAttackEffect): xatk += e.damage_per_hit
            elif isinstance(e, BlockEffect): blk += e.amount
            elif isinstance(e, DrawEffect): draw += e.amount
            elif isinstance(e, EnergyEffect): energy += e.amount
            elif isinstance(e, DebuffEffect): debuff += 1
            elif isinstance(e, BuffEffect) and e.name == "Strength": strength += e.value
            elif isinstance(e, PowerEffect): power += 1
        cost = 3.0 if c.cost == "x" else float(c.cost)
        f = np.array([1.0, cost, atk, xatk, blk, draw, energy, debuff, strength, power, float(c.exhaust), float(c.card_type in ("status", "curse"))], np.float32)
        cache[c.id] = f
    return f 

def pile(cards):
    return np.sum([card_feats(c) for c in cards], axis=0) if cards else np.zeros(N_CARD, np.float32)

def threat(e, p):
    # how much the enemy will do on this turn
    if not e.intent_sq:
        return 0.0 
    turn = e.intent_sq[e.intent_index % len(e.intent_sq)] 
    return float(sum(EffectCalculator.modified_damage(i.amount, e, p) for i in turn if isinstance(i, AttackIntent)))

def encode(s):
    # encode the entire game state into vectors 
    p = s.player 
    playable = [c for c in s.hand if c.cost == "x" or c.cost <= p.energy]
    cards = np.concatenate([pile(s.hand), pile(playable), pile(s.deck), pile(s.discard_pile)])
    curr_state = np.array([p.hp, p.hp / max(p.max_hp, 1), p.block, p.energy, p.max_energy, get_buff_value(p, "Strength"), get_buff_value(p, "Dexterity"), float(has_debuff(p, "Weak")),
                           float(has_debuff(p, "Vulnerable")), float(has_debuff(p, "Frail")), float(sum(p.powers.values())), s.turn, len(s.hand), len(s.deck), len(s.discard_pile)],
                           np.float32)
    alive = sorted([e for e in s.enemies if e.hp > 0], key=lambda e: e.hp)
    threats = [threat(e, p) for e in alive]
    slots = []
    for e, t in list(zip(alive, threats))[:K]:
        slots += [1.0, e.hp, e.hp / max(e.max_hp, 1), e.block, t, get_buff_value(e, "Strength"), float(has_debuff(e, "Vulnerable")), float(has_debuff(e, "Weak"))]
    slots += [0.0] * 8 * (K - min(K, len(alive)))
    extra = [sum(e.hp for e in alive), sum(threats), len(alive), max(0.0, sum(threats) - p.block)]

    return np.concatenate([cards, curr_state, np.array(slots, np.float32), np.array(extra, np.float32)]).astype(np.float32)