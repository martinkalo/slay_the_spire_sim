# Project Structure

This is a quick overview of the main files and folders in this repository.

#### **What’s in each folder:**

- **data/**: Default game content (cards, enemies, enemy groups), all editable JSON.
- **envs/**: Implementation of the Gym environment, battle loop, card/enemy/player logic.
    - `battle.py`: class Battle, class VictoryCondition
    - `buff_n_debuff.py`: buff and debuff implementation(not all)
    - `card.py`: class Card, class CardEffect and its children
    - `demo_battle.py`: a simple battle demonstrator with logging, designed for debugging
    - `effectcalculator.py`: modify damage and block with corresponding buffs and debuffs
    - `enemy.py`: class Enemy, class EnemyIntent and its children
    - `loader.py`: load objects for battle
    - `player_strategy.py`: class SimpleStrategy(for debugging), class RandomStrategy(for simulation)
    - `player.py`: class Player
    - `utils.py`
- **model/**: Recommendation system and any analysis modules.
- **sim/**: Scripts for running mass simulations and generating datasets.
- **tests/**: Command-line interface for playing or managing the environment.