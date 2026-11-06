import random
from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.utils import resolve_target_selector
from DeckBattleGym.envs.buff_n_debuff import apply_regen, tick_poison, tick_standard_duration


class Enemy:
    def __init__(self, id, name, hp, max_hp,
                 block=0,
                 buffs=None, 
                 debuffs=None, 
                 intent_sq=None, 
                 tags=None,
                 die_after_turn=None):
        self.id = id
        self.name = name or id
        self.hp = hp
        self.max_hp = max_hp or hp
        self.block = block or 0
        self.prev_hp = hp
        self.buffs = buffs or {}
        self.debuffs = debuffs or {}
        self.intent_sq = intent_sq
        self.intent_index = 0
        self.tags = tags
        self.die_after_turn=die_after_turn
        self.enemy_group = []
    
    def set_group(self, group):
        self.enemy_group = group
    
    def begin_turn(self, battle):
        if "Barricade" not in self.buffs:
            self.block = 0
        self.tick_buffs_and_debuffs(battle)
    
    def end_turn(self,battle=None):
        if "LoseStrength" in self.debuffs:
            amount = self.debuffs["LoseStrength"].get("value", 0)
            if "Strength" in self.buffs:
                self.buffs["Strength"]["value"] = self.buffs["Strength"]["value"] - amount
                if battle is not None and battle.if_battle_log:
                    battle.log.append(f"[EndTurn] {self.name} loses {amount} Strength.")
            del self.debuffs["LoseStrength"]
        if "GainStrength" in self.buffs:
            amount = self.buffs["GainStrength"].get("value",0)
            self.apply_buff(name="Strength", value=amount)
            if battle is not None and battle.if_battle_log:
                battle.log.append(f"[EndTurn] {self.name} gaines {amount} Strength.")
                
    def tick_buffs_and_debuffs(self, battle=None):
        # Buffs
        for name in list(self.buffs.keys()):
            entry = self.buffs[name]

            if name == "Regen":
                apply_regen(self,entry)
            if not tick_standard_duration(entry):
                del self.buffs[name]

        # Debuffs
        for name in list(self.debuffs.keys()):
            entry = self.debuffs[name]

            if name == "Poison":
                tick_poison(self, entry)
            elif not tick_standard_duration(entry):
                del self.debuffs[name]

    def take_damage(self, amount):
        damage = max(0, amount - self.block)
        self.hp -= damage
        self.block = max(0, self.block - amount)
    
    def gain_block(self, amount):
        self.block += amount
    
    def apply_buff(self, name, value, duration=None):
        if name not in self.buffs:
            self.buffs[name] = {"value": 0}

        self.buffs[name]["value"] += value

        if duration is not None:
            if "duration" in self.buffs[name]:
                self.buffs[name]["duration"] += duration
            else:
                self.buffs[name]["duration"] = duration

    def apply_debuff(self, name, duration, value=None):
        if "Artifact" in self.buffs and self.buffs["Artifact"]["value"] > 0:
            self.buffs["Artifact"]["value"] -= 1
            return
        if name not in self.debuffs:
            self.debuffs[name] = {"duration": 0}

        self.debuffs[name]["duration"] += duration

        if value is not None:
            if "value" in self.debuffs[name]:
                self.debuffs[name]["value"] += value
            else:
                self.debuffs[name]["value"] = value

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    
    def buff_before_action(self, battle):
        if "Split" in self.buffs:
            threshold = 0.5 * self.max_hp
            if self.hp <= threshold:
                split_intent = SpawnIntent(summon_enemy_id="2", amount=2)
                split_intent.execute(self, battle)
            return

    def perform_action(self, battle=None):
        if not self.intent_sq:
            return
        self.buff_before_action(battle)
        if self.hp <= 0:
            return

        intents = self.intent_sq[self.intent_index % len(self.intent_sq)]
        self.intent_index += 1
        
        for intent in intents:
            intent.execute(self, battle)


class EnemyIntent:
    def execute(self, user, battle):
        raise NotImplementedError
    

class AttackIntent(EnemyIntent):
    def __init__(self, amount):
        self.amount = amount

    def execute(self, user, battle):
        damage = EffectCalculator.modified_damage(self.amount, attacker=user, defender=battle.player)
        battle.player.take_damage(damage)

class BlockIntent(EnemyIntent):
    def __init__(self, amount, target_selector="self"):
        self.amount = amount
        self.target_selector = target_selector

    def execute(self, user, battle):
        targets = resolve_target_selector(user, self.target_selector, battle)
        for target in targets:
            block = EffectCalculator.modified_block(self.amount, user=target)
            target.gain_block(block)

class BuffIntent(EnemyIntent):
    def __init__(self, name, value, duration=None, target_selector="self"):
        self.name = name
        self.value = value
        self.duration = duration
        self.target_selector = target_selector

    def execute(self, user, battle):
        targets = resolve_target_selector(user, self.target_selector, battle)
        for target in targets:
            target.apply_buff(self.name, self.value, self.duration)

class DebuffIntent(EnemyIntent):
    def __init__(self, name, duration, value=None):
        self.name = name
        self.duration = duration
        self.value = value
    
    def execute(self, user, battle):
        battle.player.apply_debuff(self.name, self.duration, self.value)

class HealIntent(EnemyIntent):
    def __init__(self, amount, target_selector="self"):
        self.amount = amount
        self.target_selector = target_selector

    def execute(self, user, battle):
        targets = resolve_target_selector(user, self.target_selector, battle)
        for target in targets:
            target.heal(self.amount)

class InsertCardIntent(EnemyIntent):
    def __init__(self, card_id, amount=1, destination="discard"):
        self.card_id = card_id
        self.amount = amount
        self.destination = destination

    def execute(self, user, battle):
        from DeckBattleGym.envs.card import Card

        for _ in range(self.amount):
            card = battle.make_card(self.card_id)
            if self.destination == "discard":
                battle.discard_pile.append(card)
            elif self.destination == "draw":
                index = battle.rng.randint(0, len(battle.deck))
                battle.deck.insert(index, card)
            elif self.destination == "hand":
                if len(battle.hand) < battle.hand_limit:
                    battle.hand.append(card)
                else:
                    battle.discard_pile.append(card)
        if battle.if_battle_log:
            battle.log.append(f"[Intent] {user.name} inserts {self.amount}x '{card.name}' into player's {self.destination} pile.")

class SpawnIntent(EnemyIntent):
    def __init__(self, summon_enemy_id, amount=2, threshold=None):
        self.summon_enemy_id = summon_enemy_id
        self.amount = amount
        self.threshold = threshold

    def execute(self, user, battle):
        from DeckBattleGym.envs.loader import load_enemy_by_id 

        for _ in range(self.amount):
            mid_slime = load_enemy_by_id(self.summon_enemy_id)
            mid_slime.hp = user.hp
            battle.enemies.append(mid_slime)
        user.hp = 0
        if battle.if_battle_log:
            battle.log.append(f"[Intent] {user.name} splits into {self.amount} {self.summon_enemy_id}s!")