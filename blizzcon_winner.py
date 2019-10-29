from aligulac_api import AligulacAPI, Match, Player, DualGroup
import os
from odds_utils import bets_exp_val, ml_str
import csv
from itertools import permutations


api_key = os.getenv('ALIGULAC_API_KEY', 'API KEY COULD ALSO GO HERE')
alig_api = AligulacAPI(api_key)

inf_name = 'blizzcon_winner_odds.csv'

# grp_assgnmnts = {'A': ['Dark', 'ShoWTimE', 'soO', 'SpeCial'],
grp_assgnmnts = {'A': ['Dark', 'soO'],
                 'B': ['Maru', 'TIME', 'Stats', 'Serral'],
                 'C': ['Classic', 'HeRoMaRinE', 'herO', 'Reynor'],
                 'D': ['Trap', 'Elazer', 'Rogue', 'Neeb']}

n_simulations = 1000000

groups = []
for grp_name, plyrs in sorted(grp_assgnmnts.items()):
    if len(plyrs) == 4:
        grp = DualGroup(alig_api, [Player(alig_api, p_name=p_name) for p_name in plyrs], bo=5)
    elif len(plyrs) == 2:
        grp = DualGroup(alig_api, [Player(alig_api, p_name=p_name) for p_name in plyrs], bo=5, finished=True)
    else:
        raise Exception("Should have either 4 or 2 players in the group")
    grp.get_names_ids()
    groups.append(grp)
    # print(grp)

all_plyrs = sum([grp.plyrs for grp in groups], [])
winners_percs = {plyr: 0 for plyr in all_plyrs}

print("Initializing all possible matches")
all_pos_matches = {(pla, plb): Match(alig_api, pla, plb, bo=5) for pla, plb in permutations(all_plyrs, 2)}

for iteration in range(n_simulations):
    if iteration % 1000 == 0:
        print(iteration)

    grp_outcomes = []
    for grp in groups:
        advanced_frm_grp = [out for out, perc in grp.simulate(1).items() if perc == 1][0][:2]
        grp_outcomes.append(advanced_frm_grp)

    ro8 = [all_pos_matches[(grp_outcomes[0][0], grp_outcomes[1][1])],
           all_pos_matches[(grp_outcomes[2][0], grp_outcomes[3][1])],
           all_pos_matches[(grp_outcomes[3][0], grp_outcomes[0][1])],
           all_pos_matches[(grp_outcomes[1][0], grp_outcomes[2][1])]]
    # print('Ro8:\n' + '\n'.join([str(m) for m in ro8]))

    ro4_plyrs = []
    for match in ro8:
        w, l = match.gen_outcome()
        ro4_plyrs.append(w)

    ro4 = [all_pos_matches[(ro4_plyrs[0], ro4_plyrs[1])],
           all_pos_matches[(ro4_plyrs[2], ro4_plyrs[3])]]
    # print('Ro4:\n' + '\n'.join([str(m) for m in ro4]))

    ro2_plyrs = []
    for match in ro4:
        w, l = match.gen_outcome()
        ro2_plyrs.append(w)
    ro2_match = all_pos_matches[(ro2_plyrs[0], ro2_plyrs[1])]
    # print('Ro2:\n' + str(ro2_match))

    w, l = ro2_match.gen_outcome()
    # print('Winner:\n' + str(w))

    winners_percs[w] += 1 / n_simulations

print('Likelihood of each player winning tournament:\n')
print('\n'.join(['{0}: {1:.4f}'.format(str(plyr), perc) for plyr, perc in sorted(winners_percs.items(), key=lambda kv: kv[1], reverse=True)]) + '\n')


plyrs_odds = []
with open(inf_name, 'r') as inf:
    reader = csv.DictReader(inf)
    for row in reader:
        plyr = [pl for pl in all_plyrs if pl.p_name == row['player']][0]
        odds = row['odds']
        plyrs_odds.append((plyr, odds))

exp_vals = bets_exp_val([int(p_odds) for p, p_odds in plyrs_odds], [winners_percs[p] for p, p_odds in plyrs_odds])

print('Expected value of each bet:\n')
for (p, p_odds), p_ev in zip(plyrs_odds, exp_vals):
    print("{0} ({1}): {2:0.3f}".format(p.p_name, ml_str(int(p_odds)), p_ev))