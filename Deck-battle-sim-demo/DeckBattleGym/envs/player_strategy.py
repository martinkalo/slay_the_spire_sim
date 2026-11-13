import random
from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.enemy import AttackIntent, BlockIntent

class MinimaxStrategy:
    def select_card(self, hand, player, enemies, battle):
        # assuming only 1 enemy for now
        
        player_score = 0
        enemy_score = 0
    
        best_combo = []
        best_score_diff = 0
        total_dmg = 0
        total_block = 0
        special_score = 0
        
        # LOOKING AT ENEMIES
        # no need to update index, idx will be ported on the next iteration and enemy updates intent when the turn actually plays out
        current_intent = enemies.intent_sq[self.intent_index % len(self.intent_sq)]
        
        if current_intent == AttackIntent:
            incoming_damage = current_intent.execute(battle)
            # if the enemy has weak, incoming_damage *= 0.75
            start_health = player.hp
            after_damage = max(0, start_health - incoming_damage)
            before_damage_percent = start_health / player.max_hp # proportion of max health before taking damage
            after_damage_percent = after_damage / player.max_hp # proportion of max health after taking damage
            
            player_score -= before_damage_percent - after_damage_percent # negative number for player
            
        if current_intent == BlockIntent:
            enemy_score += current_intent.execute(battle)
            
        # LOOKING AT OUR CARDS
        
        # go through cards in hand, add a playable combination to seen
        seen = {}
        playable = []
        
        for card in hand:
            if player.max_energy - card.cost >= 0:
                playable.append(card)
            
            for card in playable:
                total_dmg += card.damage # this isn't correct with the current json but the actual good one from the API has damage and block as attributes
                # if it applies vulnerable, total_dmg * 1.5
                if card.block is not None:
                    total_block += card.block #same here
                # if it applies weak, total_block * 1.3
                
                #special effects add score
                # special_score += xyz
            
            enemy_current_health = enemies.health / enemies.max_hp
            enemy_after_damage = (enemies.health - total_dmg) / enemies.max_hp
    
            enemy_score -= enemy_current_health - enemy_after_damage
            player_score += total_block
    
            score_difference = player_score - enemy_score
            
            if playable not in seen:
                seen.add(tuple(playable, score_difference))

        best_combo = max(seen[1])
        
        return best_combo
    
    # this returns a combo, but we eventually want to return just 1 card at a time to determine playing order.
    
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