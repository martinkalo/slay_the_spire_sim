def get_buff_value(entity, name):
    return entity.buffs.get(name, {}).get("value", 0)

def get_debuff_value(entity, name):
    return entity.debuffs.get(name, {}).get("value", 0)

def has_buff(entity, name):
    return name in entity.buffs

def has_debuff(entity, name):
    return name in entity.debuffs

def resolve_target_selector(user, selector, battle):
    if selector == "self":
        return [user]
    elif selector == "all_enemies":
        return [e for e in battle.enemies if e.hp > 0]
    elif selector == "boss":
        return [e for e in battle.enemies if "Boss" in getattr(e, "tags", [])]
    else:
        return [e for e in battle.enemies if e.name == selector or e.id == selector]