import requests
from os.path import join
from itertools import combinations, permutations
import random
from numpy import log2

ROOT_URL = 'http://aligulac.com/api/v1/'


class AligulacAPI:
    def __init__(self, api_key, root_url=ROOT_URL):
        self.api_key = api_key
        self.root_url = root_url
        self.default_params = {'apikey': self.api_key}

    def get(self, addnl_url='', addnl_params=None):
        url = join(self.root_url, addnl_url)
        params = self.default_params.copy()
        if addnl_params:
            params.update(addnl_params)
        resp = requests.get(url, params=params)
        return resp

    def resources(self):
        resp = self.get()
        return resp.json()

    def schema(self, endpoint):
        path = '%s/schema/' % endpoint
        resp = self.get(path)
        return resp.json()

    def player(self, filters):
        addnl_params = filters.items()
        resp = self.get('player/', addnl_params)
        return resp.json()

    def player_name_from_id(self, p_id):
        id_fltr = {'id__exact': p_id}
        plyr_resp = self.player(id_fltr)
        return plyr_resp['objects'][0]['tag']

    def predictmatch(self, ida, idb, bo=1):
        url = 'predictmatch/%s,%s/' % (ida, idb)
        addnl_params = {'bo': bo}
        resp = self.get(url, addnl_params)
        return resp.json()

    def predictdual_old(self, ids, bo=1):
        url = 'predictdual/%s,%s,%s,%s/' % tuple(ids)
        addnl_params = {'bo': bo}
        resp = self.get(url, addnl_params)
        return resp.json()

    def best_player_id_by_name(self, name):
        addnl_params = {'tag__exact': name, 'order_by': '-current_rating__rating'}
        resp = self.get('player/', addnl_params)
        jsn = resp.json()
        plyr_id = jsn['objects'][0]['id']
        return plyr_id

    def predictbracket(self, ids, bos=1):
        if log2(len(ids)) % 1 != 0:
            raise Exception('Number of players in a bracket should be a power of 2')
        if type(bos) is int:
            bos = int(log2(len(ids))) * [bos]
        url = 'predictsebracket/%s/' % ','.join(map(str, ids))
        addnl_params = {'bo': bos}
        resp = self.get(url, addnl_params)
        return resp.json()


# class Bracket:
#     def __init__(self, alig_api, p_names=None, p_ids=None):
#         if p_names and not p_ids:
#             for name in p_names:


class Player:
    def __init__(self, alig_api, p_name=None, p_id=None):
        self.alig_api = alig_api
        self.p_name = p_name
        self.p_id = p_id

    def get_name_id(self):
        if not self.p_name and not self.p_id:
            raise Exception("Need either player name or player ID")
        elif self.p_name and not self.p_id:
            self.p_name = self.p_name
            self.p_id = self.alig_api.best_player_id_by_name(self.p_name)
        elif self.p_id and not self.p_name:
            self.p_id = self.p_id
            self.p_name = self.alig_api.player_name_from_id(self.p_id)

    def __str__(self):
        return "%s (ID: %s)" % (self.p_name, self.p_id)


class Match:
    def __init__(self, alig_api, pla, plb, bo=1):
        self.alig_api = alig_api
        self.bo = bo

        if type(pla) is str:
            self.pla = Player(alig_api, p_name=pla)
        elif type(pla) is int:
            self.pla = Player(alig_api, p_id=pla)
        elif type(pla) is Player:
            self.pla = pla
        else:
            raise Exception("Players should be Players, strings, or integers")
        self.pla.get_name_id()

        if type(plb) is str:
            self.plb = Player(alig_api, p_name=plb)
        elif type(plb) is int:
            self.plb = Player(alig_api, p_id=plb)
        elif type(plb) is Player:
            self.plb = plb
        else:
            raise Exception("Players should be strings or integers")
        self.plb.get_name_id()

        self.predicted = False
        self.pred_json = None
        self.proba = None
        self.probb = None
        self.probs_dct = None

    def predict(self):
        if self.predicted:
            print("Match has already been predicted")
        else:
            self.pred_json = self.alig_api.predictmatch(self.pla.p_id, self.plb.p_id, bo=self.bo)
            self.proba = self.pred_json['proba']
            self.probb = self.pred_json['probb']

            self.probs_dct = {self.pla: self.proba,
                              self.plb: self.probb}

            self.predicted = True

    def gen_outcome(self):
        if not self.predicted:
            self.predict()

        if random.random() < self.proba:
            return self.pla, self.plb
        else:
            return self.plb, self.pla

    def __str__(self):
        if self.predicted:
            return "Best of {0} match between {1} (win probability: {2}) and {3} (win probability: {4})".format(self.bo, self.pla, self.proba, self.plb, self.probb)
        else:
            return "Best of {0} match between {1} and {2} (not yet predicted)".format(self.bo, self.pla, self.plb)


