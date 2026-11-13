import random
from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.enemy import AttackIntent, BlockIntent
from DeckBattleGym.envs.card import AttackEffect, BlockEffect
from DeckBattleGym.sim.mcts import MCTS
from DeckBattleGym.sim.mcts import MCTS, END

class MCTSStrategy:
    def __init__(self, iterations=200, seed=0, **kw):
        self.mcts = MCTS(iterations=iterations, seed=seed, **kw)
        self._target = None

    def select_card(self, hand, player, enemies, battle):
        a = self.mcts.search(battle)               
        if a[0] == "end":
            return None
        self._target = a[2]
        return battle.hand[a[1]]

    def select_target(self, card, player, enemies, battle):
        return battle._resolve_targets(card, self._target)    

class SimpleStrategy:
    def select_card(self, hand, player, enemies, battle):
        for card in hand:
            if card.cost == "x":
                return card
            elif isinstance(card.cost, (int, float)) and card.cost <= player.energy:
                return card
        return None

    def select_target(self, card, player, enemies, battle):
        sel = card.target_selector
        alive = [e for e in enemies if e.hp > 0]

        if sel == "all_enemies":
            return alive
        elif sel == "random_enemy":
            return [random.choice(alive)] if alive else []
        elif sel == "lowest_hp":
            return [min(alive, key=lambda e: e.hp)] if alive else []
        elif sel == "single_enemy":
            target = next((e for e in alive), None)
            return [target] if target else []
        elif sel == "self":
            return [player]
        else:
            raise ValueError(f"Unknown target_selector: {sel}")
        
class RandomStrategy:
    def select_card(self, hand, player, enemies, battle):
        can_play = []
        for card in hand:
            if card.cost == "x":
                can_play.append(card)
            elif isinstance(card.cost, (int, float)) and card.cost <= player.energy:
                can_play.append(card)
        return battle.rng.choice(can_play) if can_play else None

    def select_target(self, card, player, enemies, battle):
        sel = card.target_selector
        alive = [e for e in enemies if e.hp > 0]

        if sel == "all_enemies":
            return alive
        elif sel == "random_enemy":
            return [battle.rng.choice(alive)] if alive else []
        elif sel == "lowest_hp":
            return [min(alive, key=lambda e: e.hp)] if alive else []
        elif sel == "single_enemy":
            return [battle.rng.choice(alive)] if alive else []
        elif sel == "self":
            return [player]
        else:
            return []
        

class ManualStrategy:
    def select_card(self, hand, player, enemies, battle):
        return None 

    def select_target(self, card, player, enemies, battle):
        return []