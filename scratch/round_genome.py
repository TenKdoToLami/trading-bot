import json
import os

source = "best_genome_v3.json"
target = "best_genome_v3_rounded.json"

if not os.path.exists(source):
    print(f"Error: {source} not found.")
    exit(1)

with open(source, "r") as f:
    g = json.load(f)

def round_brain(b):
    # Weights to 2 decimal places
    for k in b['w']:
        b['w'][k] = round(float(b['w'][k]), 2)
    # Threshold to 2 decimal places
    b['t'] = round(float(b['t']), 2)
    # Lookbacks to Integers
    for k in b['lookbacks']:
        b['lookbacks'][k] = int(round(float(b['lookbacks'][k])))

round_brain(g['panic'])
round_brain(g['bull'])
# Lock days to Integer
g['lock_days'] = int(round(float(g.get('lock_days', 0))))

with open(target, "w") as f:
    json.dump(g, f, indent=2)

print(f"Successfully rounded {source} -> {target}")
