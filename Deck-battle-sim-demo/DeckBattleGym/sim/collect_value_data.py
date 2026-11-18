import sys, os, random
import numpy as np
from multiprocessing import Pool, cpu_count
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from DeckBattleGym.envs.player_strategy import RandomStrategy
from DeckBattleGym.sim.experiment import make, BASE
from DeckBattleGym.sim.mcts import MCTS
from DeckBattleGym.sim.heuristic import heuristic_action
from DeckBattleGym.sim.encode import encode

# this is the training data based off of simulating hundreds of MCTS battles 

DECKS = ["deck01", "deck02", "deck03", "deck04", "deck05", "deck06", "deck07"]
GROUPS = ["group01", "group02", "group03", "group04", "group06", "group07"]   
HPS = [80, 50, 35, 25]
SEEDS = range(40)
ITERS = 200
OUT = os.path.join(BASE, "value_data.npz")


def work(task):
    # use the data from mcts
    deck, group, hp, seed = task
    b = make(deck, group, hp, seed, RandomStrategy())
    b.start()
    mcts = MCTS(iterations=ITERS, seed=seed, rollout_policy=heuristic_action)
    xs = []
    while not b.is_terminal():
        xs.append(encode(b))
        b.apply(mcts.search(b))
    z = mcts.evaluate(b)                    
    return np.stack(xs), z, deck, group


if __name__ == "__main__":
    # use the data and switch up the hp to see fights in bad situations 
    tasks = [(d, g, hp, s) for d in DECKS for g in GROUPS for hp in HPS for s in SEEDS]
    random.Random(0).shuffle(tasks)
    X, y, decks, groups = [], [], [], []
    with Pool(max(1, cpu_count() - 1)) as pool:
        for i, (xs, z, d, g) in enumerate(pool.imap_unordered(work, tasks), 1):
            X.append(xs); y += [z] * len(xs); decks += [d] * len(xs); groups += [g] * len(xs)
            if i % 100 == 0:
                print(f"{i}/{len(tasks)} battles, {sum(len(a) for a in X)} samples", flush=True)
    np.savez(OUT, X=np.concatenate(X), y=np.array(y, np.float32), deck=np.array(decks), group=np.array(groups))
    print("saved", OUT)