from copy import deepcopy
from DeckBattleGym.envs.effectcalculator import EffectCalculator
from DeckBattleGym.envs.utils import get_buff_value, get_debuff_value, has_buff, has_debuff


class Card:
    def __init__(self, id, name, cost, effects, card_type,
                 rarity=None,
                 playable=True,
                 target_selector=None, 
                 ethereal=False, 
                 exhaust=False, 
                 innate=False, 
                 retain=False, 
                 shuffle_back=False):
        self.id = id
        self.name = name
        self.cost = cost
        self.effects = effects
        self.card_type = card_type
        self.rarity = rarity
        self.playable = playable
        self.target_selector = target_selector
        self.ethereal = ethereal
        self.exhaust = exhaust
        self.innate = innate
        self.retain = retain
        self.shuffle_back = shuffle_back

    def apply(self, user, targets, battle=None):
        if not targets:
            raise ValueError(f"[CardError] Card '{self.name}' expected at least one target but got: {targets}.")
        
        for effect in self.effects:
            if isinstance(effect, (GenerateCardEffect,DrawEffect)):
                effect.apply(user, targets[0], battle=battle)
            else:
                for target in targets:
                    effect.apply(user, target, battle=battle)


class CardEffect:
    def apply(self, user, target, battle=None):
        raise NotImplementedError


class AttackEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        damage = EffectCalculator.modified_damage(self.amount, attacker=user, defender=target)
        target.take_damage(damage)

class BlockEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        block = EffectCalculator.modified_block(self.amount, user)
        user.gain_block(block)


class BlockBasedAttack(CardEffect):
    def __init__(self):
        super().__init__()

    def apply(self, user, target, battle=None):
        damage = EffectCalculator.modified_damage(user.block, attacker=user, defender=target)
        target.take_damage(damage)


class BuffEffect(CardEffect):
    def __init__(self, name, value, duration=None):
        self.name = name
        self.value = value
        self.duration = duration

    def apply(self, user, target, battle=None):
        target.apply_buff(self.name, self.value, self.duration)


class DebuffEffect(CardEffect):
    def __init__(self, name, duration, value=None):
        self.name = name
        self.duration = duration
        self.value = value

    def apply(self, user, target, battle=None):
        target.apply_debuff(self.name, self.duration, self.value)


class DoubleBlockEffect(CardEffect):
    def apply(self, user, target, battle=None):
        user.block *= 2


class DoubleStrengthEffect(CardEffect):
    def apply(self, user, target, battle=None):
        current = get_buff_value(user, "Strength")
        if current > 0:
            user.buffs["Strength"]["value"] += current
        else:
            return


class DrawEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target=None, battle=None):
        if battle is None:
            raise ValueError("DrawEffect requires access to the battle context.")
        battle.draw_cards(self.amount)


class EnergyEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        user.energy += self.amount


class ExhaustByTypeEffect(CardEffect):
    def __init__(self, block_per_card=0, 
                 attack_per_card=0,
                 exclude_types=None,
                 include_types=None):
        self.block_per_card = block_per_card
        self.attack_per_card = attack_per_card
        self.exclude_types = exclude_types or []  
        self.include_types = include_types 
    
    def apply(self, user, target, battle=None):
        count = 0

        if self.include_types:
            to_exhaust = [card for card in battle.hand if card.card_type not in self.include_types]
        else:
            to_exhaust = [card for card in battle.hand if card.card_type not in self.exclude_types]

        for card in to_exhaust:
            battle.hand.remove(card)
            battle.exhaust_pile.append(card)
            user.trigger_on_exhaust(battle)
            count += 1

        if self.block_per_card > 0:
            user.block += count * self.block_per_card 

        if self.attack_per_card > 0:
                damage=EffectCalculator.modified_damage(count*self.attack_per_card, attacker=user, defender=target)
                target.take_damage(damage)
                


class GenerateCardEffect(CardEffect):
    def __init__(self, card_id, amount=1, destination="hand"):
        self.card_id = card_id
        self.amount = amount
        self.destination = destination  # "hand", "draw", "discard"

    def apply(self, user, target, battle=None):
        for _ in range(self.amount):
            card = battle.make_card(self.card_id)
            if self.destination == "hand":
                if len(battle.hand) < battle.hand_limit:
                    battle.hand.append(card)
                else:
                    battle.discard_pile.append(card) 
            elif self.destination == "draw":
                index = battle.rng.randint(0, len(battle.deck))
                battle.deck.insert(index, card)
            elif self.destination == "discard":
                battle.discard_pile.append(card)

            if battle.if_battle_log:
                battle.log.append(f"[Effect] Created {card.name} in {self.destination}.")


class HPEffect(CardEffect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, user, target, battle=None):
        hp_changed = user.hp + self.amount
        user.hp=min(hp_changed, user.max_hp)


class PowerEffect(CardEffect):
    def __init__(self, name, value=1):
        self.name = name
        self.value = value

    def apply(self, user, target, battle=None):
        if self.name in user.powers:
            user.powers[self.name] += self.value
        else:
            user.powers[self.name] = self.value


class ReaperAttackEffect(CardEffect):
    def __init__(self, ratio=1, attack=1):
        self.ratio =ratio
        self.attack = attack
    
    def apply(self, user, target, battle=None):
        target.prev_hp = target.hp
        damage=EffectCalculator.modified_damage(self.attack, attacker=user, defender=target)
        target.take_damage(damage)
        hp_reaped = max(0, target.prev_hp - max(target.hp,0))
        hp_new= user.hp + hp_reaped * self.ratio
        user.hp=min(hp_new, user.max_hp)
        if battle.if_battle_log:
            battle.log.append(f"[Effect] Reaped {hp_reaped}")


class StatusEffect(CardEffect):
    def __init__(self, name, temporary=True):
        self.name = name
        self.temporary = temporary

    def apply(self, user, target, battle=None):
        if "status_flags" not in user.__dict__:
            user.status_flags = {}
        user.status_flags[self.name] = {
            "value": True,
            "temporary": self.temporary
        }


class XAttackEffect(CardEffect):
    def __init__(self,damage_per_hit):
        self.damage_per_hit = damage_per_hit

    def apply(self, user, target, battle=None):
        x_value=user.energy
        for _ in range(x_value):
            damage = EffectCalculator.modified_damage(self.damage_per_hit, attacker=user, defender=target)
            target.take_damage(damage)


