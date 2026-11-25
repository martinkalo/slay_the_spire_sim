import subprocess
import csv, os

ALL_OUT = "all_c_experiments.csv"
OUT_CSV = "experiment_results.csv"
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

c_vals = [1.2, 1.5, 1.7, 1.75]
for c in c_vals:
    subprocess.run(["python", r"Deck-battle-sim-demo\DeckBattleGym\sim\experiment.py", f"{c}"])
    with open(os.path.join(BASE, ALL_OUT), "a", newline="") as outfile, \
        open(os.path.join(BASE, OUT_CSV), "r", newline="") as infile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            writer.writerow(row)
    subprocess.run(["python", r"Deck-battle-sim-demo\DeckBattleGym\sim\analyze.py", f"{c}"])
