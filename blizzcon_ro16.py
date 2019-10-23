from aligulac_api import AligulacAPI, Match
import os
from odds_utils import nway_implied_probs, bets_exp_val, dec_to_amer, fmt_lines_exp_vals
import numpy as np
import csv
from collections import defaultdict


api_key = os.getenv('ALIGULAC_API_KEY', 'API KEY COULD ALSO GO HERE')
alig_api = AligulacAPI(api_key)

inf_name = 'blizzcon_ro16_odds.csv'

exp_val_src = 'nit'

sources = set()
ro16 = defaultdict(dict)

with open(inf_name, 'r') as inf:
    reader = csv.DictReader(inf)
    for row in reader:
        sources.add(row['source'])

        row['a_odds'] = float(row['a_odds'])
        row['b_odds'] = float(row['b_odds'])

        if row['format'] == 'dec':
            row['a_odds'] = dec_to_amer(row['a_odds'])
            row['b_odds'] = dec_to_amer(row['b_odds'])
        ro16[(row['player_a'], row['player_b'])]['%s_odds' % row['source']] = (row['a_odds'], row['b_odds'])

# Round of 16
for ro16_match in ro16:
    match = Match(alig_api, ro16_match[0], ro16_match[1], bo=5)
    match.predict()
    alig_probs = (match.proba, match.probb)
    ro16[ro16_match]['alig_probs'] = alig_probs

    for source in sources:
        imp, vig = nway_implied_probs(ro16[ro16_match]['%s_odds' % source])
        ro16[ro16_match]['%s_probs' % source] = tuple(imp)
        ro16[ro16_match]['%s_vig' % source] = vig
        ro16[ro16_match]['alig_%s_exp_val' % source] = bets_exp_val(ro16[ro16_match]['%s_odds' % source], alig_probs)


print("Average vigs:")
for source in sources:
    avg_vig = np.mean([ro16[match]['%s_vig' % source] for match in ro16])
    print("{0}: {1:.2f}%".format(source, 100 * avg_vig))

print("\nRound of 16 matches bets expected values"
      "\nUsing nit odds, Aligulac predictions (based on 1 unit bets):\n")

for match in ro16:
    out_str = fmt_lines_exp_vals([match[0], match[1]], [ro16[match]['%s_odds' % exp_val_src][0], ro16[match]['%s_odds' % exp_val_src][1]],
                                 [ro16[match]['alig_nit_exp_val'][0], ro16[match]['alig_nit_exp_val'][1]])
    print(out_str)
