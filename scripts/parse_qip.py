import re, sys
t = open(sys.argv[1], encoding='latin-1', errors='replace').read()
# collapse the wrapped lines inside each field
blocks = re.split(r'Indicator #', t)
print("TOTAL BLOCKS:", len(blocks)-1)
for i, b in enumerate(blocks[1:], 1):
    b = b[:2600]
    lines = [l.strip() for l in b.split('\n') if l.strip()]
    print("\n========== INDICATOR BLOCK", i, "==========")
    print(' | '.join(lines[:80]))
