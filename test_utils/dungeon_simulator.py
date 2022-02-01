from itertools import product

values = sorted(["health", "mana", "power", "defense", "energy"])

printed = False
for f, s in product(values, values):
    if s < f:
        if not printed:
            print()
            printed = True
        continue
    print(f, s, sep="\t")
    printed = False
