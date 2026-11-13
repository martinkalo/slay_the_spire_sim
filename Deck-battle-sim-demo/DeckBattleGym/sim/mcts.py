import math 
import random 

END = ("end",)

class Node:
    __slots__ = ("key", "children", "visits", "value")

    def __init__(self, key=None):
        self.key = key
        self.children = {}
        self.visits = 0 
        self.value = 0.0 

class MCTS:
    def __init__(self, iterations=300, c=1.0, max_rollout_turns=15, max_rollout_steps=400, seed=0, rollout_policy = None, max_tree_turns=1):
        self.iterations = iterations
        self.c = c 
        self.max_rollout_turns = max_rollout_turns
        self.max_rollout_steps = max_rollout_steps
        self.rng = random.Random(seed)
        self.rollout_policy = rollout_policy
        self.max_tree_turns = max_tree_turns

    @staticmethod
    def action_map(s):
        # taking the key and giving the corresponding action result 
        #  makes a dictionary mapping the card id to the index in the current hand since it can be different after the deck is shuffled 
        m = {}
        for action in s.legal_actions():
            if action[0] == "end":
                m[END] = action 
            else:
                m[("play", s.hand[action[1]].id, action[2])] = action 
        return m

    def ucb(self, parent, child):
        # selection algorithm based on balancing visiting new nodes while also exploring promising nodes 
        if child.visits == 0:
            return float("inf")
        return (child.value / child.visits + self.c * math.sqrt(math.log(parent.visits + 1) / child.visits))

    @staticmethod
    def evaluate(s):
        # give a numeric score for this state in the game to indicate how good the agent is playing 
        win, hp_percent = s.result()
        # highest score if win 
        if win:
            return 0.5 + 0.5 * hp_percent
        total = sum(e.max_hp for e in s.enemies) or 1 
        left = sum(max(0, e.hp) for e in s.enemies)
        progress = 1 - left / total
        lost = 1 - max(0, hp_percent)                    
        net = progress - lost
        # give a higher score the lower the enemy is and the higher you are 
        return 0.45 * (0.5 + 0.5 * net)

    def rollout(self, s): 
        # pick what actions to move forward 
        start_turn, steps = s.turn, 0 
        while (not s.is_terminal() and steps < self.max_rollout_steps and s.turn - start_turn < self.max_rollout_turns):
            # strategy for what to do 
            if self.rollout_policy:
                action = self.rollout_policy(s)
            else:
                plays = [action for action in s.legal_actions() if action[0] == "play"]
                action = s.rng.choice(plays) if plays else END
            s.apply(action)
            steps += 1 
        return self.evaluate(s)

    def iterate(self, root, root_state):
        # don't do this on the actual state 
        s = root_state.clone()
        start_turn = s.turn
        s.rng = random.Random(self.rng.getrandbits(32))
        # make sure the agent does not know the sequence of cards in the actual deck 
        s.rng.shuffle(s.deck)

        node, path = root, [root]
        while not s.is_terminal():
            actions = self.action_map(s)
            # look through unexplored nodes and see their children, keep track of where we have been for selection
            unexplored = [k for k in actions if k not in node.children]
            if unexplored:
                k = self.rng.choice(unexplored)
                node.children[k] = Node(k)
                s.apply(actions[k])
                node = node.children[k]
                path.append(node)
                break
            # pick the child with the best ucb score 
            k = max(actions, key=lambda key: self.ucb(node, node.children[key]))
            s.apply(actions[k])
            node = node.children[k]
            path.append(node)
            if k == END and s.turn - start_turn >= self.max_tree_turns:
                break

        # calculate the benefit of being at this state 
        reward = self.rollout(s)
        for node in path:
            node.visits += 1 
            node.value += reward

    def search(self, battle):
        actions = self.action_map(battle)
        if len(actions) == 1:
            return next(iter(actions.values()))
        root = Node()
        # for the number of iterations loop through and see the best path taken
        for i in range(self.iterations):
            self.iterate(root, battle)
        self.last_root = root 
        best = max(root.children, key=lambda k: root.children[k].visits)
        return actions[best]

def play_battle(battle, iterations=300, seed=0, **kw):
    battle.start()
    mcts = MCTS(iterations=iterations, seed=seed, **kw)
    while not battle.is_terminal():
        battle.apply(mcts.search(battle))
    win, hp_percent = battle.result()
    return {"win": win, "final_hp": battle.player.hp, "turns": battle.turn, "battle log": battle.log}