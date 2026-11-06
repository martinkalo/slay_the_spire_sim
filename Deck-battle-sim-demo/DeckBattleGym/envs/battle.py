import os
import random
import copy


class VictoryCondition:
    def is_victory(self, player, enemies, turn):
        return all(e.hp <= 0 for e in enemies)

    def is_defeat(self, player, enemies, turn):
        return player.hp <= 0
    

class Battle:
    def __init__(self, player, enemies, deck,
                draw_per_turn:int=5, hand_limit:int=10,
                card_pool=None,
                victory_condition=None, 
                if_battle_log=False, seed=0, record_actions=True):
        self.player = player
        self.enemies = enemies
        self.deck = deck
        self.original_deck = deck[:]
        self.draw_per_turn = draw_per_turn
        self.hand_limit = hand_limit
        self.card_pool = card_pool or []
        self.card_id_map = {c["id"]: c for c in self.card_pool}
        self.victory_condition = victory_condition or VictoryCondition()
        self.if_battle_log= if_battle_log
        self.hand = []
        self.picked_card = []
        self.discard_pile = []
        self.exhaust_pile = []
        self.used_powers = []
        self.turn = 0
        self.log = []
        self.simulation_log={
            "turns":[]
        }
        self.rng = random.Random(seed)
        self.running_log = None
        self._card_templates = {}
        self.record_actions = record_actions
    
    def _get_battle_count(self):
        counter = 1
        while os.path.exists(f"battle_log_{counter}.txt"):
            counter += 1
        return counter

    def log_state(self):
        enemy_states = [f"{enemy.name}(HP: {enemy.hp}, Block:{enemy.block}, Buffs: {enemy.buffs}, Debuffs: {enemy.debuffs})" for enemy in self.enemies]
        self.log.append(f"[Turn {self.turn} End] Player HP: {self.player.hp}, Block: {self.player.block}, Buffs: {self.player.buffs}, Debuffs: {self.player.debuffs}, Powers: {self.player.powers}")
        for e_state in enemy_states:
            self.log.append(f"Enemy: {e_state}")
    
    def battle_start(self):
        self.rng.shuffle(self.deck)

    def draw_cards(self, num, hand_limit=None):
        drawn = 0
        drawn_cards = []
        hand_limit = hand_limit or self.hand_limit
        if "NoDraw" in self.player.debuffs:
            if self.if_battle_log:
                self.log.append("Prevented from drawing cards this turn.")
            return
        else:
            for _ in range(num):
                if len(self.hand) >= hand_limit:
                    if self.if_battle_log:
                        self.log.append("[Draw] Hand limit reached. Cannot draw more cards.")
                    break

                if not self.deck and self.discard_pile:
                    self.deck = self.discard_pile[:]
                    self.rng.shuffle(self.deck)
                    self.discard_pile.clear()
            
                if self.deck:
                    card = self.deck.pop()
                    self.hand.append(card)
                    drawn_cards.append(card.name)
                    drawn += 1
                    self.player.after_draw_card(card, battle=self)
                else:
                    break

        if self.if_battle_log:
            self.log.append(f"[Turn {self.turn}] Drew cards: {', '.join(drawn_cards)}")
            card_names = [card.name for card in self.hand]
            self.log.append(f"[Turn {self.turn}] Hand cards: {', '.join(card_names)}")
        return drawn

    def make_card(self, card_id):
        tmpl = self._card_templates.get(card_id)
        if tmpl is None:
            from DeckBattleGym.envs.loader import load_card_by_id
            tmpl = self._card_templates[card_id] = load_card_by_id(self.card_pool, card_id)
        return copy.copy(tmpl) 
    
    def play_card(self, card, user, targets=None):
        if not isinstance(targets, list):
            targets = [targets]
        if self.if_battle_log:
            if targets:
                target_names = ", ".join(t.name for t in targets)
                target_info = f"targeting {target_names}"
            else:
                target_info = "with no target"
            self.log.append(f"[Play] {user.name} plays {card.name} {target_info}.")
        elif self.running_log is not None:
            target_ids = [getattr(t, "id", "unknown") for t in targets]   
            self.running_log["actions"].append({
                "card":card.id,
                "targets":target_ids
            })
        #print(f"DEBUG: battle play card target {[t.name for t in targets]}")
        self.picked_card.append(card)
        if card in self.hand:
            self.hand.remove(card)
        card.apply(user, targets, battle=self)
        if card.cost =="x":
            actual_cost=user.energy
        else:
            actual_cost=card.cost
        user.energy -= actual_cost

        if getattr(card, 'exhaust', False):
            self.exhaust_pile.append(card)
            user.trigger_on_exhaust(self)
        elif getattr(card, 'shuffle_back', False):
            index = self.rng.randint(0, len(self.deck))
            self.deck.insert(index, card)
        elif card.card_type == "power":
            self.used_powers.append(card)
        else:
            self.discard_pile.append(card)

        #if card in self.hand:
        #    self.hand.remove(card)

    def start(self):
        self.battle_start()
        self._begin_player_turn() 

    def _begin_player_turn(self):
        self.turn += 1
        if self.if_battle_log:
            self.log.append(f"\n--- Turn {self.turn} ---")
        self.player.begin_turn(self)
        self.draw_cards(self.draw_per_turn)
        if not self.if_battle_log and self.record_actions:
            self.running_log = {"turn": self.turn, "hand": [c.id for c in self.hand], "actions": []}

    def legal_actions(self):
        p = self.player
        acts, seen = [("end",)], set()
        alive = [j for j, e in enumerate(self.enemies) if e.hp > 0]
        for i, c in enumerate(self.hand):
            if not getattr(c, "playable", True):
                continue
            if c.card_type == "attack" and "Entangled" in p.buffs:
                continue
            if c.cost != "x" and c.cost > p.energy:
                continue
            opts = alive if c.target_selector == "single_enemy" else [None]
            for t in opts:
                key = (c.id, t)
                if key not in seen:
                    seen.add(key)
                    acts.append(("play", i, t))
        return acts

    def _resolve_targets(self, card, t):
        alive = [e for e in self.enemies if e.hp > 0]
        sel = card.target_selector
        if sel == "self":
            return [self.player]
        if sel == "all_enemies":
            return alive
        if sel == "random_enemy":
            return [self.rng.choice(alive)] if alive else []
        if sel == "lowest_hp":
            return [min(alive, key=lambda e: e.hp)] if alive else []
        return [self.enemies[t]]                     

    def apply(self, action):
        if action[0] == "play":
            _, i, t = action
            card = self.hand[i]
            self.play_card(card, self.player, self._resolve_targets(card, t))
        else:
            self._end_turn()
        return self.is_terminal()

    def _end_turn(self):
        self.player.end_turn(self)
        if self.running_log is not None:
            self.running_log["hp_left"] = self.player.hp
            self.simulation_log["turns"].append(self.running_log)
            self.running_log = None
        self.cleanup()
        if self.is_terminal():            
            return
        self.enemy_turn()
        if self.is_terminal():
            return
        if self.if_battle_log:
            self.log_state()
        self._begin_player_turn()     

    def is_terminal(self):
        vc = self.victory_condition
        return (vc.is_victory(self.player, self.enemies, self.turn) or vc.is_defeat(self.player, self.enemies, self.turn))

    def result(self):
        """(win, hp_fraction) for the reward function."""
        win = self.victory_condition.is_victory(self.player, self.enemies, self.turn)
        return win, max(0, self.player.hp) / self.player.max_hp

    def clone(self):
        memo = {id(self.card_pool): self.card_pool,
                id(self.card_id_map): self.card_id_map,
                id(self.victory_condition): self.victory_condition,
                id(self.log): [],
                id(self.simulation_log): {"turns": []}}
        for c in (self.hand + self.deck + self.discard_pile + self.exhaust_pile
                + self.used_powers + self.picked_card + self.original_deck):
            memo[id(c)] = c
        memo[id(self._card_templates)] = self._card_templates    
        for e in self.enemies:
            memo[id(e.intent_sq)] = e.intent_sq        
        b = copy.deepcopy(self, memo)
        b.record_actions = False
        b.running_log = None
        return b

    def run(self):
        self.start()
        p = self.player
        while not self.is_terminal():
            acts = self.legal_actions()
            playable = [self.hand[a[1]] for a in acts if a[0] == "play"]
            playable = list(dict.fromkeys(playable))  
            card = p.strategy.select_card(playable, p, self.enemies, self) if playable else None
            targets = p.strategy.select_target(card, p, self.enemies, self) if card else []
            if card is None or not targets:
                self.apply(("end",))
            else:
                self.play_card(card, p, targets)
        self.check_victory()          
        self.simulation_log["final_hp"] = p.hp
        self.simulation_log["turns_taken"] = self.turn
        self.cleanup_after_battle()
        self.simulation_log.setdefault("win", False)
        if self.if_battle_log:
            for entry in self.log:
                print(entry)
            self.save_log_to_file()
        
    def enemy_turn(self):
        if self.if_battle_log:
            self.log.append(f"[Turn {self.turn}] Enemies' turn begins.")
        for enemy in list(self.enemies):
            if self.player.hp <= 0:
                break
            if enemy.hp > 0:
                if enemy.die_after_turn is not None and self.turn >= enemy.die_after_turn:
                    enemy.hp = 0
                    if self.if_battle_log:
                        self.log.append(f"[AutoDeath] {enemy.name} dies automatically after turn {self.turn}.")
                    continue
                enemy.begin_turn(self)
                if enemy.hp <= 0:
                    continue
                enemy.perform_action(self)
                enemy.end_turn(self)
        
    def cleanup(self):
        cards_to_discard = []
        cards_to_exhaust = []

        for card in self.hand:
            if card.name == "Burn":
                self.player.take_damage(2)
                cards_to_discard.append(card)
            elif getattr(card, 'ethereal', False):
                cards_to_exhaust.append(card)
                self.player.trigger_on_exhaust(self)
            elif not getattr(card, 'retain', False):
                cards_to_discard.append(card)

        for card in cards_to_discard:
            self.hand.remove(card)
            self.discard_pile.append(card)

        for card in cards_to_exhaust:
            self.hand.remove(card)
            self.exhaust_pile.append(card)
    

    def cleanup_after_battle(self):
        self.deck = self.original_deck[:]
        self.hand = []
        self.discard_pile.clear()
        self.exhaust_pile.clear()
        self.used_powers.clear()

    def check_victory(self):
        if self.victory_condition.is_victory(self.player, self.enemies, self.turn):
            if self.if_battle_log:
                self.log.append("[Battle] You win!")
            else:
                self.simulation_log["win"]=True
            return True
        if self.victory_condition.is_defeat(self.player, self.enemies, self.turn):
            if self.if_battle_log:
                self.log.append("[Battle] You lose!")
            else:
                self.simulation_log["win"]=False
            return True
        return False

    def save_log_to_file(self):
        filename = f"battle_log_{self._get_battle_count()}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for entry in self.log:
                f.write(entry + "\n")