class DualGroup:
    def __init__(self, alig_api, plyrs, bo=1, finished=False):
        self.alig_api = alig_api
        self.bo = bo
        self.finished = finished

        if not finished and len(plyrs) != 4:
            raise Exception("Need exactly 4 players for a dual tournament group")
        if finished and len(plyrs) != 2:
            raise Exception("A finished group should have 2 players, in order of their placement")

        if not all([type(plyr) is Player for plyr in plyrs]):
            raise Exception("All players should be instances of Player")
        else:
            self.plyrs = plyrs

        self.predicted = False
        self.pred_json = None
        self.probs_dct = None

        self.pos_matches = {(pla, plb): Match(alig_api, pla, plb, bo=self.bo) for pla, plb in permutations(self.plyrs, 2)}
        self.pos_outcomes = tuple(permutations(self.plyrs, 4))

    def get_names_ids(self):
        for plyr in self.plyrs:
            plyr.get_name_id()

    def simulate(self, n):
        if self.finished:
            return {(self.plyrs[0], self.plyrs[1], None, None): 1}
        else:
            outcomes_percs = {pos_outcome: 0 for pos_outcome in self.pos_outcomes}

            match1 = self.pos_matches[(self.plyrs[0], self.plyrs[1])]
            match2 = self.pos_matches[(self.plyrs[2], self.plyrs[3])]

            for iteration in range(n):
                m1_winner, m1_loser = match1.gen_outcome()
                m2_winner, m2_loser = match2.gen_outcome()

                w_match = self.pos_matches[(m1_winner, m2_winner)]
                l_match = self.pos_matches[(m1_loser, m2_loser)]

                w_winner, w_loser = w_match.gen_outcome()
                l_winner, l_loser = l_match.gen_outcome()

                d_match = self.pos_matches[(w_loser, l_winner)]

                d_winner, d_loser = d_match.gen_outcome()

                grp_outcome = (w_winner, d_winner, d_loser, l_loser)
                outcomes_percs[grp_outcome] += 1 / n

            return outcomes_percs

    # def predict(self):
    #     for pos_match in self.pos_matches.values():
    #         pos_match.predict()
    #
    #     a, b, c, d = tuple(self.plyrs)
    #
    #     p_ab = self.pos_matches[frozenset((a, b))].probs_dct[a]
    #     p_ba = 1 - p_ab
    #     p_ac = self.pos_matches[frozenset((a, c))].probs_dct[a]
    #     p_ca = 1 - p_ac
    #     p_ad = self.pos_matches[frozenset((a, d))].probs_dct[a]
    #     p_da = 1 - p_ad
    #
    #     p_bc = self.pos_matches[frozenset((b, c))].probs_dct[b]
    #     p_cb = 1 - p_bc
    #     p_bd = self.pos_matches[frozenset((b, d))].probs_dct[b]
    #     p_db = 1 - p_bd
    #
    #     p_cd = self.pos_matches[frozenset((c, d))].probs_dct[c]
    #     p_dc = 1 - p_cd
    #
    #     outcomes = dict()
    #
    #     outcomes[(a, b)] = p_ab * (p_cd * p_ac + p_dc * p_ad) * (p_cd * p_bd + p_dc * p_bc) * (p_bc * p_cd + p_bd * p_dc)
    #     outcomes[(b, a)] = p_ba * (p_cd * p_bc + p_dc * p_bd) * (p_cd * p_ad + p_dc * p_ac) * (p_ac * p_cd + p_ad * p_dc)
    #
    #     outcomes[(c, d)] = p_cd * (p_ab * p_ca + p_ba * p_cb) * (p_ab * p_db + p_ba * p_da) * (p_da * p_ab + p_db * p_ba)
    #     outcomes[(d, c)] = p_dc * (p_ab * p_da + p_ba * p_db) * (p_ab * p_cb + p_ba * p_ca) * (p_ca * p_ab + p_cb * p_ba)
    #
    #     outcomes[(a, c)] = p_ab * (p_cd * p_ac * (p_cb * p_bd + p_cd * p_db) + p_dc * p_ad * p_cb * p_cd)
    #     outcomes[(a, d)] = p_ab * (p_dc * p_ad * (p_db * p_bc + p_dc * p_cb) + p_cd * p_ac * p_db * p_dc)
    #
    #     outcomes[(b, c)] = p_ba * (p_cd * p_bc * (p_ca * p_ad + p_cd * p_da) + p_dc * p_bd * p_ca * p_cd)
    #     outcomes[(b, d)] = p_ba * (p_dc * p_bd * (p_da * p_ac + p_dc * p_ca) + p_cd * p_bc * p_da * p_dc)
    #
    #     outcomes[(c, a)] = p_cd * (p_ab * p_ca * (p_ab * p_bd + p_ad * p_db) + p_ba * p_ad * p_ab)
    #     outcomes[(c, b)] = p_cd * (p_ba * p_cb * (p_ba * p_ad + p_bd * p_da) + p_ab * p_bd * p_ba)
    #
    #     outcomes[(d, a)] = p_dc * (p_ab * p_da * (p_ab * p_bc + p_ac * p_cb) + p_ba * p_ac * p_ab)
    #     outcomes[(d, b)] = p_dc * (p_ba * p_db * (p_ba * p_ac + p_bc * p_ca) + p_ab * p_bc * p_ba)
    #
    #     # total = sum(outcomes.values())
    #     # for pair in outcomes:
    #     #     outcomes[pair] /= total
    #     self.probs_dct = outcomes


    def predict_old(self):
        return self.alig_api.predictdual_old([plyr.p_id for plyr in self.plyrs], bo=self.bo)

    def __str__(self):
        return "Dual Tournament group (best of %s matches) with players: %s" % (self.bo, ', '.join([str(plyr) for plyr in self.plyrs]))
