#from enemy import SpawnIntent

# buff类
def apply_regen(entity, entry):
    entity.heal(entry["value"])

def apply_strength_gain(entity, entry):
    gain = entry.get("value", 0)
    entity.apply_buff("Strength", gain)


# debuff类
def tick_poison(entity, entry):
    damage = entry["value"]
    entity.hp -= damage
    entry["value"] -= 1
    return entry["value"] > 0

def tick_standard_duration(entry):
    if "duration" in entry:
        entry["duration"] -= 1
        return entry["duration"] > 0
    return True