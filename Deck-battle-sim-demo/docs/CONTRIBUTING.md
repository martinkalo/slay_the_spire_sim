# Contributing Guide

Thanks for your interest in improving DeckBattle-Sim!

## How to contribute

- **Add a new card:**  
  Edit `data/card.json` and add your card object, following the existing schema;
  You can also add more card effects for the new card. The existing card effects can be found in `envs/card.py`.
  
- **Add a new enemy or enemy group:**  
  Edit `data/enemy.json` or `data/enemy_group.json`;
  You can also add more intents for enemies. The existing intents are in `envs/enemy.py`.

- **Try your changes:** 
  1. Run a demo battle:
  - build a `debug_deck` in `data/deck.json`("deck05");
  - replace the default setup in `envs/demo_battle.py` with debug deck and dummy enmmies in `data/enemy.json`(enemy.id=="0") and `data/enemy_group.json`("group00" for single enemy and "group000" for group of enemies);
  - run `envs/demo_battle.py` and see the generated log file.
  2. Run a sample simulation or play test:
  - replace the default setup as in `README.md`;
  - run `/tests/battle_with_recomend.py`.

