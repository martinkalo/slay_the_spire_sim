from DeckBattleGym.envs.utils import get_buff_value, get_debuff_value, has_buff, has_debuff


class EffectCalculator:
    
    @staticmethod
    def modified_damage(base_damage, attacker, defender):
        damage = base_damage

        damage += get_buff_value(attacker, "Strength")

        if has_debuff(attacker, "Weak"):
            damage = int(damage * 0.75)

        if has_buff(defender, "Intangible"):
            damage = min(damage, 1)

        if has_debuff(defender, "Vulnerable"):
            damage = int(damage * 1.5)

        return max(0, damage)

    @staticmethod
    def modified_block(base_block, user):
        block = base_block

        if has_debuff(user, "Frail"):
            block = int(block * 0.75)

        block += get_buff_value(user, "Dexterity")

        return max(0, block)
