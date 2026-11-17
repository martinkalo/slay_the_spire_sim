import subprocess
from experiment import main as e_main
from analyze import main as a_main

c_vals = [0.5, 0.75, 1.0, 1.41, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
for c in c_vals:
    e_main(c=c)
